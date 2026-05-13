"""Product definition for term life insurance."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TermLifeProduct:
    """A simple level-premium term life insurance product.

    Attributes
    ----------
    issue_age:
        Age of the insured at policy issue.
    term_years:
        Length of the coverage period in years.
    face_amount:
        Death benefit paid if the insured dies during the term.
    gender:
        ``"M"`` or ``"F"``.
    smoker:
        ``True`` for a smoker, ``False`` otherwise.
    premium_frequency:
        Number of premium payments per year (1 = annual, 12 = monthly).
        Currently used only to scale the displayed modal premium.
    """

    issue_age: int
    term_years: int
    face_amount: float
    gender: str = "M"
    smoker: bool = False
    premium_frequency: int = 1

    def __post_init__(self) -> None:
        if self.issue_age < 0 or self.issue_age > 100:
            raise ValueError("issue_age must be between 0 and 100")
        if self.term_years <= 0:
            raise ValueError("term_years must be positive")
        if self.face_amount <= 0:
            raise ValueError("face_amount must be positive")
        if self.gender.upper() not in {"M", "F"}:
            raise ValueError("gender must be 'M' or 'F'")
        if self.premium_frequency not in {1, 2, 4, 12}:
            raise ValueError("premium_frequency must be one of 1, 2, 4, 12")
