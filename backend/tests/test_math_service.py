"""Unit test cho Math Engine (SymPy) - nguồn sự thật toán học."""

from __future__ import annotations

import math
import time

import pytest

from app.schemas.math import SolveStep
from app.services.math_service import (
    MathEngineError,
    _real_roots,
    analyze_expression,
    canonical_expression,
    normalize_expression,
    solve_equation,
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

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("t^2 - 1", "t**2 - 1"),
            ("z = 2*t + 1", "2*t + 1"),
            ("f(u) = u^2 + 2*u", "u**2 + 2*u"),
        ],
    )
    def test_canonical_ho_tro_bien_nguon(
        self, raw: str, expected: str
    ) -> None:
        assert canonical_expression(raw) == expected

    def test_bieu_thuc_trong(self) -> None:
        with pytest.raises(MathEngineError):
            normalize_expression("   ")

    def test_bieu_thuc_vo_nghia(self) -> None:
        with pytest.raises(MathEngineError):
            analyze_expression("abc!!!")

    @pytest.mark.parametrize(
        "payload",
        [
            "().__class__.__mro__",
            "__import__('os').system('echo unsafe')",
            "Symbol('x')",
            "unknown(x)",
            "x.real",
            "[x]",
        ],
    )
    def test_tu_choi_payload_ngoai_allowlist(self, payload: str) -> None:
        with pytest.raises(MathEngineError):
            analyze_expression(payload)

    @pytest.mark.parametrize(
        "expression",
        [
            "1e309*x + 1",
            "-1e309*x",
            "x**(2**100)",
            "(x + 1)**(2**20)",
            "x**((-1)**0.5)",
        ],
    )
    def test_tu_choi_so_khong_huu_han_va_so_mu_long(
        self, expression: str
    ) -> None:
        with pytest.raises(MathEngineError):
            analyze_expression(expression)

    def test_so_thap_phan_hop_le(self) -> None:
        result = analyze_expression("0.5x + 1")
        assert result.linear.a == pytest.approx(0.5)


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

    def test_bien_nguon_bat_ky_va_dinh_nghia_ham(self) -> None:
        quadratic = analyze_expression("t^2 - 1")
        assert quadratic.source_variable == "t"
        assert quadratic.canonical_expression == "t**2 - 1"

        linear = analyze_expression("z = 2*t + 1")
        assert linear.kind == "linear"
        assert linear.source_variable == "t"
        assert linear.dependent_variable == "z"

        function = analyze_expression("f(t) = t^2 - 1")
        assert function.source_variable == "t"
        assert function.dependent_variable == "f"

    @pytest.mark.parametrize(
        ("left_definition", "right_definition"),
        [
            ("z = 2 t + 1", "2t+1 = z"),
            ("g(u) = 3u - 4", "3 u-4 = g ( u )"),
        ],
    )
    def test_dinh_nghia_ham_doi_xung_co_cung_ket_qua(
        self, left_definition: str, right_definition: str
    ) -> None:
        left = analyze_expression(left_definition)
        right = analyze_expression(right_definition)

        assert left.kind == right.kind == "linear"
        assert left.linear == right.linear
        assert left.source_variable == right.source_variable
        assert left.dependent_variable == right.dependent_variable
        assert left.canonical_expression == right.canonical_expression

    @pytest.mark.parametrize("expression", ["x+y=2", "2x+1=5", "x=2", "x=x+1"])
    def test_phuong_trinh_khong_phai_dinh_nghia_ham_bi_tu_choi(
        self, expression: str
    ) -> None:
        with pytest.raises(MathEngineError):
            analyze_expression(expression)


