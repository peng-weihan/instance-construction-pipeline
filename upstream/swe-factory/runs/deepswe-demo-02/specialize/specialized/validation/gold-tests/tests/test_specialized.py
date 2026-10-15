from calc import merge_many
def test_one_layer():
    assert merge_many({"a": 1}) == {"a": 1}
def test_three_layers():
    assert merge_many({"a": 1}, {"b": 2}, {"a": 3}) == {"a": 3, "b": 2}
def test_empty_layer():
    assert merge_many({}, {"b": 2}, {}) == {"b": 2}
