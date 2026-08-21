"""Test các provider nhận dạng thật (Ollama Vision, Pix2Text) với HTTP mock."""

from __future__ import annotations

import json

import httpx
import pytest

from app.providers.normalize import to_expression, to_problem_expression
from app.providers.ollama_copilot import OllamaCopilotProvider
from app.providers.ollama_vision import OllamaVisionProvider
from app.providers.pix2text import Pix2TextProvider
from app.providers.rule_based_copilot import RuleBasedCopilotProvider
from app.schemas.copilot import CopilotRequest, CopilotMathInput
from app.services.math_service import MathEngineError, analyze_expression
from app.services.recognition_diagnostics import check_all, check_provider_availability


def _quadratic_request() -> CopilotRequest:
    return CopilotRequest(
        expression="x**2 - 4*x + 3",
        activity_type="quadratic_function",
        math=CopilotMathInput(
            expression="x**2 - 4*x + 3",
            a=1.0,
            b=-4.0,
            c=3.0,
            vertex=[2.0, -1.0],
            roots=[1.0, 3.0],
            axis="x = 2",
            y_intercept=3.0,
            discriminant=4.0,
            direction="up",
        ),
    )


class TestNormalize:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("z=2t+1", "z=2t+1"),
            ("2u+3=9", "2u+3=9"),
            (r"f(t) = \frac{t^{2}-1}{2}", "f(t) = (t**(2)-1)/(2)"),
            ("y = t² × 2", "y = t**2 * 2"),
        ],
    )
    def test_to_problem_expression_giu_relation(
        self, raw: str, expected: str
    ) -> None:
        assert to_problem_expression(raw) == expected

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("y = x^2 - 4x + 3", "x**2 - 4x + 3"),
            ("f(x)=2*x+1", "2*x+1"),
            ("x^2 - 4x + 3", "x**2 - 4x + 3"),
            ("  x + 1  ", "x + 1"),
            (r"\frac{2 x+3}{x-1}", "(2 x+3)/(x-1)"),
            (r"y = \frac{2 x+3}{x-1}", "(2 x+3)/(x-1)"),
            (r"\frac{\frac{1}{2}}{x}", "((1)/(2))/(x)"),
            (r"x^{2}", "x**(2)"),
            (r"\sqrt{x}", "sqrt(x)"),
            (r"\sqrt[3]{x}", "x**(1/(3))"),
            (r"2\cdot 3^x", "2* 3**x"),
            (r"\left(\frac{1}{2}\right)", "((1)/(2))"),
            (r"\sin(x)", "sin(x)"),
            (r"\log_{10}(x)", "log(x,10)"),
            (r"\lg(x)", "lg(x)"),
            (r"\pi", "pi"),
            (r"\frac{x^2 - 4x + 3}{x - 1}", "(x**2 - 4x + 3)/(x - 1)"),
            (r"2^{\frac{x}{2}}", "2**((x)/(2))"),
        ],
    )
    def test_to_expression(self, raw: str, expected: str) -> None:
        assert to_expression(raw) == expected

    @pytest.mark.parametrize(
        ("raw", "kind", "extra"),
        [
            (r"\frac{2 x+3}{x-1}", "rational", None),
            (r"\log_{10}(x)", "logarithmic", 10.0),
            (r"\lg(x)", "logarithmic", 10.0),
            (r"\sin(x)", "trigonometric", None),
            (r"x^{2}", "quadratic", None),
        ],
    )
    def test_latex_phan_tich_duoc(self, raw: str, kind: str, extra: object) -> None:
        result = analyze_expression(to_expression(raw))
        assert result.kind == kind
        if kind == "logarithmic":
            assert result.logarithmic.base == extra

    def test_latex_sqrt_ngoai_pham_vi_bao_loi(self) -> None:
        with pytest.raises(MathEngineError):
            analyze_expression(to_expression(r"\sqrt{x}"))