class TestSolveEquation:
    def test_solve_step_giu_contract_cu_khi_khong_co_metadata(self) -> None:
        step = SolveStep(expression="x = 1", explanation="Nghiệm", latex="x=1")
        assert step.expression == "x = 1"
        assert step.explanation == "Nghiệm"
        assert step.latex == "x=1"
        assert step.metadata is None

    def test_linear(self) -> None:
        result = solve_equation("2u + 3 = 9")
        assert result.status == "solved"
        assert result.solve_for == "u"
        assert result.degree == 1
        assert result.answers[0].exact == "3"
        assert result.verified is True
        assert [step.metadata.kind for step in result.steps] == [
            "equation",
            "transformation",
            "coefficient_identification",
            "transformation",
            "formula",
            "answer",
            "verification",
        ]
        assert all(step.latex for step in result.steps)

    def test_linear_steps_dung_gia_tri_sympy_chinh_xac(self) -> None:
        result = solve_equation("0.5*x + 0.25 = 1")
        coefficients = result.steps[2].metadata.values
        assert coefficients == {"a": "1/2", "b": "-3/4"}
        assert result.answers[0].exact == "3/2"
        assert result.steps[-1].metadata.rule == "exact_substitution"
        assert result.steps[-1].metadata.values == {"3/2": "0"}

    def test_quadratic_va_can_chinh_xac(self) -> None:
        simple = solve_equation("t^2 - 1 = 0")
        assert [answer.exact for answer in simple.answers] == ["-1", "1"]

        irrational = solve_equation("u^2 - 2 = 0")
        assert {answer.exact for answer in irrational.answers} == {
            "-sqrt(2)",
            "sqrt(2)",
        }
        assert all(answer.approximate is not None for answer in irrational.answers)

        assert [step.metadata.kind for step in irrational.steps] == [
            "equation",
            "transformation",
            "coefficient_identification",
            "discriminant",
            "formula",
            "answer",
            "verification",
        ]
        assert irrational.steps[3].metadata.values["discriminant"] == "8"

    def test_quadratic_khong_co_nghiem_thuc_van_co_buoc_xac_minh(self) -> None:
        result = solve_equation("x^2 + 1 = 0")
        assert result.status == "no_solution"
        assert result.answers == []
        assert result.steps[-1].metadata.kind == "verification"
        assert result.steps[-1].expression == "discriminant = -4 < 0"

    def test_symbol_khac_la_tham_so(self) -> None:
        result = solve_equation("x + y = 2", "x")
        assert result.variables == ["x", "y"]
        assert result.answers[0].exact == "2 - y"

    def test_he_so_suy_bien_co_day_du_nhanh(self) -> None:
        linear = solve_equation("a*x + b = 0", "x")
        assert linear.status == "conditional"
        assert {case.status for case in linear.cases} == {
            "solved",
            "no_solution",
            "infinite_solutions",
        }
        assert any(step.metadata.kind == "case_analysis" for step in linear.steps)

        quadratic = solve_equation("a*x^2 + b*x + c = 0", "x")
        assert quadratic.status == "conditional"
        assert any(
            case.status == "solved" and "a = 0" in case.condition
            for case in quadratic.cases
        )
        assert quadratic.steps[3].metadata.values["discriminant"] == "-4*a*c + b**2"
        positive = next(case for case in quadratic.cases if "b**2 > 0" in case.condition)
        repeated = next(case for case in quadratic.cases if "b**2 = 0" in case.condition)
        negative = next(case for case in quadratic.cases if "b**2 < 0" in case.condition)
        assert len(positive.answers) == 2
        assert len(repeated.answers) == 1
        assert negative.status == "no_solution"

    @pytest.mark.parametrize(
        ("expression", "status", "classification"),
        [("0*x = 0", "infinite_solutions", "identity"), ("0*x = 1", "no_solution", "contradiction")],
    )
    def test_phuong_trinh_suy_bien_hang(
        self, expression: str, status: str, classification: str
    ) -> None:
        result = solve_equation(expression)
        assert result.status == status
        assert result.classification == classification
        assert [step.metadata.kind for step in result.steps[-2:]] == [
            "answer",
            "verification",
        ]

    def test_phuong_trinh_hang_phu_thuoc_tham_so(self) -> None:
        result = solve_equation("0*x + a = 0", "x")
        assert result.status == "conditional"
        assert [(case.condition, case.status) for case in result.cases] == [
            ("a = 0", "infinite_solutions"),
            ("a != 0", "no_solution"),
        ]
        assert result.steps[-1].metadata.values["case_count"] == "2"

    def test_thieu_solve_for_khi_nhieu_bien(self) -> None:
        with pytest.raises(MathEngineError, match="variables: x, y"):
            solve_equation("x + y = 2")

    @pytest.mark.parametrize(
        "expression",
        ["__import__('os').system('echo unsafe')", "x.real = 1", "unknown(x)=0"],
    )
    def test_payload_khong_an_toan(self, expression: str) -> None:
        with pytest.raises(MathEngineError):
            solve_equation(expression)

    def test_bac_lon_hon_hai(self) -> None:
        with pytest.raises(MathEngineError, match="bậc nhất và bậc hai"):
            solve_equation("u^3 - 1 = 0")


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

    def test_giu_he_so_goc_va_metadata_diem_khuyet(self) -> None:
        result = analyze_expression("(2*x - 2)/(x - 1)")
        r = result.rational
        assert result.kind == "rational"
        assert (r.a, r.b, r.c, r.d) == pytest.approx((2, -2, 1, -1))
        assert r.poles == pytest.approx([1])
        assert r.holes == pytest.approx([1])
        assert r.vertical_asymptotes == []
        assert r.root is None
        assert r.domain == "x ≠ 1"
        assert all(point[0] != 1 for point in r.sample_points)

    def test_tu_choi_bac_cao_du_triet_tieu(self) -> None:
        with pytest.raises(MathEngineError):
            analyze_expression("(x^2 - 1)/(x - 1)")

    def test_phan_thuc_hang_co_hole_khong_loi(self) -> None:
        result = analyze_expression("(x - 1)/(x - 1)")
        r = result.rational
        assert (r.a, r.b, r.c, r.d) == pytest.approx((1, -1, 1, -1))
        assert r.holes == pytest.approx([1])
        assert r.root is None

    def test_giu_moi_loai_tru_mien_tu_tong_phan_thuc(self) -> None:
        result = analyze_expression("(x - 1)/(x - 1) + 1/(x - 2)")
        r = result.rational
        assert r.poles == pytest.approx([1, 2])
        assert r.holes == pytest.approx([1])
        assert r.vertical_asymptotes == ["x = 2"]
        assert r.root is None
        assert r.domain == "x ≠ 1; 2"

    def test_domain_dedup_bang_nghiem_sympy_chinh_xac(self) -> None:
        import sympy as sp

        x = sp.Symbol("x")
        roots = _real_roots(
            [x - 1, 2 * (x - 1), x - (sp.Integer(10**13) + 1) / 10**13],
            "Điểm loại trừ",
        )
        assert len(roots) == 2
        assert roots[0] == pytest.approx(1)
        assert roots[1] > roots[0]

    def test_so_sanh_hole_root_va_zero_domain_chinh_xac(self) -> None:
        hole_near_zero = analyze_expression("(x - 1e-13)/(x - 1e-13)").rational
        assert hole_near_zero.y_intercept == pytest.approx(1)

        close_root = analyze_expression("(x - 1.0000000000001)/(x - 1)").rational
        assert close_root.root == pytest.approx(1.0000000000001)

    def test_structural_routing_giu_hole_khi_rut_gon_thanh_polynomial(self) -> None:
        result = analyze_expression("(x - 1)/(x - 1) + x")
        assert result.kind == "rational"
        assert result.rational.holes == pytest.approx([1])
        assert result.rational.root == pytest.approx(-1)

    def test_structural_routing_chay_trong_budget_truoc_wildcard(self) -> None:
        started = time.perf_counter()
        result = analyze_expression("(x - 1)/(x - 1)")
        assert time.perf_counter() - started < 1.0
        assert result.rational.holes == pytest.approx([1])

    def test_tu_choi_cubic_term_truoc_khi_tong_triet_tieu(self) -> None:
        with pytest.raises(MathEngineError):
            analyze_expression("(x**3 - 1)/(x - 1) - x**2 - x")

    @pytest.mark.parametrize("expression", ["(x-x)/(x-x)", "0/(x-x)"])
    def test_tu_choi_mau_goc_dong_nhat_bang_0(self, expression: str) -> None:
        with pytest.raises(MathEngineError):
            analyze_expression(expression)


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

    def test_tim_nghiem_tiep_xuc(self) -> None:
        result = analyze_expression("sin(x) + 1")
        assert any(abs(root + math.pi / 2) < 0.02 for root in result.trigonometric.roots)

    def test_tu_choi_chu_ky_khong_huu_han(self) -> None:
        with pytest.raises(MathEngineError):
            analyze_expression("sin(1e-309*x)")

    @pytest.mark.parametrize("expression", ["sin(1e-12*x)", "sin(x + 1e12)"])
    def test_tu_choi_period_hoac_phase_vuot_budget(self, expression: str) -> None:
        with pytest.raises(MathEngineError):
            analyze_expression(expression)

    def test_lay_mau_theo_so_buoc_co_dinh(self) -> None:
        result = analyze_expression("sin(0.001*x)")
        assert len(result.trigonometric.sample_points) <= 50

    def test_nghiem_tan_so_cao_khong_bi_lam_tron_hoac_gop(self) -> None:
        result = analyze_expression("sin(1000000*x)")
        roots = result.trigonometric.roots
        assert len(roots) >= 3
        assert len(set(roots)) == len(roots)
        assert min(abs(left - right) for left, right in zip(roots, roots[1:])) < 1e-5

    def test_nghiem_tan_so_1e16_dedup_theo_ulp_va_chu_ky(self) -> None:
        roots = analyze_expression("sin(1e16*x)").trigonometric.roots
        assert len(roots) >= 3
        assert all(left < right for left, right in zip(roots, roots[1:]))

    def test_clamp_target_sat_bien_va_dedup_nghiem_tiep_xuc(self) -> None:
        result = analyze_expression("sin(x) - 1.0000000000000002")
        roots = result.trigonometric.roots
        assert len(roots) == 2
        assert all(left < right for left, right in zip(roots, roots[1:]))

    def test_tu_choi_period_nho_hon_ulp_tai_phase(self) -> None:
        with pytest.raises(MathEngineError):
            analyze_expression("sin(1e17*x + 1e17)")


