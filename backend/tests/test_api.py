"""Test tích hợp cho API (math, recognize, health)."""

from __future__ import annotations

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
            "/api/math/activity", json={"expression": "sin(x)"}
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


class TestRecognize:
    def test_mock_recognize(self, client: TestClient) -> None:
        response = client.post("/api/recognize", json={})
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "mock"
        assert 0.0 <= data["confidence"] <= 1.0
        assert data["expression"]