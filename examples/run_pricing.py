"""Example: price a 20-year level term life policy.

Run from the repo root with::

    python examples/run_pricing.py
"""

from __future__ import annotations

import os
import sys

# Allow running directly without installing the package.
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))

import pandas as pd

from life_pricing import PricingAssumptions, TermLifeProduct, price_policy


def main() -> None:
    product = TermLifeProduct(
        issue_age=35,
        term_years=20,
        face_amount=500_000,
        gender="M",
        smoker=False,
        premium_frequency=12,
    )
    assumptions = PricingAssumptions()

    result = price_policy(product, assumptions)

    print("=" * 72)
    print("Term Life Pricing – Headline Results")
    print("=" * 72)
    print(f"  Issue age            : {product.issue_age}")
    print(f"  Term                 : {product.term_years} years")
    print(f"  Face amount          : {product.face_amount:>12,.0f}")
    print(f"  Gender / smoker      : {product.gender} / {product.smoker}")
    print(f"  Discount rate        : {assumptions.discount_rate:.2%}")
    print(f"  Mortality loading    : {assumptions.mortality.mortality_loading:.2f}x")
    print(f"  Target profit margin : {assumptions.target_profit_margin:.2%}")
    print("-" * 72)
    print(f"  Annual premium       : {result.annual_premium:>12,.2f}")
    print(f"  Monthly premium      : {result.modal_premium:>12,.2f}")
    print(f"  Rate per $1,000      : {result.premium_rate_per_1000:>12,.2f}")
    print(f"  Achieved margin      : {result.achieved_profit_margin:.2%}")
    print("=" * 72)

    proj = result.projection
    print("\nPresent-value summary (per policy issued):")
    print(f"  PV(premium)      = {proj.pv_premium:>12,.2f}")
    print(f"  PV(commission)   = {proj.pv_commission:>12,.2f}")
    print(f"  PV(expenses)     = {proj.pv_expenses:>12,.2f}")
    print(f"  PV(death claims) = {proj.pv_benefits:>12,.2f}")
    print(f"  PV(profit)       = {proj.pv_profit:>12,.2f}")

    show_cols = [
        "policy_year",
        "age",
        "inforce_boy",
        "deaths",
        "lapses",
        "premium",
        "commission",
        "death_benefit",
        "net_cashflow",
        "pv_net_cashflow",
    ]
    pd.options.display.float_format = "{:,.2f}".format
    print("\nCash flow projection:")
    print(proj.table[show_cols].to_string(index=False))


if __name__ == "__main__":
    main()
