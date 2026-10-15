"""External time/score supervision around the unchanged official Harbor Codex command."""
import asyncio,hashlib,json,os,shlex,tempfile,time,uuid
from pathlib import Path
from .official_codex_environment import OfficialCodexDockerEnvironment
from .docker_runtime import DockerController,DockerScorer
from .trajectory import TurnOutageTracker,terminal_turn_failure
from .static_native import report_activity
from harbor.environments.base import ExecResult

class ExternalOfficialSupervisor:
    def __init__(self, environment, protocol):
        self.environment=environment
        self.protocol=protocol
        self._controller=None

    async def prepare(self):
        e,p=self.environment,self.protocol
        from .native_audit_tools import verify_installed_tools
        await verify_installed_tools(e)
        wrapper='#!/bin/sh\nexec python3 /tmp/edgebench-adapter/submission_client.py "$@"\n'
        await e.checked('/usr/bin/python3 -I -c '+shlex.quote("from pathlib import Path;p=Path('/usr/local/bin/sforge-submit');assert p.read_text()=="+repr(wrapper)+" and p.stat().st_uid==0 and not p.stat().st_mode&0o022"))
        await e.checked('mkdir -p /tmp/edgebench-adapter /opt/edgebench-runtime /edgebench-ipc; chmod 700 /opt/edgebench-runtime; chown agent:agent /edgebench-ipc; chmod 700 /edgebench-ipc')
        await e.upload_file(Path(__file__).with_name('learning_guardian.py'),'/opt/edgebench-runtime/learning_guardian.py')
        await e.upload_file(Path(__file__).with_name('submission_client.py'),'/tmp/edgebench-adapter/submission_client.py')
        await e.checked('chmod 600 /opt/edgebench-runtime/learning_guardian.py; chmod 644 /tmp/edgebench-adapter/submission_client.py')
        await e.upload_file(Path(p['ipc_host'])/'public.json','/edgebench-ipc/public.json')
        await e.checked('chmod 644 /edgebench-ipc/public.json')
        self._controller=DockerController(e,p['controller_root'],p['ipc_host'],p['artifacts'],
            DockerScorer(p['docker_task_dir'],p['verifier_image'],p['verifier_timeout_sec']),
            interval=p['interval_sec'],cooldown=p['cooldown_sec'],direction=p['score_direction'],
            selection=p['selection'],grading_workers=p.get('grading_workers',3))

    async def run(self, official_command, env, cwd):
        e,p=self.environment,self.protocol
        if cwd not in (None,p['workdir']):raise ValueError('Official command cwd differs from task workdir')
        await self.prepare()
        observer_id=uuid.uuid4().hex
        await report_activity('start',observer_id,e.name)
        e.evidence['observer_task_id']=observer_id;e.save()
        controller=self._controller
        controller.learning_budget_seconds=p['budget_sec']
        controller.start()
        checkpoint=asyncio.create_task(self.checkpoint_loop(e))
        deadline=time.monotonic()+p['budget_sec'];turn=0;status='infrastructure_exception'
        outages=TurnOutageTracker(p.get('runtime_max_outage_sec',600))
        official_command_hash=hashlib.sha256(official_command.encode()).hexdigest()
        controller.event('official_adapter_command_received',adapter='harbor.agents.installed.codex:Codex',command_sha256=official_command_hash)
        try:
            while time.monotonic()<deadline:
                if controller.rejected.is_set():raise RuntimeError('External grading/checkpoint infrastructure rejected the run')
                remaining=deadline-time.monotonic()
                command=official_command if turn==0 or 'codex exec resume ' in official_command else official_command.replace('codex exec ','codex exec resume --last ',1)
                if turn and command==official_command and 'codex exec resume ' not in command:
                    raise RuntimeError('Official command cannot be resumed unambiguously')
                wrapped='set -o pipefail; '+command
                trace='/logs/agent/model-'+str(turn)+'.connect.trace'
                wrapped='LD_LIBRARY_PATH=/opt/edgebench-native-audit/lib /opt/edgebench-native-audit/bin/strace -f -e trace=connect -o '+shlex.quote(trace)+' /bin/bash -c '+shlex.quote(wrapped)
                began=time.monotonic()
                execution=asyncio.create_task(self.launch_owned_turn(e,wrapped,env,turn,remaining))
                if turn==0:
                    await self.synchronize_owned_start(e)
                    deadline=controller.started+p['budget_sec']
                rejection=asyncio.create_task(controller.rejected.wait())
                done,_=await asyncio.wait([execution,rejection],return_when=asyncio.FIRST_COMPLETED)
                if rejection in done and not execution.done():
                    await e.exec('/usr/bin/python3 -I /opt/edgebench-runtime/learning_guardian.py stop',user='root',cwd='/',timeout_sec=15)
                rejection.cancel();await asyncio.gather(rejection,return_exceptions=True)
                result=await execution
                from .storage_safe_evidence import append_host_stream
                append_host_stream(self.environment,Path(p['controller_root']),result.stdout or '')
                controller.event('official_codex_turn_exit',turn=turn,actual_return_code=result.return_code,actual_seconds=time.monotonic()-began,command_sha256=hashlib.sha256(command.encode()).hexdigest())
                stop=await e.exec('test -f /opt/edgebench-runtime/learning-stop.json',user='root',cwd='/',timeout_sec=10)
                if stop.return_code==0:
                    state=await e.exec('cat /opt/edgebench-runtime/learning-stop.json',user='root',cwd='/',timeout_sec=10)
                    if json.loads(state.stdout).get('reason')=='learning_budget_exhausted':
                        status='budget_exhausted';break
                    raise RuntimeError('Learning was stopped before its full formal budget')
                if controller.rejected.is_set():raise RuntimeError('External infrastructure rejected the run')
                events=[]
                for line in (result.stdout or '').splitlines():
                    try:item=json.loads(line)
                    except ValueError:continue
                    if isinstance(item,dict):events.append(item)
                failed=bool(result.return_code) or terminal_turn_failure(result.stdout) or any(x.get('type')=='error' for x in events)
                # Thread/config startup errors may have no turn.failed event.
                # They still count as real outages and receive bounded backoff.
                outage=outages.observe(failed,result.stdout,began,time.monotonic())
                if failed:
                    controller.event('official_codex_runtime_failure',turn=turn,**outage)
                    if outage['persistent']:raise RuntimeError('Native startup/API outage exceeded its infrastructure budget')
                    await asyncio.sleep(min(45*min(outage['consecutive_failures'],3),max(0,deadline-time.monotonic())))
                elif not any(x.get('type')=='turn.completed' for x in events):
                    raise RuntimeError('Official CLI returned without an actual completed model turn')
                turn+=1
            else:status='budget_exhausted'
        finally:
            checkpoint.cancel();await asyncio.gather(checkpoint,return_exceptions=True)
            await self.freeze_owned_learning(e,status)
            await self.checkpoint_sessions(e)
            # Preserve the exact raw streams from every official CLI invocation;
            # the stock adapter's per-call tee otherwise replaces codex.txt.
            # Native streams and sessions are already sealed in root-private host evidence.
            await controller.finish(final=status=='budget_exhausted')
            if controller.rejected.is_set():raise RuntimeError('Final scoring/drain infrastructure rejected the formal run')
        return ExecResult(stdout='',stderr='',return_code=0)

    async def launch_owned_turn(self,environment,cli,env,turn,remaining):
        root='/opt/edgebench-runtime'
        spec={'command':cli,'env':env,'cwd':self.protocol['workdir'],'budget_sec':self.protocol['budget_sec']}
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'turn.json';path.write_text(json.dumps(spec))
            remote=root+'/turn-'+str(turn)+'.json'
            await environment.upload_file(path,remote)
        command='/usr/bin/python3 -I '+root+'/learning_guardian.py launch '+shlex.quote(remote)
        return await environment.exec(command=command,user='root',cwd='/',timeout_sec=int(remaining)+45)

    async def synchronize_owned_start(self,environment):
        import datetime
        began=time.monotonic()
        result=await environment.exec('/usr/bin/python3 -I -c '+shlex.quote(
            "import time;from pathlib import Path;p=Path('/opt/edgebench-runtime/learning-window.json');end=time.monotonic()+10\nwhile not p.exists() and time.monotonic()<end:time.sleep(.01)\nassert p.exists();print(p.read_text())"),user='root',cwd='/',timeout_sec=15)
        if result.return_code:raise RuntimeError('No trusted remote learning START record')
        state=json.loads(result.stdout)
        now=time.monotonic()
        cloud_utc=datetime.datetime.fromisoformat(state['started_utc'])
        age=(datetime.datetime.now(datetime.timezone.utc)-cloud_utc).total_seconds()
        if age<0 or age>now-began+30:raise RuntimeError('Cloud learning clock mapping unavailable')
        self._controller.started=now-age
        self._controller.cloud_learning_started_monotonic=state['started_monotonic']
        self._controller.event('cloud_learning_start_mapping',remote_started_utc=state['started_utc'],remote_started_monotonic=state['started_monotonic'],remote_deadline_monotonic=state['deadline_monotonic'],host_receipt_monotonic=now,host_read_rtt_sec=now-began,host_clock_mapping='UTC mapping; remote monotonic watchdog authoritative')

    async def freeze_owned_learning(self,environment,status):
        root='/opt/edgebench-runtime'
        # Deadline shutdown is performed locally by the already running watchdog,
        # independently of the host API. Early shutdown only applies to explicit
        # probe completion or genuine infrastructure failure.
        if status in ('budget_exhausted',):
            check=await environment.exec('/usr/bin/python3 -I -c '+shlex.quote(
                "import time,json;from pathlib import Path;p=Path('/opt/edgebench-runtime/learning-stop.json');deadline=time.monotonic()+10\nwhile not p.exists() and time.monotonic()<deadline:time.sleep(.05)\nassert p.exists(),'Local deadline watchdog did not confirm learning stop';print(p.read_text())"),user='root',cwd='/',timeout_sec=15)
        else:
            check=await environment.exec('/usr/bin/python3 -I '+root+'/learning_guardian.py stop',user='root',cwd='/',timeout_sec=15)
        if check.return_code:raise RuntimeError('Owned learning freeze failed')
        record=json.loads(check.stdout)
        if record['surviving_learning_processes']:raise RuntimeError('Agent/tool processes survived learning freeze')
        self._controller.trusted_learning_stop_record=record
        folder=Path(self.protocol['controller_root']);folder.mkdir(parents=True,exist_ok=True)
        (folder/'cloud-learning-stop.json').write_text(json.dumps(record,indent=2))
        if record.get('learning_window_sec') is not None and record['reason']=='learning_budget_exhausted':
            if record['actual_all_stop_dispatched_elapsed_sec']-record['learning_window_sec']>1:
                self._controller.capture_failure('learning_deadline_dispatch_late',RuntimeError('Local deadline dispatch exceeded 1s tolerance'))
            self._controller.authoritative_learning_elapsed=float(record['actual_all_stop_dispatched_elapsed_sec'])
            self._controller.confirmed_final_cutoff={'planned_budget_sec':record['learning_window_sec'],'actual_stop_dispatch_elapsed_sec':record['actual_stop_dispatch_elapsed_sec'],'actual_all_stop_dispatched_elapsed_sec':record['actual_all_stop_dispatched_elapsed_sec'],'stop_dispatch_lateness_sec':record['stop_dispatch_lateness_sec'],'surviving_learning_processes':record['surviving_learning_processes'],'validated':record['actual_all_stop_dispatched_elapsed_sec']-record['learning_window_sec']<=1}
        self._controller.event('local_learning_freeze',**record)

    async def checkpoint_sessions(self, environment):
        # Verify any actual CLI or daemon process, rather than trusting a version string.
        expected = self.protocol['codex_static_package']['bin/codex']
        probe = ('import os,json,hashlib,time;from pathlib import Path;rows=[];'
                 '\nfor p in Path("/proc").glob("[0-9]*/exe"):\n'
                 ' try:\n  exe=p.resolve(strict=True)\n  if exe.name!="codex":continue\n'
                 '  sha=hashlib.sha256(exe.read_bytes()).hexdigest()\n'
                 '  assert sha==' + repr(expected) + ',"Actual CLI/daemon hash differs from modified package"\n'
                 '  rows.append({"pid":int(p.parent.name),"exe":str(exe),"sha256":sha})\n'
                 ' except (FileNotFoundError,PermissionError,ProcessLookupError):continue\n'
                 'print(json.dumps({"at":time.time(),"processes":rows}))')
        checked = await environment.exec(command='python3 -c ' + shlex.quote(probe), user='root', cwd='/', timeout_sec=60)
        if checked.return_code:
            raise RuntimeError('Actual CLI/daemon binary identity audit failed')
        folder = Path(self.protocol['controller_root'])
        folder.mkdir(parents=True, exist_ok=True)
        with (folder/'binary-identity.jsonl').open('a') as stream:
            stream.write(checked.stdout.strip() + '\n')
        from .storage_safe_evidence import checkpoint_sessions_to_host
        await checkpoint_sessions_to_host(environment,folder)

    async def checkpoint_loop(self, environment):
        while True:
            await asyncio.sleep(30)
            try:
                from .static_native import report_activity
                if environment.evidence.get('observer_task_id'):
                    await report_activity('heartbeat', environment.evidence['observer_task_id'])
                await self.checkpoint_sessions(environment)
            except Exception as exc:
                self._controller.capture_failure('checkpoint_or_identity_error', exc)
                return


