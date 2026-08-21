"""Curated and allowlisted educational references for trusted math topics."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import html
import os
import re
import threading
import time
from urllib.parse import quote

import httpx

from app.schemas.knowledge import (
    KnowledgeCacheProvenance,
    KnowledgeCitation,
    KnowledgeItem,
    KnowledgeRequest,
    KnowledgeResponse,
)
from app.services.math_service import MathEngineError, analyze_expression, solve_equation

_USER_AGENT = "MathTeacherKnowledge/1.0 (https://github.com/Swon010191/Math_teacher)"
_WARNING = (
    "Tài liệu này chỉ dùng để tham khảo giáo dục; hãy đối chiếu nguồn trích dẫn "
    "và không xem đây là lời giải hoặc kết luận duy nhất."
)
_PROJECT_URL = "https://github.com/Swon010191/Math_teacher"

_TOPICS = {
    "linear_function": {
        "vi.wikipedia.org": "Hàm số bậc nhất",
        "en.wikipedia.org": "Linear function",
        "en.wikibooks.org": "High School Mathematics Extensions/Linear Functions",
    },
    "quadratic_function": {
        "vi.wikipedia.org": "Hàm số bậc hai",
        "en.wikipedia.org": "Quadratic function",
        "en.wikibooks.org": "High School Mathematics Extensions/Quadratic Functions",
    },
    "linear_equation": {
        "vi.wikipedia.org": "Phương trình bậc nhất",
        "en.wikipedia.org": "Linear equation",
        "en.wikibooks.org": "Elementary Algebra/Linear Equations",
    },
    "quadratic_equation": {
        "vi.wikipedia.org": "Phương trình bậc hai",
        "en.wikipedia.org": "Quadratic equation",
        "en.wikibooks.org": "Elementary Algebra/Quadratic Equations",
    },
}

_FALLBACKS = {
    "linear_function": (
        "Hàm số bậc nhất",
        "Hàm số bậc nhất có dạng y = ax + b với a khác 0. Đồ thị là một đường "
        "thẳng; a mô tả độ dốc và b là tung độ giao điểm với trục tung.",
    ),
    "quadratic_function": (
        "Hàm số bậc hai",
        "Hàm số bậc hai có dạng y = ax^2 + bx + c với a khác 0. Đồ thị là "
        "một parabol; dấu của a quyết định hướng mở, còn đỉnh và trục đối xứng "
        "giúp mô tả vị trí của đồ thị.",
    ),
    "linear_equation": (
        "Phương trình bậc nhất",
        "Phương trình bậc nhất một ẩn có thể đưa về dạng ax + b = 0 với a khác "
        "0. Giải phương trình là thực hiện các phép biến đổi tương đương để cô lập ẩn.",
    ),
    "quadratic_equation": (
        "Phương trình bậc hai",
        "Phương trình bậc hai một ẩn có dạng ax^2 + bx + c = 0 với a khác 0. "
        "Biệt thức giúp xác định số nghiệm thực; nghiệm cần được kiểm tra lại trong "
        "phương trình ban đầu.",
    ),
}


@dataclass
class _CacheEntry:
    item: KnowledgeItem
    citation: KnowledgeCitation
    stored_at: float


class KnowledgeService:
    def __init__(self, http_client: httpx.Client | None = None) -> None:
        timeout = _float_env("KNOWLEDGE_HTTP_TIMEOUT_SECONDS", 1.5, 0.1, 10.0)
        self._client = http_client or httpx.Client(
            timeout=timeout,
            follow_redirects=False,
            headers={"User-Agent": _USER_AGENT, "Accept": "application/json"},
        )
        self._cache: OrderedDict[str, _CacheEntry] = OrderedDict()
        self._translation_cache: OrderedDict[str, tuple[str, float]] = OrderedDict()
        self._lock = threading.Lock()

    def related(self, request: KnowledgeRequest) -> KnowledgeResponse:
        topic = _derive_topic(request.expression)
        fallback_item, fallback_citation = _fallback(topic, request.include_original)
        items = [fallback_item]
        citations = [fallback_citation]
        statuses = ["builtin"]
        external_enabled = _bool_env("KNOWLEDGE_EXTERNAL_ENABLED", True)

        if external_enabled:
            for host, title in _TOPICS[topic].items():
                result = self._source(topic, host, title)
                if result is None:
                    continue
                item, citation, status = result
                item = item.model_copy(
                    update={
                        "original_text": item.original_text if request.include_original else None,
                        "vietnamese_text": self._vietnamese(item, topic)
                        if request.include_vietnamese
                        else None,
                    }
                )
                if item.original_language == "vi" and request.include_vietnamese:
                    item.translation_status = "original"
                elif item.original_language == "en" and item.vietnamese_text:
                    item.translation_status = "machine_translated"
                elif item.original_language == "en" and request.include_vietnamese:
                    item.translation_status = "unavailable"
                else:
                    item.translation_status = "not_requested"
                items.append(item)
                citations.append(citation)
                statuses.append(status)

        items, citations = _deduplicate(items, citations)
        return KnowledgeResponse(
            topic=topic,
            items=items,
            citations=citations,
            cache=KnowledgeCacheProvenance(
                statuses=list(dict.fromkeys(statuses)),
                external_attempted=external_enabled,
            ),
            warning=_WARNING,
        )

    def _source(
        self, topic: str, host: str, title: str
    ) -> tuple[KnowledgeItem, KnowledgeCitation, str] | None:
        key = f"{topic}:{host}"
        now = time.monotonic()
        ttl = _float_env("KNOWLEDGE_CACHE_TTL_SECONDS", 900.0, 1.0, 86400.0)
        stale_ttl = _float_env("KNOWLEDGE_CACHE_STALE_SECONDS", 86400.0, ttl, 604800.0)
        cached = self._cached(key)
        if cached and now - cached.stored_at <= ttl:
            return cached.item.model_copy(update={"cache_status": "fresh"}), cached.citation, "fresh"
        try:
            item, citation = self._fetch(host, title)
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            if cached and now - cached.stored_at <= stale_ttl:
                return cached.item.model_copy(update={"cache_status": "stale"}), cached.citation, "stale"
            return None
        self._store(key, _CacheEntry(item, citation, now))
        return item, citation, "network"

    def _fetch(self, host: str, requested_title: str) -> tuple[KnowledgeItem, KnowledgeCitation]:
        api_url = f"https://{host}/w/api.php"
        params = {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "prop": "extracts|revisions",
            "exintro": "1",
            "explaintext": "1",
            "rvprop": "ids|timestamp",
            "redirects": "1",
            "titles": requested_title,
        }
        max_bytes = _int_env("KNOWLEDGE_MAX_RESPONSE_BYTES", 262144, 4096, 1048576)
        with self._client.stream("GET", api_url, params=params) as response:
            response.raise_for_status()
            content_type = response.headers.get("content-type", "").lower()
            if "json" not in content_type:
                raise ValueError("MediaWiki response is not JSON")
            length = response.headers.get("content-length")
            if length and int(length) > max_bytes:
                raise ValueError("MediaWiki response is too large")
            body = bytearray()
            for chunk in response.iter_bytes():
                body.extend(chunk)
                if len(body) > max_bytes:
                    raise ValueError("MediaWiki response is too large")
        payload = httpx.Response(200, content=bytes(body)).json()
        pages = payload["query"]["pages"]
        if not isinstance(pages, list) or not pages or pages[0].get("missing") is True:
            raise ValueError("MediaWiki page is missing")
        page = pages[0]
        extract = _plain_text(page.get("extract", ""))
        title = _plain_text(page.get("title", requested_title), 200)
        if not extract or not title:
            raise ValueError("MediaWiki page has no usable text")
        revision = page.get("revisions", [{}])[0]
        page_url = f"https://{host}/wiki/{quote(requested_title.replace(' ', '_'), safe='/')}"
        source_id = f"mediawiki:{host}"
        retrieved = datetime.now(timezone.utc).isoformat()
        license_name = "CC BY-SA 4.0"
        license_url = "https://creativecommons.org/licenses/by-sa/4.0/"
        citation_id = f"{source_id}:{requested_title}"
        item = KnowledgeItem(
            id=citation_id,
            source_id=source_id,
            title=title,
            original_text=extract,
            vietnamese_text=extract if host.startswith("vi.") else None,
            original_language="vi" if host.startswith("vi.") else "en",
            translation_status="original" if host.startswith("vi.") else "unavailable",
            citation_id=citation_id,
            cache_status="network",
        )
        citation = KnowledgeCitation(
            id=citation_id,
            source_id=source_id,
            title=title,
            url=page_url,
            contributors_url=f"{page_url}?action=history",
            license_name=license_name,
            license_url=license_url,
            revision=str(revision.get("revid") or revision.get("timestamp") or "unknown"),
            retrieved_at=retrieved,
        )
        return item, citation

    def _vietnamese(self, item: KnowledgeItem, topic: str) -> str | None:
        if item.original_language == "vi":
            return item.original_text
        if not _bool_env("KNOWLEDGE_OLLAMA_TRANSLATION_ENABLED", False) or not item.original_text:
            return None
        cache_key = hashlib.sha256(
            f"{item.id}\0{item.original_text}".encode("utf-8")
        ).hexdigest()
        now = time.monotonic()
        ttl = _float_env("KNOWLEDGE_CACHE_TTL_SECONDS", 900.0, 1.0, 86400.0)
        with self._lock:
            cached = self._translation_cache.get(cache_key)
            if cached and now - cached[1] <= ttl:
                self._translation_cache.move_to_end(cache_key)
                return cached[0]
        prompt = (
            f"Dịch đoạn tài liệu về chủ đề {topic.replace('_', ' ')} sang tiếng Việt. "
            "Chỉ trả về bản dịch thuần văn bản, không thêm dữ kiện:\n" + item.original_text
        )
        try:
            response = self._client.post(
                os.environ.get("OLLAMA_URL", "http://localhost:11434").rstrip("/") + "/api/chat",
                json={
                    "model": os.environ.get("OLLAMA_MODEL_COPILOT", "llama3.2"),
                    "stream": False,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=_float_env("KNOWLEDGE_OLLAMA_TIMEOUT_SECONDS", 3.0, 0.1, 30.0),
            )
            response.raise_for_status()
            translated = _plain_text(response.json()["message"]["content"])
            if not translated:
                return None
            maximum = _int_env("KNOWLEDGE_CACHE_MAX_ENTRIES", 24, 1, 128)
            with self._lock:
                self._translation_cache[cache_key] = (translated, now)
                self._translation_cache.move_to_end(cache_key)
                while len(self._translation_cache) > maximum:
                    self._translation_cache.popitem(last=False)
            return translated
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            return None

    def _cached(self, key: str) -> _CacheEntry | None:
        with self._lock:
            entry = self._cache.get(key)
            if entry:
                self._cache.move_to_end(key)
            return entry

    def _store(self, key: str, entry: _CacheEntry) -> None:
        maximum = _int_env("KNOWLEDGE_CACHE_MAX_ENTRIES", 24, 1, 128)
        with self._lock:
            self._cache[key] = entry
            self._cache.move_to_end(key)
            while len(self._cache) > maximum:
                self._cache.popitem(last=False)


def _derive_topic(expression: str) -> str:
    if "=" in expression:
        try:
            analysis = analyze_expression(expression)
        except MathEngineError:
            solved = solve_equation(expression)
            if solved.degree in (1, 2):
                return "linear_equation" if solved.degree == 1 else "quadratic_equation"
            raise MathEngineError("Chủ đề phương trình chưa được hỗ trợ.")
    else:
        analysis = analyze_expression(expression)
    if analysis.kind in ("linear", "quadratic"):
        return f"{analysis.kind}_function"
    raise MathEngineError("Knowledge API hiện chỉ hỗ trợ chủ đề bậc nhất và bậc hai.")


def _fallback(topic: str, include_original: bool) -> tuple[KnowledgeItem, KnowledgeCitation]:
    title, text = _FALLBACKS[topic]
    citation_id = f"builtin:{topic}"
    item = KnowledgeItem(
        id=citation_id,
        source_id="builtin:curated-vi",
        title=title,
        original_text=text if include_original else None,
        vietnamese_text=text,
        original_language="vi",
        translation_status="original",
        citation_id=citation_id,
        cache_status="builtin",
    )
    citation = KnowledgeCitation(
        id=citation_id,
        source_id="builtin:curated-vi",
        title=title,
        url=f"{_PROJECT_URL}/tree/main/backend/app/services/knowledge_service.py",
        contributors_url=f"{_PROJECT_URL}/graphs/contributors",
        license_name="MIT License",
        license_url=f"{_PROJECT_URL}/blob/main/LICENSE",
        revision="builtin-v1",
        retrieved_at=datetime.now(timezone.utc).isoformat(),
    )
    return item, citation


def _plain_text(value: object, limit: int = 2500) -> str:
    if not isinstance(value, str):
        return ""
    text = html.unescape(re.sub(r"<[^>]*>", " ", value))
    text = "".join(char for char in text if char in "\n\t" or ord(char) >= 32)
    return re.sub(r"\s+", " ", text).strip()[:limit]


def _deduplicate(
    items: list[KnowledgeItem], citations: list[KnowledgeCitation]
) -> tuple[list[KnowledgeItem], list[KnowledgeCitation]]:
    kept: list[KnowledgeItem] = []
    citation_ids: set[str] = set()
    seen: set[tuple[str, str]] = set()
    for item in items:
        comparable = item.original_text or item.vietnamese_text
        marker = (
            (item.original_language, comparable.casefold())
            if comparable
            else (item.source_id, item.title.casefold())
        )
        if marker in seen:
            continue
        seen.add(marker)
        kept.append(item)
        citation_ids.add(item.citation_id)
    return kept, [citation for citation in citations if citation.id in citation_ids]


def _bool_env(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    return default if raw is None else raw.strip().lower() in {"1", "true", "yes", "on"}


def _float_env(name: str, default: float, minimum: float, maximum: float) -> float:
    try:
        return min(max(float(os.environ.get(name, default)), minimum), maximum)
    except ValueError:
        return default


def _int_env(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        return min(max(int(os.environ.get(name, default)), minimum), maximum)
    except ValueError:
        return default


knowledge_service = KnowledgeService()
