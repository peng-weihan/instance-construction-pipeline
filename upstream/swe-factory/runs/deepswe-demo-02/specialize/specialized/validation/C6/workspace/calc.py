def combine(parent, child):
    return {**parent, **child}

def plain(value):
    return dict(value)

def merge_many(*layers):
    result = {}
    for layer in layers:
        result.update(layer)
    return result
