"""Year-by-year cash flow projection for a term life policy.

Conventions
-----------

* Cash flows are projected on a *per-policy-issued* basis. The starting
  in-force is 1.0 and decrements by deaths and lapses each year.
* Premiums, commissions and acquisition expenses occur at the **start**
  of the policy year (BOY).
* Maintenance expenses are assumed to occur mid-year.
* Death claims are assumed to occur mid-year on average; lapses occur at
  the end of the year (so a policy that lapses still pays a full year's
  premium and is at risk for death during that year).
* All cash flows are discounted to time 0 using a continuously-compounded
  approximation: BOY flows at ``t``, MOY flows at ``t + 0.5``, EOY flows
  at ``t + 1``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

import pandas as pd

from .assumptions import PricingAssumptions
from .product import TermLifeProduct


@dataclass
class CashflowProjection:
    """Container for a projected cash flow table.

    The ``table`` DataFrame has one row per policy year with columns:

    - ``policy_year``          1-indexed policy year
    - ``age``                  attained age at start of year
    - ``inforce_boy``          in-force count at start of year
    - ``deaths``               expected deaths during the year
    - ``lapses``               expected end-of-year lapses
    - ``inforce_eoy``          in-force count at end of year
    - ``premium``              gross premium income (BOY)
    - ``commission``           commission paid (BOY)
    - ``acquisition_expense``  acquisition expense (BOY, year 1 only)
    - ``maintenance_expense``  maintenance expense (MOY)
    - ``premium_tax``          premium tax (BOY)
    - ``death_benefit``        death claims paid (MOY)
    - ``net_cashflow``         insurer net cash flow for the year
                               (premium - commission - expenses
                                - premium_tax - death_benefit)
    - ``discount_factor``      composite discount factor used for PV
    - ``pv_net_cashflow``      present value of ``net_cashflow``
    """

    table: pd.DataFrame
    pv_premium: float
    pv_benefits: float
    pv_expenses: float
    pv_commission: float
    pv_profit: float

    @property
    def profit_margin(self) -> float:
        """Profit margin = PV(profit) / PV(premium)."""
        if self.pv_premium == 0:
            return 0.0
        return self.pv_profit / self.pv_premium


def _discount(rate: float, t: float) -> float:
    return 1.0 / ((1.0 + rate) ** t)


def project_cashflows(
    product: TermLifeProduct,
    assumptions: PricingAssumptions,
    annual_premium: float,
) -> CashflowProjection:
    """Project the policy cash flows for ``product`` given ``annual_premium``.

    Returns
    -------
    CashflowProjection
        Year-by-year projection plus headline PV figures.
    """
    rate = assumptions.discount_rate
    rows: List[dict] = []

    inforce = 1.0
    pv_premium = 0.0
    pv_benefits = 0.0
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
        death_benefit = deaths * product.face_amount

        net = (
            premium
            - commission
            - acquisition
            - premium_tax
            - maintenance
            - death_benefit
        )

        pv_premium += premium * df_boy
        pv_commission += commission * df_boy
        pv_expenses += acquisition * df_boy + maintenance * df_moy
        pv_benefits += death_benefit * df_moy
        pv_year = (
            (premium - commission - acquisition - premium_tax) * df_boy
            - maintenance * df_moy
            - death_benefit * df_moy
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
                "premium_tax": premium * assumptions.premium_tax_pct,
                "death_benefit": death_benefit,
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
        pv_benefits=pv_benefits,
        pv_expenses=pv_expenses,
        pv_commission=pv_commission,
        pv_profit=pv_profit,
    )
