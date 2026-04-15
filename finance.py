"""Simple finance helpers."""


def present_value(amount: float, years: int, annual_rate_percents: list[float]) -> float:
    """Calculate present value for a future amount using varying annual interest.

    Formula:
        PV = amount / product(1 + r_i)
    where r_i = annual_rate_percents[i] / 100 for each year.
    """
    if years < 0:
        raise ValueError("years must be non-negative")
    if len(annual_rate_percents) != years:
        raise ValueError("annual_rate_percents length must equal years")

    discount_factor = 1.0
    for rate_percent in annual_rate_percents:
        if rate_percent <= -100:
            raise ValueError("each annual rate must be greater than -100")
        discount_factor *= 1 + (rate_percent / 100)

    return amount / discount_factor
