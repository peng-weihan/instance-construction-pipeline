import json, sys
case = json.load(sys.stdin)
print(json.dumps({"routes": [[c["id"]] for c in case["customers"]]}))
