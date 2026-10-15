import json,sys
c=json.load(sys.stdin)
print(json.dumps({"routes":[[x["id"]] for x in c["customers"][:-1]]}))
