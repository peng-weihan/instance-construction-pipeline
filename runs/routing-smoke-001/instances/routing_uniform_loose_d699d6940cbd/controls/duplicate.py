import json,sys
c=json.load(sys.stdin)
r=[[x["id"]] for x in c["customers"]]
r.append(r[0])
print(json.dumps({"routes":r}))
