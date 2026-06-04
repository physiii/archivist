import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_search_module():
    root_str = str(REPO_ROOT)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    name = "archivist_search_retrieval_expansion_test"
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / "search.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)  # type: ignore
    return module


def test_sparse_bm25_text_failure_falls_back_to_lexical_query(monkeypatch):
    search = _load_search_module()
    captured = {}

    monkeypatch.setattr(search, "_get_milvus_connection", lambda host: "alias")
    monkeypatch.setattr(search, "_release_milvus_connection", lambda alias: None)
    monkeypatch.setattr(search, "_ensure_collection_loaded", lambda *a, **k: "loaded")
    monkeypatch.setattr(search.utility, "has_collection", lambda *a, **k: True)

    class _Field:
        def __init__(self, name):
            self.name = name

    class _Schema:
        fields = [
            _Field("id"),
            _Field("text"),
            _Field("sparse"),
            _Field("hash"),
            _Field("embedding_model"),
            _Field("creation_date"),
            _Field("path"),
            _Field("source_id"),
            _Field("filehash"),
            _Field("t_start_ms"),
            _Field("t_end_ms"),
            _Field("chunk_duration_s"),
            _Field("level"),
            _Field("parent_id"),
            _Field("doc_type"),
            _Field("source_type"),
            _Field("topic_label"),
            _Field("language"),
            _Field("tags"),
        ]

    class _Collection:
        schema = _Schema()
        num_entities = 1
        indexes = []

        def __init__(self, *args, **kwargs):
            pass

        def search(self, **kwargs):
            captured["search_data"] = kwargs["data"]
            captured["search_param"] = kwargs["param"]
            raise RuntimeError("`search_data` value ['bio computing architecture'] is illegal")

        def query(self, **kwargs):
            captured.setdefault("query_exprs", []).append(kwargs["expr"])
            return [
                {
                    "id": 42,
                    "text": "Different compute architecture and structure for a semantic space.",
                    "hash": "parent-hash",
                    "embedding_model": "local_model",
                    "creation_date": 1,
                    "path": "/media/mass/Documents/example.vtt",
                    "source_id": "/media/mass/Documents/example.vtt",
                    "filehash": "file-hash",
                    "t_start_ms": 1000,
                    "t_end_ms": 61000,
                    "chunk_duration_s": 60,
                    "level": 1,
                    "parent_id": "",
                    "doc_type": "transcript_vtt",
                    "source_type": "transcript",
                    "topic_label": "",
                    "language": "",
                    "tags": "level_1,duration_60s",
                }
            ]

    monkeypatch.setattr(search, "Collection", _Collection)

    results = search.search_vectorstore(
        "bio computing architecture",
        collection_name="transcripts",
        mode="bm25",
        limit=1,
    )

    assert captured["search_data"] == ["bio computing architecture"]
    assert captured["search_param"]["metric_type"] == "BM25"
    assert "architecture" in captured["query_exprs"][0]
    assert "compute" in captured["query_exprs"][0]
    assert results[0]["text"].startswith("Different compute architecture")
    assert results[0]["retrieval_mode"] == "lexical_fallback"
    assert results[0]["distance"] > 0


def test_transcript_short_hit_expands_to_parent_window():
    search = _load_search_module()
    captured = {}
    child = {
        "id": "child-row",
        "text": "Different compute architecture.",
        "hash": "child-hash",
        "embedding_model": "local_model",
        "creation_date": "1970-01-01T00:00:01",
        "filehash": "file-hash",
        "path": "/media/mass/Documents/example.vtt",
        "source_id": "/media/mass/Documents/example.vtt",
        "tags": "level_1,duration_60s",
        "chunk_duration_s": 60,
        "level": 1,
        "t_start_ms": 1000,
        "t_end_ms": 61000,
        "parent_id": "parent-chunk-id",
        "doc_type": "transcript_vtt",
        "source_type": "transcript",
        "topic_label": "",
        "language": "",
        "distance": 0.05,
    }

    class _Collection:
        def query(self, **kwargs):
            captured["expr"] = kwargs["expr"]
            return [
                {
                    "id": 99,
                    "text": (
                        "Longer conversation window about back propagation, a different "
                        "compute architecture, semantic space, Euclidean relationships, "
                        "and geometrically defined relationships."
                    ),
                    "hash": "parent-hash",
                    "embedding_model": "local_model",
                    "creation_date": 1,
                    "path": "/media/mass/Documents/example.vtt",
                    "source_id": "/media/mass/Documents/example.vtt",
                    "filehash": "file-hash",
                    "t_start_ms": 0,
                    "t_end_ms": 3600000,
                    "chunk_duration_s": 3600,
                    "level": 2,
                    "parent_id": "",
                    "doc_type": "transcript_vtt",
                    "source_type": "transcript",
                    "topic_label": "",
                    "language": "",
                    "tags": "level_2,duration_3600s",
                }
            ]

    expanded = search._expand_transcript_context_results(
        _Collection(),
        [child],
        "bio computing architecture",
        [
            "id",
            "text",
            "hash",
            "embedding_model",
            "creation_date",
            "path",
            "source_id",
            "filehash",
            "t_start_ms",
            "t_end_ms",
            "chunk_duration_s",
            "level",
            "parent_id",
            "doc_type",
            "source_type",
            "topic_label",
            "language",
            "tags",
        ],
        None,
        limit=1,
        prefers_lower=True,
    )

    assert "level == 2" in captured["expr"]
    assert expanded[0]["id"] == "child-row"
    assert expanded[0]["context_id"] == 99
    assert expanded[0]["context_expanded"] is True
    assert expanded[0]["matched_text"] == "Different compute architecture."
    assert "semantic space" in expanded[0]["text"]
    assert expanded[0]["level"] == 2
