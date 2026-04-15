# FredPanGH

## Present value helper

This repository includes a simple finance utility:

```python
from finance import present_value

# X payable in Y years with constant interest Z%
pv = present_value(amount=1000, years=5, annual_rate_percent=7)
print(round(pv, 2))  # 712.99
```

Formula used:

`PV = X / (1 + Z/100)^Y`
