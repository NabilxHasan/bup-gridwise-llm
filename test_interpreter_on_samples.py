import json
from pathlib import Path
from app.models import BatteryInput
from app.interpreter import deterministic_fallback_interpret, parse_time_window
from app.guardrail import apply_guardrails

def test_all():
    sample_path = Path(__file__).resolve().parent / "data" / "sample_cases.json"
    with open(sample_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    all_matched = True
    for c in data["cases"]:
        cid = c["id"]
        label = c.get("label", "")
        battery = BatteryInput(**c["input"]["battery"])
        notes = c["input"]["operator_notes"]
        expected_dirs = c["expected_output"]["directive_interpretation"]

        raw = deterministic_fallback_interpret(notes, battery)
        guarded = apply_guardrails(raw, len(notes), battery.capacity_kwh)

        case_ok = True
        diff_msgs = []
        for exp, act in zip(expected_dirs, guarded):
            if exp["note_index"] != act.note_index:
                case_ok = False
                diff_msgs.append(f"note_index {exp['note_index']} != {act.note_index}")
            if exp["applies"] != act.applies:
                case_ok = False
                diff_msgs.append(f"applies {exp['applies']} != {act.applies}")
            if exp["directive_type"] != act.directive_type:
                case_ok = False
                diff_msgs.append(f"type {exp['directive_type']} != {act.directive_type}")
            if exp["applies"]:
                exp_adj = exp["structured_adjustment"]
                act_adj = act.structured_adjustment
                if act_adj is None:
                    case_ok = False
                    diff_msgs.append(f"act_adj is None for {exp['directive_type']}")
                else:
                    if exp_adj.get("hours") != act_adj.get("hours"):
                        case_ok = False
                        diff_msgs.append(f"hours {exp_adj.get('hours')} != {act_adj.get('hours')}")
                    if "factor" in exp_adj and abs(exp_adj["factor"] - act_adj.get("factor", 0)) > 0.01:
                        case_ok = False
                        diff_msgs.append(f"factor {exp_adj.get('factor')} != {act_adj.get('factor')}")
                    if "minimum_energy_kwh" in exp_adj and abs(exp_adj["minimum_energy_kwh"] - act_adj.get("minimum_energy_kwh", 0)) > 0.01:
                        case_ok = False
                        diff_msgs.append(f"min_kwh {exp_adj.get('minimum_energy_kwh')} != {act_adj.get('minimum_energy_kwh')}")
                    if "max_grid_kwh" in exp_adj and abs(exp_adj["max_grid_kwh"] - act_adj.get("max_grid_kwh", 0)) > 0.01:
                        case_ok = False
                        diff_msgs.append(f"max_grid {exp_adj.get('max_grid_kwh')} != {act_adj.get('max_grid_kwh')}")

        status = "PASS" if case_ok else "FAIL"
        if not case_ok:
            all_matched = False
            print(f"[{status}] {cid} ({label}): {diff_msgs}")
            for n in notes:
                print(f"   Note: '{n}' -> parsed hours: {parse_time_window(n)}")
        else:
            print(f"[{status}] {cid} ({label})")

    if all_matched:
        print("\nALL 10 SAMPLE CASES DIRECTIVES MATCHED EXPECTED GROUND TRUTH 100%!")
    else:
        print("\nSOME DIRECTIVES DIFFERED - CHECK ABOVE")

if __name__ == "__main__":
    test_all()
