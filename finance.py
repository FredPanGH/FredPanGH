"""Simple finance helpers."""


def present_value(
    payments: list[float], years: int, annual_rate_percents: list[float]
) -> float:
    """Calculate present value for yearly cashflows using varying annual interest.

    Formula:
        PV = sum(CF_t / product(1 + r_i for i in 1..t)) for t in 1..years
    where CF_t is the payment at year t and r_i = annual_rate_percents[i-1] / 100.
    """
    if years < 0:
        raise ValueError("years must be non-negative")
    if len(payments) != years:
        raise ValueError("payments length must equal years")
    if len(annual_rate_percents) != years:
        raise ValueError("annual_rate_percents length must equal years")

    present_value_total = 0.0
    cumulative_discount_factor = 1.0

    for payment, rate_percent in zip(payments, annual_rate_percents):
        if rate_percent <= -100:
            raise ValueError("each annual rate must be greater than -100")
        cumulative_discount_factor *= 1 + (rate_percent / 100)
        present_value_total += payment / cumulative_discount_factor

    return present_value_total
