from __future__ import annotations

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.knowledge import KnowledgeRequest
from app.services import knowledge_service as knowledge_module
from app.services.knowledge_service import KnowledgeService


def _wiki_response(request: httpx.Request, text: str | None = None) -> httpx.Response:
    host = request.url.host
    title = request.url.params["titles"]
    return httpx.Response(
        200,
        headers={"content-type": "application/json"},
        json={
            "query": {
                "pages": [
                    {
                        "title": title,
                        "extract": text or f"Reference prose from {host}.",
                        "revisions": [{"revid": 123, "timestamp": "2026-01-01T00:00:00Z"}],
                    }
                ]
            }
        },
    )


@pytest.mark.parametrize(
    ("expression", "topic"),
    [
        ("2*x + 1", "linear_function"),
        ("f(t) = t**2 - 1", "quadratic_function"),
        ("2*x + 1 = 0", "linear_equation"),
        ("x**2 - 1 = 0", "quadratic_equation"),
    ],
)
def test_derives_topic_with_trusted_math_and_always_has_fallback(
    monkeypatch: pytest.MonkeyPatch, expression: str, topic: str
) -> None:
    monkeypatch.setenv("KNOWLEDGE_EXTERNAL_ENABLED", "false")
    response = KnowledgeService().related(KnowledgeRequest(expression=expression))

    assert response.schema_version == "1.0"
    assert response.topic == topic
    assert response.items[0].source_id == "builtin:curated-vi"
    assert response.items[0].vietnamese_text
    assert response.items[0].original_language == "vi"
    assert response.items[0].translation_status == "original"
    assert response.citations[0].id == response.items[0].citation_id
    assert response.warning.startswith("Tài liệu này chỉ dùng để tham khảo giáo dục")
    assert response.cache.statuses == ["builtin"]


def test_mediawiki_is_allowlisted_bounded_plain_and_deterministic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return _wiki_response(request, f"Safe <b>prose</b> from {request.url.host}.\x00")

    monkeypatch.setenv("KNOWLEDGE_EXTERNAL_ENABLED", "true")
    service = KnowledgeService(httpx.Client(transport=httpx.MockTransport(handler)))
    response = service.related(KnowledgeRequest(expression="x + 987654"))

    assert [request.url.host for request in requests] == [
        "vi.wikipedia.org",
        "en.wikipedia.org",
        "en.wikibooks.org",
    ]
    assert all(request.url.path == "/w/api.php" for request in requests)
    assert all("987654" not in str(request.url) for request in requests)
    assert [item.source_id for item in response.items] == [
        "builtin:curated-vi",
        "mediawiki:vi.wikipedia.org",
        "mediawiki:en.wikipedia.org",
        "mediawiki:en.wikibooks.org",
    ]
    assert all("<" not in (item.original_text or "") for item in response.items)
    assert all("\x00" not in (item.original_text or "") for item in response.items)
    assert response.cache.statuses == ["builtin", "network"]
    for citation in response.citations:
        assert citation.url.startswith("https://")
        assert citation.contributors_url.startswith("https://")
        assert citation.license_name and citation.license_url
        assert citation.revision and citation.retrieved_at
    external = [citation for citation in response.citations if citation.source_id.startswith("mediawiki:")]
    assert all(citation.license_name == "CC BY-SA 4.0" for citation in external)