class TestOllamaVisionProvider:
    def test_recognize_parse_json(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            body = request.read().decode()
            assert "images" in body
            assert "toàn bộ công thức/phương trình" in body
            return httpx.Response(
                200,
                json={
                    "response": (
                        '{"latex": "y = x^2 - 4x + 3", '
                        '"expression": "y = x**2 - 4*x + 3", "confidence": 0.91}'
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
        assert result.expression == "y = x**2 - 4*x + 3"
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
        assert result.expression == "y = x**2 - 4x + 3"
        assert result.confidence == pytest.approx(0.9)

    def test_recognize_results_la_chuoi(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"results": "y = x^2 - 4x + 3"})

        client = httpx.Client(transport=httpx.MockTransport(handler))
        provider = Pix2TextProvider(url="http://p2t:8503", http_client=client)
        result = provider.recognize(image_base64="QUJD")
        assert result.provider == "pix2text"
        assert result.expression == "y = x**2 - 4x + 3"

    def test_recognize_bao_toan_latex_equation(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={"results": [{"text": r"2u + \frac{3}{1} = 9"}]},
            )

        client = httpx.Client(transport=httpx.MockTransport(handler))
        result = Pix2TextProvider(
            url="http://p2t:8503", http_client=client
        ).recognize(image_base64="QUJD")
        assert result.expression == "2u + (3)/(1) = 9"

    def test_khong_nhan_dang_duoc(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"results": []})

        client = httpx.Client(transport=httpx.MockTransport(handler))
        provider = Pix2TextProvider(url="http://p2t:8503", http_client=client)
        with pytest.raises(RuntimeError, match="không nhận dạng được"):
            provider.recognize(image_base64="QUJD")


class TestRuleBasedCopilot:
    def test_linear_dung_ten_bien_nguon_va_phu_thuoc(self) -> None:
        provider = RuleBasedCopilotProvider(delay_seconds=0)
        request = CopilotRequest(
            expression="z = 2*t + 1",
            activity_type="linear_function",
            math=CopilotMathInput(
                expression="2*t + 1",
                source_variable="t",
                dependent_variable="z",
                a=2,
                b=1,
                root=-0.5,
                y_intercept=1,
            ),
        )
        result = provider.suggest(request)
        prose = " ".join(
            [result.summary, *result.key_points, *result.questions, *result.teaching_steps]
        )
        assert "z = 2*t + 1" in prose
        assert "t = -0.5" in prose
        assert "x =" not in prose and "y =" not in prose

    def test_khong_doi_nham_khi_bien_nguon_la_y(self) -> None:
        provider = RuleBasedCopilotProvider(delay_seconds=0)
        request = CopilotRequest(
            expression="z = 2*y + 1",
            activity_type="linear_function",
            math=CopilotMathInput(
                expression="2*y + 1",
                source_variable="y",
                dependent_variable="z",
                a=2,
                b=1,
                root=-0.5,
                y_intercept=1,
            ),
        )
        result = provider.suggest(request)
        prose = " ".join(
            [result.summary, *result.key_points, *result.questions, *result.teaching_steps]
        )
        assert "z = 2*y + 1" in prose
        assert "y = -0.5" in prose

    def test_suggest_quadratic(self) -> None:
        provider = RuleBasedCopilotProvider(delay_seconds=0)
        result = provider.suggest(_quadratic_request())
        assert result.provider == "rule_based"
        assert "parabol" in result.summary
        assert any("I(2; -1)" in p for p in result.key_points)
        assert result.examples

    def test_suggest_linear(self) -> None:
        provider = RuleBasedCopilotProvider(delay_seconds=0)
        request = CopilotRequest(
            expression="2*x + 1",
            activity_type="linear_function",
            math=CopilotMathInput(
                expression="2*x + 1", a=2.0, b=1.0, root=-0.5, y_intercept=1.0
            ),
        )
        result = provider.suggest(request)
        assert "đường thẳng" in result.summary
        assert any("(-0.5; 0)" in p for p in result.key_points)

    def test_log_dien_giai_direction_da_xac_minh(self) -> None:
        provider = RuleBasedCopilotProvider(delay_seconds=0)
        request = CopilotRequest(
            expression="-log(x, 2)",
            activity_type="logarithmic_function",
            math=CopilotMathInput(
                expression="-log(x)/log(2)",
                a=-1,
                base=2,
                root=1,
                direction="down",
                domain="x > 0",
                asymptotes=["x = 0"],
            ),
        )
        result = provider.suggest(request)
        assert "nghịch biến" in result.summary
        assert not any("b > 1 hàm đồng biến" in point for point in result.key_points)

    def test_rational_dien_giai_diem_khuyet_khong_phai_tiem_can_dung(self) -> None:
        provider = RuleBasedCopilotProvider(delay_seconds=0)
        request = CopilotRequest(
            expression="(2*x - 2)/(x - 1)",
            activity_type="rational_function",
            math=CopilotMathInput(
                expression="(2*x - 2)/(x - 1)",
                a=2,
                b=-2,
                c=1,
                d=-1,
                holes=[1],
                domain="x ≠ 1",
                asymptotes=["y = 2"],
            ),
        )
        result = provider.suggest(request)
        text = " ".join([result.summary, *result.key_points]).lower()
        assert "điểm khuyết" in text
        assert "tiệm cận đứng" not in text
        assert "x = ?" not in result.summary
        assert "không cắt trục hoành" in result.summary

    def test_exponential_toan_bo_prose_bam_direction_da_xac_minh(self) -> None:
        provider = RuleBasedCopilotProvider(delay_seconds=0)
        request = CopilotRequest(
            expression="-2**x",
            activity_type="exponential_function",
            math=CopilotMathInput(
                expression="-2**x",
                a=-1,
                base=2,
                direction="down",
                y_intercept=-1,
                asymptotes=["y = 0"],
            ),
        )
        result = provider.suggest(request)
        prose = " ".join(
            [result.summary, *result.key_points, *result.questions, *result.teaching_steps]
        ).lower()
        assert "nghịch biến" in prose
        assert "b > 1 hàm đồng biến" not in prose
        assert "cơ số b lớn hơn 1 hay nhỏ hơn 1? hàm số đồng biến hay nghịch biến?" not in prose

    def test_rational_c_bang_0_chi_noi_asymptote_co_that(self) -> None:
        provider = RuleBasedCopilotProvider(delay_seconds=0)
        request = CopilotRequest(
            expression="(2*x + 1)/3",
            activity_type="rational_function",
            math=CopilotMathInput(
                expression="(2*x + 1)/3",
                a=2,
                b=1,
                c=0,
                d=3,
                domain="R",
                asymptotes=[],
                root=-0.5,
                y_intercept=1 / 3,
            ),
        )
        result = provider.suggest(request)
        prose = " ".join([result.summary, *result.key_points]).lower()
        assert "a/c" not in prose
        assert "tiệm cận ngang" not in prose
        assert "tiệm cận đứng" not in prose


class TestOllamaCopilot:
    def test_prompt_chua_metadata_bien(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.read().decode())
            prompt = body["messages"][1]["content"]
            assert '"source_variable": "t"' in prompt
            assert '"dependent_variable": "z"' in prompt
            return httpx.Response(
                200,
                json={
                    "message": {
                        "content": (
                            '{"summary":"ok","key_points":[],"questions":[],'
                            '"examples":[],"teaching_steps":[],"confidence":1}'
                        )
                    }
                },
            )

        provider = OllamaCopilotProvider(
            url="http://ollama:11434",
            model="llama3.2",
            http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        )
        result = provider.suggest(
            CopilotRequest(
                expression="z = 2*t + 1",
                activity_type="linear_function",
                math=CopilotMathInput(
                    expression="2*t + 1",
                    source_variable="t",
                    dependent_variable="z",
                    a=2,
                    b=1,
                ),
            )
        )
        assert result.provider == "ollama"

    def test_suggest_parse_json(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            body = request.read().decode()
            assert '"format":"json"' in body
            return httpx.Response(
                200,
                json={
                    "message": {
                        "content": (
                            '{"summary": "Giải thích", "key_points": ["Điểm 1"], '
                            '"questions": ["Câu hỏi?"], '
                            '"examples": [{"prompt": "VD?", "solution": "Giải"}], '
                            '"teaching_steps": ["Bước 1"], "confidence": 0.9}'
                        )
                    }
                },
            )

        client = httpx.Client(transport=httpx.MockTransport(handler))
        provider = OllamaCopilotProvider(
            url="http://ollama:11434", model="llama3.2", http_client=client
        )
        result = provider.suggest(_quadratic_request())
        assert result.provider == "ollama"
        assert result.summary == "Giải thích"
        assert result.confidence == pytest.approx(0.9)

    def test_json_sai_schema(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"message": {"content": "{oops"}})

        client = httpx.Client(transport=httpx.MockTransport(handler))
        provider = OllamaCopilotProvider(
            url="http://ollama:11434", model="llama3.2", http_client=client
        )
        with pytest.raises(RuntimeError, match="JSON"):
            provider.suggest(_quadratic_request())

    def test_khong_ket_noi_duoc(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection refused", request=request)

        client = httpx.Client(transport=httpx.MockTransport(handler))
        provider = OllamaCopilotProvider(
            url="http://localhost:11434", model="llama3.2", http_client=client
        )
        with pytest.raises(RuntimeError, match="Ollama"):
            provider.suggest(_quadratic_request())


class TestRecognitionDiagnostics:
    """Kiểm tra khả dụng provider qua ping dịch vụ ngoài (HTTP mock)."""

    def test_mock_luon_san_sang(self) -> None:
        result = check_provider_availability("mock")
        assert result.available is True
        assert "Giả lập" in result.detail

    def test_ollama_server_chet(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection refused", request=request)

        client = httpx.Client(transport=httpx.MockTransport(handler))
        result = check_provider_availability("ollama_vision", http_client=client)
        assert result.available is False
        assert "ollama serve" in result.detail

    def test_ollama_chay_nhung_thieu_model(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"models": [{"name": "llama3.2"}]})

        client = httpx.Client(transport=httpx.MockTransport(handler))
        result = check_provider_availability("ollama_vision", http_client=client)
        assert result.available is True
        assert "ollama pull llava" in result.detail

    def test_ollama_du_model(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"models": [{"name": "llava:latest"}]})

        client = httpx.Client(transport=httpx.MockTransport(handler))
        result = check_provider_availability("ollama_vision", http_client=client)
        assert result.available is True
        assert "sẵn sàng" in result.detail

    def test_pix2text_chet(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection refused", request=request)

        client = httpx.Client(transport=httpx.MockTransport(handler))
        result = check_provider_availability("pix2text", http_client=client)
        assert result.available is False
        assert "p2t serve" in result.detail

    def test_pix2text_song(self) -> None:
        client = httpx.Client(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, text="<html>p2t</html>")
            )
        )
        result = check_provider_availability("pix2text", http_client=client)
        assert result.available is True
        assert "sẵn sàng" in result.detail

    def test_provider_khong_xac_dinh(self) -> None:
        result = check_provider_availability("spam")
        assert result.available is False
        assert "không xác định" in result.detail

    def test_check_all_du_3_provider(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection refused", request=request)

        client = httpx.Client(transport=httpx.MockTransport(handler))
        results = check_all(http_client=client)
        assert [r.provider for r in results] == ["mock", "ollama_vision", "pix2text"]
        assert results[0].available is True
        assert results[1].available is False
        assert results[2].available is False
