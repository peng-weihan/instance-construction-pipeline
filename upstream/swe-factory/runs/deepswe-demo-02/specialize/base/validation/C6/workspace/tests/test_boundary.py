from calc import combine
def test_none_value():
    assert combine({"a": 1}, {"a": None}) == {"a": None}
