"""Unit test cho Math Engine (SymPy) - nguồn sự thật toán học."""

from __future__ import annotations

import math

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


class TestAnalyzeRational:
    def test_nhan_dang_rational(self) -> None:
        result = analyze_expression("y = (2x + 1)/(x - 1)")
        assert result.kind == "rational"
        r = result.rational
        assert r.a == 2
        assert r.b == 1
        assert r.c == 1
        assert r.d == -1
        assert r.poles == pytest.approx([1.0])
        assert r.vertical_asymptotes == ["x = 1"]
        assert r.horizontal_asymptote == "y = 2"
        assert r.root == pytest.approx(-0.5)
        assert r.y_intercept == pytest.approx(-1.0)
        assert r.domain == "x ≠ 1"
        assert len(r.sample_points) > 10

    def test_rational_tu_so_hang_so(self) -> None:
        result = analyze_expression("1/(x + 1)")
        r = result.rational
        assert r.a == 0
        assert r.b == 1
        assert r.c == 1
        assert r.d == 1
        assert r.root is None
        assert r.horizontal_asymptote == "y = 0"

    def test_rational_hep_nghich_dao(self) -> None:
        result = analyze_expression("1/x")
        r = result.rational
        assert r.poles == pytest.approx([0.0])
        assert r.vertical_asymptotes == ["x = 0"]
        assert r.y_intercept is None

    def test_rational_bac_tu_cao_bi_tu_choi(self) -> None:
        with pytest.raises(MathEngineError):
            analyze_expression("(x^2 - 1)/(x - 2)")


class TestAnalyzeTrig:
    def test_nhan_dang_sin(self) -> None:
        result = analyze_expression("2*sin(x) + 1")
        assert result.kind == "trigonometric"
        t = result.trigonometric
        assert t.func == "sin"
        assert t.amplitude == 2
        assert t.period == pytest.approx(2 * math.pi)
        assert t.midline == 1
        assert t.max_value == 3
        assert t.min_value == -1
        assert len(t.sample_points) > 10

    def test_nhan_dang_cos_phan_shift(self) -> None:
        result = analyze_expression("cos(x - 1)")
        t = result.trigonometric
        assert t.func == "cos"
        assert t.phase_shift == pytest.approx(1.0)
        assert t.amplitude == 1

    def test_trig_co_nghiem(self) -> None:
        result = analyze_expression("sin(x)")
        assert len(result.trigonometric.roots) > 0


class TestAnalyzeExponential:
    def test_nhan_dang_mu_co_so_2(self) -> None:
        result = analyze_expression("2**x")
        assert result.kind == "exponential"
        e = result.exponential
        assert e.base == 2
        assert e.direction == "up"
        assert e.horizontal_asymptote == "y = 0"
        assert e.y_intercept == 1
        assert e.x_intercept is None

    def test_mu_voi_hang_so(self) -> None:
        result = analyze_expression("2*3**x + 1")
        e = result.exponential
        assert e.a == 2
        assert e.base == 3
        assert e.c == 1
        assert e.horizontal_asymptote == "y = 1"
        assert e.y_intercept == 3

    def test_mu_co_nghiem(self) -> None:
        result = analyze_expression("2**x - 1")
        e = result.exponential
        assert e.x_intercept == pytest.approx(0.0)

    def test_mu_theo_e(self) -> None:
        result = analyze_expression("e^x")
        assert result.kind == "exponential"
        assert result.exponential.base == pytest.approx(math.e)

    def test_mu_voi_he_so_am(self) -> None:
        result = analyze_expression("-2**x")
        e = result.exponential
        assert e.a == -1
        assert e.direction == "up"


class TestAnalyzeLogarithmic:
    def test_nhan_dang_log_tu_nhien(self) -> None:
        result = analyze_expression("log(x)")
        assert result.kind == "logarithmic"
        lg = result.logarithmic
        assert lg.base == pytest.approx(math.e)
        assert lg.domain == "x > 0"
        assert lg.vertical_asymptote == "x = 0"
        assert lg.x_intercept == pytest.approx(1.0)
        assert len(lg.sample_points) > 10

    def test_log_co_so_10(self) -> None:
        result = analyze_expression("2*log(x, 10) + 1")
        lg = result.logarithmic
        assert lg.base == 10
        assert lg.x_intercept == pytest.approx(10**-0.5)

    def test_ln_duoc_ho_tro(self) -> None:
        result = analyze_expression("ln(x) - 1")
        lg = result.logarithmic
        assert lg.base == pytest.approx(math.e)
        assert lg.x_intercept == pytest.approx(math.e)


