from __future__ import annotations

import json
from io import BytesIO

import pytest

import scripts.run_daily_ingestion as daily


def test_run_once_posts_to_configured_ingestion_url(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):  # noqa: ANN001
            return None

        def read(self):
            return json.dumps({"ingested_count": 2, "activities": []}).encode("utf-8")

    def fake_urlopen(request, timeout=0):  # noqa: ANN001
        captured["url"] = request.full_url
        captured["method"] = request.get_method()
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(daily, "urlopen", fake_urlopen)

    result = daily.run_once("http://example.com/api/ingest")

    assert captured == {"url": "http://example.com/api/ingest", "method": "POST", "timeout": 60}
    assert result == {"ingested_count": 2, "activities": []}


def test_run_once_raises_useful_error_on_http_failure(monkeypatch) -> None:
    def fake_urlopen(request, timeout=0):  # noqa: ANN001
        raise daily.HTTPError(request.full_url, 500, "Server Error", hdrs=None, fp=BytesIO(b"boom"))

    monkeypatch.setattr(daily, "urlopen", fake_urlopen)

    with pytest.raises(RuntimeError, match="HTTP 500: boom"):
        daily.run_once("http://example.com/ingest")
