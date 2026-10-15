from calc import combine
def test_parent():
    assert combine({"a": 1}, {}) == {"a": 1}
def test_child():
    assert combine({}, {"b": 2}) == {"b": 2}
def test_override():
    assert combine({"a": 1, "b": 2}, {"a": 3}) == {"a": 3, "b": 2}
def test_unicode():
    assert combine({"名字": "甲"}, {"名字": "乙"}) == {"名字": "乙"}
