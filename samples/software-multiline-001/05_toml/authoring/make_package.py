from pathlib import Path
import json,tarfile,shutil,hashlib,difflib
R=Path(__file__).resolve().parents[1]
sha='ceac6e4412420d5a5c19e4f7293ad005cf1a31b2'
S=R/'authoring/sources'/f'toml-{sha}'
for p in ['environment','verifier/private','verifier/tests','tests/probe/src','solution','authoring/near-misses','authoring/evidence']:(R/p).mkdir(parents=True,exist_ok=True)
D=R/'authoring/starter'
if D.exists():shutil.rmtree(D)
shutil.copytree(S,D)
changes=[]
def replace(file,start,end,new):
 p=D/file;s=p.read_text();a=s.index(start);b=s.index(end,a)
 original=s[a:b];p.write_text(s[:a]+new+'\n\n'+s[b:]);changes.append({'path':file,'start_marker':start,'end_marker':end,'removed_lines':original.count('\n'),'replacement':new,'original_sha256':hashlib.sha256(original.encode()).hexdigest()})
replace('crates/toml_parser/src/decoder/string.rs','fn escape_seq_char(', '\nfn hexescape(','''fn escape_seq_char(stream: &mut &str, _raw: Raw<'_>, _error: &mut dyn ErrorSink) -> char {
    // Recovery gap: escape identifiers currently survive as literal characters.
    stream.next_token().unwrap_or('\\\\')
}''')
replace('crates/toml_parser/src/decoder/string.rs','fn mlb_escaped_nl(', '\n/// `mlb-unescaped`', '''fn mlb_escaped_nl(stream: &mut &str, _raw: Raw<'_>, _error: &mut dyn ErrorSink) {
    // Recovery gap: consume only the immediate newline, leaving indentation.
    if stream.starts_with("\\r\\n") { *stream = &stream[2..]; }
    else if stream.starts_with('\\n') { *stream = &stream[1..]; }
}''')
replace('crates/toml_edit/src/encode.rs','pub(crate) fn encode_formatted<','\npub(crate) fn encode_array(','''pub(crate) fn encode_formatted<T: ValueRepr>(
    this: &Formatted<T>, buf: &mut dyn Write, _input: Option<&str>,
    _default_decor: (&str, &str),
) -> Result {
    // Recovery gap: canonical value spelling erases raw representation/decor.
    let repr = this.default_repr();
    buf.write_str(repr.as_raw().as_str().unwrap_or(""))
}''')
replace('crates/toml_writer/src/string.rs','\nfn write_toml_value<W:', '\n#[derive(Copy, Clone, Debug)]\nstruct ValueMetrics', '''fn write_toml_value<W: crate::TomlWrite + ?Sized>(
    decoded: &str, _encoding: Option<Encoding>, _newline: bool, writer: &mut W,
) -> core::fmt::Result {
    // Recovery gap: naive quoting loses key/literal/multiline/escape policy.
    write!(writer, "\\\"{decoded}\\\"")
}''')
(R/'authoring/mask-manifest.json').write_text(json.dumps({'commit':sha,'changes':changes},indent=2)+'\n')
patch=''
for file in sorted({c['path'] for c in changes}):
 a=(D/file).read_text().splitlines(True);b=(S/file).read_text().splitlines(True)
 patch+=''.join(difflib.unified_diff(a,b,fromfile='a/'+file,tofile='b/'+file))
(R/'solution/restore.patch').write_text(patch)
# Full workspace including all licenses and original tests; no .git or reference restoration.
with tarfile.open(R/'environment/starter.tar.gz','w:gz') as tf:
 for p in sorted(D.rglob('*')):
  if p.is_file():tf.add(p,arcname='submission/'+p.relative_to(D).as_posix())
with tarfile.open(R/'solution/reference.tar.gz','w:gz') as tf:
 for p in sorted(S.rglob('*')):
  if p.is_file():tf.add(p,arcname='submission/'+p.relative_to(S).as_posix())
# Semantically distinct partial implementations, generated only in private authoring context.
for name,kind in [('unicode-ascii-only','unicode'),('discard-formatting','decor')]:
 n=R/'authoring/near-misses'/name
 if n.exists():shutil.rmtree(n)
 shutil.copytree(S,n)
 if kind=='unicode':
  p=n/'crates/toml_parser/src/decoder/string.rs';s=p.read_text();s=s.replace("'U' => hexescape(stream, 8, raw, error),", "'U' => { let c = hexescape(stream, 8, raw, error); if c.is_ascii() { c } else { '?' } },");p.write_text(s)
 else:
  p=n/'crates/toml_edit/src/encode.rs';s=p.read_text();s=s.replace('    decor.prefix_encode(buf, input, default_decor.0)?;', '// near miss: dropped prefix',1).replace('    decor.suffix_encode(buf, input, default_decor.1)?;', '// near miss: dropped suffix',1);p.write_text(s)
# Probe is trusted evaluation scaffolding, not an alternate TOML implementation.
probe=(R/'authoring/harness/Cargo.toml').read_text()
probe=probe.replace('../sources/toml-'+sha, '/home/workspace/toml-string-recovery/submission')
(R/'tests/probe/Cargo.toml').write_text(probe)
shutil.copyfile(R/'authoring/harness/src/main.rs',R/'tests/probe/src/main.rs')
if (R/'authoring/harness/Cargo.lock').exists():shutil.copyfile(R/'authoring/harness/Cargo.lock',R/'tests/probe/Cargo.lock')
print(json.dumps({'masked_files':len({c['path'] for c in changes}),'removed_lines':sum(c['removed_lines'] for c in changes),'starter_bytes':(R/'environment/starter.tar.gz').stat().st_size}))
