# FredPanGH

## Present value helper

This repository includes a simple finance utility:

```python
from finance import present_value

# X payable in Y years with yearly varying interest rates (in %)
pv = present_value(amount=1000, years=5, annual_rate_percents=[7, 6.5, 7.2, 6.8, 7.0])
print(round(pv, 2))  # 716.34
```

Formula used:

`PV = X / Π(i=1..Y) (1 + Z_i/100)`
