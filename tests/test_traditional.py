"""Tests for the traditional (endowment) life pricing model."""

import math

import pytest

from life_pricing import (
    PricingAssumptions,
    TermLifeProduct,
    TraditionalLifeProduct,
    default_surrender_schedule,
    price_policy,
    price_traditional_policy,
    project_traditional_cashflows,
)


def make_endowment(**overrides):
    defaults = dict(
        issue_age=35,
        term_years=20,
        sum_assured=100_000,
        maturity_benefit=100_000,
        gender="M",
        smoker=False,
    )
    defaults.update(overrides)
    return TraditionalLifeProduct(**defaults)


def test_default_surrender_schedule_shape():
    sched = default_surrender_schedule(20)
    assert len(sched) == 20
    assert sched[0] == 0.0
    assert sched[1] == 0.0
    assert math.isclose(sched[2], 0.30)
    assert math.isclose(sched[-1], 0.90)
    assert all(b >= a - 1e-12 for a, b in zip(sched, sched[1:]))


def test_default_surrender_schedule_short_term():
    sched = default_surrender_schedule(3)
    assert sched == [0.0, 0.0, 0.30]


def test_maturity_defaults_to_sum_assured():
    p = TraditionalLifeProduct(35, 20, sum_assured=100_000)
    assert p.maturity_benefit == 100_000


def test_invalid_surrender_factors_length_raises():
    with pytest.raises(ValueError):
        TraditionalLifeProduct(
            35, 10, 100_000, surrender_value_factors=[0.0, 0.5]
        )


def test_projection_has_maturity_only_in_last_year():
    product = make_endowment(term_years=15)
    proj = project_traditional_cashflows(
        product, PricingAssumptions(), annual_premium=5000.0
    )
    assert (proj.table["maturity_benefit"].iloc[:-1] == 0).all()
    assert proj.table["maturity_benefit"].iloc[-1] > 0


def test_surrender_benefit_zero_in_lockin_years():
    product = make_endowment()
    proj = project_traditional_cashflows(
        product, PricingAssumptions(), annual_premium=5000.0
    )
    assert math.isclose(proj.table["surrender_benefit"].iloc[0], 0.0)
    assert math.isclose(proj.table["surrender_benefit"].iloc[1], 0.0)
    assert proj.table["surrender_benefit"].iloc[2] > 0


def test_linearity_in_premium():
    """PV(profit) must be linear in P even with surrender benefits."""
    product = make_endowment()
    a = PricingAssumptions()
    p0 = project_traditional_cashflows(product, a, 0.0).pv_profit
    p1 = project_traditional_cashflows(product, a, 1.0).pv_profit
    p1000 = project_traditional_cashflows(product, a, 1000.0).pv_profit
    predicted = p0 + (p1 - p0) * 1000.0
    assert math.isclose(predicted, p1000, rel_tol=1e-9, abs_tol=1e-6)


def test_solved_premium_hits_10pc_target():
    product = make_endowment()
    result = price_traditional_policy(
        product, PricingAssumptions(target_profit_margin=0.10)
    )
    assert math.isclose(
        result.achieved_profit_margin, 0.10, rel_tol=1e-9, abs_tol=1e-9
    )


def test_endowment_is_more_expensive_than_term():
    """An endowment with the same death benefit should always cost more
    than the corresponding term policy because of the maturity benefit
    plus guaranteed surrender values."""
    a = PricingAssumptions(target_profit_margin=0.10)
    term = price_policy(
        TermLifeProduct(35, 20, 100_000, "M", False), a
    )
    endow = price_traditional_policy(
        make_endowment(sum_assured=100_000, maturity_benefit=100_000), a
    )
    assert endow.annual_premium > 5 * term.annual_premium


def test_zero_maturity_with_zero_sv_close_to_term():
    """An endowment with zero maturity benefit and zero surrender values
    should price very close to the corresponding term product."""
    a = PricingAssumptions(target_profit_margin=0.08)
    term = price_policy(TermLifeProduct(40, 15, 250_000, "M", False), a)
    endow = price_traditional_policy(
        TraditionalLifeProduct(
            40,
            15,
            sum_assured=250_000,
            maturity_benefit=0.0,
            surrender_value_factors=[0.0] * 15,
        ),
        a,
    )
    assert math.isclose(endow.annual_premium, term.annual_premium, rel_tol=1e-9)


def test_higher_maturity_benefit_means_higher_premium():
    a = PricingAssumptions(target_profit_margin=0.10)
    low = price_traditional_policy(
        make_endowment(maturity_benefit=50_000), a
    )
    high = price_traditional_policy(
        make_endowment(maturity_benefit=200_000), a
    )
    assert high.annual_premium > low.annual_premium


def test_higher_surrender_values_mean_higher_premium():
    a = PricingAssumptions(target_profit_margin=0.10)
    low_sv = price_traditional_policy(
        make_endowment(surrender_value_factors=[0.0] * 20), a
    )
    default_sv = price_traditional_policy(make_endowment(), a)
    assert default_sv.annual_premium > low_sv.annual_premium
