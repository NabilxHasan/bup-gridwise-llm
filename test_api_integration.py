import os
import json
from pathlib import Path

# Enable offline mock for local testing without external API quota constraints
os.environ["GRIDWISE_DEV_OFFLINE_MOCK"] = "1"

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

DATA_PATH = Path(__file__).resolve().parent / "data" / "sample_cases.json"

def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200, f"Health check failed: {resp.status_code}"
    data = resp.json()
    assert data.get("status") == "ok", f"Expected status 'ok', got {data}"
    print("[PASS] GET /health returns 200 and {'status': 'ok'}")

def test_sample_cases():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    all_passed = True
    for c in data["cases"]:
        cid = c["id"]
        label = c.get("label", "")
        payload = c["input"]
        expected = c["expected_output"]

        resp = client.post("/optimize-energy", json=payload)
        assert resp.status_code == 200, f"API failed on {cid}: status={resp.status_code}, text={resp.text}"

        res_json = resp.json()

        # Check top-level fields
        assert res_json["scenario_id"] == payload["scenario_id"]
        assert len(res_json["hourly_plan"]) == 24
        assert len(res_json["directive_interpretation"]) == len(payload["operator_notes"])

        # Check cost match
        cost_diff = abs(res_json["total_cost_bdt"] - expected["total_cost_bdt"])
        grid_diff = abs(res_json["total_grid_kwh"] - expected["total_grid_kwh"])

        status = "PASS" if cost_diff <= 0.05 else "FAIL"
        if status == "FAIL":
            all_passed = False

        print(f"[{status}] {cid} ({label}): Cost ours={res_json['total_cost_bdt']} ref={expected['total_cost_bdt']} (diff={cost_diff:.2f}) | Grid ours={res_json['total_grid_kwh']} ref={expected['total_grid_kwh']}")

    assert all_passed, "Some cases failed matching optimal cost!"
    print("\n[ALL 10 SAMPLES PASSED API ENDPOINT TEST WITH 100% ACCURACY!]")

def test_malformed_input():
    resp = client.post("/optimize-energy", json={"invalid": "payload"})
    assert resp.status_code in (400, 422), f"Expected 400/422 on bad input, got {resp.status_code}"
    print(f"[PASS] Malformed input safely rejected with HTTP {resp.status_code}")

if __name__ == "__main__":
    test_health()
    test_sample_cases()
    test_malformed_input()
