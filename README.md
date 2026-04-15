# FredPanGH

## Present value helper

This repository includes a simple finance utility:

```python
from finance import present_value

# Beginning-of-year + mid-year + end-of-year cashflows with yearly varying rates (in %)
pv = present_value(
    beginning_year_payments=[30, 35, 40, 45, 50],
    payments=[200, 220, 240, 260, 280],
    mid_year_payments=[50, 60, 70, 80, 90],
    years=5,
    annual_rate_percents=[7, 6.5, 7.2, 6.8, 7.0],
)
print(round(pv, 2))  # 1441.33
```

Formula used:

`PV = Σ(t=1..Y) [CF_begin_t / Π(i=1..t-1)(1 + Z_i/100) + CF_mid_t / (Π(i=1..t-1)(1 + Z_i/100) * (1 + Z_t/100)^0.5) + CF_end_t / Π(i=1..t)(1 + Z_i/100)]`
