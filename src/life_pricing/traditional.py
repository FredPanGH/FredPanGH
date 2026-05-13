"""Traditional life insurance product (endowment / whole life).

A *traditional* life product combines:

1. **Protection** – a death benefit paid if the insured dies while the
   policy is in force.
2. **Savings** – a maturity benefit paid if the insured survives to the
   end of the term (endowment) or to a very advanced age (whole life
   modelled as an endowment-at-100, etc.).
3. **Guaranteed cash values** – a surrender benefit paid to a
   policyholder who voluntarily terminates the policy.

Compared with term life, the surrender benefit and maturity benefit are
the defining features. The premium is typically several times higher
than a comparable term policy because part of every premium funds the
guaranteed savings element.

The model in this module is a small extension of
:func:`life_pricing.cashflow.project_cashflows`:

* a **maturity benefit** is paid at end-of-term to in-force policies,
* a **surrender benefit** is paid at end-of-year to lapsing policies,
  equal to ``surrender_value_factor[year] × cumulative_premiums_paid``.

Because the surrender benefit is proportional to cumulative premiums
paid (linear in the annual premium ``P``) and the maturity benefit /
death benefit / fixed expenses are independent of ``P``, the cash flow
projection remains *linear* in ``P``. The same closed-form premium
solver used for term life therefore applies here, just with extra terms
in the constants.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import pandas as pd

from .assumptions import PricingAssumptions
from .cashflow import CashflowProjection
from .pricing import PricingResult


def default_surrender_schedule(term_years: int) -> List[float]:
    """A simple, illustrative guaranteed-surrender-value (GSV) schedule.

    The factor returned is multiplied by **cumulative premiums paid** to
    obtain the surrender benefit for a policy that lapses at the end of
    a given policy year.

    Defaults:

    * Years 1–2:        0% (no surrender value during the early lock-in)
    * Year 3:           30%
    * Years 4 → term:   linear ramp from 30% to 90%
    """
    schedule: List[float] = []
    for year in range(1, term_years + 1):
        if year <= 2:
            schedule.append(0.0)
        elif term_years <= 3:
            schedule.append(0.30)
        else:
            frac = (year - 3) / (term_years - 3)
            schedule.append(0.30 + (0.90 - 0.30) * frac)
    return schedule


@dataclass
class TraditionalLifeProduct:
    """A traditional non-participating endowment policy.

    Attributes
    ----------
    issue_age:
        Age at issue.
    term_years:
        Length of the policy in years. The maturity benefit is paid at
        the end of this period if the insured survives.
    sum_assured:
        Death benefit paid on death within the term.
    maturity_benefit:
        Payable at end of term if the insured is alive. Defaults to
        ``sum_assured`` (a classical endowment). Set to 0 to obtain a
        pure level-premium term policy with cash values.
    gender:
        ``"M"`` or ``"F"``.
    smoker:
        ``True`` for smoker.
    premium_frequency:
        Premium payments per year (1, 2, 4 or 12).
    surrender_value_factors:
        Guaranteed-surrender-value factors (one per policy year) applied
        to cumulative premiums paid. Defaults to
        :func:`default_surrender_schedule`.
    """

    issue_age: int
    term_years: int
    sum_assured: float
    maturity_benefit: Optional[float] = None
    gender: str = "M"
    smoker: bool = False
    premium_frequency: int = 1
    surrender_value_factors: Optional[List[float]] = None

    def __post_init__(self) -> None:
        if self.issue_age < 0 or self.issue_age > 100:
            raise ValueError("issue_age must be between 0 and 100")
        if self.term_years <= 0:
            raise ValueError("term_years must be positive")
        if self.sum_assured <= 0:
            raise ValueError("sum_assured must be positive")
        if self.gender.upper() not in {"M", "F"}:
            raise ValueError("gender must be 'M' or 'F'")
        if self.premium_frequency not in {1, 2, 4, 12}:
            raise ValueError("premium_frequency must be one of 1, 2, 4, 12")

        if self.maturity_benefit is None:
            self.maturity_benefit = self.sum_assured
        if self.maturity_benefit < 0:
            raise ValueError("maturity_benefit must be non-negative")

        if self.surrender_value_factors is None:
            self.surrender_value_factors = default_surrender_schedule(self.term_years)
        if len(self.surrender_value_factors) != self.term_years:
            raise ValueError(
                "surrender_value_factors must have length == term_years"
            )
        if any(f < 0 for f in self.surrender_value_factors):
            raise ValueError("surrender_value_factors must be non-negative")

    def surrender_value(self, policy_year: int, cumulative_premium: float) -> float:
        """Return the guaranteed surrender value for a policy that lapses
        at the end of ``policy_year`` having paid ``cumulative_premium``.
        """
        factor = self.surrender_value_factors[policy_year - 1]
        return factor * cumulative_premium


def _discount(rate: float, t: float) -> float:
    return 1.0 / ((1.0 + rate) ** t)


def project_traditional_cashflows(
    product: TraditionalLifeProduct,
    assumptions: PricingAssumptions,
    annual_premium: float,
) -> CashflowProjection:
    """Project per-policy cash flows for a traditional endowment.

    Timing conventions match :func:`life_pricing.cashflow.project_cashflows`:

    * Premium, commission, acquisition expense, premium tax: BOY.
    * Maintenance expense, death benefit: MOY.
    * Surrender benefit, maturity benefit, lapses: EOY.
    """
    rate = assumptions.discount_rate
    rows: List[dict] = []

    inforce = 1.0
    cumulative_premium = 0.0
    pv_premium = 0.0
    pv_death_benefits = 0.0
    pv_maturity = 0.0
    pv_surrender = 0.0
    pv_expenses = 0.0
    pv_commission = 0.0
    pv_profit = 0.0

    for year in range(1, product.term_years + 1):
        age = product.issue_age + year - 1
        qx = assumptions.mortality.q(
            age, gender=product.gender, smoker=product.smoker
        )
        lapse = assumptions.lapse_rate(year)

        df_boy = _discount(rate, year - 1)
        df_moy = _discount(rate, year - 0.5)
        df_eoy = _discount(rate, year)

        deaths = inforce * qx
        survivors_pre_lapse = inforce - deaths
        lapses = survivors_pre_lapse * lapse
        inforce_eoy = survivors_pre_lapse - lapses

        premium = inforce * annual_premium
        cumulative_premium += annual_premium

        if year == 1:
            commission_rate = assumptions.commission_pct_year1
            acquisition = inforce * (
                assumptions.acquisition_expense_per_policy
                + assumptions.acquisition_expense_pct_premium * annual_premium
            )
        else:
            commission_rate = assumptions.commission_pct_renewal
            acquisition = 0.0

        commission = premium * commission_rate
        premium_tax = premium * assumptions.premium_tax_pct
        maintenance = inforce * assumptions.maintenance_expense(year)
        death_benefit = deaths * product.sum_assured

        sv_per_policy = product.surrender_value(year, cumulative_premium)
        surrender_benefit = lapses * sv_per_policy

        if year == product.term_years:
            maturity_benefit = inforce_eoy * float(product.maturity_benefit)
        else:
            maturity_benefit = 0.0

        net = (
            premium
            - commission
            - acquisition
            - premium_tax
            - maintenance
            - death_benefit
            - surrender_benefit
            - maturity_benefit
        )

        pv_premium += premium * df_boy
        pv_commission += commission * df_boy
        pv_expenses += acquisition * df_boy + maintenance * df_moy
        pv_death_benefits += death_benefit * df_moy
        pv_surrender += surrender_benefit * df_eoy
        pv_maturity += maturity_benefit * df_eoy

        pv_year = (
            (premium - commission - acquisition - premium_tax) * df_boy
            - maintenance * df_moy
            - death_benefit * df_moy
            - surrender_benefit * df_eoy
            - maturity_benefit * df_eoy
        )
        pv_profit += pv_year

        rows.append(
            {
                "policy_year": year,
                "age": age,
                "inforce_boy": inforce,
                "deaths": deaths,
                "lapses": lapses,
                "inforce_eoy": inforce_eoy,
                "premium": premium,
                "commission": commission,
                "acquisition_expense": acquisition,
                "maintenance_expense": maintenance,
                "premium_tax": premium_tax,
                "death_benefit": death_benefit,
                "surrender_benefit": surrender_benefit,
                "maturity_benefit": maturity_benefit,
                "net_cashflow": net,
                "discount_factor": df_eoy,
                "pv_net_cashflow": pv_year,
            }
        )

        inforce = inforce_eoy

    table = pd.DataFrame(rows)
    return CashflowProjection(
        table=table,
        pv_premium=pv_premium,
        pv_benefits=pv_death_benefits + pv_maturity + pv_surrender,
        pv_expenses=pv_expenses,
        pv_commission=pv_commission,
        pv_profit=pv_profit,
    )


def _solve_traditional_premium(
    product: TraditionalLifeProduct,
    assumptions: PricingAssumptions,
) -> float:
    """Closed-form solver for the level annual premium.

    The cash flow model is linear in the annual premium ``P``: every
    premium-dependent flow (gross premium, commission, premium tax, the
    premium-related part of acquisition expense, surrender benefits as a
    % of cumulative premiums) scales linearly with ``P``, and every
    other flow (maintenance expense, fixed acquisition expense, death
    benefit, maturity benefit) is independent of ``P``. We therefore
    evaluate the projection at ``P = 0`` and ``P = 1`` to recover

    .. code::

        PV(profit)  = a · P + b
        PV(premium) = c · P

    and return ``P* = -b / (a - target · c)``.
    """
    proj0 = project_traditional_cashflows(product, assumptions, 0.0)
    proj1 = project_traditional_cashflows(product, assumptions, 1.0)

    b = proj0.pv_profit
    a = proj1.pv_profit - b
    c = proj1.pv_premium - proj0.pv_premium

    target = assumptions.target_profit_margin
    denom = a - target * c
    if denom == 0:
        raise ValueError(
            "Cannot solve for premium: PV(profit) is independent of premium "
            "given these assumptions."
        )
    premium = -b / denom
    if premium < 0:
        raise ValueError(
            "Solved premium is negative – check your assumptions "
            f"(got {premium:.2f})."
        )
    return premium


def price_traditional_policy(
    product: TraditionalLifeProduct,
    assumptions: PricingAssumptions | None = None,
) -> PricingResult:
    """Price a traditional endowment policy.

    Returns
    -------
    PricingResult
        Solved annual / modal premium, premium rate per $1,000 of
        sum-assured-or-maturity-benefit, and the full cash flow
        projection at the solved premium.
    """
    if assumptions is None:
        assumptions = PricingAssumptions(target_profit_margin=0.10)

    annual_premium = _solve_traditional_premium(product, assumptions)
    projection = project_traditional_cashflows(product, assumptions, annual_premium)
    modal_premium = annual_premium / product.premium_frequency
    reference_benefit = max(product.sum_assured, float(product.maturity_benefit or 0))
    rate_per_1000 = annual_premium / (reference_benefit / 1000.0)

    return PricingResult(
        annual_premium=annual_premium,
        modal_premium=modal_premium,
        premium_rate_per_1000=rate_per_1000,
        projection=projection,
        target_profit_margin=assumptions.target_profit_margin,
    )
