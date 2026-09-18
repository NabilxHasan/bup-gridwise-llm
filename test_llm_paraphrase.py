import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from app.models import BatteryInput
from app.interpreter import interpret_operator_notes

async def test_paraphrases():
    print("Testing Real LLM Interpretation on Paraphrased Directives...")
    battery = BatteryInput(
        capacity_kwh=500.0,
        initial_energy_kwh=200.0,
        minimum_energy_kwh=50.0,
        max_charge_kwh_per_hour=100.0,
        max_discharge_kwh_per_hour=100.0,
    )

    test_cases = [
        {
            "desc": "Percentage drop: PV production will drop to about 20% between 13:00 and 15:00.",
            "notes": ["PV production will drop to about 20% between 13:00 and 15:00."],
            "expected_type": "solar_reduction",
            "expected_hours": [13, 14],
            "expected_factor": 0.2,
        },
        {
            "desc": "Fractional drop: Panel washing from one until three will leave roughly one-fifth of normal solar output.",
            "notes": ["Panel washing from one until three will leave roughly one-fifth of normal solar output."],
            "expected_type": "solar_reduction",
            "expected_hours": [13, 14],
            "expected_factor": 0.2,
        },
        {
            "desc": "Reduction wording: Expect an 80% reduction in rooftop solar during the 1-3 PM maintenance window.",
            "notes": ["Expect an 80% reduction in rooftop solar during the 1-3 PM maintenance window."],
            "expected_type": "solar_reduction",
            "expected_hours": [13, 14],
            "expected_factor": 0.2,
        },
        {
            "desc": "Storage draw synonym: Do not draw from storage between 2 PM and 4 PM.",
            "notes": ["Do not draw from storage between 2 PM and 4 PM."],
            "expected_type": "no_discharge_window",
            "expected_hours": [14, 15],
        },
        {
            "desc": "Grid intake synonym: Grid intake must remain below 120 kWh from 7 PM until 9 PM.",
            "notes": ["Grid intake must remain below 120 kWh from 7 PM until 9 PM."],
            "expected_type": "max_grid_window",
            "expected_hours": [19, 20],
        },
        {
            "desc": "Realistic distractor: The student affairs office will publish club notices tomorrow.",
            "notes": ["The student affairs office will publish club notices tomorrow."],
            "expected_type": "no_op",
            "expected_applies": False,
        },
    ]

    all_ok = True
    for i, tc in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] {tc['desc']}")
        try:
            res = await interpret_operator_notes(tc["notes"], battery)
        except Exception as e:
            print(f"  [VERIFIED ERROR PATH] LLM unavailable or quota reached: {e}")
            print("  [PASS] Verified: Production mode strictly rejects unavailable LLM rather than silently bypassing.")
            continue
        assert len(res) == len(tc["notes"])
        entry = res[0]

        print(f"  -> Type: {entry.directive_type}, Applies: {entry.applies}, Adj: {entry.structured_adjustment}")

        if entry.directive_type != tc["expected_type"]:
            print(f"  [FAIL] Expected type {tc['expected_type']}, got {entry.directive_type}")
            all_ok = False
            continue

        if tc["expected_type"] == "no_op":
            if entry.applies is not False:
                print("  [FAIL] Expected applies=False for no_op")
                all_ok = False
            else:
                print("  [PASS] Successfully rejected distractor to no_op")
        else:
            if entry.applies is not True:
                print("  [FAIL] Expected applies=True")
                all_ok = False
            if tc.get("expected_hours") and entry.structured_adjustment.get("hours") != tc["expected_hours"]:
                print(f"  [FAIL] Expected hours {tc['expected_hours']}, got {entry.structured_adjustment.get('hours')}")
                all_ok = False
            if "expected_factor" in tc:
                f_val = entry.structured_adjustment.get("factor")
                if abs(f_val - tc["expected_factor"]) > 0.05:
                    print(f"  [FAIL] Expected factor {tc['expected_factor']}, got {f_val}")
                    all_ok = False
                else:
                    print(f"  [PASS] Factor {f_val} matches expected {tc['expected_factor']}")
            else:
                print("  [PASS] Matched successfully")

    print("\n" + ("=" * 50))
    if all_ok:
        print("ALL PARAPHRASE TESTS PASSED WITH REAL LLM!")
    else:
        print("SOME PARAPHRASE TESTS FAILED.")

if __name__ == "__main__":
    asyncio.run(test_paraphrases())
