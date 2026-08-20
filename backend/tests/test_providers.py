"""Test các provider nhận dạng thật (Ollama Vision, Pix2Text) với HTTP mock."""

from __future__ import annotations

import httpx
import pytest

from app.providers.normalize import to_expression
from app.providers.ollama_vision import OllamaVisionProvider
from app.providers.pix2text import Pix2TextProvider


class TestNormalize:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("y = x^2 - 4x + 3", "x**2 - 4x + 3"),
            ("f(x)=2*x+1", "2*x+1"),
            ("x^2 - 4x + 3", "x**2 - 4x + 3"),
            ("  x + 1  ", "x + 1"),
        ],
    )
    def test_to_expression(self, raw: str, expected: str) -> None:
        assert to_expression(raw) == expected


class TestOllamaVisionProvider:
    def test_recognize_parse_json(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            body = request.read()
            assert "images" in body.decode()
            return httpx.Response(
                200,
                json={
                    "response": (
                        '{"latex": "y = x^2 - 4x + 3", '
                        '"expression": "x**2 - 4*x + 3", "confidence": 0.91}'
                    )
                },
            )

        client = httpx.Client(transport=httpx.MockTransport(handler))
        provider = OllamaVisionProvider(
            url="http://ollama:11434", model="llava", http_client=client
        )
        result = provider.recognize(image_base64="data:image/png;base64,QUJD")
        assert result.provider == "ollama_vision"
        assert result.latex == "y = x^2 - 4x + 3"
        assert result.expression == "x**2 - 4*x + 3"
        assert result.confidence == pytest.approx(0.91)

    def test_khong_ket_noi_duoc(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection refused", request=request)

        client = httpx.Client(transport=httpx.MockTransport(handler))
        provider = OllamaVisionProvider(
            url="http://localhost:11434", model="llava", http_client=client
        )
        with pytest.raises(RuntimeError, match="Ollama"):
            provider.recognize(image_base64="QUJD")

    def test_thieu_anh(self) -> None:
        client = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, json={})))
        provider = OllamaVisionProvider(url="http://x", model="llava", http_client=client)
        with pytest.raises(ValueError, match="Thiếu ảnh"):
            provider.recognize(image_base64=None)


class TestPix2TextProvider:
    def test_recognize_parse_results(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "POST"
            return httpx.Response(
                200,
                json={"results": [{"type": "formula", "text": "y = x^2 - 4x + 3"}]},
            )

        client = httpx.Client(transport=httpx.MockTransport(handler))
        provider = Pix2TextProvider(url="http://p2t:8503", http_client=client)
        result = provider.recognize(image_base64="QUJD")
        assert result.provider == "pix2text"
        assert result.expression == "x**2 - 4x + 3"
        assert result.confidence == pytest.approx(0.9)

    def test_khong_nhan_dang_duoc(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"results": []})

        client = httpx.Client(transport=httpx.MockTransport(handler))
        provider = Pix2TextProvider(url="http://p2t:8503", http_client=client)
        with pytest.raises(RuntimeError, match="không nhận dạng được"):
            provider.recognize(image_base64="QUJD")