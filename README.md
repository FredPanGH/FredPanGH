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
