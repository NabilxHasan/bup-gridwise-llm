import argparse
import time
import json
import httpx

def main():
    parser = argparse.ArgumentParser(description="GridWise Remote or Local API Tester")
    parser.add_argument("--url", default="https://bup-gridwise-llm.onrender.com", help="Base URL of service")
    parser.add_argument("--sample", default=r"C:\Users\nabil\Downloads\BUP_CSE_FEST_2026_Participant_Docs\BUP_CSE_FEST_2026_Preli_Public_Sample_Cases.json", help="Path to sample cases JSON")
    args = parser.parse_args()

    base_url = args.url.rstrip("/")
    print(f"Testing GridWise endpoint at: {base_url}\n")

    # 1. Health check
    t0 = time.time()
    try:
        with httpx.Client(timeout=15.0) as client:
            h_resp = client.get(f"{base_url}/health")
            h_time = time.time() - t0
            print(f"[HEALTH] Status: {h_resp.status_code}, Body: {h_resp.json()}, Time: {h_time:.3f}s")
            assert h_resp.status_code == 200 and h_resp.json().get("status") == "ok"
    except Exception as e:
        print(f"[FATAL] /health failed: {e}")
        return

    # 2. Test sample cases
    with open(args.sample, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"\nRunning {len(data['cases'])} test scenarios against /optimize-energy:")
    latencies = []
    all_ok = True

    with httpx.Client(timeout=30.0) as client:
        for c in data["cases"]:
            cid = c["id"]
            inp = c["input"]
            exp = c["expected_output"]

            t_start = time.time()
            resp = client.post(f"{base_url}/optimize-energy", json=inp)
            elapsed = time.time() - t_start
            latencies.append(elapsed)

            if resp.status_code != 200:
                print(f"[{cid}] FAILED HTTP {resp.status_code}: {resp.text}")
                all_ok = False
                continue

            res = resp.json()
            cost_diff = abs(res["total_cost_bdt"] - exp["total_cost_bdt"])
            status = "PASS" if cost_diff <= 0.05 else "WARN"
            print(f"[{status}] {cid} ({elapsed:.3f}s): Cost={res['total_cost_bdt']} (ref={exp['total_cost_bdt']}, diff={cost_diff:.2f}) | Grid={res['total_grid_kwh']}")

    avg_lat = sum(latencies) / len(latencies)
    p95_lat = sorted(latencies)[int(len(latencies) * 0.95)]
    print(f"\nSummary:")
    print(f"- Scenarios tested: {len(latencies)}")
    print(f"- Average latency:  {avg_lat:.3f}s")
    print(f"- p95 latency:      {p95_lat:.3f}s (Threshold for max points: <= 5.0s)")
    if all_ok and p95_lat <= 5.0:
        print("\nALL TESTS PASSED & QUALIFIED FOR FULL RELIABILITY/PERFORMANCE POINTS!")

if __name__ == "__main__":
    main()
