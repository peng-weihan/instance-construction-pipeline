"""Independent workloads and semantic predicates. Never imported by candidates."""
import json

COMMON = r"""
import json
from pathlib import Path
import pytest

def body(*row):
    with Path('body.jsonl').open('a') as f:
        f.write(json.dumps(row)+'\n')
"""
CASES = {
'basic': COMMON + r"""
@pytest.fixture(scope='module')
def base(request):
    body('setup','base')
    request.addfinalizer(lambda:body('end','base'))
    return object()
@pytest.fixture
def consumer(base,request):
    body('setup','consumer')
    assert request.getfixturevalue('base') is base
    assert request.getfixturevalue('base') is base
    request.addfinalizer(lambda:body('end','consumer'))
    return base
def test_a(consumer,request):
    assert request.getfixturevalue('base') is consumer
    assert request.getfixturevalue('base') is consumer
    body('call','a')
def test_b(consumer):
    body('call','b')
""",
'dynamic': COMMON + r"""
@pytest.fixture
def hidden(request):
    body('setup','hidden')
    yield 23
    body('end','hidden')
@pytest.fixture
def caller(request):
    assert request.getfixturevalue('hidden') == 23
    assert request.getfixturevalue('hidden') == 23
    try: request.getfixturevalue('absent')
    except pytest.FixtureLookupError: body('missing')
    return 23
def test_dynamic(caller):
    assert caller==23
""",
'params': COMMON + r"""
class Hostile:
    def __init__(self,value):self.value=value
    def __eq__(self,other):
        body('equal')
        raise ValueError('non-scalar')
    def __repr__(self):
        body('repr')
        raise AssertionError('trace must not format parameter')
P=[Hostile(1),Hostile(2)]
@pytest.fixture(scope='module',params=P,ids=['one','two'])
def base(request):
    body('setup','base',request.param.value)
    yield request.param.value
    body('end','base',request.param.value)
@pytest.fixture(scope='module')
def dependent(base):
    body('setup','dependent',base)
    yield base
    body('end','dependent',base)
def test_a(dependent):body('call',dependent)
def test_b(dependent):body('call',dependent)
""",
'failure': COMMON + r"""
@pytest.fixture(scope='module')
def broken(request):
    body('setup','broken')
    request.addfinalizer(lambda:body('end','broken'))
    raise LookupError('expected')
def test_a(broken):pass
def test_b(broken):pass
@pytest.fixture
def skipped():
    pytest.skip('expected')
def test_c(skipped):pass
@pytest.fixture
def cleanup(request):
    def last():body('fin',3);raise ValueError('three')
    def middle():body('fin',2);raise RuntimeError('two')
    request.addfinalizer(lambda:body('fin',1))
    request.addfinalizer(middle)
    request.addfinalizer(last)
    return 9
def test_d(cleanup):assert cleanup==9
""",
'override': COMMON + r"""
@pytest.fixture
def token():
    body('setup','outer');return 2
class TestOverride:
    @pytest.fixture
    def token(self,token):
        body('setup','inner');return token+3
    def test_value(self,token):assert token==5
""",
'hooks': COMMON + r"""
@pytest.fixture(scope='module')
def base():
    body('setup','base');return 8
@pytest.fixture
def via(base):return base
def test_a(via,request):
    request.config._observer_request=request
    assert request.getfixturevalue('base')==8
def test_b(via):assert via==8
""",
}
OBSERVER = r"""
import json
from pathlib import Path
import pytest
config_ref=None
reentered=False
def pytest_configure(config):
    global config_ref
    config_ref=config
@pytest.hookimpl(optionalhook=True)
def pytest_fixture_trace_event(event):
    global reentered
    before=dict(event)
    try:
        event['seq']=-100
    except TypeError:
        pass
    else:
        Path('mutable').write_text('bad')
    with Path('hook.jsonl').open('a') as f:
        f.write(json.dumps(before,sort_keys=True)+'\n')
    if before['event']=='cache_hit' and not reentered:
        req=getattr(config_ref,'_observer_request',None)
        if req is not None:
            reentered=True
            req.getfixturevalue('base')
@pytest.hookimpl(wrapper=True)
def pytest_fixture_setup(fixturedef,request):
    if fixturedef.argname=='via':
        bodyfile=Path('plugin.jsonl')
        with bodyfile.open('a') as f:f.write('before\n')
    result=yield
    if fixturedef.argname=='via':
        with Path('plugin.jsonl').open('a') as f:f.write('after\n')
    return result
"""

def select(rows,event,name=None):
    definitions={r['fixture']:r for r in rows if r.get('event')=='definition'}
    return [r for r in rows if r.get('event')==event and (name is None or definitions.get(r.get('fixture'),{}).get('name')==name)]