@pytest.mark.parametrize("failure", ["network", "content_type", "oversize"])
def test_external_failure_or_limit_returns_fallback(
    monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if failure == "network":
            raise httpx.ConnectError("offline", request=request)
        if failure == "content_type":
            return httpx.Response(200, headers={"content-type": "text/html"}, text="bad")
        return httpx.Response(
            200,
            headers={"content-type": "application/json", "content-length": "999999"},
            content=b"{}",
        )

    monkeypatch.setenv("KNOWLEDGE_EXTERNAL_ENABLED", "true")
    service = KnowledgeService(httpx.Client(transport=httpx.MockTransport(handler)))
    response = service.related(KnowledgeRequest(expression="x + 1"))

    assert len(response.items) == 1
    assert response.items[0].source_id == "builtin:curated-vi"


def test_cache_is_fresh_then_stale_on_source_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0
    clock = [0.0]

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls > 3:
            raise httpx.ConnectError("offline", request=request)
        return _wiki_response(request)

    monkeypatch.setenv("KNOWLEDGE_EXTERNAL_ENABLED", "true")
    monkeypatch.setenv("KNOWLEDGE_CACHE_TTL_SECONDS", "1")
    monkeypatch.setenv("KNOWLEDGE_CACHE_STALE_SECONDS", "100")
    monkeypatch.setattr(knowledge_module.time, "monotonic", lambda: clock[0])
    service = KnowledgeService(httpx.Client(transport=httpx.MockTransport(handler)))

    first = service.related(KnowledgeRequest(expression="x + 1"))
    clock[0] = 0.5
    second = service.related(KnowledgeRequest(expression="x + 1"))
    clock[0] = 2.0
    third = service.related(KnowledgeRequest(expression="x + 1"))

    assert first.cache.statuses == ["builtin", "network"]
    assert second.cache.statuses == ["builtin", "fresh"]
    assert third.cache.statuses == ["builtin", "stale"]
    assert calls == 6


def test_flags_and_failed_translation_keep_english_original(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prompts: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/chat":
            prompts.append(request.read().decode())
            raise httpx.ConnectError("ollama offline", request=request)
        return _wiki_response(request)

    monkeypatch.setenv("KNOWLEDGE_EXTERNAL_ENABLED", "true")
    monkeypatch.setenv("KNOWLEDGE_OLLAMA_TRANSLATION_ENABLED", "true")
    service = KnowledgeService(httpx.Client(transport=httpx.MockTransport(handler)))
    response = service.related(KnowledgeRequest(expression="x + 987654"))

    english = [item for item in response.items if item.original_language == "en"]
    assert all(item.original_text for item in english)
    assert all(item.vietnamese_text is None for item in english)
    assert all(item.translation_status == "unavailable" for item in english)
    assert prompts and all("987654" not in prompt for prompt in prompts)

    without_text = service.related(
        KnowledgeRequest(
            expression="x + 987654", include_original=False, include_vietnamese=False
        )
    )
    assert without_text.items[0].vietnamese_text  # Built-in fallback is unconditional.
    assert without_text.items[0].original_text is None
    assert all(item.original_text is None for item in without_text.items[1:])
    assert all(item.vietnamese_text is None for item in without_text.items[1:])


def test_successful_ollama_translation_is_reused_from_cache(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ollama_calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal ollama_calls
        if request.url.path == "/api/chat":
            ollama_calls += 1
            return httpx.Response(200, json={"message": {"content": "Bản dịch tiếng Việt."}})
        return _wiki_response(request)

    monkeypatch.setenv("KNOWLEDGE_EXTERNAL_ENABLED", "true")
    monkeypatch.setenv("KNOWLEDGE_OLLAMA_TRANSLATION_ENABLED", "true")
    service = KnowledgeService(httpx.Client(transport=httpx.MockTransport(handler)))

    first = service.related(KnowledgeRequest(expression="x + 1"))
    second = service.related(KnowledgeRequest(expression="x + 1"))

    assert ollama_calls == 2  # Hai nguồn tiếng Anh, chỉ dịch một lần cho mỗi nguồn.
    assert all(
        item.vietnamese_text == "Bản dịch tiếng Việt."
        for item in first.items
        if item.original_language == "en"
    )
    assert all(
        item.translation_status == "machine_translated"
        for item in second.items
        if item.original_language == "en"
    )


def test_api_rejects_client_topic_url_and_unsupported_expression(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("KNOWLEDGE_EXTERNAL_ENABLED", "false")
    client = TestClient(app)

    untrusted = client.post(
        "/api/knowledge/related",
        json={"expression": "x + 1", "topic": "quadratic", "url": "https://evil.test"},
    )
    assert untrusted.status_code == 422
    assert client.post(
        "/api/knowledge/related", json={"expression": "x + 1"}
    ).json()["topic"] == "linear_function"
    response = client.post("/api/knowledge/related", json={"expression": "sin(x)"})
    assert response.status_code == 400
    assert client.post("/api/knowledge/related", json={}).status_code == 422
