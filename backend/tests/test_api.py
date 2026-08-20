"""Test tích hợp cho API (math, recognize, health)."""

from __future__ import annotations

import math

import pytest
from fastapi.testclient import TestClient

from app.main import app


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

    def test_analyze_thieu_truong(self, client: TestClient) -> None:
        response = client.post("/api/math/analyze", json={})
        assert response.status_code == 422


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