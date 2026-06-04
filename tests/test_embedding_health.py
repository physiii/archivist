import json

import embedding_health


class _Response:
    def __init__(self, status_code=200, body=None, text=None):
        self.status_code = status_code
        self._body = body if body is not None else {}
        self.text = text if text is not None else json.dumps(self._body)

    def json(self):
        return self._body


def test_embedding_health_ok(monkeypatch):
    def fake_post(url, json, timeout):  # noqa: A002
        assert url == "http://embed.local:8000/v1/embeddings"
        assert json["model"] == "local-default"
        assert timeout == 8.0
        return _Response(body={"data": [{"embedding": [0.0] * 2560}]})

    monkeypatch.setattr(embedding_health.requests, "post", fake_post)

    status = embedding_health.check_embedding_service(host="embed.local", port=8000)

    assert status["status"] == "ok"
    assert status["model"] == "local-default"
    assert status["vector_dim"] == 2560


def test_embedding_health_rejects_http_error(monkeypatch):
    monkeypatch.setattr(
        embedding_health.requests,
        "post",
        lambda *args, **kwargs: _Response(status_code=502, text="backend unavailable"),
    )

    status = embedding_health.check_embedding_service(host="embed.local", port=8000)

    assert status["status"] == "error"
    assert status["severity"] == "error"
    assert status["http_status"] == 502
    assert "backend unavailable" in status["error"]


def test_embedding_health_rejects_dimension_mismatch(monkeypatch):
    monkeypatch.setattr(
        embedding_health.requests,
        "post",
        lambda *args, **kwargs: _Response(body={"data": [{"embedding": [0.0] * 1024}]}),
    )

    status = embedding_health.check_embedding_service(host="embed.local", port=8000)

    assert status["status"] == "error"
    assert status["vector_dim"] == 1024
    assert status["expected_dim"] == 2560
