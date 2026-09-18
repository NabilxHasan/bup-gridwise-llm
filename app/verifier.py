from typing import List, Tuple
from app.models import HourInput, BatteryInput, DirectiveInterpretationEntry, HourlyPlanEntry


def verify_schedule(
    hours: List[HourInput],
    battery: BatteryInput,
    directives: List[DirectiveInterpretationEntry],
    hourly_plan: List[HourlyPlanEntry],
) -> Tuple[bool, str]:
    """
    Simulates the official judge harness checks independently.
    Returns (True, "OK") if all constraints pass, or (False, error_msg) if any check fails.
    """
    if len(hourly_plan) != 24:
        return False, f"Expected 24 entries in hourly_plan, got {len(hourly_plan)}"

    # Effective solar & reserve calculation
    effective_solar = [h.solar_kwh for h in hours]
    min_reserve = [battery.minimum_energy_kwh for _ in range(24)]
    no_charge = set()
    no_discharge = set()
    max_grid = [float('inf') for _ in range(24)]

    for d in directives:
        if not d.applies or not d.structured_adjustment:
            continue
        adj = d.structured_adjustment
        aff_h = adj.get("hours", [])
        if d.directive_type == "solar_reduction":
            factor = float(adj.get("factor", 1.0))
            for h in aff_h:
                if 0 <= h < 24:
                    effective_solar[h] = min(effective_solar[h], hours[h].solar_kwh * factor)
        elif d.directive_type == "minimum_battery_reserve":
            m = float(adj.get("minimum_energy_kwh", 0.0))
            for h in aff_h:
                if 0 <= h < 24:
                    min_reserve[h] = max(min_reserve[h], m)
        elif d.directive_type == "no_charge_window":
            no_charge.update(aff_h)
        elif d.directive_type == "no_discharge_window":
            no_discharge.update(aff_h)
        elif d.directive_type == "max_grid_window":
            cap = float(adj.get("max_grid_kwh", float('inf')))
            for h in aff_h:
                if 0 <= h < 24:
                    max_grid[h] = min(max_grid[h], cap)

    current_energy = battery.initial_energy_kwh
    TOL = 0.02  # slightly more than 0.01 tolerance for float safety

    for h, entry in enumerate(hourly_plan):
        if entry.hour != h:
            return False, f"Hour index mismatch at {h}: {entry.hour}"

        # Non-negative check
        if entry.grid_kwh < -TOL or entry.solar_used_kwh < -TOL or entry.battery_kwh < -TOL:
            return False, f"Negative value in hour {h}"

        # Solar limit
        if entry.solar_used_kwh > effective_solar[h] + TOL:
            return False, f"Solar used {entry.solar_used_kwh} exceeds effective solar {effective_solar[h]} in hour {h}"

        # Grid cap
        if entry.grid_kwh > max_grid[h] + TOL:
            return False, f"Grid kwh {entry.grid_kwh} exceeds cap {max_grid[h]} in hour {h}"

        # Battery actions
        charge_kwh = 0.0
        discharge_kwh = 0.0
        if entry.battery_action == "charge":
            if h in no_charge and entry.battery_kwh > TOL:
                return False, f"Charging not allowed in hour {h}"
            if entry.battery_kwh > battery.max_charge_kwh_per_hour + TOL:
                return False, f"Charge {entry.battery_kwh} exceeds max charge rate in hour {h}"
            charge_kwh = entry.battery_kwh
            current_energy += charge_kwh
        elif entry.battery_action == "discharge":
            if h in no_discharge and entry.battery_kwh > TOL:
                return False, f"Discharging not allowed in hour {h}"
            if entry.battery_kwh > battery.max_discharge_kwh_per_hour + TOL:
                return False, f"Discharge {entry.battery_kwh} exceeds max discharge rate in hour {h}"
            discharge_kwh = entry.battery_kwh
            current_energy -= discharge_kwh
        elif entry.battery_action == "idle":
            if abs(entry.battery_kwh) > TOL:
                return False, f"Battery kwh must be 0 when idle in hour {h}"
        else:
            return False, f"Invalid battery action {entry.battery_action} in hour {h}"

        # Battery bounds
        if current_energy < min_reserve[h] - TOL:
            return False, f"Battery energy {current_energy} below reserve {min_reserve[h]} in hour {h}"
        if current_energy > battery.capacity_kwh + TOL:
            return False, f"Battery energy {current_energy} above capacity {battery.capacity_kwh} in hour {h}"

        # Energy balance
        # grid + solar_used + discharge = demand + charge
        left = entry.grid_kwh + entry.solar_used_kwh + discharge_kwh
        right = hours[h].demand_kwh + charge_kwh
        if abs(left - right) > TOL:
            return False, f"Energy balance broken in hour {h}: left={left}, right={right}, diff={abs(left - right)}"

    # End of day neutrality
    if abs(current_energy - battery.initial_energy_kwh) > TOL:
        return False, f"End of day battery neutrality failed: {current_energy} vs initial {battery.initial_energy_kwh}"

    return True, "OK"