class SupervisedOfficialCodexEnvironment(OfficialCodexDockerEnvironment):
    """Intercept the stock adapter's model command, never its source/agent API."""
    def __init__(self,*args,protocol,**kwargs):
        self.protocol=json.loads(Path(protocol).read_text())
        self._official_command_running=False
        self._official_command_seen=False
        super().__init__(*args,**kwargs)

    async def exec(self,command,*,user=None,cwd=None,env=None,timeout_sec=None,**kwargs):
        is_model=('codex exec ' in command and '--dangerously-bypass-approvals-and-sandbox' in command and '| tee /logs/agent/codex.txt' in command)
        if is_model:
            if self._official_command_running or self._official_command_seen:raise RuntimeError('Duplicate official formal model entry')
            if str(self._resolve_user(user)) not in ('agent','1500'):raise RuntimeError('Official model must run as agent UID1500')
            if '--model gpt-6.1-sol' not in command:raise RuntimeError('Wrong official model command')
            self._official_command_seen=True;self._official_command_running=True
            effective=self._merge_env(env) or {};effective['HOME']='/home/agent'
            try:return await ExternalOfficialSupervisor(self,self.protocol).run(command,effective,cwd)
            finally:self._official_command_running=False
        return await super().exec(command,user=user,cwd=cwd,env=env,timeout_sec=timeout_sec,**kwargs)
