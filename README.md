# IFRS 17 CSM Calculation Helpers

Small Python helpers for IFRS 17 contractual service margin (CSM) examples.

## Files

- `ifrs17_csm.py`: calculation functions
- `test_ifrs17_csm.py`: unit tests

## Run tests

```bash
python3 -m unittest -v
```

## Example usage

```python
from ifrs17_csm import (
    InitialRecognitionInputs,
    CSMYearInputs,
    calculate_initial_csm,
    build_csm_rollforward_schedule,
    build_ifrs17_csm_disclosure,
    project_csm_over_horizon,
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

## 50-year projection usage

```python
from ifrs17_csm import project_csm_over_horizon

fifty_year_schedule = project_csm_over_horizon(
    opening_csm=100.0,
    projection_years=50,
    locked_in_rates=0.03,  # scalar repeated across all years
    future_service_adjustments=[0.0] * 50,
    coverage_units_provided=[2.0] * 50,  # totals inferred as runoff
)
```
