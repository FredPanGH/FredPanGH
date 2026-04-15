"""Simple finance helpers."""


def present_value(amount: float, years: float, annual_rate_percent: float) -> float:
    """Calculate present value for a future amount using constant annual interest.

    Formula:
        PV = amount / (1 + r) ** years

    where r = annual_rate_percent / 100.
    """
    if years < 0:
        raise ValueError("years must be non-negative")
    if annual_rate_percent <= -100:
        raise ValueError("annual_rate_percent must be greater than -100")

    rate = annual_rate_percent / 100
    return amount / ((1 + rate) ** years)
