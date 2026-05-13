"""Tests for the cash flow projection."""

import math

from life_pricing import PricingAssumptions, TermLifeProduct, project_cashflows


def make_product(**overrides):
    defaults = dict(
        issue_age=35,
        term_years=10,
        face_amount=100_000,
        gender="M",
        smoker=False,
    )
    defaults.update(overrides)
    return TermLifeProduct(**defaults)


def test_projection_has_one_row_per_year():
    product = make_product(term_years=15)
    proj = project_cashflows(product, PricingAssumptions(), annual_premium=500.0)
    assert len(proj.table) == 15
    assert list(proj.table["policy_year"]) == list(range(1, 16))


def test_inforce_decrements_and_starts_at_one():
    product = make_product()
    proj = project_cashflows(product, PricingAssumptions(), annual_premium=500.0)
    assert math.isclose(proj.table["inforce_boy"].iloc[0], 1.0)
    for i in range(len(proj.table) - 1):
        assert proj.table["inforce_eoy"].iloc[i] >= proj.table["inforce_boy"].iloc[i + 1] - 1e-12
        assert proj.table["inforce_eoy"].iloc[i] < proj.table["inforce_boy"].iloc[i] + 1e-12


def test_year1_acquisition_only_in_year_1():
    product = make_product()
    proj = project_cashflows(product, PricingAssumptions(), annual_premium=500.0)
    assert proj.table["acquisition_expense"].iloc[0] > 0
    assert (proj.table["acquisition_expense"].iloc[1:] == 0).all()


def test_zero_premium_gives_negative_pv_profit():
    product = make_product()
    proj = project_cashflows(product, PricingAssumptions(), annual_premium=0.0)
    assert proj.pv_premium == 0.0
    assert proj.pv_profit < 0


def test_linearity_in_premium():
    """PV(profit) must be linear in the annual premium."""
    product = make_product()
    a = PricingAssumptions()
    p0 = project_cashflows(product, a, 0.0).pv_profit
    p1 = project_cashflows(product, a, 1.0).pv_profit
    p1000 = project_cashflows(product, a, 1000.0).pv_profit
    predicted = p0 + (p1 - p0) * 1000.0
    assert math.isclose(predicted, p1000, rel_tol=1e-9, abs_tol=1e-6)


def test_higher_face_amount_gives_higher_pv_benefits():
    a = PricingAssumptions()
    small = project_cashflows(make_product(face_amount=50_000), a, 0.0)
    big = project_cashflows(make_product(face_amount=500_000), a, 0.0)
    assert big.pv_benefits > small.pv_benefits
