"""Premium solver for a level-premium term life product.

The pricing model is *linear* in the annual premium ``P``: every premium-
dependent cash flow (gross premium, commission, premium tax, the
premium-related part of acquisition expense) scales linearly with ``P``;
every other cash flow (maintenance expenses, death benefits, fixed
acquisition expense) is independent of ``P``. Therefore both

* PV(profit)  = a · P + b
* PV(premium) = c · P

with constants ``a, b, c`` that depend only on the assumptions and the
product. The target profit margin constraint

.. math::

    \\text{margin} = \\frac{\\text{PV(profit)}}{\\text{PV(premium)}}
                   = \\text{target}

can therefore be solved in closed form

.. math::

    P^\\star = \\frac{-b}{a - \\text{target} \\cdot c}

We exploit this by evaluating :func:`~life_pricing.cashflow.project_cashflows`
at ``P = 0`` and ``P = 1`` to recover ``a, b, c`` and then computing
``P*`` analytically.
"""

from __future__ import annotations

from dataclasses import dataclass

from .assumptions import PricingAssumptions
from .cashflow import CashflowProjection, project_cashflows
from .product import TermLifeProduct


@dataclass
class PricingResult:
    """Headline pricing result."""

    annual_premium: float
    modal_premium: float
    premium_rate_per_1000: float
    projection: CashflowProjection
    target_profit_margin: float

    @property
    def achieved_profit_margin(self) -> float:
        return self.projection.profit_margin


def _solve_premium(
    product: TermLifeProduct,
    assumptions: PricingAssumptions,
) -> float:
    """Solve for the level annual premium that hits the profit-margin target."""
    proj0 = project_cashflows(product, assumptions, annual_premium=0.0)
    proj1 = project_cashflows(product, assumptions, annual_premium=1.0)

    b = proj0.pv_profit
    a = proj1.pv_profit - b
    c = proj1.pv_premium - proj0.pv_premium

    target = assumptions.target_profit_margin
    denom = a - target * c
    if denom == 0:
        raise ValueError(
            "Cannot solve for premium: profit is independent of premium "
            "given these assumptions."
        )
    premium = -b / denom
    if premium < 0:
        raise ValueError(
            "Solved premium is negative – check your assumptions "
            f"(got {premium:.2f})."
        )
    return premium


def price_policy(
    product: TermLifeProduct,
    assumptions: PricingAssumptions | None = None,
) -> PricingResult:
    """Price a term life policy.

    Returns
    -------
    PricingResult
        Solved annual / modal premium plus the full cash flow projection
        evaluated at that premium.
    """
    if assumptions is None:
        assumptions = PricingAssumptions()

    annual_premium = _solve_premium(product, assumptions)
    projection = project_cashflows(product, assumptions, annual_premium)
    modal_premium = annual_premium / product.premium_frequency
    rate_per_1000 = annual_premium / (product.face_amount / 1000.0)

    return PricingResult(
        annual_premium=annual_premium,
        modal_premium=modal_premium,
        premium_rate_per_1000=rate_per_1000,
        projection=projection,
        target_profit_margin=assumptions.target_profit_margin,
    )
