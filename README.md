# IFRS 17 CSM Calculation Helpers

Small Python helpers for IFRS 17 contractual service margin (CSM) examples.

## Files

- `ifrs17_csm.py`: calculation functions
- `test_ifrs17_csm.py`: unit tests

## Run tests

```bash
python -m unittest -v
```

## Example usage

```python
from ifrs17_csm import (
    InitialRecognitionInputs,
    CSMYearInputs,
    calculate_initial_csm,
    build_csm_rollforward_schedule,
    build_ifrs17_csm_disclosure,
)

initial = calculate_initial_csm(
    InitialRecognitionInputs(
        pv_future_outflows=1000.0,
        risk_adjustment=20.0,
        pv_future_inflows=1120.0,
    )
)

schedule = build_csm_rollforward_schedule(
    opening_csm=100.0,
    years=[
        CSMYearInputs("Year1", 0.03, -12.0, 25.0, 100.0),
        CSMYearInputs("Year2", 0.03, 4.0, 35.0, 75.0),
        CSMYearInputs("Year3", 0.03, -1.0, 40.0, 40.0),
    ],
)

disclosure_rows = build_ifrs17_csm_disclosure(schedule)
print(initial)
print(schedule)
print(disclosure_rows)
```
