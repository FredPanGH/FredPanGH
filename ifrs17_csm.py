"""IFRS 17 CSM calculation helpers.

This module implements reusable functions for:
1) Initial recognition CSM calculations.
2) Annual CSM roll-forward calculations.
3) Multi-year CSM roll-forward schedules.
4) IFRS 17 disclosure-style CSM reconciliation output.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class InitialRecognitionInputs:
    """Inputs used to calculate initial CSM at contract recognition."""

    pv_future_outflows: float
    risk_adjustment: float
    pv_future_inflows: float


@dataclass(frozen=True)
class CSMYearInputs:
    """Assumptions required for one year of CSM roll-forward."""

    year_label: str
    locked_in_rate: float
    future_service_adjustment: float
    coverage_units_provided: float
    coverage_units_total_start: float
    opening_csm_override: float | None = None


def calculate_initial_csm(inputs: InitialRecognitionInputs) -> dict[str, float]:
    """Calculate day-1 fulfilment cash flows, CSM, and loss.

    FCF = PV(outflows) + RA - PV(inflows)
    If FCF < 0, initial CSM = -FCF and day-1 loss is zero.
    If FCF > 0, the group is onerous at initial recognition and CSM is zero.
    """

    fcf = inputs.pv_future_outflows + inputs.risk_adjustment - inputs.pv_future_inflows
    initial_csm = -fcf if fcf < 0 else 0.0
    day1_loss_pnl = fcf if fcf > 0 else 0.0
    net_lrc_initial = fcf + initial_csm

    return {
        "fulfilment_cash_flows": fcf,
        "initial_csm": initial_csm,
        "day1_loss_pnl": day1_loss_pnl,
        "net_lrc_initial": net_lrc_initial,
    }


def roll_forward_csm_year(
    *,
    opening_csm: float,
    locked_in_rate: float,
    future_service_adjustment: float,
    coverage_units_provided: float,
    coverage_units_total_start: float,
) -> dict[str, float]:
    """Roll forward CSM for a single reporting period.

    The function applies:
      - interest accretion on opening CSM;
      - future service adjustments (unlocks CSM);
      - release to insurance revenue via coverage units.

    If adverse changes drive CSM below zero before release, the deficit is
    reported as `loss_component_expense` and CSM is floored at zero.
    """

    if coverage_units_total_start <= 0:
        raise ValueError("coverage_units_total_start must be > 0")
    if coverage_units_provided < 0:
        raise ValueError("coverage_units_provided must be >= 0")
    if coverage_units_provided > coverage_units_total_start:
        raise ValueError("coverage_units_provided cannot exceed coverage_units_total_start")

    interest_accretion = opening_csm * locked_in_rate
    csm_before_floor = opening_csm + interest_accretion + future_service_adjustment

    loss_component_expense = 0.0
    csm_before_release = csm_before_floor
    if csm_before_floor < 0:
        loss_component_expense = -csm_before_floor
        csm_before_release = 0.0

    release_ratio = coverage_units_provided / coverage_units_total_start
    csm_release = csm_before_release * release_ratio
    closing_csm = csm_before_release - csm_release

    return {
        "opening_csm": opening_csm,
        "locked_in_rate": locked_in_rate,
        "interest_accretion": interest_accretion,
        "future_service_adjustment": future_service_adjustment,
        "csm_before_release": csm_before_release,
        "coverage_units_provided": coverage_units_provided,
        "coverage_units_total_start": coverage_units_total_start,
        "release_ratio": release_ratio,
        "csm_release": csm_release,
        "loss_component_expense": loss_component_expense,
        "closing_csm": closing_csm,
    }


def build_csm_rollforward_schedule(
    *,
    opening_csm: float,
    years: Iterable[CSMYearInputs],
) -> list[dict[str, float | str]]:
    """Build a multi-year CSM roll-forward schedule from annual assumptions."""

    schedule: list[dict[str, float | str]] = []
    previous_closing = opening_csm

    for assumptions in years:
        effective_opening = (
            assumptions.opening_csm_override
            if assumptions.opening_csm_override is not None
            else previous_closing
        )

        year_result = roll_forward_csm_year(
            opening_csm=effective_opening,
            locked_in_rate=assumptions.locked_in_rate,
            future_service_adjustment=assumptions.future_service_adjustment,
            coverage_units_provided=assumptions.coverage_units_provided,
            coverage_units_total_start=assumptions.coverage_units_total_start,
        )
        schedule_row: dict[str, float | str] = {"year": assumptions.year_label}
        schedule_row.update(year_result)
        schedule.append(schedule_row)
        previous_closing = year_result["closing_csm"]

    return schedule


def build_ifrs17_csm_disclosure(schedule: Iterable[dict[str, float | str]]) -> list[dict[str, float | str]]:
    """Map annual roll-forward rows to IFRS 17-style CSM disclosure labels."""

    disclosure_rows: list[dict[str, float | str]] = []
    for row in schedule:
        disclosure_rows.append(
            {
                "year": row["year"],
                "opening_contractual_service_margin": float(row["opening_csm"]),
                "interest_accreted_on_csm": float(row["interest_accretion"]),
                "changes_related_to_future_service": float(row["future_service_adjustment"]),
                "csm_recognized_in_insurance_revenue": -float(row["csm_release"]),
                "closing_contractual_service_margin": float(row["closing_csm"]),
                "loss_component_expense": float(row["loss_component_expense"]),
            }
        )
    return disclosure_rows


def example_three_year_assumptions() -> list[CSMYearInputs]:
    """Return the sample assumptions used in earlier walkthrough examples."""

    return [
        CSMYearInputs(
            year_label="Year1",
            locked_in_rate=0.03,
            future_service_adjustment=-12.0,
            coverage_units_provided=25.0,
            coverage_units_total_start=100.0,
        ),
        CSMYearInputs(
            year_label="Year2",
            locked_in_rate=0.03,
            future_service_adjustment=4.0,
            coverage_units_provided=35.0,
            coverage_units_total_start=75.0,
        ),
        CSMYearInputs(
            year_label="Year3",
            locked_in_rate=0.03,
            future_service_adjustment=-1.0,
            coverage_units_provided=40.0,
            coverage_units_total_start=40.0,
        ),
    ]


if __name__ == "__main__":
    initial = calculate_initial_csm(
        InitialRecognitionInputs(
            pv_future_outflows=1000.0,
            risk_adjustment=20.0,
            pv_future_inflows=1120.0,
        )
    )
    print("Initial recognition:", initial)

    rollforward = build_csm_rollforward_schedule(
        opening_csm=100.0,
        years=example_three_year_assumptions(),
    )
    print("CSM roll-forward schedule:")
    for item in rollforward:
        print(item)

    disclosure = build_ifrs17_csm_disclosure(rollforward)
    print("IFRS 17 disclosure rows:")
    for item in disclosure:
        print(item)
