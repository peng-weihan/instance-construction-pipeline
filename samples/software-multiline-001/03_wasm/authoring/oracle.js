// Independent V8 WebAssembly oracle, authoring only. Not copied to work image.
const fs = require('fs');
for (const line of fs.readFileSync(0,'utf8').trim().split('\n')) {
  try {
    const req=JSON.parse(line); let mod;
    try {mod=new WebAssembly.Module(Buffer.from(req.module,'hex'));}
    catch(e) {console.log(JSON.stringify({error:'invalid'}));continue;}
    let instance;
    try {instance=new WebAssembly.Instance(mod,{});}
    catch(e) {console.log(JSON.stringify({error:'trap'}));continue;}
    const results=[];
    for (const call of req.calls||[]) {
      try {let value=instance.exports[call.export](...(call.args||[]));results.push(value===undefined?null:value);}
      catch(e) {results.push({trap:true});}
    }
    const memory=(req.memory||[]).map(x=>Buffer.from(instance.exports.memory.buffer).subarray(x.offset,x.offset+x.length).toString('hex'));
    console.log(JSON.stringify({results,memory}));
  } catch(e) {console.error(String(e));process.exitCode=2;}
}
