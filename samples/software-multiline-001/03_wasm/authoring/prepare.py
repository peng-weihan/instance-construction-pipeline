#!/usr/bin/env python3
"""Pinned author-only preparation. Default is entirely offline and checks bundles."""
import pathlib,hashlib,tarfile,subprocess,sys,shutil,argparse,platform,os,urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1];WASM=ROOT.name=='03_wasm'
SOURCES={
 'wasm':[('spec.tar.gz','2f0b2e82aaa5da1bc8ab4def6f091647a8355ba0961b54265dc071f698d81a34','https://codeload.github.com/WebAssembly/spec/tar.gz/d910f03bd6d6477656fc5070b5098e8f909305d3')],
 'jq':[('jq.tar.gz','eeef5d733152158e735a3c2024bd0d74c5c8a55696e5ee71cfd31a46381f709d','https://codeload.github.com/jqlang/jq/tar.gz/71c2ab509a8628dbbad4bc7b3f98a64aa90d3297'),('jq-1.7.1-release.tar.gz','478c9ca129fd2e3443fe27314b455e211e0d8c60bc8ff7df703873deeee580c2','https://github.com/jqlang/jq/releases/download/jq-1.7.1/jq-1.7.1.tar.gz')]
}
p=argparse.ArgumentParser();p.add_argument('--fetch-missing',action='store_true');p.add_argument('--regenerate',action='store_true');p.add_argument('--build-reference',action='store_true');p.add_argument('--fetch-node',action='store_true');a=p.parse_args()
for name,digest,url in SOURCES['wasm' if WASM else 'jq']:
    archive=ROOT/'authoring/sources'/name
    if not archive.exists():
        if not a.fetch_missing:raise RuntimeError('missing bundled source '+str(archive))
        urllib.request.urlretrieve(url,archive)
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==digest,name
    with tarfile.open(archive) as t:
        for member in t.getmembers():
            pp=pathlib.PurePosixPath(member.name)
            if pp.is_absolute() or '..' in pp.parts or member.issym() or member.islnk():
                # Official archives contain some internal symlinks; do not silently expand them.
                if not (ROOT/'authoring/sources'/pp.parts[0]).exists():raise RuntimeError('archive links require audited extraction: '+member.name)
        top=t.getmembers()[0].name.split('/')[0]
        if not (ROOT/'authoring/sources'/top).exists():t.extractall(ROOT/'authoring/sources',filter='data')
if WASM:
    source=ROOT/'authoring/sources/spec-d910f03bd6d6477656fc5070b5098e8f909305d3'
    shutil.copytree(source/'document/core',ROOT/'environment/specification/core',dirs_exist_ok=True)
    shutil.copy2(source/'document/core/LICENSE',ROOT/'environment/specification/LICENSE')
    shutil.copy2(source/'test/LICENSE',ROOT/'authoring/UPSTREAM-TEST-LICENSE')
    if a.regenerate:
        tools=ROOT/'authoring/tools';py=tools/'bin/python'
        if not py.exists():subprocess.run([sys.executable,'-m','venv',str(tools)],check=True)
        subprocess.run([str(py),'-m','pip','install','--no-index','--find-links',str(ROOT/'authoring/wheels'),'--require-hashes','-r',str(ROOT/'authoring/requirements-lock.txt')],check=True)
        env=os.environ.copy()
        if a.fetch_node:
            system='darwin' if sys.platform=='darwin' else 'linux';machine='arm64' if platform.machine() in ('arm64','aarch64') else 'x64';name=f'node-v24.13.1-{system}-{machine}.tar.gz'
            sums={line.split()[1]:line.split()[0] for line in (ROOT/'authoring/node-v24.13.1-SHASUMS256.txt').read_text().splitlines()}
            archive=ROOT/'authoring/sources'/name
            if not archive.exists():urllib.request.urlretrieve('https://nodejs.org/dist/v24.13.1/'+name,archive)
            assert hashlib.sha256(archive.read_bytes()).hexdigest()==sums[name]
            with tarfile.open(archive) as t:t.extractall(ROOT/'authoring/sources',filter='data')
            env['PATH']=str(ROOT/'authoring/sources'/name[:-7]/'bin')+os.pathsep+env.get('PATH','')
        assert subprocess.check_output(['node','--version'],env=env,text=True).strip()=='v24.13.1'
        subprocess.run([str(py),str(ROOT/'authoring/generate_cases.py')],env=env,check=True)
else:
    source=ROOT/'authoring/sources/jq-1.7.1'
    (ROOT/'environment/manual').mkdir(exist_ok=True)
    shutil.copy2(source/'docs/content/manual/v1.7/manual.yml',ROOT/'environment/manual/manual.yml')
    shutil.copy2(source/'COPYING',ROOT/'environment/manual/COPYING')
    shutil.copy2(source/'COPYING',ROOT/'solution/COPYING')
    if a.build_reference:
        build=ROOT/'authoring/build';build.mkdir(exist_ok=True)
        for name,cmd in [('configure',[str(source/'configure'),'--disable-docs','--disable-maintainer-mode','--disable-shared','--enable-static','--without-oniguruma']),('make',['make','-j2'])]:
            with (build/(name+'.log')).open('w') as log:subprocess.run(cmd,cwd=build,stdout=log,stderr=subprocess.STDOUT,check=True)
    if a.regenerate:subprocess.run([sys.executable,str(ROOT/'authoring/generate_cases.py')],check=True)
raw=(ROOT/'verifier/private/cases.json').read_bytes();assert hashlib.sha256(raw).hexdigest()==(ROOT/'verifier/private/cases.sha256').read_text().strip()
assert (ROOT/'tests/grader.py').read_bytes()==(ROOT/'verifier/tests/grader.py').read_bytes()
print('bundled source hashes, frozen fixture hash and authoritative grader copies: verified; no container was run')