def check(name,runs,spec):
    """Checks consume fixture-body evidence, not reference-generated golden traces."""
    expected_values=spec['expectations']
    def rows(case):return runs[case]['on']['trace']
    def events(case,event,fixture=None):return select(rows(case),event,fixture)
    def ends(case,fixture):return events(case,'setup_end',fixture)
    if name=='schema':
        r=rows('basic')
        return bool(r) and all(x.get('schema')==spec['schema_version'] for x in r) and [x.get('seq') for x in r]==list(range(1,len(r)+1))
    if name=='definitions':
        d=events('override','definition','token')
        return len(d)==2 and len({x['fixture'] for x in d})==2 and len({x['baseid'] for x in d})==2
    if name=='instance_balance':
        for case in runs:
            starts=events(case,'setup_start'); ends_=events(case,'setup_end')
            if not starts or {(x['fixture'],x['instance']) for x in starts}!={(x['fixture'],x['instance']) for x in ends_}:return False
            if len({x['instance'] for x in starts})!=len(starts):return False
        return True
    if name=='deterministic':
        return all(r['on']['trace'] and r['on']['trace']==r['repeat']['trace'] for r in runs.values())
    if name=='static_edges':
        r=rows('basic'); d=events('basic','definition'); ids={x['name']:x['fixture'] for x in d}
        return any(x.get('parent')==ids.get('consumer') and x.get('fixture')==ids.get('base') and x.get('kind')=='static' for x in select(r,'resolve'))
    if name=='dynamic_edges':
        d={x['name']:x['fixture'] for x in events('dynamic','definition')}
        r=events('dynamic','resolve','hidden')
        return len([x for x in r if x.get('parent')==d.get('caller') and x.get('kind')=='dynamic' and x.get('outcome')=='passed'])==2
    if name=='missing_resolution':
        r=[x for x in events('dynamic','resolve') if x.get('requested')=='absent']
        return len(r)==1 and r[0].get('outcome')=='error' and r[0].get('error')=='FixtureLookupError' and r[0].get('fixture') is None
    if name=='override_edges':
        r=events('override','resolve','token')
        return any(x.get('parent') is not None and x['parent']!=x['fixture'] and x.get('kind')=='static' for x in r)
    if name=='item_cache':
        r=events('basic','cache_hit','base')
        return sum(x.get('layer')=='item' for x in r)>=expected_values['minimum_item_cache_hits'] and len(events('basic','setup_start','base'))==1
    if name=='instance_cache':
        return any(x.get('layer')=='instance' and x.get('outcome')=='value' for x in events('basic','cache_hit','base'))
    if name=='cached_exception':
        return len(events('failure','setup_start','broken'))==1 and any(x.get('outcome')=='error' and x.get('layer')=='instance' for x in events('failure','cache_hit','broken'))
    if name=='parameter_identity':
        r=events('params','setup_start','base')
        return len(r)==2 and [x.get('param_index') for x in r]==[0,1] and len({x['instance'] for x in r})==2 and runs['params']['on']['body'].count(['repr'])==0
    if name=='parameter_reason':
        r=events('params','invalidate','base')
        return [x.get('reason') for x in r]==['parameter','scope']
    if name=='dependency_reason':
        r=events('params','invalidate','dependent')
        return len(r)==2 and r[0].get('reason')=='dependency'
    if name=='no_duplicate_finish':
        for case in runs:
            a=events(case,'setup_start');b=events(case,'invalidate');c=events(case,'finalize_start');d=events(case,'finalize_end')
            key=lambda r:sorted((x['fixture'],x['instance']) for x in r)
            if not a or key(a)!=key(b) or key(a)!=key(c) or key(a)!=key(d):return False
        return True
    if name=='finalizer_lifo':
        r=events('failure','finalizer_start','cleanup')
        return [x.get('ordinal') for x in r]==expected_values['cleanup_ordinals'] and [x for x in runs['failure']['on']['body'] if x[0]=='fin']==[['fin',3],['fin',2],['fin',1]]
    if name=='setup_failure':
        r=ends('failure','broken')
        return len(r)==1 and r[0].get('outcome')=='error' and r[0].get('error')=='LookupError'
    if name=='setup_skip':
        r=ends('failure','skipped')
        return len(r)==1 and r[0].get('outcome')=='skipped' and r[0].get('error')=='Skipped'
    if name=='all_finalizer_errors':
        r=events('failure','finalizer_end','cleanup');e=events('failure','finalize_end','cleanup')
        return len(r)==4 and [x.get('error') for x in r]==['ValueError','RuntimeError',None,None] and len(e)==1 and e[0].get('errors')==2
    if name=='failure_cleanup':
        return len(events('failure','invalidate','broken'))==1 and ['end','broken'] in runs['failure']['on']['body']
    if name=='observer_stream':
        r=runs['hooks']['on']
        return bool(r['trace']) and r['trace']==r['hook'] and not r['mutable']
    if name=='observer_reentry':
        r=events('hooks','cache_hit','base')
        return len(r)>=expected_values['minimum_observer_cache_hits'] and runs['hooks']['on']['hook']==rows('hooks')
    if name=='reports':
        expected=expected_values['report_counts']
        for case,n in expected.items():
            r=events(case,'report')
            if len(r)!=n or not all(x.get('when') in ('setup','call','teardown') and x.get('outcome') in ('passed','failed','skipped') and 'test_case.py::' in x.get('nodeid','') for x in r):return False
        return any(x['when']=='teardown' and x['outcome']=='failed' for x in events('failure','report'))
    if name=='noninterference':
        expected=expected_values['exit_codes']
        return all(r['on']['exit']==r['off']['exit']==expected[k] and r['on']['body']==r['off']['body'] and r['on']['plugin']==r['off']['plugin'] and not r['off']['trace'] for k,r in runs.items())
    raise KeyError(name)
