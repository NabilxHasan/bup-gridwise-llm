# GridWise LLM — Smart Campus Energy Optimization Service
**BUP CSE Fest 2026 Hackathon · Online Preliminary Round**
**Team: `DU_Ubermensch`**

GridWise LLM is an autonomous, high-performance energy scheduling service built for the BUP CSE Fest 2026 Hackathon in association with Poridhi.io. It converts natural-language campus operator directives into structured constraints using language models, filters outputs through deterministic mathematical guardrails, and executes an exact 24-hour Linear Programming (LP) optimization via HiGHS to minimize grid electricity costs while maintaining battery neutrality, grid limits, and energy balance.

---

## 1. System Architecture

The pipeline strictly implements the canonical flow defined in Section 03 of the Problem Statement:

```
┌─────────────────────────────────────────┐
│     Energy Scenario + Operator Notes    │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│        LLM Directive Interpreter        │
│   (Gemini 2.5 Flash / Groq / OpenAI)    │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│         Deterministic Guardrail         │
│  (Type safety, strict rejection to no_op)│
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│          Exact HiGHS LP Solver          │
│       (SciPy linprog / method='highs')  │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│         Shadow Replay Verifier          │
│    (Zero-tolerance invariant replay)    │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│         Structured JSON Response        │
│          (Section 10 API Schema)        │
└─────────────────────────────────────────┘
```

### Component Details:

1. **LLM Interpreter (`app/interpreter.py`)**:
   - Analyzes 1–3 natural-language operator directives in a single structured-output prompt.
   - Normalizes time intervals to whole-hour start-inclusive, end-exclusive windows (e.g., 1 PM to 3 PM $\rightarrow$ `[13, 14]`).
   - Maps inputs strictly into canonical directives (`solar_reduction`, `minimum_battery_reserve`, `no_charge_window`, `no_discharge_window`, `max_grid_window`, `no_op`).
   - Normalizes factors as remaining usable fractions (e.g., "80% reduction" $\rightarrow$ factor `0.2`).
   - Features a 3-attempt retry loop with exponential backoff on HTTP 429 rate limits or transient timeouts.
   - **Compliance Rule 04**: In production, the language model is mandatory in the interpretation path. If LLM providers are unavailable, the service returns a controlled HTTP 500 rather than bypassing the LLM requirement with silent keyword matching. (An isolated `GRIDWISE_DEV_OFFLINE_MOCK=1` mode is provided strictly for offline unit testing without external API credentials).

2. **Deterministic Guardrails (`app/guardrail.py`)**:
   - Enforces unique integers $0..23$ in ascending order. Malformed inputs (e.g. `13.8`, booleans, negative numbers) are strictly rejected to `no_op`.
   - Numeric bounds validation: out-of-range values (e.g. $factor \notin [0.0, 1.0]$, reserve $> capacity$) are safely rejected to `no_op` rather than inventing clamped values.
   - Strict `no_op` semantics: `applies = false` with `structured_adjustment = null`. All other valid directives use `applies = true`.
   - Preserves exact 1:1 `note_index` ordering ($0..N-1$).

3. **Exact Mathematical Optimizer (`app/optimizer.py`)**:
   - Formulates the 24-hour dispatch as a continuous Linear Program (LP) solved via C++ **HiGHS** (`scipy.optimize.linprog(..., method='highs')`).
   - 120 decision variables: grid import $g_h$, solar used $s_h$, battery charge $c_h$, battery discharge $d_h$, and battery state $E_h$ for $h \in [0..23]$.
   - Hard equality constraints enforce hourly energy balance, battery state transitions, and end-of-day battery neutrality ($E_{23} = E_{\text{init}}$).
   - Uses an $\epsilon$-penalty ($10^{-6} \cdot (c_h + d_h)$) in the objective function, mathematically guaranteeing zero simultaneous charge and discharge at optimality.
   - Solves in **$< 5$ milliseconds**, easily satisfying the $p95 \le 5\text{s}$ rubric for full latency marks.

4. **Shadow Replay Verifier (`app/verifier.py`)**:
   - Replays the entire 24-hour schedule hour-by-hour against all physical invariants and directive constraints before responding.
   - Recalculates `total_grid_kwh`, `total_cost_bdt`, and `peak_grid_kwh` to within 0.01 tolerance.
   - Returns a controlled HTTP 500 error if any generated schedule fails verification, preventing invalid schedules from ever being served.

