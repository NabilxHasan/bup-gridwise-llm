import os
import re
import json
import logging
from typing import List, Dict, Any, Optional
import httpx

from app.models import DirectiveInterpretationEntry, BatteryInput
from app.guardrail import apply_guardrails

logger = logging.getLogger("gridwise.interpreter")

SYSTEM_PROMPT = """You are the official GridWise operator directive parser for the BUP CSE Fest 2026 Smart Campus Energy Challenge.
Your job is to parse 1 to 3 campus operator notes into machine-checkable structured directives.

Each operator note must map to EXACTLY ONE of the following 6 directive types:
1. solar_reduction: usable solar is reduced.
   structured_adjustment: {"hours": [sorted ascending unique ints 0..23], "factor": float}
   CRITICAL: "factor" is the USABLE FRACTION REMAINING (between 0.0 and 1.0).
   - "80% reduction" means factor is 0.2.
   - "drop to 20%" means factor is 0.2.
   - "leave about half" means factor is 0.5.
   - "roughly one-fifth" means factor is 0.2.
   - "roughly 25%" means factor is 0.25.

2. minimum_battery_reserve: keep battery energy at or above a required level.
   structured_adjustment: {"hours": [sorted ascending unique ints 0..23], "minimum_energy_kwh": float}
   - If stated in kWh (e.g. "at least 90 kWh", "80 kWh to remain in the battery"), use that number.
   - If stated as percentage of battery capacity (e.g. "at least 50% of the battery capacity"), calculate: (pct / 100) * battery_capacity_kwh.

3. no_charge_window: battery charging unavailable.
   structured_adjustment: {"hours": [sorted ascending unique ints 0..23]}

4. no_discharge_window: battery discharging unavailable.
   structured_adjustment: {"hours": [sorted ascending unique ints 0..23]}

5. max_grid_window: grid import cannot exceed a stated amount.
   structured_adjustment: {"hours": [sorted ascending unique ints 0..23], "max_grid_kwh": float}

6. no_op: note does not affect the 24-hour schedule (e.g. cafeteria menu, library hours, seminar room bookings, sports deadlines).
   applies: false
   structured_adjustment: null

TIME CONVENTION:
Hours are whole-hour integers from 0 to 23.
Start hour is INCLUDED, end hour is EXCLUDED.
- "1 PM to 3 PM" -> [13, 14]
- "noon until 2 PM" -> [12, 13]
- "10 AM until noon" -> [10, 11]
- "6 PM until 9 PM" -> [18, 19, 20]
- "2 AM until 5 AM" -> [2, 3, 4]
- "between 11 AM and 2 PM" -> [11, 12, 13]
- "6 PM until 10 PM" -> [18, 19, 20, 21]

OUTPUT FORMAT:
Return strictly a JSON object:
{
  "directive_interpretation": [
    {
      "note_index": 0,
      "applies": true,
      "directive_type": "...",
      "structured_adjustment": {...},
      "explanation": "..."
    }
  ]
}
"""


def parse_time_window(text: str) -> List[int]:
    """Deterministic parser for start-inclusive, end-exclusive time windows."""
    t_lower = text.lower()

    def to_hour(val_str: str, period: Optional[str] = None) -> Optional[int]:
        val_str = val_str.strip().lower()
        if val_str == "noon" or val_str == "12 noon":
            return 12
        if val_str == "midnight" or val_str == "12 midnight":
            return 0
        m = re.match(r"^(\d{1,2})(?::(\d{2}))?\s*(am|pm)?$", val_str)
        if not m:
            return None
        h = int(m.group(1))
        p = m.group(3) or (period.lower() if period else None)
        if p == "pm" and h < 12:
            h += 12
        elif p == "am" and h == 12:
            h = 0
        return h if 0 <= h <= 24 else None

    patterns = [
        r"(?:from|between|during)?\s*([0-9]{1,2}(?::[0-9]{2})?\s*(?:am|pm)?|noon|midnight)\s*(?:until|to|and|-)\s*([0-9]{1,2}(?::[0-9]{2})?\s*(?:am|pm)?|noon|midnight)",
        r"([0-9]{1,2})-([0-9]{1,2})\s*(am|pm)\s*maintenance window",
    ]

    start_h = None
    end_h = None

    for pat in patterns:
        m = re.search(pat, t_lower)
        if m:
            g = m.groups()
            if len(g) == 3 and g[2] in ("am", "pm"):
                period = g[2]
                start_h = to_hour(g[0], period)
                end_h = to_hour(g[1], period)
            else:
                p1_str = g[0]
                p2_str = g[1]
                p2_period = "pm" if "pm" in p2_str else ("am" if "am" in p2_str else None)
                start_h = to_hour(p1_str, p2_period)
                end_h = to_hour(p2_str)
            if start_h is not None and end_h is not None:
                break

    if start_h is not None and end_h is not None:
        if end_h <= start_h:
            return []
        return list(range(start_h, end_h))

    return []


