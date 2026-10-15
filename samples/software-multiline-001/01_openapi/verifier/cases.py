"""Author-created OpenAPI inputs and independent SDK behavior assertions."""
BASE = {"type": "object", "properties": {"id": {"type": "integer"}}, "required": ["id"]}
TAGGED = {"oneOf": [
    {"type": "object", "properties": {"kind": {"const": "cat"}, "lives": {"type": "integer"}}, "required": ["kind", "lives"]},
    {"type": "object", "properties": {"kind": {"const": "dog"}, "bark": {"type": "boolean"}}, "required": ["kind", "bark"]},
]}
SCHEMAS = {
    "nested": {"Base": BASE, "Envelope": {"allOf": [{"allOf": [{"$ref": "#/components/schemas/Base"}, {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}]}], "properties": {"note": {"type": "string"}}}},
    "union": {"Base": BASE, "Envelope": {"type": "object", "properties": {"payload": {"allOf": [{"$ref": "#/components/schemas/Base"}, TAGGED]}}, "required": ["payload"]}},
    "arrays": {"Envelope": {"type": "object", "properties": {"rows": {"type": "array"}, "choice": {"anyOf": [{"type": "array"}, {"type": "string"}]}}, "required": ["rows", "choice"]}},
    "siblings": {"Base": BASE, "Envelope": {"allOf": [{"$ref": "#/components/schemas/Base"}], "properties": {"child": {"$ref": "#/components/schemas/Base"}, "shade": {"type": "string", "default": "blue"}}, "required": ["child"]}},
    "wire": {"Base": BASE, "Envelope": {"allOf": [{"$ref": "#/components/schemas/Base"}, {"type": "object", "properties": {"detail": {"allOf": [BASE, TAGGED]}}, "required": ["detail"]}]}},
    "conflict": {"Envelope": {"allOf": [{"type": "object", "properties": {"id": {"type": "integer"}}}, {"type": "object", "properties": {"id": {"type": "string"}}}]}},
}
ASSERTIONS = {
"nested": '''
obj = Envelope.from_dict({"id": 7, "name": "Ada"})
assert obj.id == 7 and obj.name == "Ada"
assert isinstance(obj.note, Unset)
assert obj.to_dict() == {"id": 7, "name": "Ada"}
try:
    Envelope.from_dict({"id": 7})
except KeyError:
    pass
else:
    raise AssertionError("nested required name lost")
try:
    Envelope.from_dict({"name": "Ada"})
except KeyError:
    pass
else:
    raise AssertionError("inherited required id lost")
obj.note = "hi"
assert obj.to_dict()["note"] == "hi"
''',
"union": '''
for data, field, value in [({"kind":"cat","lives":9,"id":3}, "lives", 9), ({"kind":"dog","bark":True,"id":4}, "bark", True)]:
    obj = Envelope.from_dict({"payload": data})
    assert not isinstance(obj.payload, dict)
    assert obj.payload.id == data["id"] and getattr(obj.payload, field) == value
    assert obj.payload.kind == data["kind"]
    assert obj.to_dict() == {"payload": data}
''',
"arrays": '''
for choice in [[1, None, {"x": [False]}], "literal"]:
    data = {"rows": [1, None, {"a": [True, "s"]}], "choice": choice}
    obj = Envelope.from_dict(data)
    assert obj.rows == data["rows"] and obj.choice == choice
    assert obj.to_dict() == data
''',
"siblings": '''
obj = Envelope.from_dict({"id":2,"child":{"id":5}})
assert obj.id == 2 and obj.child.id == 5
# Missing wire values stay UNSET; constructor defaults are an SDK annotation.
assert isinstance(obj.shade, Unset)
assert Envelope(id=2, child=obj.child).shade == "blue"
obj.shade = "red"
assert obj.to_dict() == {"id":2,"child":{"id":5},"shade":"red"}
''',
"wire": '''
import asyncio, json, httpx
from pilot_client import Client
from pilot_client.api.default import echo
payload = {"id":17,"detail":{"id":21,"kind":"dog","bark":True}}
obj = Envelope.from_dict(payload)
assert obj.id == 17 and obj.detail.id == 21 and obj.detail.bark is True
seen = []
def transport(request):
    assert request.method == "POST" and request.url.path == "/echo"
    assert json.loads(request.content) == payload
    assert request.headers["content-type"] == "application/json"
    seen.append(1)
    return httpx.Response(200, json=payload)
client = Client(base_url="http://example.invalid")
client.set_httpx_client(httpx.Client(base_url=client._base_url, transport=httpx.MockTransport(transport)))
result = echo.sync(client=client, body=obj)
assert result.id == 17 and result.detail.id == 21 and result.detail.bark is True
async def run():
    async with httpx.AsyncClient(base_url=client._base_url, transport=httpx.MockTransport(transport)) as ac:
        client.set_async_httpx_client(ac)
        result = await echo.asyncio(client=client, body=obj)
        assert result.detail.kind == "dog" and result.detail.bark is True
asyncio.run(run())
assert len(seen) == 2
''',
}

def document(name):
    schema = {"$ref": "#/components/schemas/Envelope"}
    return {"openapi": "3.1.1", "info": {"title": "Pilot", "version": "1.0"},
            "paths": {"/echo": {"post": {"operationId": "echo", "requestBody": {"required": True, "content": {"application/json": {"schema": schema}}},
             "responses": {"200": {"description": "echo", "content": {"application/json": {"schema": schema}}}}}}},
            "components": {"schemas": SCHEMAS[name]}}
