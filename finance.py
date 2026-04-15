"""Simple finance helpers."""

from datetime import date


def present_value(
    beginning_year_payments: list[float],
    payments: list[float],
    mid_year_payments: list[float],
    years: int,
    annual_rate_percents: list[float],
) -> float:
    """Calculate present value for beginning-, mid-, and end-year cashflows.

    This function assumes policy-year timing.
    """
    if years < 0:
        raise ValueError("years must be non-negative")
    if len(beginning_year_payments) != years:
        raise ValueError("beginning_year_payments length must equal years")
    if len(payments) != years:
        raise ValueError("payments length must equal years")
    if len(mid_year_payments) != years:
        raise ValueError("mid_year_payments length must equal years")
    if len(annual_rate_percents) != years:
        raise ValueError("annual_rate_percents length must equal years")

    present_value_total = 0.0
    cumulative_discount_factor = 1.0  # product of full-year factors through t-1

    for begin_payment, payment, mid_payment, rate_percent in zip(
        beginning_year_payments, payments, mid_year_payments, annual_rate_percents
    ):
        if rate_percent <= -100:
            raise ValueError("each annual rate must be greater than -100")

        present_value_total += begin_payment / cumulative_discount_factor

        annual_factor = 1 + (rate_percent / 100)
        mid_year_discount_factor = cumulative_discount_factor * (annual_factor**0.5)
        present_value_total += mid_payment / mid_year_discount_factor

        cumulative_discount_factor *= annual_factor
        present_value_total += payment / cumulative_discount_factor

    return present_value_total


def _days_in_year(year: int) -> int:
    """Return number of days in a calendar year."""
    return 366 if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0) else 365


def _discount_factor_calendar_year(
    valuation_date: date,
    payment_date: date,
    annual_rate_percents: list[float],
    base_year: int | None = None,
) -> float:
    """Build discount factor from valuation date to payment date."""
    if payment_date < valuation_date:
        raise ValueError("payment_date must be on or after valuation_date")

    factor = 1.0
    current = valuation_date
    base_year = valuation_date.year if base_year is None else base_year

    while current < payment_date:
        rate_index = current.year - base_year
        if rate_index >= len(annual_rate_percents):
            raise ValueError(
                "annual_rate_percents must cover all calendar years through final payment"
            )

        rate_percent = annual_rate_percents[rate_index]
        if rate_percent <= -100:
            raise ValueError("each annual rate must be greater than -100")

        next_year = date(current.year + 1, 1, 1)
        segment_end = min(payment_date, next_year)
        days = (segment_end - current).days
        year_fraction = days / _days_in_year(current.year)

        factor *= (1 + (rate_percent / 100)) ** year_fraction
        current = segment_end

    return factor


def present_value_calendar_year(
    beginning_year_payments: list[float],
    mid_year_payments: list[float],
    end_year_payments: list[float],
    annual_rate_percents: list[float],
    valuation_date: date | None = None,
) -> float:
    """Calculate PV on a calendar-year basis from valuation date.

    Assumptions:
    - valuation_date defaults to today's date.
    - annual_rate_percents[0] is the rate for valuation year, [1] for next year, etc.
    - payment vectors are aligned to calendar years starting at valuation year.
      For year t (1-based):
        - beginning payment date: Jan 1
        - mid-year payment date: Jul 1
        - end-year payment date: Dec 31
    - payments dated before valuation_date are ignored.
    """
    valuation_date = valuation_date or date.today()

    years = len(beginning_year_payments)
    if len(mid_year_payments) != years:
        raise ValueError("mid_year_payments length must equal beginning_year_payments")
    if len(end_year_payments) != years:
        raise ValueError("end_year_payments length must equal beginning_year_payments")
    if len(annual_rate_percents) < years:
        raise ValueError(
            "annual_rate_percents must include at least one rate per projected calendar year"
        )

    present_value_total = 0.0
    base_year = valuation_date.year

    for offset in range(years):
        year = base_year + offset
        cashflows = (
            (beginning_year_payments[offset], date(year, 1, 1)),
            (mid_year_payments[offset], date(year, 7, 1)),
            (end_year_payments[offset], date(year, 12, 31)),
        )

        for amount, payment_date in cashflows:
            if payment_date < valuation_date:
                continue

            discount_factor = _discount_factor_calendar_year(
                valuation_date=valuation_date,
                payment_date=payment_date,
                annual_rate_percents=annual_rate_percents,
            )
            present_value_total += amount / discount_factor

    return present_value_total


def _present_value_cashflows_calendar_year(
    cashflows: list[tuple[float, date]],
    valuation_date: date,
    annual_rate_percents: list[float],
    base_year: int,
) -> float:
    """Present value of dated cashflows with calendar-year rates."""
    total = 0.0
    for amount, payment_date in cashflows:
        if payment_date < valuation_date:
            continue
        discount_factor = _discount_factor_calendar_year(
            valuation_date=valuation_date,
            payment_date=payment_date,
            annual_rate_percents=annual_rate_percents,
            base_year=base_year,
        )
        total += amount / discount_factor
    return total


