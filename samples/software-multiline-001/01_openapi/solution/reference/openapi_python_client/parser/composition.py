"""Lower the supported composition profile before the existing typed parser.

This is SDK lowering, not a general JSON Schema validator. In particular, we
preserve annotations but never populate missing JSON instance values.
"""
from copy import deepcopy
from typing import Any


class CompositionError(ValueError):
    pass


def normalize_document(document: dict[str, Any]) -> dict[str, Any]:
    document = deepcopy(document)
    components = document.get("components", {}).get("schemas", {})

    def resolve(schema: dict[str, Any], path: str, stack: tuple[str, ...]) -> dict[str, Any]:
        ref = schema.get("$ref")
        if ref is None:
            return schema
        if not ref.startswith("#/components/schemas/"):
            raise CompositionError(f"{path}: only local schema references are supported in intersections")
        if ref in stack:
            raise CompositionError(f"{path}: cyclic allOf reference {ref}")
        name = ref.removeprefix("#/components/schemas/").replace("~1", "/").replace("~0", "~")
        if name not in components:
            raise CompositionError(f"{path}: unresolved reference {ref}")
        base = resolve(deepcopy(components[name]), path, (*stack, ref))
        siblings = {k: v for k, v in schema.items() if k != "$ref"}
        return merge(base, siblings, path, (*stack, ref)) if siblings else base

    def merge(a: dict[str, Any], b: dict[str, Any], path: str, stack: tuple[str, ...]) -> dict[str, Any]:
        a, b = resolve(a, path, stack), resolve(b, path, stack)
        if a.get("allOf"):
            a = lower(a, path, stack)
        if b.get("allOf"):
            b = lower(b, path, stack)
        # Distribute intersections over disjoint object variants. Keep branch
        # ordering and names; the existing parser owns generated class naming.
        for left, right in ((a, b), (b, a)):
            operator = "oneOf" if left.get("oneOf") else "anyOf" if left.get("anyOf") else None
            if operator:
                common = {k: v for k, v in left.items() if k != operator}
                return {operator: [merge(merge(common, right, path, stack), branch, path, stack)
                                   for branch in left[operator]]}
        result = deepcopy(a)
        for key, value in b.items():
            if key == "properties":
                props = result.setdefault(key, {})
                for name, prop in value.items():
                    props[name] = merge(props[name], prop, f"{path}/properties/{name}", stack) if name in props else deepcopy(prop)
            elif key == "required":
                result[key] = list(dict.fromkeys([*result.get(key, []), *value]))
            elif key == "type" and key in result and result[key] != value:
                # JSON Schema integer is a subset of number.
                if {result[key], value} == {"integer", "number"}:
                    result[key] = "integer"
                else:
                    raise CompositionError(f"{path}: incompatible allOf types {result[key]!r} and {value!r}")
            elif key == "enum" and key in result:
                result[key] = [v for v in result[key] if v in value]
                if not result[key]:
                    raise CompositionError(f"{path}: empty enum intersection")
            elif key in ("title", "description", "default", "example", "examples"):
                result[key] = deepcopy(value)
            elif key not in result or result[key] == value:
                result[key] = deepcopy(value)
            else:
                raise CompositionError(f"{path}: unsupported conflicting allOf keyword {key}")
        return result

    def lower(schema: dict[str, Any], path: str, stack: tuple[str, ...] = ()) -> dict[str, Any]:
        schema = deepcopy(schema)
        if "allOf" in schema:
            branches = schema.pop("allOf")
            acc: dict[str, Any] = {}
            for index, branch in enumerate(branches):
                acc = merge(acc, lower(resolve(branch, f"{path}/allOf/{index}", stack), path, stack), path, stack)
            schema = merge(acc, schema, path, stack)
        if schema.get("type") == "array" and "items" not in schema and "prefixItems" not in schema:
            schema["items"] = {}
        for key in ("properties", "$defs"):
            if key in schema:
                schema[key] = {name: lower(sub, f"{path}/{key}/{name}", stack) for name, sub in schema[key].items()}
        for key in ("oneOf", "anyOf", "prefixItems"):
            if key in schema:
                schema[key] = [lower(sub, f"{path}/{key}/{i}", stack) for i, sub in enumerate(schema[key])]
        for key in ("items", "additionalProperties"):
            if isinstance(schema.get(key), dict):
                schema[key] = lower(schema[key], f"{path}/{key}", stack)
        return schema

    # Walk OpenAPI containers, then switch to the schema vocabulary. Do not
    # traverse examples/defaults as if they contained JSON Schemas.
    def containers(value: Any, path: str = "#") -> Any:
        if isinstance(value, list):
            return [containers(v, f"{path}/{i}") for i, v in enumerate(value)]
        if not isinstance(value, dict):
            return value
        return {key: lower(v, f"{path}/{key}") if key == "schema" and isinstance(v, dict)
                else v if key in ("example", "examples", "default")
                else containers(v, f"{path}/{key}") for key, v in value.items()}

    document = containers(document)
    if components:
        document["components"]["schemas"] = {
            name: lower(schema, f"#/components/schemas/{name}") for name, schema in components.items()
        }
    return document