class TestComplexityGuard:
    def test_chan_projected_degree_truoc_expand(self) -> None:
        with pytest.raises(MathEngineError):
            analyze_expression("(x + 1)^3 * (x + 2)^3 * (x + 3)^3")

    def test_chan_tich_10_factor_trig_truoc_expand_trong_budget(self) -> None:
        expression = "*".join(["(sin(x)+cos(x))"] * 10)
        started = time.perf_counter()
        with pytest.raises(MathEngineError):
            analyze_expression(expression)
        assert time.perf_counter() - started < 1.0

    def test_chan_tich_to_hop_ben_trong_doi_so_ham(self) -> None:
        factors = [f"(sin(x+{i})+cos(x+{i}))" for i in range(10)]
        expression = "sin(" + "*".join(factors) + ")"
        started = time.perf_counter()
        with pytest.raises(MathEngineError):
            analyze_expression(expression)
        assert time.perf_counter() - started < 1.0


class TestFiniteDerivedFacts:
    @pytest.mark.parametrize(
        "expression",
        [
            "1e-308*sin(x)-1e308",
            "1e308*sin(x)-1e308",
            "1e308*2**x+1e308",
        ],
    )
    def test_overflow_derived_fact_bi_tu_choi(self, expression: str) -> None:
        with pytest.raises(MathEngineError):
            analyze_expression(expression)


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
        assert e.direction == "down"

    def test_exp_so_mu_am_van_la_ham_mu(self) -> None:
        result = analyze_expression("exp(-x)")
        assert result.kind == "exponential"
        assert result.exponential.base == pytest.approx(math.exp(-1))
        assert result.exponential.direction == "down"

    @pytest.mark.parametrize(
        ("expression", "base", "direction"),
        [
            ("1/2**x", 0.5, "down"),
            ("2**(-x)", 0.5, "down"),
            ("2**(2*x)", 4.0, "up"),
        ],
    )
    def test_cac_dang_mu_tuong_duong(
        self, expression: str, base: float, direction: str
    ) -> None:
        result = analyze_expression(expression)
        assert result.kind == "exponential"
        assert result.exponential.base == pytest.approx(base)
        assert result.exponential.direction == direction

    def test_tu_choi_effective_base_bi_underflow(self) -> None:
        with pytest.raises(MathEngineError):
            analyze_expression("exp(-1000*x)")


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

    def test_log_he_so_am_nghich_bien(self) -> None:
        result = analyze_expression("-log(x, 2)")
        points = result.logarithmic.sample_points
        assert points[0][1] > points[-1][1]

    @pytest.mark.parametrize("expression", ["log(x, 10) + 1000", "log(x, 0.1) + 1000"])
    def test_tu_choi_nghiem_log_khong_huu_han(self, expression: str) -> None:
        with pytest.raises(MathEngineError):
            analyze_expression(expression)


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


