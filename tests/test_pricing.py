"""Tests for the premium solver."""

import math

from life_pricing import PricingAssumptions, TermLifeProduct, price_policy


def test_solved_premium_hits_target_margin():
    product = TermLifeProduct(
        issue_age=40, term_years=20, face_amount=250_000
    )
    result = price_policy(product, PricingAssumptions())
    assert math.isclose(
        result.achieved_profit_margin,
        result.target_profit_margin,
        rel_tol=1e-9,
        abs_tol=1e-9,
    )


def test_premium_increases_with_age():
    a = PricingAssumptions()
    cheap = price_policy(
        TermLifeProduct(issue_age=30, term_years=20, face_amount=100_000), a
    )
    pricey = price_policy(
        TermLifeProduct(issue_age=55, term_years=20, face_amount=100_000), a
    )
    assert pricey.annual_premium > cheap.annual_premium


def test_premium_increases_with_term():
    a = PricingAssumptions()
    short = price_policy(
        TermLifeProduct(issue_age=40, term_years=10, face_amount=100_000), a
    )
    long = price_policy(
        TermLifeProduct(issue_age=40, term_years=30, face_amount=100_000), a
    )
    assert long.annual_premium > short.annual_premium


def test_smoker_pays_more_than_nonsmoker():
    a = PricingAssumptions()
    ns = price_policy(
        TermLifeProduct(40, 20, 100_000, smoker=False), a
    )
    sm = price_policy(
        TermLifeProduct(40, 20, 100_000, smoker=True), a
    )
    assert sm.annual_premium > ns.annual_premium


def test_male_pays_more_than_female_same_age():
    a = PricingAssumptions()
    male = price_policy(
        TermLifeProduct(45, 20, 100_000, gender="M"), a
    )
    female = price_policy(
        TermLifeProduct(45, 20, 100_000, gender="F"), a
    )
    assert male.annual_premium > female.annual_premium


def test_premium_scales_roughly_with_face_amount():
    """Premium per $1,000 should be similar across face amounts.

    They are not exactly equal because the per-policy fixed costs
    (acquisition fee, maintenance expense) are spread over face amount.
    """
    a = PricingAssumptions()
    small = price_policy(
        TermLifeProduct(40, 20, 100_000), a
    )
    big = price_policy(
        TermLifeProduct(40, 20, 1_000_000), a
    )
    assert big.premium_rate_per_1000 < small.premium_rate_per_1000
    assert big.premium_rate_per_1000 > 0.5 * small.premium_rate_per_1000


def test_higher_target_margin_gives_higher_premium():
    product = TermLifeProduct(40, 20, 250_000)
    low = price_policy(
        product, PricingAssumptions(target_profit_margin=0.05)
    )
    high = price_policy(
        product, PricingAssumptions(target_profit_margin=0.15)
    )
    assert high.annual_premium > low.annual_premium


def test_modal_premium_consistent_with_frequency():
    product = TermLifeProduct(
        35, 20, 500_000, premium_frequency=12
    )
    result = price_policy(product)
    assert math.isclose(
        result.modal_premium * 12, result.annual_premium, rel_tol=1e-12
    )
