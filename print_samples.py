import json
from pathlib import Path

sample_path = Path(__file__).resolve().parent / "data" / "sample_cases.json"
with open(sample_path, "r", encoding="utf-8") as f:
    data = json.load(f)

for c in data["cases"]:
    print(f"=== {c['id']}: {c.get('label')} ===")
    print(f"Battery: {c['input']['battery']}")
    for i, note in enumerate(c['input']['operator_notes']):
        print(f"  Note {i}: {note}")
    print("  Directives:")
    for d in c['expected_output']['directive_interpretation']:
        print(f"    idx={d['note_index']} type={d['directive_type']} applies={d['applies']} adj={d['structured_adjustment']}")
    print()
