# FredPanGH

## Present value helper

This repository includes a simple finance utility:

```python
from finance import present_value

# End-of-year + mid-year cashflows with yearly varying interest rates (in %)
pv = present_value(
    payments=[200, 220, 240, 260, 280],
    mid_year_payments=[50, 60, 70, 80, 90],
    years=5,
    annual_rate_percents=[7, 6.5, 7.2, 6.8, 7.0],
)
print(round(pv, 2))  # 1268.36
```

Formula used:

`PV = Σ(t=1..Y) [CF_mid_t / (Π(i=1..t-1)(1 + Z_i/100) * (1 + Z_t/100)^0.5) + CF_end_t / Π(i=1..t)(1 + Z_i/100)]`
