import json

with open(r"C:\Users\nabil\Downloads\BUP_CSE_FEST_2026_Participant_Docs\BUP_CSE_FEST_2026_Preli_Public_Sample_Cases.json", "r", encoding="utf-8") as f:
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
