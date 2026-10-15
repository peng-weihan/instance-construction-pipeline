from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
ref=lambda n:{'$ref':'#/components/schemas/'+n}
record={'type':'object','required':['seq','label'],'properties':{'seq':{'type':'integer'},'label':{'type':'string'},'state':{'type':'string','enum':['ready','done']}}}
response={'description':'Incremental records','content':{'application/x-ndjson':{'schema':ref('Event')}}}
paths={}
for name,security in [('secured',None),('anonymous',[]),('optional',[{}, {'bearer':[]}])]:
    op={'operationId':name,'tags':['feed'],'responses':{'200':response,'409':{'description':'Conflict'}}}
    if security is not None:op['security']=security
    if name=='anonymous':
        op['requestBody']={'required':True,'content':{'application/json':{'schema':ref('Filter')},'multipart/form-data':{'schema':ref('Upload')}}}
        paths['/'+name]={'post':op}
    else: paths['/'+name]={'get':op}
paths['/plain']={'get':{'operationId':'plain','tags':['feed'],'security':[], 'responses':{'200':{'description':'ordinary','content':{'application/json':{'schema':ref('Event')}}}}}}
paths['/numbers']={'get':{'operationId':'numbers','tags':['feed'],'responses':{'201':{'description':'primitive records','content':{'application/x-ndjson':{'schema':{'type':'integer'}}}}}}}
spec={'openapi':'3.0.3','info':{'title':'Stream Contract','version':'1.0'},'security':[{'bearer':[]}], 'paths':paths,'components':{'securitySchemes':{'bearer':{'type':'http','scheme':'bearer'}},'schemas':{'Event':record,'Filter':{'type':'object','required':['query'],'properties':{'query':{'type':'string'}}},'Upload':{'type':'object','required':['label','files'],'properties':{'label':{'type':'string'},'files':{'type':'array','items':{'type':'string','format':'binary'}}}}}}}
public=root/'task/environment/public';public.mkdir(exist_ok=True)
(public/'stream-contract.json').write_text(json.dumps(spec,indent=2)+'\n')
(public/'config.json').write_text(json.dumps({'package_name_override':'stream_sdk','project_name_override':'stream-sdk','post_hooks':[]},indent=2)+'\n')
priv=root/'task/verifier/private';priv.mkdir(exist_ok=True)
(priv/'stream-contract.json').write_text(json.dumps(spec,indent=2)+'\n')
(priv/'config.json').write_text((public/'config.json').read_text())
