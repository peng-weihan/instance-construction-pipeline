from pathlib import Path
p=Path(__file__).resolve().parents[1]/'task/solution/reference/openapi_python_client/templates/endpoint_macros.py.jinja'
s=p.read_text().replace('{% elif endpoint.bodies | length > 1 %}\nbody:', '{% elif endpoint.bodies | length > 1 %}\n{% set body_required = endpoint.bodies | map(attribute="prop.required") | min %}\nbody:').replace('{%- for body in endpoint.bodies -%}{% set body_required = body_required and body.prop.required %}','{%- for body in endpoint.bodies -%}')
p.write_text(s)
# Required body detection is a real existing multi-media bug exposed by this streaming POST.
p=p.parent/'endpoint_module.py.jinja';p.write_text(p.read_text().replace('from ...types import Response, UNSET','from ...types import Response, UNSET, Unset'))
