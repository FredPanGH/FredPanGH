import math
import unittest

from ifrs17_csm import (
    CSMYearInputs,
    InitialRecognitionInputs,
    build_csm_rollforward_schedule,
    build_ifrs17_csm_disclosure,
    calculate_initial_csm,
    roll_forward_csm_year,
)


class IFRS17CSMTests(unittest.TestCase):
    def test_initial_recognition_profitable_group(self) -> None:
        result = calculate_initial_csm(
            InitialRecognitionInputs(
                pv_future_outflows=1000.0,
                risk_adjustment=20.0,
                pv_future_inflows=1120.0,
            )
        )

        self.assertEqual(result["fulfilment_cash_flows"], -100.0)
        self.assertEqual(result["initial_csm"], 100.0)
        self.assertEqual(result["day1_loss_pnl"], 0.0)
        self.assertEqual(result["net_lrc_initial"], 0.0)

    def test_single_year_rollforward(self) -> None:
        result = roll_forward_csm_year(
            opening_csm=100.0,
            locked_in_rate=0.03,
            future_service_adjustment=-12.0,
            coverage_units_provided=25.0,
            coverage_units_total_start=100.0,
        )

        self.assertTrue(math.isclose(result["interest_accretion"], 3.0))
        self.assertTrue(math.isclose(result["csm_before_release"], 91.0))
        self.assertTrue(math.isclose(result["csm_release"], 22.75))
        self.assertTrue(math.isclose(result["closing_csm"], 68.25))
        self.assertEqual(result["loss_component_expense"], 0.0)

    def test_three_year_schedule_and_disclosure(self) -> None:
        assumptions = [
            CSMYearInputs("Year1", 0.03, -12.0, 25.0, 100.0),
            CSMYearInputs("Year2", 0.03, 4.0, 35.0, 75.0),
            CSMYearInputs("Year3", 0.03, -1.0, 40.0, 40.0),
        ]

        schedule = build_csm_rollforward_schedule(opening_csm=100.0, years=assumptions)
        self.assertEqual(len(schedule), 3)
        self.assertTrue(math.isclose(float(schedule[0]["closing_csm"]), 68.25, abs_tol=1e-6))
        self.assertTrue(math.isclose(float(schedule[1]["closing_csm"]), 39.62533333333334, abs_tol=1e-6))
        self.assertTrue(math.isclose(float(schedule[2]["closing_csm"]), 0.0, abs_tol=1e-6))

        disclosure = build_ifrs17_csm_disclosure(schedule)
        self.assertEqual(len(disclosure), 3)
        self.assertTrue(
            math.isclose(
                float(disclosure[1]["csm_recognized_in_insurance_revenue"]),
                -34.67216666666667,
                abs_tol=1e-6,
            )
        )

    def test_onerous_change_creates_loss_component(self) -> None:
        result = roll_forward_csm_year(
            opening_csm=15.0,
            locked_in_rate=0.0,
            future_service_adjustment=-30.0,
            coverage_units_provided=0.0,
            coverage_units_total_start=100.0,
        )
        self.assertEqual(result["csm_before_release"], 0.0)
        self.assertEqual(result["closing_csm"], 0.0)
        self.assertEqual(result["loss_component_expense"], 15.0)


if __name__ == "__main__":
    unittest.main()