def deterministic_fallback_interpret(
    notes: List[str],
    battery: BatteryInput,
) -> List[Dict[str, Any]]:
    """High-precision deterministic rule parser for operator notes as a fallback."""
    results = []
    for idx, note in enumerate(notes):
        n_lower = note.lower()
        hours = parse_time_window(note)

        is_distractor = any(kw in n_lower for kw in [
            "cafeteria", "menu", "seminar room", "registration", "deadline",
            "library", "book", "club notices", "sports office", "publish"
        ])

        if is_distractor or not hours:
            results.append({
                "note_index": idx,
                "applies": False,
                "directive_type": "no_op",
                "structured_adjustment": None,
                "explanation": "Note does not affect today's energy schedule.",
            })
            continue

        # 1. Solar reduction
        if any(kw in n_lower for kw in ["solar", "pv", "panel", "cloud", "washing", "cleaning", "inverter"]):
            factor = 0.5
            m_pct = re.search(r"(\d+)%", n_lower)
            if m_pct:
                pct = float(m_pct.group(1))
                if "reduction" in n_lower or "reduced by" in n_lower or "drop by" in n_lower:
                    factor = max(0.0, min(1.0, 1.0 - (pct / 100.0)))
                else:
                    factor = max(0.0, min(1.0, pct / 100.0))
            elif "one-fifth" in n_lower:
                factor = 0.2
            elif "half" in n_lower:
                factor = 0.5
            elif "quarter" in n_lower:
                factor = 0.25

            results.append({
                "note_index": idx,
                "applies": True,
                "directive_type": "solar_reduction",
                "structured_adjustment": {"hours": hours, "factor": factor},
                "explanation": f"Solar reduction applied for hours {hours} with factor {factor}.",
            })

        # 2. No charge window
        elif any(kw in n_lower for kw in ["charger", "charging"]) or ("charge" in n_lower and any(kw in n_lower for kw in ["isolated", "unavailable", "disabled", "maintenance", "not charge"])):
            results.append({
                "note_index": idx,
                "applies": True,
                "directive_type": "no_charge_window",
                "structured_adjustment": {"hours": hours},
                "explanation": f"Battery charging unavailable during hours {hours}.",
            })

        # 3. No discharge window
        elif "discharge" in n_lower and any(kw in n_lower for kw in ["not discharge", "disabled", "testing", "unavailable"]):
            results.append({
                "note_index": idx,
                "applies": True,
                "directive_type": "no_discharge_window",
                "structured_adjustment": {"hours": hours},
                "explanation": f"Battery discharging unavailable during hours {hours}.",
            })

        # 4. Minimum battery reserve
        elif any(kw in n_lower for kw in ["reserve", "stored in the battery", "remain in the battery", "in the battery"]) or ("battery" in n_lower and "at least" in n_lower):
            min_kwh = battery.minimum_energy_kwh
            m_pct = re.search(r"(\d+)%\s*of\s*(?:the\s*)?battery capacity", n_lower)
            if m_pct:
                pct = float(m_pct.group(1))
                min_kwh = (pct / 100.0) * battery.capacity_kwh
            else:
                m_kwh = re.search(r"(\d+(?:\.\d+)?)\s*kwh", n_lower)
                if m_kwh:
                    min_kwh = float(m_kwh.group(1))

            results.append({
                "note_index": idx,
                "applies": True,
                "directive_type": "minimum_battery_reserve",
                "structured_adjustment": {"hours": hours, "minimum_energy_kwh": min_kwh},
                "explanation": f"Minimum battery reserve of {min_kwh} kWh required for hours {hours}.",
            })

        # 5. Max grid window
        elif any(kw in n_lower for kw in ["grid", "feeder", "transformer", "substation", "intake"]):
            max_grid = 1e6
            m_kwh = re.search(r"(\d+(?:\.\d+)?)\s*kwh", n_lower)
            if m_kwh:
                max_grid = float(m_kwh.group(1))

            results.append({
                "note_index": idx,
                "applies": True,
                "directive_type": "max_grid_window",
                "structured_adjustment": {"hours": hours, "max_grid_kwh": max_grid},
                "explanation": f"Grid import capped at {max_grid} kWh during hours {hours}.",
            })

        else:
            results.append({
                "note_index": idx,
                "applies": False,
                "directive_type": "no_op",
                "structured_adjustment": None,
                "explanation": "Note does not affect today's energy schedule.",
            })

    return results


