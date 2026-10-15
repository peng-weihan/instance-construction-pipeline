def combine(parent, child):
    return {**parent, **child}

def plain(value):
    return dict(value)

def merge_many(*layers):
    return {}
