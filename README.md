# FredPanGH

## Present value helper

This repository includes finance utilities for both policy-year and calendar-year projections.

### Policy-year basis

```python
from finance import present_value

pv = present_value(
    beginning_year_payments=[30, 35, 40, 45, 50],
    payments=[200, 220, 240, 260, 280],  # end-year payments
    mid_year_payments=[50, 60, 70, 80, 90],
    years=5,
    annual_rate_percents=[7, 6.5, 7.2, 6.8, 7.0],
)
print(round(pv, 2))  # 1441.33
```

### Calendar-year basis (from valuation date)

```python
from datetime import date
from finance import present_value_calendar_year

pv = present_value_calendar_year(
    beginning_year_payments=[30, 35, 40, 45, 50],
    mid_year_payments=[50, 60, 70, 80, 90],
    end_year_payments=[200, 220, 240, 260, 280],
    annual_rate_percents=[7, 6.5, 7.2, 6.8, 7.0],
    valuation_date=date(2026, 4, 15),
)
print(round(pv, 2))  # 1439.06
```

Calendar-year assumptions:
- `annual_rate_percents[0]` is the rate for valuation year, then next calendar years.
- Payment timing each projected year:
  - beginning: Jan 1
  - mid: Jul 1
  - end: Dec 31
- Any payment date before valuation date is ignored.

Calendar-year formula:

`PV = Σ [CF_date / DF(valuation_date -> payment_date)]`

where `DF` compounds piecewise by calendar year using that year's annual rate.

## Life insurance valuation (calendar-year basis)

Use `life_insurance_valuation_calendar_year(...)` to:
- value projected outflows (expenses, charges, commissions, lapse/death benefits),
- solve for a level annual premium that achieves a target PV profit margin (default 10%),
- produce a prospective reserve schedule from valuation date and each Jan 1.

```python
from datetime import date
from finance import life_insurance_valuation_calendar_year

result = life_insurance_valuation_calendar_year(
    expenses_beginning=[20, 18, 17, 16, 15],
    charges_mid_year=[8, 8, 8, 7, 7],
    commissions_beginning=[40, 10, 8, 6, 5],
    lapse_death_benefits_end_year=[120, 130, 145, 160, 175],
    annual_rate_percents=[5.0, 5.2, 5.1, 5.0, 4.8],
    target_profit_margin=0.10,
    valuation_date=date(2026, 4, 15),
)

print("Annual premium:", round(result["annual_premium"], 2))
print("PV premiums:", round(result["pv_premiums"], 2))
print("PV outflows:", round(result["pv_outflows"], 2))
print("PV profit margin:", round(result["profit_margin"], 4))
print("Reserve schedule:", result["reserve_schedule"])
# Expected from this sample:
# Annual premium: 233.45
# PV premiums: 837.86
# PV outflows: 754.07
# PV profit margin: 0.1
```

Returned fields:
- `annual_premium`
- `pv_premiums`
- `pv_outflows`
- `pv_profit`
- `profit_margin`
- `reserve_schedule` (list of `(date_iso, reserve)` tuples)
