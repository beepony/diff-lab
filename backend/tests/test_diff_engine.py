from diff_engine import diff


def test_find_diff_matches_duplicate_values_by_occurrence():
    result = diff("x\nx", "x", "find_diff", {"skip_empty": True})

    assert result["summary"].items() >= {
        "match": 1,
        "diff_a": 1,
        "diff_b": 0,
        "intersect": 0,
        "total": 2,
    }.items()
    assert [row["status"] for row in result["rows"]] == ["match", "diff_a"]


def test_vlookup_treats_empty_string_as_a_match_when_not_skipped():
    result = diff("\n", "\n", "vlookup", {"skip_empty": False})

    assert result["rows"] == [{"a": "", "b": "", "status": "match"}]
    assert result["summary"]["match"] == 1


def test_intersect_is_stable_and_uses_a_column_order():
    result = diff("b\na\nb", "a\nb", "intersect", {"skip_empty": True})

    assert result["rows"] == [
        {"a": "b", "b": "b", "status": "intersect"},
        {"a": "a", "b": "a", "status": "intersect"},
    ]
