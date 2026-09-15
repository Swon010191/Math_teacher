"""Test tích hợp cho API (math, recognize, health)."""

from __future__ import annotations

import math
import re
import time

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.copilot import CopilotSuggestion


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


class TestHealth:
    def test_health(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["recognition_provider"] == "mock"
        assert data["copilot_provider"] == "rule_based"


class TestCopilot:
    def test_activity_bien_nguon_mo_copilot_dung_ten_trusted(
        self, client: TestClient
    ) -> None:
        activity_response = client.post(
            "/api/math/activity", json={"expression": "z = 2*t + 1"}
        )
        assert activity_response.status_code == 200
        activity = activity_response.json()
        activity["math"]["source_variable"] = "fake_x"
        activity["math"]["dependent_variable"] = "fake_y"

        response = client.post(
            "/api/copilot/suggest",
            json={
                "expression": "z = 2*t + 1",
                "activity_type": activity["type"],
                "math": activity["math"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        prose = " ".join(
            [
                data["summary"],
                *data["key_points"],
                *data["questions"],
                *data["teaching_steps"],
                *(item["prompt"] for item in data["examples"]),
                *(item["solution"] for item in data["examples"]),
            ]
        )
        assert "z = 2*t + 1" in prose
        assert "t = -0.5" in prose
        assert "fake_x" not in prose and "fake_y" not in prose
        assert re.search(r"\b[xy]\b", prose) is None

    def test_suggest_quadratic(self, client: TestClient) -> None:
        response = client.post(
            "/api/copilot/suggest",
            json={
                "expression": "x**2 - 4*x + 3",
                "activity_type": "quadratic_function",
                "math": {
                    "expression": "x**2 - 4*x + 3",
                    "a": 1.0,
                    "b": -4.0,
                    "c": 3.0,
                    "vertex": [2.0, -1.0],
                    "roots": [1.0, 3.0],
                    "axis": "x = 2",
                    "y_intercept": 3.0,
                    "discriminant": 4.0,
                    "direction": "up",
                },
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "rule_based"
        assert "parabol" in data["summary"]
        assert len(data["key_points"]) >= 2
        assert len(data["questions"]) >= 2
        assert len(data["examples"]) >= 1
        assert len(data["teaching_steps"]) >= 2
        assert 0.0 <= data["confidence"] <= 1.0

    def test_suggest_linear(self, client: TestClient) -> None:
        response = client.post(
            "/api/copilot/suggest",
            json={
                "expression": "2*x + 1",
                "activity_type": "linear_function",
                "math": {
                    "expression": "2*x + 1",
                    "a": 2.0,
                    "b": 1.0,
                    "root": -0.5,
                    "y_intercept": 1.0,
                },
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "đường thẳng" in data["summary"]
        assert "(-0.5; 0)" in data["key_points"][3]

    def test_suggest_thieu_truong(self, client: TestClient) -> None:
        response = client.post("/api/copilot/suggest", json={})
        assert response.status_code == 422

    def test_suggest_rational(self, client: TestClient) -> None:
        response = client.post(
            "/api/copilot/suggest",
            json={
                "expression": "(2*x + 1)/(x - 1)",
                "activity_type": "rational_function",
                "math": {
                    "expression": "(2*x + 1)/(x - 1)",
                    "a": 2.0,
                    "b": 1.0,
                    "c": 1.0,
                    "d": -1.0,
                    "root": -0.5,
                    "y_intercept": -1.0,
                    "domain": "x ≠ 1",
                    "asymptotes": ["x = 1", "y = 2"],
                },
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "tiệm cận" in data["summary"]
        assert "tiệm cận đứng" in data["key_points"][1]
        assert len(data["teaching_steps"]) >= 2

    @pytest.mark.parametrize(
        ("expression", "fake_type", "trusted_type"),
        [
            ("x**2 - 4*x + 3", "linear_function", "quadratic_function"),
            ("-log(x, 2)", "quadratic_function", "logarithmic_function"),
            ("(2*x - 2)/(x - 1)", "linear_function", "rational_function"),
        ],
    )
    def test_provider_chi_nhan_facts_da_xac_minh_va_bieu_thuc_de_doc(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
        expression: str,
        fake_type: str,
        trusted_type: str,
    ) -> None:
        captured = []

        class CapturingProvider:
            name = "capture"

            def suggest(self, request):  # type: ignore[no-untyped-def]
                captured.append(request)
                return CopilotSuggestion(
                    provider=self.name,
                    summary="ok",
                    key_points=[],
                    questions=[],
                    examples=[],
                    teaching_steps=[],
                    confidence=1,
                )

        monkeypatch.setattr(
            "app.services.copilot_service._build_provider", lambda: CapturingProvider()
        )
        response = client.post(
            "/api/copilot/suggest",
            json={
                "expression": expression,
                "activity_type": fake_type,
                "math": {
                    "expression": "FAKE",
                    "a": 999,
                    "roots": [999],
                    "direction": "up",
                },
            },
        )
        assert response.status_code == 200
        trusted = captured[0]
        assert trusted.activity_type == trusted_type
        assert "Symbol(" not in trusted.math.expression
        assert "Integer(" not in trusted.math.expression
        if trusted_type == "logarithmic_function":
            assert trusted.math.direction == "down"
        if trusted_type == "rational_function":
            assert trusted.math.holes == [1]
            assert trusted.math.asymptotes == ["y = 2"]

    def test_trusted_request_khong_tin_metadata_bien_client(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        captured = []

        class CapturingProvider:
            name = "capture"

            def suggest(self, request):  # type: ignore[no-untyped-def]
                captured.append(request)
                return CopilotSuggestion(
                    provider=self.name,
                    summary="ok",
                    key_points=[],
                    questions=[],
                    examples=[],
                    teaching_steps=[],
                    confidence=1,
                )

        monkeypatch.setattr(
            "app.services.copilot_service._build_provider", lambda: CapturingProvider()
        )
        response = client.post(
            "/api/copilot/suggest",
            json={
                "expression": "z = 2*t + 1",
                "activity_type": "quadratic_function",
                "math": {
                    "expression": "fake",
                    "source_variable": "attacker",
                    "dependent_variable": "spoofed",
                },
            },
        )
        assert response.status_code == 200
        assert captured[0].math.source_variable == "t"
        assert captured[0].math.dependent_variable == "z"
        assert captured[0].math.expression == "2*t + 1"

    def test_copilot_bieu_thuc_khong_hop_le_tra_400(self, client: TestClient) -> None:
        response = client.post(
            "/api/copilot/suggest",
            json={
                "expression": "__import__('os').system('echo unsafe')",
                "activity_type": "quadratic_function",
                "math": {"expression": "x**2", "a": 1},
            },
        )
        assert response.status_code == 400
        assert "không hợp lệ" in response.json()["detail"].lower()


class TestCopilotProvider:
    @pytest.fixture(autouse=True)
    def reset_provider(self) -> None:
        from app.services.copilot_settings import set_active_copilot_provider

        yield
        set_active_copilot_provider("rule_based")

    def test_get_provider_mac_dinh_rule_based(self, client: TestClient) -> None:
        response = client.get("/api/copilot/provider")
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "rule_based"
        assert set(data["available"]) == {"rule_based", "ollama"}

    def test_doi_provider(self, client: TestClient) -> None:
        response = client.put("/api/copilot/provider", json={"provider": "ollama"})
        assert response.status_code == 200
        assert response.json()["provider"] == "ollama"
        check = client.get("/api/copilot/provider")
        assert check.json()["provider"] == "ollama"
        health = client.get("/health")
        assert health.json()["copilot_provider"] == "ollama"

    def test_doi_provider_khong_hop_le(self, client: TestClient) -> None:
        response = client.put("/api/copilot/provider", json={"provider": "spam"})
        assert response.status_code == 400
        assert "spam" in response.json()["detail"]

    def test_suggest_dung_provider_da_doi(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("OLLAMA_URL", "http://127.0.0.1:1")
        client.put("/api/copilot/provider", json={"provider": "ollama"})
        response = client.post(
            "/api/copilot/suggest",
            json={
                "expression": "x**2 - 4*x + 3",
                "activity_type": "quadratic_function",
                "math": {"expression": "x**2 - 4*x + 3", "a": 1.0},
            },
        )
        assert response.status_code == 500
        assert "ollama" in response.json()["detail"]


class TestRecognizeProvider:
    @pytest.fixture(autouse=True)
    def reset_provider(self) -> None:
        from app.services.recognition_settings import set_active_provider

        yield
        set_active_provider("mock")

    def test_get_provider_mac_dinh_mock(self, client: TestClient) -> None:
        response = client.get("/api/recognize/provider")
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "mock"
        assert set(data["available"]) == {"mock", "ollama_vision", "pix2text"}

    def test_doi_provider(self, client: TestClient) -> None:
        response = client.put(
            "/api/recognize/provider", json={"provider": "ollama_vision"}
        )
        assert response.status_code == 200
        assert response.json()["provider"] == "ollama_vision"
        check = client.get("/api/recognize/provider")
        assert check.json()["provider"] == "ollama_vision"

    def test_doi_provider_khong_hop_le(self, client: TestClient) -> None:
        response = client.put(
            "/api/recognize/provider", json={"provider": "spam"}
        )
        assert response.status_code == 400
        assert "spam" in response.json()["detail"]

    def test_recognize_dung_provider_da_doi(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("OLLAMA_URL", "http://127.0.0.1:1")
        client.put("/api/recognize/provider", json={"provider": "ollama_vision"})
        response = client.post("/api/recognize", json={})
        assert response.status_code == 500
        assert "ollama_vision" in response.json()["detail"]


class TestProvidersStatus:
    def test_status_mock_san_sang_provider_that_chet(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("OLLAMA_URL", "http://127.0.0.1:1")
        monkeypatch.setenv("PIX2TEXT_URL", "http://127.0.0.1:1")
        response = client.get("/api/recognize/providers/status")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        by_name = {item["provider"]: item for item in data}
        assert by_name["mock"]["available"] is True
        assert "Giả lập" in by_name["mock"]["detail"]
        assert by_name["ollama_vision"]["available"] is False
        assert "ollama serve" in by_name["ollama_vision"]["detail"]
        assert by_name["pix2text"]["available"] is False
        assert "p2t serve" in by_name["pix2text"]["detail"]


class TestMathAnalyze:
    def test_analyze_quadratic(self, client: TestClient) -> None:
        response = client.post(
            "/api/math/analyze", json={"expression": "y = x^2 - 4x + 3"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["kind"] == "quadratic"
        assert data["quadratic"]["vertex"] == [2.0, -1.0]
        assert data["quadratic"]["roots"] == [1.0, 3.0]

    def test_analyze_bieu_thuc_sai(self, client: TestClient) -> None:
        response = client.post("/api/math/analyze", json={"expression": "abc!!!"})
        assert response.status_code == 400

    def test_analyze_payload_ngoai_allowlist(self, client: TestClient) -> None:
        response = client.post(
            "/api/math/analyze",
            json={"expression": "__import__('os').system('echo unsafe')"},
        )
        assert response.status_code == 400

    @pytest.mark.parametrize(
        "expression",
        ["(x**3 - 1)/(x - 1) - x**2 - x", "(x-x)/(x-x)", "0/(x-x)"],
    )
    def test_analyze_rational_structural_invalid_tra_400(
        self, client: TestClient, expression: str
    ) -> None:
        response = client.post("/api/math/analyze", json={"expression": expression})
        assert response.status_code == 400

    @pytest.mark.parametrize(
        "expression",
        [
            "*".join(["(sin(x)+cos(x))"] * 10),
            "1e-308*sin(x)-1e308",
            "1e308*sin(x)-1e308",
            "1e308*2**x+1e308",
        ],
    )
    def test_analyze_complexity_va_derived_overflow_tra_400(
        self, client: TestClient, expression: str
    ) -> None:
        started = time.perf_counter()
        response = client.post("/api/math/analyze", json={"expression": expression})
        assert response.status_code == 400
        assert "null" not in response.text.lower()
        assert time.perf_counter() - started < 1.0

    def test_analyze_thieu_truong(self, client: TestClient) -> None:
        response = client.post("/api/math/analyze", json={})
        assert response.status_code == 422

    def test_analyze_va_activity_bao_toan_bien_nguon(self, client: TestClient) -> None:
        analyzed = client.post(
            "/api/math/analyze", json={"expression": "z = 2*t + 1"}
        )
        assert analyzed.status_code == 200
        assert analyzed.json()["source_variable"] == "t"
        assert analyzed.json()["dependent_variable"] == "z"

        activity = client.post(
            "/api/math/activity", json={"expression": "t^2 - 1"}
        )
        assert activity.status_code == 200
        assert activity.json()["math"]["source_variable"] == "t"
        assert activity.json()["math"]["expression"] == "t**2 - 1"

    @pytest.mark.parametrize(
        ("left_definition", "right_definition", "source", "dependent"),
        [
            ("z = 2 t + 1", "2t+1 = z", "t", "z"),
            ("g(u) = 2u + 1", "2 u+1 = g (u)", "u", "g"),
        ],
    )
    def test_analyze_va_activity_dinh_nghia_ham_doi_xung(
        self,
        client: TestClient,
        left_definition: str,
        right_definition: str,
        source: str,
        dependent: str,
    ) -> None:
        analyzed = [
            client.post("/api/math/analyze", json={"expression": expression})
            for expression in (left_definition, right_definition)
        ]
        assert all(response.status_code == 200 for response in analyzed)
        analyze_data = [response.json() for response in analyzed]
        for data in analyze_data:
            assert data["kind"] == "linear"
            assert data["linear"]["a"] == 2
            assert data["linear"]["b"] == 1
            assert data["source_variable"] == source
            assert data["dependent_variable"] == dependent
            assert data["canonical_expression"] == f"2*{source} + 1"

        activities = [
            client.post("/api/math/activity", json={"expression": expression})
            for expression in (left_definition, right_definition)
        ]
        assert all(response.status_code == 200 for response in activities)
        activity_data = [response.json() for response in activities]
        graph_metadata = [
            {
                "type": data["type"],
                "math": data["math"],
                "widgets": data["widgets"],
            }
            for data in activity_data
        ]
        assert graph_metadata[0] == graph_metadata[1]
        assert graph_metadata[0]["type"] == "linear_function"
        assert graph_metadata[0]["math"]["expression"] == f"2*{source} + 1"
        assert graph_metadata[0]["math"]["source_variable"] == source
        assert graph_metadata[0]["math"]["dependent_variable"] == dependent
        assert graph_metadata[0]["math"]["a"] == 2
        assert graph_metadata[0]["math"]["b"] == 1
        assert graph_metadata[0]["widgets"][0]["type"] == "graph"

    @pytest.mark.parametrize("expression", ["x+y=2", "2x+1=5", "x=2"])
    def test_analyze_khong_nhan_phuong_trinh_la_dinh_nghia_ham(
        self, client: TestClient, expression: str
    ) -> None:
        response = client.post("/api/math/analyze", json={"expression": expression})
        assert response.status_code == 400


class TestMathSolve:
    def test_solve_linear_api(self, client: TestClient) -> None:
        response = client.post(
            "/api/math/solve", json={"expression": "2u + 3 = 9"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["answers"][0]["exact"] == "3"
        assert data["verified"] is True
        assert data["steps"][2]["metadata"] == {
            "kind": "coefficient_identification",
            "rule": "linear_coefficients",
            "values": {"a": "2", "b": "-6"},
        }

    @pytest.mark.parametrize(
        "payload",
        [
            {"expression": "x+y=2"},
            {"expression": "u^3=1"},
            {"expression": "__import__('os').system('echo unsafe')"},
        ],
    )
    def test_solve_loi_tra_400(self, client: TestClient, payload: dict) -> None:
        response = client.post("/api/math/solve", json=payload)
        assert response.status_code == 400

    def test_solve_nhieu_bien_co_solve_for(self, client: TestClient) -> None:
        response = client.post(
            "/api/math/solve",
            json={"expression": "x+y=2", "solve_for": "x"},
        )
        assert response.status_code == 200
        assert response.json()["answers"][0]["exact"] == "2 - y"


class TestMathActivity:
    def test_tao_activity_quadratic(self, client: TestClient) -> None:
        response = client.post(
            "/api/math/activity", json={"expression": "x**2 - 4*x + 3"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["schemaVersion"] == "1.0"
        assert data["type"] == "quadratic_function"
        assert data["math"]["vertex"] == [2.0, -1.0]
        assert data["math"]["a"] == 1.0
        assert data["math"]["b"] == -4.0
        assert data["math"]["c"] == 3.0
        assert [w["type"] for w in data["widgets"]] == [
            "graph",
            "parameter_slider",
        ]
        assert len(data["steps"]) == 3
        assert data["solution"]["verified"] is True
        assert data["solution"]["solve_for"] == "x"
        assert [answer["exact"] for answer in data["solution"]["answers"]] == [
            "1",
            "3",
        ]

    def test_activity_khong_hop_le(self, client: TestClient) -> None:
        response = client.post(
            "/api/math/activity", json={"expression": "tan(x)"}
        )
        assert response.status_code == 400

    def test_tao_activity_linear(self, client: TestClient) -> None:
        response = client.post(
            "/api/math/activity", json={"expression": "2*x + 1"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["schemaVersion"] == "1.0"
        assert data["type"] == "linear_function"
        assert data["math"]["a"] == 2.0
        assert data["math"]["b"] == 1.0
        assert data["math"]["y_intercept"] == 1.0
        assert data["math"]["root"] == -0.5
        assert [w["type"] for w in data["widgets"]] == [
            "graph",
            "parameter_slider",
        ]
        assert len(data["steps"]) == 2
        assert data["solution"]["verified"] is True
        assert data["solution"]["answers"][0]["exact"] == "-1/2"

    def test_tao_activity_rational(self, client: TestClient) -> None:
        response = client.post(
            "/api/math/activity", json={"expression": "(2*x+1)/(x-1)"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["schemaVersion"] == "1.0"
        assert data["type"] == "rational_function"
        assert data["math"]["a"] == 2.0
        assert data["math"]["b"] == 1.0
        assert data["math"]["c"] == 1.0
        assert data["math"]["d"] == -1.0
        assert data["math"]["asymptotes"] == ["x = 1", "y = 2"]
        assert data["math"]["domain"] == "x ≠ 1"
        assert data["math"]["root"] == -0.5
        assert data["widgets"][1]["parameters"] == ["a", "b", "c", "d"]
        assert len(data["steps"]) == 3
        assert data["solution"] is None

    def test_activity_solution_bao_toan_bien_nguon(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/api/math/activity", json={"expression": "z = 2*t + 1"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["math"]["source_variable"] == "t"
        assert data["math"]["dependent_variable"] == "z"
        assert data["math"]["expression"] == "2*t + 1"
        assert data["solution"]["solve_for"] == "t"
        assert data["solution"]["canonical_equation"] == "2*t + 1 = 0"
        assert data["solution"]["verified"] is True

    def test_activity_rational_giu_diem_khuyet_va_he_so_goc(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/api/math/activity", json={"expression": "(2*x-2)/(x-1)"}
        )
        assert response.status_code == 200
        math_data = response.json()["math"]
        assert [math_data[key] for key in ("a", "b", "c", "d")] == [2, -2, 1, -1]
        assert math_data["holes"] == [1]
        assert math_data["asymptotes"] == ["y = 2"]

    def test_tao_activity_trig(self, client: TestClient) -> None:
        response = client.post(
            "/api/math/activity", json={"expression": "2*sin(x) + 1"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["schemaVersion"] == "1.0"
        assert data["type"] == "trig_function"
        assert data["math"]["func"] == "sin"
        assert data["math"]["amplitude"] == 2.0
        assert data["math"]["period"] == pytest.approx(2 * math.pi)
        assert data["math"]["max_value"] == 3.0
        assert data["math"]["min_value"] == -1.0
        assert data["widgets"][1]["parameters"] == ["a", "b", "c", "d"]

    def test_tao_activity_exponential(self, client: TestClient) -> None:
        response = client.post(
            "/api/math/activity", json={"expression": "2**x"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["schemaVersion"] == "1.0"
        assert data["type"] == "exponential_function"
        assert data["math"]["base"] == 2.0
        assert data["math"]["asymptotes"] == ["y = 0"]
        assert data["math"]["y_intercept"] == 1.0

    def test_tao_activity_logarithmic(self, client: TestClient) -> None:
        response = client.post(
            "/api/math/activity", json={"expression": "log(x)"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["schemaVersion"] == "1.0"
        assert data["type"] == "logarithmic_function"
        assert data["math"]["base"] == pytest.approx(math.e)
        assert data["math"]["asymptotes"] == ["x = 0"]
        assert data["math"]["root"] == pytest.approx(1.0)


class TestRecognize:
    def test_mock_recognize(self, client: TestClient) -> None:
        response = client.post("/api/recognize", json={})
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "mock"
        assert 0.0 <= data["confidence"] <= 1.0
        assert data["expression"]
        assert "=" in data["expression"]

    def test_loi_provider_khong_lo_url(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("PIX2TEXT_URL", "http://127.0.0.1:1")
        assert client.put("/api/recognize/provider", json={"provider": "pix2text"}).status_code == 200
        try:
            response = client.post(
                "/api/recognize",
                json={"image_base64": "aGVsbG8=", "hint": "x+1"},
            )
            assert response.status_code == 500
            assert "127.0.0.1" not in response.json()["detail"]
        finally:
            client.put("/api/recognize/provider", json={"provider": "mock"})
