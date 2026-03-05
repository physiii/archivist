import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from movietime_items import _build_filter_expr, _normalized_record, _to_tags


def test_to_tags_handles_json_and_list():
    assert _to_tags('["Genre:Drama","genre:drama","Kind:movie"]') == ["genre:drama", "kind:movie"]
    assert _to_tags(["A", "a", "", None, "B"]) == ["a", "b"]
    assert _to_tags(None) == []


def test_build_filter_expr_includes_kind_year_and_tags():
    expr = _build_filter_expr(
        {
            "kind": "movie",
            "yearMin": 1990,
            "yearMax": 2000,
            "tagsAll": ["genre:drama", "kind:movie"],
            "tagsAny": ["director:stanley kubrick", "actor:malcolm mcdowell"],
        }
    )
    assert expr is not None
    assert 'kind == "movie"' in expr
    assert "year >= 1990" in expr
    assert "year <= 2000" in expr
    assert "tags like" in expr
    assert " and " in expr
    assert " or " in expr


def test_normalized_record_defaults_and_hash():
    rec = _normalized_record(
        {
            "source_id": "movietime:item:42",
            "item_id": 42,
            "kind": "movie",
            "chunk_tag": "summary",
            "title": "A Clockwork Orange",
            "text": "An ultra-violent youth in a dystopian society.",
            "tags": ["genre:crime", "genre:sci-fi"],
        },
        now_ts=1700000000,
    )
    assert rec["source_id"] == "movietime:item:42"
    assert rec["item_id"] == 42
    assert rec["chunk_tag"] == "summary"
    assert rec["hash"]
    parsed_tags = json.loads(rec["tags"])
    assert "genre:crime" in parsed_tags
