"""Pricing assumption set for the life insurance pricing model."""

from __future__ import annotations

from dataclasses import dataclass, field

from .mortality import MortalityTable


@dataclass
class MortalityAssumptions:
    """Wrapper around the mortality table plus a pricing margin.

    ``mortality_loading`` is a multiplicative load applied to ``q_x`` to
    build prudence into pricing (e.g. 1.10 = 10% margin on mortality).
    """

    table: MortalityTable = field(default_factory=MortalityTable)
    mortality_loading: float = 1.10

    def q(self, age: int, *, gender: str = "M", smoker: bool = False) -> float:
        q_base = self.table.q(age, gender=gender, smoker=smoker)
        return min(1.0, q_base * self.mortality_loading)


@dataclass
class PricingAssumptions:
    """Full assumption set used by the pricing engine.

    All rates are annual unless stated otherwise.

    Attributes
    ----------
    mortality:
        Mortality assumptions (table + loading).
    discount_rate:
        Annual interest rate used to discount cash flows (pricing rate).
    lapse_rates:
        Per-policy-year lapse (voluntary termination) rates. If the list is
        shorter than the projection horizon, the last value is repeated.
    acquisition_expense_per_policy:
        One-off issue expense in policy year 1 (e.g. underwriting, issue).
    acquisition_expense_pct_premium:
        First-year expense expressed as a fraction of annual premium.
    maintenance_expense_per_policy:
        Annual per-policy maintenance expense from year 2 onwards.
    maintenance_expense_inflation:
        Annual inflation rate applied to maintenance expenses.
    commission_pct_year1:
        First-year commission as a fraction of annual premium.
    commission_pct_renewal:
        Renewal commission as a fraction of annual premium from year 2.
    premium_tax_pct:
        Premium tax / levy expressed as a fraction of premium.
    target_profit_margin:
        Target profit margin expressed as PV(profits) / PV(premiums).
    """

    mortality: MortalityAssumptions = field(default_factory=MortalityAssumptions)
    discount_rate: float = 0.04
    lapse_rates: list[float] = field(
        default_factory=lambda: [0.10, 0.08, 0.07, 0.06, 0.05, 0.05]
    )
    acquisition_expense_per_policy: float = 250.0
    acquisition_expense_pct_premium: float = 0.05
    maintenance_expense_per_policy: float = 60.0
    maintenance_expense_inflation: float = 0.02
    commission_pct_year1: float = 0.55
    commission_pct_renewal: float = 0.05
    premium_tax_pct: float = 0.02
    target_profit_margin: float = 0.08

    def lapse_rate(self, policy_year: int) -> float:
        """Return the lapse rate for ``policy_year`` (1-indexed)."""
        if policy_year < 1:
            raise ValueError("policy_year must be >= 1")
        idx = min(policy_year, len(self.lapse_rates)) - 1
        return self.lapse_rates[idx]

    def maintenance_expense(self, policy_year: int) -> float:
        """Per-policy maintenance expense in ``policy_year`` (1-indexed),
        inflated from the year 1 base."""
        years = max(policy_year - 1, 0)
        return self.maintenance_expense_per_policy * (
            (1.0 + self.maintenance_expense_inflation) ** years
        )