def _premium_discount_factor_sum(
    premium_dates: list[date],
    valuation_date: date,
    annual_rate_percents: list[float],
    base_year: int,
) -> float:
    """Sum discount factors for level premium cashflows."""
    factor_sum = 0.0
    for premium_date in premium_dates:
        if premium_date < valuation_date:
            continue
        discount_factor = _discount_factor_calendar_year(
            valuation_date=valuation_date,
            payment_date=premium_date,
            annual_rate_percents=annual_rate_percents,
            base_year=base_year,
        )
        factor_sum += 1 / discount_factor
    return factor_sum


def life_insurance_valuation_calendar_year(
    expenses_beginning: list[float],
    charges_mid_year: list[float],
    commissions_beginning: list[float],
    lapse_death_benefits_end_year: list[float],
    annual_rate_percents: list[float],
    target_profit_margin: float = 0.10,
    valuation_date: date | None = None,
) -> dict[str, float | list[tuple[str, float]]]:
    """Run life-insurance valuation on calendar-year basis.

    Assumptions:
    - valuation_date defaults to today's date.
    - annual_rate_percents are calendar-year rates, starting from valuation year.
    - premium is a single level amount paid at Jan 1 each projected calendar year.
    - outflows:
      - expenses and commissions at Jan 1
      - charges at Jul 1
      - lapse/death benefits at Dec 31

    target_profit_margin is defined on a PV basis:
        PV(profit) / PV(premiums) = target_profit_margin
    """
    valuation_date = valuation_date or date.today()

    years = len(expenses_beginning)
    if years == 0:
        raise ValueError("at least one projected year is required")
    if len(charges_mid_year) != years:
        raise ValueError("charges_mid_year length must equal expenses_beginning")
    if len(commissions_beginning) != years:
        raise ValueError("commissions_beginning length must equal expenses_beginning")
    if len(lapse_death_benefits_end_year) != years:
        raise ValueError(
            "lapse_death_benefits_end_year length must equal expenses_beginning"
        )
    if len(annual_rate_percents) < years:
        raise ValueError(
            "annual_rate_percents must include at least one rate per projected year"
        )
    if not (0 <= target_profit_margin < 1):
        raise ValueError("target_profit_margin must be in [0, 1)")

    base_year = valuation_date.year
    outflow_cashflows: list[tuple[float, date]] = []
    premium_dates: list[date] = []

    for offset in range(years):
        year = base_year + offset
        premium_dates.append(date(year, 1, 1))
        outflow_cashflows.extend(
            [
                (expenses_beginning[offset], date(year, 1, 1)),
                (commissions_beginning[offset], date(year, 1, 1)),
                (charges_mid_year[offset], date(year, 7, 1)),
                (lapse_death_benefits_end_year[offset], date(year, 12, 31)),
            ]
        )

    pv_outflows = _present_value_cashflows_calendar_year(
        cashflows=outflow_cashflows,
        valuation_date=valuation_date,
        annual_rate_percents=annual_rate_percents,
        base_year=base_year,
    )
    premium_factor_sum = _premium_discount_factor_sum(
        premium_dates=premium_dates,
        valuation_date=valuation_date,
        annual_rate_percents=annual_rate_percents,
        base_year=base_year,
    )
    if premium_factor_sum == 0:
        raise ValueError("no future premium dates on or after valuation_date")

    annual_premium = pv_outflows / ((1 - target_profit_margin) * premium_factor_sum)
    pv_premiums = annual_premium * premium_factor_sum
    pv_profit = pv_premiums - pv_outflows

    reserve_schedule: list[tuple[str, float]] = []
    valuation_points = [valuation_date] + [
        date(base_year + offset, 1, 1) for offset in range(1, years + 1)
    ]
    for reserve_date in valuation_points:
        pv_outflows_from_reserve_date = _present_value_cashflows_calendar_year(
            cashflows=outflow_cashflows,
            valuation_date=reserve_date,
            annual_rate_percents=annual_rate_percents,
            base_year=base_year,
        )
        premium_factor_from_reserve_date = _premium_discount_factor_sum(
            premium_dates=premium_dates,
            valuation_date=reserve_date,
            annual_rate_percents=annual_rate_percents,
            base_year=base_year,
        )
        reserve = pv_outflows_from_reserve_date - (
            annual_premium * premium_factor_from_reserve_date
        )
        reserve_schedule.append((reserve_date.isoformat(), reserve))

    return {
        "annual_premium": annual_premium,
        "pv_premiums": pv_premiums,
        "pv_outflows": pv_outflows,
        "pv_profit": pv_profit,
        "profit_margin": pv_profit / pv_premiums,
        "reserve_schedule": reserve_schedule,
    }