class TestTenRiengVoNghia:
    def test_abc_bi_tu_choi(self) -> None:
        with pytest.raises(MathEngineError):
            analyze_expression("abc")

    def test_bien_mot_ky_tu_van_hop_le(self) -> None:
        result = analyze_expression("x")
        assert result.kind == "linear"


class TestLogNgoacLong:
    """Hoi quy: log co co so phai chiu duoc bieu thuc long nhau."""

    def test_log10_sin_x_cong_1_parse_duoc(self) -> None:
        normalized = normalize_expression("log10(sin(x)+1)")
        assert "log(" in normalized
        assert "10" in normalized

    def test_lg_tich_ngoac_long(self) -> None:
        normalized = normalize_expression("lg((x+1)*2)")
        assert "10" in normalized

    def test_log2_bien_don(self) -> None:
        result = analyze_expression("log2(x)")
        assert result.kind == "logarithmic"
        assert result.logarithmic is not None
        assert result.logarithmic.base == pytest.approx(2.0)


class TestNormalizeNhieuBien:
    def test_normalize_bien_t(self) -> None:
        assert "Symbol('t'" in normalize_expression("t^2-1")

    def test_bo_ve_trai_ten_bat_ky(self) -> None:
        normalized = normalize_expression("z = 2*t + 1")
        assert "Pow" not in normalized
        assert "t" in normalized
