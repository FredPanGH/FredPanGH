"""Life insurance pricing model.

A small, transparent actuarial pricing engine for level-premium term life
insurance. The package exposes:

* :class:`~life_pricing.assumptions.PricingAssumptions` – the full set of
  pricing assumptions (mortality, lapse, expenses, interest, commission,
  profit target).
* :class:`~life_pricing.product.TermLifeProduct` – the product definition
  (face amount, term, issue age, gender, smoker status, premium frequency).
* :class:`~life_pricing.cashflow.project_cashflows` – projects the policy
  cash flows year by year given a premium.
* :func:`~life_pricing.pricing.price_policy` – solves for the level annual
  premium that meets the equivalence principle plus a profit loading, and
  returns the full projection plus headline metrics.
"""

from .assumptions import MortalityAssumptions, PricingAssumptions
from .product import TermLifeProduct
from .cashflow import CashflowProjection, project_cashflows
from .pricing import PricingResult, price_policy

__all__ = [
    "MortalityAssumptions",
    "PricingAssumptions",
    "TermLifeProduct",
    "CashflowProjection",
    "project_cashflows",
    "PricingResult",
    "price_policy",
]
