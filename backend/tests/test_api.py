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
        assert response.json()["status"] == "ok"


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