class TestPreprocessInput:
    """Các dạng viết biểu thức khác nhau (ngoặc nhọn, mũ Unicode, ký hiệu, lg)."""

    def test_ngoac_nhon_trong_so_mu(self) -> None:
        result = analyze_expression("2*3**{x}-1")
        assert result.kind == "exponential"
        e = result.exponential
        assert e.base == 3
        assert e.c == -1

    def test_ngoac_nhon_latex_3_mu_x(self) -> None:
        result = analyze_expression("3^{x}")
        assert result.kind == "exponential"
        assert result.exponential.base == 3

    def test_ngoac_nhon_voi_ve_trai(self) -> None:
        result = analyze_expression("y=2*3^{x}")
        assert result.kind == "exponential"

    def test_ngoac_nhon_bieu_thuc_so_mu(self) -> None:
        result = analyze_expression("2^{(x)}-3")
        assert result.kind == "exponential"
        assert result.exponential.c == -3

    def test_mu_unicode_bac_hai(self) -> None:
        result = analyze_expression("x²-4x+3")
        assert result.kind == "quadratic"
        q = result.quadratic
        assert q.a == 1
        assert q.b == -4
        assert q.c == 3

    def test_mu_unicode_bac_ba_bi_tu_choi(self) -> None:
        with pytest.raises(MathEngineError):
            analyze_expression("2x³+1")

    def test_mu_unicode_am(self) -> None:
        result = analyze_expression("x⁻¹+1")
        assert result.kind == "rational"

    def test_nhan_giua_la_cham(self) -> None:
        result = analyze_expression("2·3^x")
        assert result.kind == "exponential"
        assert result.exponential.a == 2

    def test_nhan_giua_la_cham_nhan(self) -> None:
        result = analyze_expression("2×3^x")
        assert result.kind == "exponential"

    def test_chia_la_gach_cheo(self) -> None:
        result = analyze_expression("x÷2+1")
        assert result.kind == "linear"

    def test_lg_la_log_co_so_10(self) -> None:
        result = analyze_expression("lg(x)")
        assert result.kind == "logarithmic"
        assert result.logarithmic.base == 10

    def test_log10_la_log_co_so_10(self) -> None:
        result = analyze_expression("log10(x)")
        assert result.kind == "logarithmic"
        assert result.logarithmic.base == 10

    def test_log2_la_log_co_so_2(self) -> None:
        result = analyze_expression("log2(x)")
        assert result.kind == "logarithmic"
        assert result.logarithmic.base == 2

    def test_subscript_co_so_log(self) -> None:
        result = analyze_expression("log₂(x)")
        assert result.kind == "logarithmic"
        assert result.logarithmic.base == 2

    def test_log_khong_co_so_van_la_ln(self) -> None:
        result = analyze_expression("log(x)")
        assert result.logarithmic.base == pytest.approx(math.e)

    def test_he_so_ky_tu_bi_tu_choi(self) -> None:
        with pytest.raises(MathEngineError):
            analyze_expression("a*3**{x}-1")


class TestUnsupported:
    def test_bac_ba_bi_tu_choi(self) -> None:
        with pytest.raises(MathEngineError):
            analyze_expression("x^3 - 1")

    def test_tan_bi_tu_choi(self) -> None:
        with pytest.raises(MathEngineError):
            analyze_expression("tan(x)")

    def test_tich_trig_bi_tu_choi(self) -> None:
        with pytest.raises(MathEngineError):
            analyze_expression("sin(x)*cos(x)")

    def test_hon_hop_bi_tu_choi(self) -> None:
        with pytest.raises(MathEngineError):
            analyze_expression("sin(x) + 1/x")

    def test_bien_mu_bien_bi_tu_choi(self) -> None:
        with pytest.raises(MathEngineError):
            analyze_expression("x^x")