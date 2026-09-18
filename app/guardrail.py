from typing import List, Dict, Any, Optional
from app.models import DirectiveInterpretationEntry


VALID_DIRECTIVE_TYPES = {
    "solar_reduction",
    "minimum_battery_reserve",
    "no_charge_window",
    "no_discharge_window",
    "max_grid_window",
    "no_op",
}


def sanitize_hours(hours_val: Any) -> List[int]:
    """Ensure hours are unique integers from 0 to 23 in strictly ascending order."""
    if not isinstance(hours_val, (list, tuple)):
        return []
    valid_h = set()
    for h in hours_val:
        try:
            h_int = int(h)
            if 0 <= h_int <= 23:
                valid_h.add(h_int)
        except (ValueError, TypeError):
            continue
    return sorted(list(valid_h))


def validate_and_repair_directive(
    raw_entry: Dict[str, Any],
    expected_index: int,
    battery_capacity: float = 1000.0,
) -> DirectiveInterpretationEntry:
    """Deterministic guardrail to validate and sanitize a single directive entry."""
    directive_type = str(raw_entry.get("directive_type", "no_op")).strip().lower()
    if directive_type not in VALID_DIRECTIVE_TYPES:
        directive_type = "no_op"

    explanation = str(raw_entry.get("explanation", "")).strip()
    if not explanation:
        explanation = f"Interpreted directive for note {expected_index}."

    if directive_type == "no_op":
        return DirectiveInterpretationEntry(
            note_index=expected_index,
            applies=False,
            directive_type="no_op",
            structured_adjustment=None,
            explanation=explanation or "This note does not affect the 24-hour energy schedule.",
        )

    adj = raw_entry.get("structured_adjustment")
    if not isinstance(adj, dict):
        return DirectiveInterpretationEntry(
            note_index=expected_index,
            applies=False,
            directive_type="no_op",
            structured_adjustment=None,
            explanation=explanation or "Malformed adjustment; ignored.",
        )

    hours = sanitize_hours(adj.get("hours"))
    if not hours:
        # Without valid hours, directive cannot be applied deterministically
        return DirectiveInterpretationEntry(
            note_index=expected_index,
            applies=False,
            directive_type="no_op",
            structured_adjustment=None,
            explanation=explanation or "No valid hours found; treated as no_op.",
        )

    sanitized_adj: Dict[str, Any] = {"hours": hours}

    if directive_type == "solar_reduction":
        raw_factor = adj.get("factor")
        try:
            factor = float(raw_factor)
            factor = max(0.0, min(1.0, factor))
        except (ValueError, TypeError):
            factor = 1.0
        sanitized_adj["factor"] = factor

    elif directive_type == "minimum_battery_reserve":
        raw_min = adj.get("minimum_energy_kwh")
        try:
            min_kwh = float(raw_min)
            min_kwh = max(0.0, min(battery_capacity, min_kwh))
        except (ValueError, TypeError):
            min_kwh = 0.0
        sanitized_adj["minimum_energy_kwh"] = min_kwh

    elif directive_type == "max_grid_window":
        raw_max = adj.get("max_grid_kwh")
        try:
            max_grid = float(raw_max)
            max_grid = max(0.0, max_grid)
        except (ValueError, TypeError):
            max_grid = 1e6
        sanitized_adj["max_grid_kwh"] = max_grid

    elif directive_type in ("no_charge_window", "no_discharge_window"):
        pass  # Only hours needed

    return DirectiveInterpretationEntry(
        note_index=expected_index,
        applies=True,
        directive_type=directive_type,
        structured_adjustment=sanitized_adj,
        explanation=explanation,
    )


def apply_guardrails(
    raw_interpretations: List[Dict[str, Any]],
    num_notes: int,
    battery_capacity: float = 1000.0,
) -> List[DirectiveInterpretationEntry]:
    """Enforces 1:1 mapping in exact note_index order 0..N-1."""
    by_index = {}
    for item in raw_interpretations:
        if isinstance(item, dict) and "note_index" in item:
            try:
                idx = int(item["note_index"])
                if 0 <= idx < num_notes and idx not in by_index:
                    by_index[idx] = item
            except (ValueError, TypeError):
                pass

    final_list: List[DirectiveInterpretationEntry] = []
    for i in range(num_notes):
        raw = by_index.get(i)
        if raw is None and i < len(raw_interpretations) and isinstance(raw_interpretations[i], dict):
            raw = raw_interpretations[i]
        if raw is None:
            raw = {"note_index": i, "directive_type": "no_op", "applies": False, "structured_adjustment": None, "explanation": "Fallback no_op."}

        sanitized = validate_and_repair_directive(raw, expected_index=i, battery_capacity=battery_capacity)
        final_list.append(sanitized)

    return final_list
