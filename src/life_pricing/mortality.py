"""Mortality model.

A simple Gompertz–Makeham style parametric mortality model is used so the
pricing engine is fully self-contained (no external mortality tables
required). The force of mortality at attained age ``x`` is

.. math::

    \\mu_x = A + B \\cdot c^{x}

and the one-year death probability is

.. math::

    q_x = 1 - e^{-\\mu_x}

The default parameters are calibrated to give a mortality curve that is
broadly consistent with a modern industry standard select-and-ultimate
table for a healthy non-smoker male. Gender and smoker adjustments are
applied as multiplicative loadings on :math:`\\mu_x`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Optional

import math


@dataclass(frozen=True)
class MakehamParameters:
    """Parameters for the Gompertz–Makeham mortality law."""

    A: float = 0.0007
    B: float = 0.00005
    c: float = 1.09


@dataclass
class MortalityTable:
    """One-year death probabilities ``q_x`` indexed by attained age.

    If ``table`` is provided it overrides the parametric Makeham model.
    Otherwise ``q_x`` is generated on the fly from :class:`MakehamParameters`.
    Gender (``female_factor``) and smoker (``smoker_factor``) loadings are
    applied multiplicatively to the force of mortality.
    """

    makeham: MakehamParameters = field(default_factory=MakehamParameters)
    female_factor: float = 0.75  # Female mortality ~25% lower than male
    smoker_factor: float = 1.75  # Smoker mortality ~75% higher than non-smoker
    table: Optional[Mapping[int, float]] = None
    max_age: int = 120

    def q(self, age: int, *, gender: str = "M", smoker: bool = False) -> float:
        """Return the one-year death probability at attained ``age``."""
        if age >= self.max_age:
            return 1.0
        if self.table is not None and age in self.table:
            base_q = float(self.table[age])
            mu = -math.log(max(1.0 - base_q, 1e-12))
        else:
            mu = self.makeham.A + self.makeham.B * (self.makeham.c ** age)

        if gender.upper().startswith("F"):
            mu *= self.female_factor
        if smoker:
            mu *= self.smoker_factor

        mu = max(mu, 0.0)
        return 1.0 - math.exp(-mu)

    def survival_curve(
        self,
        start_age: int,
        years: int,
        *,
        gender: str = "M",
        smoker: bool = False,
    ) -> list[float]:
        """Return ``[tpx for t in 0..years]`` – survival probabilities from
        ``start_age`` to ``start_age + t``.
        """
        out = [1.0]
        p = 1.0
        for t in range(years):
            qx = self.q(start_age + t, gender=gender, smoker=smoker)
            p *= 1.0 - qx
            out.append(p)
        return out
