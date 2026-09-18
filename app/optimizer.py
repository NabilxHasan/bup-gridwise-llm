from typing import List, Dict, Any, Tuple
import numpy as np
from scipy.optimize import linprog

from app.models import HourInput, BatteryInput, DirectiveInterpretationEntry, HourlyPlanEntry


def solve_energy_schedule(
    hours: List[HourInput],
    battery: BatteryInput,
    directives: List[DirectiveInterpretationEntry],
) -> Tuple[List[HourlyPlanEntry], float, float, float]:
    """
    Solves the 24-hour campus energy dispatch problem using Linear Programming (HiGHS).
    Guarantees mathematically optimal grid cost while satisfying all physical and directive constraints.
    """
    N = 24
    hours = sorted(hours, key=lambda h: h.hour)
    demand = np.array([h.demand_kwh for h in hours], dtype=float)
    solar = np.array([h.solar_kwh for h in hours], dtype=float)
    tariff = np.array([h.tariff_bdt_per_kwh for h in hours], dtype=float)

    # 1. Process Directives
    effective_solar = solar.copy()
    min_reserve = np.full(N, battery.minimum_energy_kwh, dtype=float)
    allow_charge = np.ones(N, dtype=bool)
    allow_discharge = np.ones(N, dtype=bool)
    max_grid = np.full(N, np.inf, dtype=float)

    for d in directives:
        if not d.applies or not d.structured_adjustment:
            continue
        adj = d.structured_adjustment
        affected_hours = adj.get("hours", [])

        if d.directive_type == "solar_reduction":
            factor = float(adj.get("factor", 1.0))
            for h in affected_hours:
                if 0 <= h < N:
                    effective_solar[h] = min(effective_solar[h], solar[h] * factor)

        elif d.directive_type == "minimum_battery_reserve":
            req_min = float(adj.get("minimum_energy_kwh", 0.0))
            for h in affected_hours:
                if 0 <= h < N:
                    min_reserve[h] = max(min_reserve[h], req_min)

        elif d.directive_type == "no_charge_window":
            for h in affected_hours:
                if 0 <= h < N:
                    allow_charge[h] = False

        elif d.directive_type == "no_discharge_window":
            for h in affected_hours:
                if 0 <= h < N:
                    allow_discharge[h] = False

        elif d.directive_type == "max_grid_window":
            cap = float(adj.get("max_grid_kwh", np.inf))
            for h in affected_hours:
                if 0 <= h < N:
                    max_grid[h] = min(max_grid[h], cap)

    # 2. Decision Variables: 5 * 24 = 120 variables
    # x = [g_0..g_23, s_0..s_23, c_0..c_23, d_0..d_23, E_0..E_23]
    IDX_G = 0
    IDX_S = N
    IDX_C = 2 * N
    IDX_D = 3 * N
    IDX_E = 4 * N
    TOTAL_VARS = 5 * N

    # Objective: min sum(g_h * tariff_h + 1e-6 * (c_h + d_h))
    # Epsilon penalty prevents simultaneous charging and discharging when tariffs are tied
    c_obj = np.zeros(TOTAL_VARS)
    for h in range(N):
        c_obj[IDX_G + h] = tariff[h]
        c_obj[IDX_C + h] = 1e-6
        c_obj[IDX_D + h] = 1e-6

    # Equality Constraints (A_eq @ x = b_eq)
    # Equations:
    # 1. Energy balance for each h: g_h + s_h - c_h + d_h = demand[h]  (24 equations)
    # 2. Battery state transitions:
    #    h = 0: E_0 - c_0 + d_0 = initial_energy_kwh
    #    h > 0: E_h - E_{h-1} - c_h + d_h = 0  (24 equations)
    # 3. End-of-day battery neutrality: E_23 = initial_energy_kwh (1 equation)
    num_eq = N + N + 1
    A_eq = np.zeros((num_eq, TOTAL_VARS))
    b_eq = np.zeros(num_eq)

    # Energy balance
    for h in range(N):
        A_eq[h, IDX_G + h] = 1.0
        A_eq[h, IDX_S + h] = 1.0
        A_eq[h, IDX_C + h] = -1.0
        A_eq[h, IDX_D + h] = 1.0
        b_eq[h] = demand[h]

    # Battery transitions
    row = N
    # h = 0
    A_eq[row, IDX_E + 0] = 1.0
    A_eq[row, IDX_C + 0] = -1.0
    A_eq[row, IDX_D + 0] = 1.0
    b_eq[row] = battery.initial_energy_kwh
    row += 1

    for h in range(1, N):
        A_eq[row, IDX_E + h] = 1.0
        A_eq[row, IDX_E + h - 1] = -1.0
        A_eq[row, IDX_C + h] = -1.0
        A_eq[row, IDX_D + h] = 1.0
        b_eq[row] = 0.0
        row += 1

    # Neutrality: E_23 = initial_energy_kwh
    A_eq[row, IDX_E + 23] = 1.0
    b_eq[row] = battery.initial_energy_kwh

    # Variable Bounds
    bounds = []
    # g_h
    for h in range(N):
        ub = None if np.isinf(max_grid[h]) else max_grid[h]
        bounds.append((0.0, ub))
    # s_h
    for h in range(N):
        bounds.append((0.0, max(0.0, effective_solar[h])))
    # c_h
    for h in range(N):
        ub = battery.max_charge_kwh_per_hour if allow_charge[h] else 0.0
        bounds.append((0.0, ub))
    # d_h
    for h in range(N):
        ub = battery.max_discharge_kwh_per_hour if allow_discharge[h] else 0.0
        bounds.append((0.0, ub))
    # E_h
    for h in range(N):
        lb = min_reserve[h]
        ub = battery.capacity_kwh
        bounds.append((lb, ub))

    # Solve using HiGHS
    res = linprog(c_obj, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method="highs")
    if not res.success:
        raise ValueError(f"Linear programming optimization failed: {res.message}")

    x = res.x
    hourly_plan: List[HourlyPlanEntry] = []
    current_energy = battery.initial_energy_kwh

    for h in range(N):
        raw_g = max(0.0, x[IDX_G + h])
        raw_s = max(0.0, min(effective_solar[h], x[IDX_S + h]))
        raw_c = max(0.0, x[IDX_C + h])
        raw_d = max(0.0, x[IDX_D + h])

        # Net simultaneous charge/discharge
        net = raw_c - raw_d
        if net > 1e-4:
            action = "charge"
            bat_kwh = net
            current_energy += bat_kwh
        elif net < -1e-4:
            action = "discharge"
            bat_kwh = -net
            current_energy -= bat_kwh
        else:
            action = "idle"
            bat_kwh = 0.0

        # Exact energy balance: grid = demand + charge - solar_used - discharge
        if action == "charge":
            req_from_sources = demand[h] + bat_kwh
        elif action == "discharge":
            req_from_sources = max(0.0, demand[h] - bat_kwh)
        else:
            req_from_sources = demand[h]

        solar_used = min(req_from_sources, raw_s)
        grid_kwh = max(0.0, req_from_sources - solar_used)

        hourly_plan.append(
            HourlyPlanEntry(
                hour=h,
                grid_kwh=round(grid_kwh, 4),
                solar_used_kwh=round(solar_used, 4),
                battery_action=action,
                battery_kwh=round(bat_kwh, 4),
                battery_energy_after_kwh=round(current_energy, 4),
            )
        )

    # Calculate recalculated summary metrics
    total_grid_kwh = round(sum(entry.grid_kwh for entry in hourly_plan), 2)
    total_cost_bdt = round(sum(entry.grid_kwh * hours[entry.hour].tariff_bdt_per_kwh for entry in hourly_plan), 2)
    peak_grid_kwh = round(max(entry.grid_kwh for entry in hourly_plan), 2)

    return hourly_plan, total_grid_kwh, total_cost_bdt, peak_grid_kwh
