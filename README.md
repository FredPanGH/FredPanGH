# Life Insurance Pricing Model

A small, transparent actuarial pricing engine for level-premium term life
insurance, written in pure Python with `numpy` / `pandas`.

The model takes a product definition and a set of pricing assumptions and
solves for the level annual premium that meets a target profit margin
using the **equivalence principle plus profit loading**.

## Quick start

```bash
pip install -r requirements.txt
PYTHONPATH=src python3 examples/run_pricing.py
PYTHONPATH=src python3 -m pytest tests -q
```

Example output (35-year-old male non-smoker, $500,000 face, 20-year term):

```
Annual premium       :     1,963.53
Monthly premium      :       163.63
Rate per $1,000      :         3.93
Achieved margin      : 8.00%
```

## Repository layout

```
src/life_pricing/
  assumptions.py   Pricing assumption set (mortality, lapse, expenses, ...)
  mortality.py     Gompertz–Makeham mortality model with gender/smoker loads
  product.py       TermLifeProduct dataclass
  cashflow.py      Year-by-year cash flow projection
  pricing.py       Closed-form premium solver
examples/
  run_pricing.py   End-to-end demo script
tests/             Pytest unit tests
```

## Product

`TermLifeProduct` represents a level-premium term life policy:

| Field               | Description                                          |
| ------------------- | ---------------------------------------------------- |
| `issue_age`         | Age of the insured at policy issue                   |
| `term_years`        | Coverage period in years                             |
| `face_amount`       | Death benefit paid if the insured dies in the term   |
| `gender`            | `"M"` or `"F"`                                       |
| `smoker`            | `True` / `False`                                     |
| `premium_frequency` | Premium payments per year (1, 2, 4 or 12)            |

## Basic assumptions

All assumptions live in `PricingAssumptions` (`src/life_pricing/assumptions.py`).
The defaults are summarised below.

### Mortality

A parametric **Gompertz–Makeham** law is used so the engine is fully
self-contained:

\[
\mu_x = A + B \cdot c^{x}, \qquad q_x = 1 - e^{-\mu_x}
\]

Defaults: \(A = 7\times 10^{-4}\), \(B = 5\times 10^{-5}\), \(c = 1.09\).
These give a baseline curve that is broadly consistent with a healthy
non-smoker male on a modern industry standard select-and-ultimate table.

Adjustments applied multiplicatively to \(\mu_x\):

| Adjustment           | Default |
| -------------------- | ------- |
| Female factor        | 0.75    |
| Smoker factor        | 1.75    |
| Pricing mortality loading (margin) | 1.10    |

A custom `{age: q_x}` table can be passed via `MortalityTable(table=...)`
to override the parametric model.

### Lapse (voluntary termination)

Per policy year (year 1 onward), the last value is repeated thereafter:

```
[10%, 8%, 7%, 6%, 5%, 5%, ...]
```

### Expenses

| Component                                   | Default          |
| ------------------------------------------- | ---------------- |
| Acquisition expense (per policy, year 1)    | $250             |
| Acquisition expense (% of year 1 premium)   | 5%               |
| Maintenance expense (per policy, year 1)    | $60 / year       |
| Maintenance expense inflation               | 2% / year        |
| Premium tax / levy                          | 2% of premium    |

### Commission

| Component                | Default |
| ------------------------ | ------- |
| Year 1 commission        | 55% of premium |
| Renewal commission       | 5% of premium  |

### Financial

| Component                | Default |
| ------------------------ | ------- |
| Pricing discount rate    | 4% per annum |
| Target profit margin     | 8% of PV(premium) |

## Cash flow projection

For each policy year `t = 1, ..., term`:

1. Start-of-year (BOY) in-force `l_t` (starts at 1.0).
2. Expected deaths during the year: `d_t = l_t · q_x(age_t)`.
3. Survivors are reduced by lapses at end-of-year: `l_{t+1} = (l_t − d_t)·(1 − w_t)`.
4. Cash flows:
   - **Premium** at BOY: `l_t · P`.
   - **Commission** at BOY: `c_t · premium_t`.
   - **Acquisition expense** at BOY (year 1 only):
     `l_1 · (fixed_acq + pct_acq · P)`.
   - **Premium tax** at BOY: `tax · premium_t`.
   - **Maintenance expense** at mid-year:
     `l_t · maint · (1 + infl)^{t-1}`.
   - **Death benefit** at mid-year: `d_t · FaceAmount`.
5. Discounting uses `(1 + i)^{-τ}` with `τ` = 0, 0.5 or 1 for BOY, MOY
   and EOY flows respectively.

## Premium solver

Every cash flow is either linear in the premium `P` or independent of it,
so the present-value profit and premium have the form

\[
\text{PV(profit)} = a \cdot P + b, \qquad
\text{PV(premium)} = c \cdot P.
\]

The target profit margin constraint

\[
\frac{\text{PV(profit)}}{\text{PV(premium)}} = \text{target}
\]

then admits the closed-form solution

\[
P^{\star} = \frac{-b}{a - \text{target} \cdot c}.
\]

The solver evaluates the cash flow projection at `P = 0` and `P = 1`,
recovers `a`, `b`, `c` and returns `P*`. This is exact (up to floating
point) – the unit tests confirm that the achieved profit margin matches
the target to machine precision.

## Programmatic use

```python
from life_pricing import PricingAssumptions, TermLifeProduct, price_policy

product = TermLifeProduct(
    issue_age=35,
    term_years=20,
    face_amount=500_000,
    gender="M",
    smoker=False,
    premium_frequency=12,
)
result = price_policy(product, PricingAssumptions())

print(result.annual_premium)        # 1963.53
print(result.modal_premium)         # 163.63
print(result.achieved_profit_margin)  # 0.08
result.projection.table.head()      # year-by-year DataFrame
```

## Caveats

This is a teaching / illustrative model, not a production pricing system.
In particular it:

* Uses a parametric mortality law instead of a regulator-approved table.
* Ignores reserving, capital requirements and reinsurance.
* Does not model policy options (riders, conversion, premium holidays).
* Treats lapses as fully deterministic and independent of experience.

Use it to explore the *shape* of life insurance economics, not to set
real-world rates.
