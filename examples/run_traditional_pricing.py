"""Example: price a 20-year traditional (endowment) life policy.

The product pays the sum assured either on death within the term or as
a maturity benefit if the insured survives to the end of the term, and
provides a guaranteed surrender value to policyholders who lapse.

Target profit margin is set to 10% (PV(profit) / PV(premium)).

Run from the repo root with::

    PYTHONPATH=src python3 examples/run_traditional_pricing.py
"""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))

import pandas as pd

from life_pricing import (
    PricingAssumptions,
    TraditionalLifeProduct,
    price_traditional_policy,
)


def main() -> None:
    product = TraditionalLifeProduct(
        issue_age=35,
        term_years=20,
        sum_assured=500_000,
        maturity_benefit=500_000,
        gender="M",
        smoker=False,
        premium_frequency=12,
    )
    assumptions = PricingAssumptions(target_profit_margin=0.10)

    result = price_traditional_policy(product, assumptions)
    proj = result.projection

    print("=" * 72)
    print("Traditional Endowment – Headline Results")
    print("=" * 72)
    print(f"  Issue age            : {product.issue_age}")
    print(f"  Term                 : {product.term_years} years")
    print(f"  Sum assured          : {product.sum_assured:>12,.0f}")
    print(f"  Maturity benefit     : {float(product.maturity_benefit):>12,.0f}")
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

    print("\nPresent-value summary (per policy issued):")
    print(f"  PV(premium)              = {proj.pv_premium:>13,.2f}")
    print(f"  PV(commission)           = {proj.pv_commission:>13,.2f}")
    print(f"  PV(expenses)             = {proj.pv_expenses:>13,.2f}")
    print(f"  PV(death + maturity + ")
    print(f"     surrender benefits)   = {proj.pv_benefits:>13,.2f}")
    print(f"  PV(profit)               = {proj.pv_profit:>13,.2f}")

    print("\nGuaranteed surrender-value schedule:")
    sched_rows = [
        {
            "policy_year": y,
            "sv_factor": f"{product.surrender_value_factors[y - 1]:.2%}",
            "cum_premium": (y * result.annual_premium),
            "surrender_value": product.surrender_value(
                y, y * result.annual_premium
            ),
        }
        for y in range(1, product.term_years + 1)
    ]
    sched_df = pd.DataFrame(sched_rows)
    pd.options.display.float_format = "{:,.2f}".format
    print(sched_df.to_string(index=False))

    show_cols = [
        "policy_year",
        "age",
        "inforce_boy",
        "deaths",
        "lapses",
        "premium",
        "commission",
        "death_benefit",
        "surrender_benefit",
        "maturity_benefit",
        "net_cashflow",
        "pv_net_cashflow",
    ]
    print("\nCash flow projection:")
    print(proj.table[show_cols].to_string(index=False))


if __name__ == "__main__":
    main()