async def call_llm_api(notes: List[str], battery: BatteryInput) -> Optional[List[Dict[str, Any]]]:
    """Calls Gemini or OpenAI-compatible endpoint with strict JSON schema output and retry logic."""
    gemini_key = os.environ.get("GEMINI_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")
    groq_key = os.environ.get("GROQ_API_KEY")
    puku_key = os.environ.get("PUKU_API_KEY")

    prompt_content = f"""Scenario Battery Parameters:
- capacity_kwh: {battery.capacity_kwh}
- minimum_energy_kwh: {battery.minimum_energy_kwh}

Operator Notes to Interpret:
"""
    for i, note in enumerate(notes):
        prompt_content += f"Note {i}: {note}\n"

    # Priority 1: Native Gemini API with retry
    if gemini_key:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt_content}]}],
            "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.0,
            },
        }
        for attempt in range(1, 3):
            try:
                async with httpx.AsyncClient(timeout=4.0) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            text_resp = candidates[0]["content"]["parts"][0]["text"]
                            parsed = json.loads(text_resp)
                            if "directive_interpretation" in parsed and isinstance(parsed["directive_interpretation"], list):
                                return parsed["directive_interpretation"]
                    elif resp.status_code == 429:
                        logger.warning(f"Gemini 429 Rate Limit on attempt {attempt}/2. Backing off 0.8s...")
                        import asyncio
                        await asyncio.sleep(0.8)
                    else:
                        logger.warning(f"Gemini API returned HTTP {resp.status_code} on attempt {attempt}/2: {resp.text[:150]}")
            except Exception as e:
                logger.warning(f"Gemini API attempt {attempt}/2 failed or timed out: {e}")
                if attempt == 1:
                    import asyncio
                    await asyncio.sleep(0.5)

    # Priority 2: OpenAI / Groq / Puku OpenAI-compatible endpoints with retry
    api_key = openai_key or groq_key or puku_key
    if api_key:
        if groq_key:
            base_url = "https://api.groq.com/openai/v1"
            model = "llama-3.1-8b-instant"
        elif puku_key:
            base_url = "https://api.puku.sh/v1"
            model = "gpt-4o-mini"
        else:
            base_url = "https://api.openai.com/v1"
            model = "gpt-4o-mini"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt_content},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.0,
        }
        for attempt in range(1, 3):
            try:
                async with httpx.AsyncClient(timeout=4.0) as client:
                    resp = await client.post(f"{base_url}/chat/completions", headers=headers, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        content = data["choices"][0]["message"]["content"]
                        parsed = json.loads(content)
                        if "directive_interpretation" in parsed and isinstance(parsed["directive_interpretation"], list):
                            return parsed["directive_interpretation"]
                    elif resp.status_code == 429:
                        logger.warning(f"OpenAI/Groq 429 Rate Limit on attempt {attempt}/2. Backing off 0.8s...")
                        import asyncio
                        await asyncio.sleep(0.8)
                    else:
                        logger.warning(f"OpenAI/Groq API returned HTTP {resp.status_code} on attempt {attempt}/2: {resp.text[:150]}")
            except Exception as e:
                logger.warning(f"OpenAI/Groq attempt {attempt}/2 failed or timed out: {e}")
                if attempt == 1:
                    import asyncio
                    await asyncio.sleep(0.5)

    logger.warning(f"All LLM attempts failed or credentials missing for notes: {notes}. Triggering deterministic fallback parser.")
    return None


async def interpret_operator_notes(
    notes: List[str],
    battery: BatteryInput,
) -> List[DirectiveInterpretationEntry]:
    """Interprets notes via LLM with deterministic guardrails and instantaneous fallback."""
    raw_interpretations = await call_llm_api(notes, battery)

    if not raw_interpretations:
        logger.warning(
            f"[FALLBACK TRIGGERED] LLM interpretation unavailable for {len(notes)} notes: {notes}. "
            f"Invoking deterministic regex/keyword fallback parser."
        )
        raw_interpretations = deterministic_fallback_interpret(notes, battery)

    guarded_entries = apply_guardrails(
        raw_interpretations,
        num_notes=len(notes),
        battery_capacity=battery.capacity_kwh,
    )

    return guarded_entries
