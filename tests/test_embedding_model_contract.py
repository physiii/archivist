import importlib
import importlib.util
import sys
import types
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_module(name: str, relative_path: str):
    root_str = str(REPO_ROOT)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / relative_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)  # type: ignore
    return module


def test_openai_embedding_dimensions_are_registered():
    utils = _load_module("archivist_utils_test", "utils.py")
    assert utils.EMBEDDING_DIMENSIONS["text-embedding-3-small"] == 1536
    assert utils.EMBEDDING_DIMENSIONS["text-embedding-3-large"] == 3072


def test_search_vectorstore_uses_explicit_embedding_model(monkeypatch):
    utils = _load_module("utils", "utils.py")
    search = _load_module("archivist_search_test", "search.py")
    captured = {"model": None}

    monkeypatch.setattr(search.connections, "connect", lambda *a, **k: None)
    monkeypatch.setattr(search.connections, "disconnect", lambda *a, **k: None)
    monkeypatch.setattr(search.utility, "has_collection", lambda *a, **k: True)

    class _Field:
        def __init__(self, name, params=None):
            self.name = name
            self.params = params or {}

    class _Schema:
        fields = [_Field("vector", {"dim": 3})]

    class _Hit:
        id = "1"
        distance = 0.01

        def get(self, key):
            values = {
                "text": "Momentum breakout setup with confirmation and risk defined.",
                "hash": "abc",
                "embedding_model": "text-embedding-3-small",
                "creation_date": 1,
                "path": "/tmp/doc.txt",
            }
            return values.get(key)

    class _Collection:
        schema = _Schema()
        num_entities = 1
        indexes = []

        def __init__(self, *args, **kwargs):
            pass

        def load(self):
            return None

        def search(self, **kwargs):
            return [[_Hit()]]

    def _fake_embed(texts, model, **kwargs):
        captured["model"] = model
        return [[0.1, 0.2, 0.3] for _ in texts]

    monkeypatch.setattr(search, "Collection", _Collection)
    monkeypatch.setattr(search, "embed_text_to_vector", _fake_embed)
    monkeypatch.setattr(search, "validate_embeddings", lambda vectors, dim: vectors)

    results = search.search_vectorstore(
        "btc breakout",
        collection_name="gobotgo_lessons_execution",
        embedding_model="text-embedding-3-small",
    )

    assert captured["model"] == "text-embedding-3-small"
    assert results and results[0]["embedding_model"] == "text-embedding-3-small"


def test_vectorstore_search_endpoint_threads_model(monkeypatch):
    _load_module("utils", "utils.py")
    _load_module("search", "search.py")

    load_stub = types.ModuleType("load")
    load_stub.load_to_vectorstore = lambda *a, **k: None
    load_stub.load_text_to_vectorstore = lambda *a, **k: {"ok": True}
    load_stub.clear_vectorstore_collection = lambda *a, **k: {"ok": True}
    sys.modules["load"] = load_stub

    backups_stub = types.ModuleType("backups_service")
    backups_stub.BACKUP_ROOT = "/tmp"
    backups_stub.add_backup_target = lambda *a, **k: None
    backups_stub.delete_backup_target = lambda *a, **k: None
    backups_stub.get_backup_overview = lambda *a, **k: {}
    backups_stub.get_run_logs = lambda *a, **k: []
    backups_stub.list_backup_targets = lambda *a, **k: []
    backups_stub.start_backup = lambda *a, **k: None
    backups_stub.start_scheduler_best_effort = lambda *a, **k: None
    backups_stub.start_target_backup = lambda *a, **k: None
    backups_stub.stop_backup = lambda *a, **k: None
    backups_stub.update_backup_target = lambda *a, **k: None
    backups_stub.update_schedule = lambda *a, **k: None
    sys.modules["backups_service"] = backups_stub

    indexing_stub = types.ModuleType("indexing_service")
    indexing_stub.add_indexing_target = lambda *a, **k: None
    indexing_stub.delete_indexing_target = lambda *a, **k: None
    indexing_stub.get_indexing_overview = lambda *a, **k: {}
    indexing_stub.get_indexing_run_logs = lambda *a, **k: []
    indexing_stub.list_indexing_targets = lambda *a, **k: []
    indexing_stub.scan_indexing_target = lambda *a, **k: {}
    indexing_stub.start_indexing = lambda *a, **k: None
    indexing_stub.start_scheduler_best_effort = lambda *a, **k: None
    indexing_stub.start_target_indexing = lambda *a, **k: None
    indexing_stub.stop_indexing = lambda *a, **k: None
    indexing_stub.update_indexing_target = lambda *a, **k: None
    sys.modules["indexing_service"] = indexing_stub

    movietime_stub = types.ModuleType("movietime_items")
    movietime_stub.search_movietime_items = lambda *a, **k: []
    movietime_stub.upsert_movietime_items = lambda *a, **k: {"ok": True}
    sys.modules["movietime_items"] = movietime_stub

    main = _load_module("archivist_main_test", "main.py")
    captured = {}

    def _fake_search_vectorstore(query, **kwargs):
        captured["query"] = query
        captured.update(kwargs)
        return [{"id": "1", "text": "setup", "distance": 0.1}]

    monkeypatch.setattr(main, "search_vectorstore", _fake_search_vectorstore)
    client = main.app.test_client()

    resp = client.post(
        "/vectorstore",
        json={
            "type": "search",
            "query": "risk-on breakout",
            "collection": "gobotgo_lessons_execution",
            "model": "text-embedding-3-small",
        },
    )

    assert resp.status_code == 200
    assert captured["query"] == "risk-on breakout"
    assert captured["collection_name"] == "gobotgo_lessons_execution"
    assert captured["embedding_model"] == "text-embedding-3-small"
