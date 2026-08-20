"""Unit test cho Math Engine (SymPy) - nguồn sự thật toán học."""

from __future__ import annotations

import pytest

from app.services.math_service import (
    MathEngineError,
    analyze_expression,
    normalize_expression,
)


class TestNormalizeExpression:
    def test_chuyen_xor_thanh_power(self) -> None:
        assert "Pow(Symbol('x'), Integer(2))" in normalize_expression("x^2")

    def test_nhan_am_an_4x(self) -> None:
        assert "Mul" in normalize_expression("4x")

    def test_bo_ve_trai_y(self) -> None:
        normalized = normalize_expression("y = x^2 - 4x + 3")
        assert "Pow" in normalized

    def test_bo_ve_trai_fx(self) -> None:
        normalized = normalize_expression("f(x) = 2x + 1")
        assert "Integer(1)" in normalized

    def test_bieu_thuc_trong(self) -> None:
        with pytest.raises(MathEngineError):
            normalize_expression("   ")

    def test_bieu_thuc_vo_nghia(self) -> None:
        with pytest.raises(MathEngineError):
            analyze_expression("abc!!!")


class TestAnalyzeQuadratic:
    @pytest.fixture()
    def result(self) -> object:
        return analyze_expression("y = x^2 - 4x + 3")

    def test_nhan_dang_quadratic(self, result: object) -> None:
        assert result.kind == "quadratic"

    def test_he_so(self, result: object) -> None:
        q = result.quadratic
        assert q.a == 1
        assert q.b == -4
        assert q.c == 3

    def test_dinh(self, result: object) -> None:
        q = result.quadratic
        assert q.vertex == pytest.approx([2.0, -1.0])

    def test_nghiem(self, result: object) -> None:
        q = result.quadratic
        assert q.roots == pytest.approx([1.0, 3.0])

    def test_truc_doi_xung(self, result: object) -> None:
        assert result.quadratic.axis == "x = 2"

    def test_giao_diem_truc_tung(self, result: object) -> None:
        assert result.quadratic.y_intercept == 3.0

    def test_discriminant(self, result: object) -> None:
        assert result.quadratic.discriminant == 4.0

    def test_be_loi_len(self, result: object) -> None:
        assert result.quadratic.direction == "up"

    def test_diem_mau_du_sl(self, result: object) -> None:
        q = result.quadratic
        assert len(q.sample_points) > 10
        x_vals = [p[0] for p in q.sample_points]
        assert min(x_vals) <= 2.0 <= max(x_vals)


class TestAnalyzeQuadraticVariants:
    def test_he_so_a_am(self) -> None:
        result = analyze_expression("-x^2 + 6x - 5")
        q = result.quadratic
        assert q.a == -1
        assert q.direction == "down"
        assert q.vertex == pytest.approx([3.0, 4.0])
        assert q.roots == pytest.approx([1.0, 5.0])

    def test_nghiem_vo_ti(self) -> None:
        result = analyze_expression("x^2 - 2")
        q = result.quadratic
        assert q.roots == pytest.approx([-(2**0.5), 2**0.5])

    def test_vo_nghiem_thuc(self) -> None:
        result = analyze_expression("x^2 + 1")
        q = result.quadratic
        assert q.roots == []
        assert q.discriminant < 0


class TestAnalyzeLinear:
    def test_nhan_dang_linear(self) -> None:
        result = analyze_expression("y = 2x + 1")
        assert result.kind == "linear"
        assert result.linear.a == 2
        assert result.linear.b == 1
        assert result.linear.root == pytest.approx(-0.5)
        assert result.linear.y_intercept == 1


class TestUnsupported:
    def test_bac_ba_bi_tu_choi(self) -> None:
        with pytest.raises(MathEngineError):
            analyze_expression("x^3 - 1")