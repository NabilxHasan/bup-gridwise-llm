import json
import sys
from pathlib import Path
from app.models import HourInput, BatteryInput, DirectiveInterpretationEntry
from app.optimizer import solve_energy_schedule
from app.verifier import verify_schedule

def run():
    sample_path = Path(__file__).resolve().parent / "data" / "sample_cases.json"
    with open(sample_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    cases = data.get("cases", [])
    print(f"Loaded {len(cases)} sample cases.")

    all_passed = True
    for c in cases:
        cid = c["id"]
        label = c.get("label", "")
        inp = c["input"]
        expected = c["expected_output"]

        hours = [HourInput(**h) for h in inp["hours"]]
        battery = BatteryInput(**inp["battery"])
        directives = [DirectiveInterpretationEntry(**d) for d in expected["directive_interpretation"]]

        plan, total_grid, total_cost, peak_grid = solve_energy_schedule(hours, battery, directives)
        ok, msg = verify_schedule(hours, battery, directives, plan)

        ref_cost = expected["total_cost_bdt"]
        ref_grid = expected["total_grid_kwh"]
        ref_peak = expected["peak_grid_kwh"]

        cost_diff = abs(total_cost - ref_cost)
        grid_diff = abs(total_grid - ref_grid)

        status = "PASS" if ok and cost_diff <= 0.05 else "FAIL"
        if status == "FAIL":
            all_passed = False

        print(f"[{status}] {cid} ({label}): verified={ok} (msg={msg}) | Cost: ours={total_cost} ref={ref_cost} (diff={cost_diff:.2f}) | Grid: ours={total_grid} ref={ref_grid}")

    if all_passed:
        print("\nALL 10 SAMPLE CASES PASSED OPTIMIZATION & VERIFICATION!")
    else:
        print("\nSOME CASES HAD DIFFERENCES - CHECK OUTPUT ABOVE")

if __name__ == "__main__":
    run()
