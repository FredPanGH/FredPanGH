# Life Insurance Pricing Model

A small, transparent actuarial pricing engine, written in pure Python
with `numpy` / `pandas`. It currently supports two products:

1. **Term life** – level-premium pure protection.
2. **Traditional endowment** – level-premium protection + savings, with
   a guaranteed maturity benefit and guaranteed surrender values
   (a.k.a. the classical "traditional life" product).

For both products, the engine takes a product definition and a set of
pricing assumptions and solves for the level annual premium that meets a
target profit margin using the **equivalence principle plus profit
loading**.

## Quick start

```bash
pip install -r requirements.txt
PYTHONPATH=src python3 examples/run_pricing.py              # term life
PYTHONPATH=src python3 examples/run_traditional_pricing.py  # endowment
PYTHONPATH=src python3 -m pytest tests -q
```

Example output – **term life** (35M non-smoker, $500K face, 20-year term, 8% margin):

```
Annual premium       :     1,963.53
Monthly premium      :       163.63
Rate per $1,000      :         3.93
Achieved margin      : 8.00%
```

Example output – **traditional endowment** (35M non-smoker, $500K sum
assured = $500K maturity benefit, 20-year term, 10% margin):

```
Annual premium       :    16,792.27
Monthly premium      :     1,399.36
Rate per $1,000      :        33.58
Achieved margin      : 10.00%
```

The endowment costs about 8.5× the term premium for the same death
benefit – the gap is funding the maturity guarantee plus the guaranteed
surrender values.

## Repository layout

```
src/life_pricing/
  assumptions.py   Pricing assumption set (mortality, lapse, expenses, ...)
  mortality.py     Gompertz–Makeham mortality model with gender/smoker loads
  product.py       TermLifeProduct dataclass
  cashflow.py      Term life cash flow projection
  pricing.py       Term life closed-form premium solver
  traditional.py   TraditionalLifeProduct + endowment projection + solver
examples/
  run_pricing.py              Term life demo
  run_traditional_pricing.py  Endowment demo (10% profit margin)
tests/             Pytest unit tests (34 in total)
```

## Products

### Term life – `TermLifeProduct`

A level-premium pure-protection policy.

| Field               | Description                                          |
| ------------------- | ---------------------------------------------------- |
| `issue_age`         | Age of the insured at policy issue                   |
| `term_years`        | Coverage period in years                             |
| `face_amount`       | Death benefit paid if the insured dies in the term   |
| `gender`            | `"M"` or `"F"`                                       |
| `smoker`            | `True` / `False`                                     |
| `premium_frequency` | Premium payments per year (1, 2, 4 or 12)            |

### Traditional endowment – `TraditionalLifeProduct`

The classical "traditional" life product: level-premium protection plus
a guaranteed savings element.

| Field                     | Description                                                                |
| ------------------------- | -------------------------------------------------------------------------- |
| `issue_age`               | Age of the insured at policy issue                                         |
| `term_years`              | Endowment term in years                                                    |
| `sum_assured`             | Death benefit paid on death within the term                                |
| `maturity_benefit`        | Survival benefit paid at end of term (defaults to `sum_assured`)           |
| `gender`, `smoker`        | As for term life                                                           |
| `premium_frequency`       | Premium payments per year (1, 2, 4 or 12)                                  |
| `surrender_value_factors` | Per policy year – multiplier on cumulative premiums for surrender benefit  |

The default guaranteed-surrender-value (GSV) schedule is 0% for the
first 2 policy years (lock-in), 30% at year 3, then a linear ramp to
90% at maturity. Setting `maturity_benefit = 0` and a schedule of all
zeros recovers a term policy with cash values of zero (and indeed the
test suite verifies that this prices identically to `TermLifeProduct`).

A traditional product introduces two additional cash flows over a term
policy:

* **Maturity benefit** paid at the end of the term to in-force policies.
* **Surrender benefit** = `surrender_value_factor[year] × Σ premiums paid`,
  paid at end-of-year to lapsing policies.

Both flows remain linear in the annual premium `P` (the surrender
benefit is a fraction of cumulative `P`, the maturity benefit does not
depend on `P`), so the same closed-form premium solver used for term
life applies unchanged – just with extra terms in the `a`, `b`, `c`
coefficients.

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

Term life:

```python
from life_pricing import PricingAssumptions, TermLifeProduct, price_policy

product = TermLifeProduct(
    issue_age=35, term_years=20, face_amount=500_000,
    gender="M", smoker=False, premium_frequency=12,
)
result = price_policy(product, PricingAssumptions())
print(result.annual_premium)          # 1963.53
print(result.achieved_profit_margin)  # 0.08
```

Traditional endowment with a 10% profit margin:

```python
from life_pricing import (
    PricingAssumptions, TraditionalLifeProduct, price_traditional_policy,
)

product = TraditionalLifeProduct(
    issue_age=35, term_years=20,
    sum_assured=500_000, maturity_benefit=500_000,
    gender="M", smoker=False, premium_frequency=12,
)
result = price_traditional_policy(
    product, PricingAssumptions(target_profit_margin=0.10),
)
print(result.annual_premium)          # 16_792.27
print(result.modal_premium)           #  1_399.36
print(result.achieved_profit_margin)  # 0.10
result.projection.table.head()        # year-by-year DataFrame including
                                      # surrender_benefit, maturity_benefit
```

## Caveats

This is a teaching / illustrative model, not a production pricing system.
In particular it:

* Uses a parametric mortality law instead of a regulator-approved table.
* Ignores reserving, capital requirements and reinsurance.
* Does not model policy options (riders, conversion, premium holidays).
* Treats lapses as fully deterministic and independent of experience.
* Uses a "% of cumulative premiums paid" surrender value formula for the
  traditional product; a real product would credit interest on
  accumulated reserves and possibly include surrender charges separately.
* Models non-participating ("non-par") traditional products only – no
  bonuses or dividends.

Use it to explore the *shape* of life insurance economics, not to set
real-world rates.
