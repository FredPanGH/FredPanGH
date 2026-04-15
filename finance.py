"""Simple finance helpers."""


def present_value(
    beginning_year_payments: list[float],
    payments: list[float],
    mid_year_payments: list[float],
    years: int,
    annual_rate_percents: list[float],
) -> float:
    """Calculate present value for beginning-, mid-, and end-year cashflows.

    Formula:
        PV = sum(
            CF_begin_t / product(1 + r_i for i in 1..t-1)
            CF_mid_t / (product(1 + r_i for i in 1..t-1) * (1 + r_t)^0.5)
            + CF_end_t / product(1 + r_i for i in 1..t)
        ) for t in 1..years

    where:
    - CF_begin_t is the payment at beginning of year t
    - CF_mid_t is the payment at mid-year t
    - CF_end_t is the payment at end-year t
    - r_t = annual_rate_percents[t-1] / 100
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
