# FredPanGH

## Present value helper

This repository includes a simple finance utility:

```python
from finance import present_value

# Cashflow payments each year with yearly varying interest rates (in %)
pv = present_value(
    payments=[200, 220, 240, 260, 280],
    years=5,
    annual_rate_percents=[7, 6.5, 7.2, 6.8, 7.0],
)
print(round(pv, 2))  # 976.3
```

Formula used:

`PV = Σ(t=1..Y) [CF_t / Π(i=1..t)(1 + Z_i/100)]`