---

## 2. Quickstart & Local Reproduction

### Prerequisites
- Python 3.10+ (tested on Python 3.11, 3.12, and 3.14)
- Git

### 1. Clone & Setup Virtual Environment
```bash
git clone https://github.com/NabilxHasan/bup-gridwise-llm.git
cd bup-gridwise-llm

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (Command Prompt):
.venv\Scripts\activate
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration
Create a `.env` file in the root directory:
```env
PORT=8000

# Provide your preferred language model API key:
GEMINI_API_KEY=your_gemini_api_key_here
# OPENAI_API_KEY=your_openai_api_key_here
# GROQ_API_KEY=your_groq_api_key_here
```

### 3. Run Service Locally
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 3. Verification & Testing

### 1. Readiness Check (`GET /health`)
```bash
curl -X GET http://localhost:8000/health
```
**Expected Response:**
```json
{
  "status": "ok"
}
```

### 2. Run Benchmark Test Suite
Execute the bundled test suite covering all 10 official public scenarios:
```bash
python test_api_integration.py
```
**Expected Output:**
```
[PASS] GET /health returns 200 and {'status': 'ok'}
[PASS] SAMPLE-01 (Solar cleaning + distractor): Cost diff=0.00 | Grid diff=0.00
[PASS] SAMPLE-02 (Battery charging maintenance): Cost diff=0.00 | Grid diff=0.00
[PASS] SAMPLE-03 (Emergency reserve as percentage): Cost diff=0.00 | Grid diff=0.00
[PASS] SAMPLE-04 (No-discharge protection test): Cost diff=0.00 | Grid diff=0.00
[PASS] SAMPLE-05 (Temporary feeder grid cap): Cost diff=0.00 | Grid diff=0.00
[PASS] SAMPLE-06 (Multiple notes with distractor): Cost diff=0.00 | Grid diff=0.00
[PASS] SAMPLE-07 (Reserve plus transformer cap): Cost diff=0.00 | Grid diff=0.00
[PASS] SAMPLE-08 (Separate charge/discharge outages): Cost diff=0.00 | Grid diff=0.00
[PASS] SAMPLE-09 (Reduction wording normalization): Cost diff=0.00 | Grid diff=0.00
[PASS] SAMPLE-10 (Multi-constraint evening operation): Cost diff=0.00 | Grid diff=0.00

[ALL 10 SAMPLES PASSED API ENDPOINT TEST WITH 100% ACCURACY!]
[PASS] Malformed input safely rejected with HTTP 400
```

### 3. Test Live Deployed Service
```bash
python run_live_test.py --url https://bup-gridwise-llm.onrender.com
```

---

## 4. Docker Fallback Execution

A pullable Docker image is published on Docker Hub for organizer evaluation:

### Option A: Pull & Run Published Image
```bash
docker pull nabilthelegend/bup-gridwise-llm:v1
docker run -d --name gridwise-app -p 8000:8000 -e GEMINI_API_KEY="your_key" nabilthelegend/bup-gridwise-llm:v1
```

### Option B: Build & Run Locally
```bash
docker build -t bup-gridwise-llm:latest .
docker run -d --name gridwise-app -p 8000:8000 -e GEMINI_API_KEY="your_key" bup-gridwise-llm:latest
```

### Verify Container Health
```bash
curl -X GET http://localhost:8000/health
```

---

## 5. Security & Error Handling Compliance

- **Section 06.1 HTTP Status Codes**:
  - `200`: Successful health or optimization response.
  - `400`: Malformed JSON or structurally invalid requests.
  - `422`: Semantically invalid but well-formed requests (e.g. out-of-order hours).
  - `500`: Controlled internal error. Does not expose secrets, credentials, or raw stack traces.
- **Zero Committed Secrets**: No API keys, tokens, or environment files are baked into the repository or Docker image.
- **Synthetic Data**: Operates strictly on synthetic benchmark profiles without requiring live utility credentials.

---

## 6. Credits & Libraries

- **FastAPI & Uvicorn**: High-concurrency asynchronous API framework.
- **SciPy (HiGHS)**: Mathematical linear programming solver (`scipy.optimize.linprog`).
- **Pydantic v2**: High-performance schema validation and serialization.
- **HTTPX**: Non-blocking HTTP client for model inference.
