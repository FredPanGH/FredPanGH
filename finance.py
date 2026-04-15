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
) -> float:
    """Build discount factor from valuation date to payment date."""
    if payment_date < valuation_date:
        raise ValueError("payment_date must be on or after valuation_date")

    factor = 1.0
    current = valuation_date
    base_year = valuation_date.year

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
