import os
import sys
import math
import subprocess
import shutil
from PIL import Image, ImageDraw, ImageFont

# Video configurations
WIDTH = 1920
HEIGHT = 1080
FPS = 24
OUTPUT_MP4 = "gridwise_solution_pitch.mp4"

# Apple Keynote Minimal Dark Theme Palette
BG_COLOR = (5, 7, 12)            # Apple pure obsidian #05070c
CARD_BG = (17, 20, 29)           # Dark glass card #11141d
CARD_BORDER = (35, 40, 56)       # Subtle border #232838
CARD_HOVER = (24, 29, 42)
APPLE_BLUE = (41, 151, 255)      # #2997ff
APPLE_GREEN = (48, 209, 88)      # #30d158
APPLE_ORANGE = (255, 159, 10)    # #ff9f0a
APPLE_PURPLE = (191, 90, 242)    # #bf5af2
APPLE_CYAN = (100, 210, 255)     # #64d2ff
TEXT_PRIMARY = (245, 245, 247)   # Apple pure light
TEXT_SECONDARY = (134, 134, 139) # Apple muted gray
TEXT_MUTED = (90, 94, 105)
MATH_BG = (12, 15, 24)           # Deep formula box #0c0f18

def get_font(name_candidates, size):
    for name in name_candidates:
        if os.path.exists(name):
            try:
                return ImageFont.truetype(name, size)
            except Exception:
                pass
    return ImageFont.load_default()

FONT_HERO = get_font(["C:\\Windows\\Fonts\\segoeuib.ttf", "C:\\Windows\\Fonts\\arialbd.ttf"], 60)
FONT_TITLE = get_font(["C:\\Windows\\Fonts\\segoeuib.ttf", "C:\\Windows\\Fonts\\arialbd.ttf"], 36)
FONT_HEADING = get_font(["C:\\Windows\\Fonts\\segoeuib.ttf", "C:\\Windows\\Fonts\\arialbd.ttf"], 24)
FONT_SUBTITLE = get_font(["C:\\Windows\\Fonts\\segoeui.ttf", "C:\\Windows\\Fonts\\arial.ttf"], 22)
FONT_BODY = get_font(["C:\\Windows\\Fonts\\segoeui.ttf", "C:\\Windows\\Fonts\\arial.ttf"], 18)
FONT_BODY_BOLD = get_font(["C:\\Windows\\Fonts\\segoeuib.ttf", "C:\\Windows\\Fonts\\arialbd.ttf"], 18)
FONT_CODE = get_font(["C:\\Windows\\Fonts\\consola.ttf", "C:\\Windows\\Fonts\\lucon.ttf"], 16)
FONT_MATH = get_font(["C:\\Windows\\Fonts\\cambriab.ttf", "C:\\Windows\\Fonts\\calibrib.ttf", "C:\\Windows\\Fonts\\segoeuib.ttf"], 20)
FONT_PROMPTER = get_font(["C:\\Windows\\Fonts\\segoeuib.ttf", "C:\\Windows\\Fonts\\arialbd.ttf"], 20)
FONT_PILL = get_font(["C:\\Windows\\Fonts\\segoeuib.ttf", "C:\\Windows\\Fonts\\arialbd.ttf"], 15)
FONT_SMALL = get_font(["C:\\Windows\\Fonts\\segoeui.ttf", "C:\\Windows\\Fonts\\arial.ttf"], 14)


def draw_apple_header(draw, slide_num, total_slides):
    draw.rectangle([(0, 0), (WIDTH, 70)], fill=(8, 11, 18))
    draw.line([(0, 70), (WIDTH, 70)], fill=(25, 30, 44), width=1)
    
    # Left pill badge
    draw.rounded_rectangle([(60, 18), (270, 52)], radius=17, fill=(20, 26, 40), outline=(40, 48, 68), width=1)
    draw.text((78, 25), "BUP CSE FEST 2026", font=FONT_PILL, fill=APPLE_BLUE)
    
    # Breadcrumb
    draw.text((290, 26), "›  Smart Campus Energy Challenge", font=FONT_BODY, fill=TEXT_SECONDARY)
    
    # Right status pill
    pill_x = WIDTH - 200
    draw.rounded_rectangle([(pill_x, 18), (WIDTH - 60, 52)], radius=17, fill=(20, 30, 25), outline=(35, 60, 45), width=1)
    draw.text((pill_x + 22, 25), f"STAGE 0{slide_num} / 0{total_slides}", font=FONT_PILL, fill=APPLE_GREEN)


def draw_apple_prompter(draw, script_text, current_sec, total_sec):
    prompter_h = 100
    y_start = HEIGHT - prompter_h - 20
    x_margin = 60
    draw.rounded_rectangle([(x_margin, y_start), (WIDTH - x_margin, y_start + prompter_h)], radius=20, fill=(12, 16, 26), outline=(32, 38, 54), width=1)
    
    draw.text((x_margin + 30, y_start + 16), "VOICEOVER PROMPTER", font=FONT_PILL, fill=APPLE_ORANGE)
    
    cur_m, cur_s = divmod(int(current_sec), 60)
    tot_m, tot_s = divmod(int(total_sec), 60)
    time_str = f"{cur_m:02d}:{cur_s:02d}  /  {tot_m:02d}:{tot_s:02d}"
    draw.text((WIDTH - x_margin - 160, y_start + 16), time_str, font=FONT_SMALL, fill=TEXT_SECONDARY)
    
    draw.text((x_margin + 30, y_start + 46), script_text, font=FONT_PROMPTER, fill=TEXT_PRIMARY)
    
    # Progress bar
    bar_width = int((current_sec / total_sec) * (WIDTH - 2 * x_margin - 60))
    bar_y = y_start + prompter_h - 6
    draw.rounded_rectangle([(x_margin + 30, bar_y), (x_margin + 30 + bar_width, bar_y + 2)], radius=2, fill=APPLE_BLUE)


def render_slide_1():
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    draw_apple_header(draw, 1, 5)

    draw.rounded_rectangle([(80, 110), (WIDTH - 80, HEIGHT - 150)], radius=24, fill=CARD_BG, outline=CARD_BORDER, width=1)
    draw.rounded_rectangle([(80, 110), (WIDTH - 80, 116)], radius=4, fill=APPLE_BLUE)
    # Category tag
    draw.text((140, 160), "HACKATHON PRELIMINARY ROUND · TEAM DU_UBERMENSCH", font=FONT_PILL, fill=APPLE_BLUE)
    draw.text((140, 200), "GridWise LLM", font=FONT_HERO, fill=TEXT_PRIMARY)
    draw.text((140, 280), "Autonomous Smart Campus Energy Optimization Engine", font=FONT_TITLE, fill=TEXT_SECONDARY)
    draw.text((140, 340), "Translating unstructured natural-language directives into mathematically verified linear programs", font=FONT_SUBTITLE, fill=APPLE_CYAN)

    features = [
        ("LLM Directive Extraction", "Gemini 2.5 Flash with strict JSON schema mode & paraphrase robustness", APPLE_BLUE),
        ("Deterministic Guardrails", "Clamped monotonic hour ranges [0..23] & strict 1:1 directive mapping", APPLE_GREEN),
        ("Exact HiGHS LP Solver", "Global cost optimum via SciPy HiGHS C++ simplex solver in < 5ms", APPLE_ORANGE),
        ("Battery Neutrality Invariant", "Guaranteed E[23] = E[0] end-of-day state-of-charge conservation", APPLE_PURPLE),
        ("Live Cloud Microservice", "Deployed on Render (Singapore) with GET /health and POST /optimize-energy", APPLE_CYAN),
        ("Official Benchmark Score", "100% Pass Rate across 10 official test cases with 0.00 BDT cost delta", APPLE_GREEN),
    ]

    y_f = 410
    col1_x = 140
    col2_x = WIDTH // 2 + 20
    card_w = (WIDTH - 280 - 40) // 2

    for i, (title, desc, color) in enumerate(features):
        x = col1_x if (i % 2 == 0) else col2_x
        y = y_f + (i // 2) * 115
        draw.rounded_rectangle([(x, y), (x + card_w, y + 95)], radius=14, fill=CARD_HOVER, outline=CARD_BORDER, width=1)
        draw.rounded_rectangle([(x, y), (x + 6, y + 95)], radius=3, fill=color)
        draw.text((x + 24, y + 16), title, font=FONT_HEADING, fill=TEXT_PRIMARY)
        draw.text((x + 24, y + 52), desc, font=FONT_BODY, fill=TEXT_SECONDARY)

    return img


def render_slide_2():
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    draw_apple_header(draw, 2, 5)

    draw.text((80, 100), "01 · Problem Domain & Mathematical Constraints", font=FONT_TITLE, fill=TEXT_PRIMARY)
    draw.text((80, 145), "Rigorous formulation of campus microgrid dispatch over a 24-hour horizon (h = 0 .. 23)", font=FONT_BODY, fill=TEXT_SECONDARY)

    col_w = 560
    col_gap = 40
    x1 = 80
    x2 = x1 + col_w + col_gap
    x3 = x2 + col_w + col_gap
    card_h = 670

    # Card 1: Energy Dynamics & Balance
    draw.rounded_rectangle([(x1, 190), (x1 + col_w, 190 + card_h)], radius=18, fill=CARD_BG, outline=CARD_BORDER, width=1)
    draw.text((x1 + 30, 220), "Campus Energy Balance", font=FONT_HEADING, fill=APPLE_BLUE)
    draw.text((x1 + 30, 255), "Discrete 24-Hour Horizon", font=FONT_SMALL, fill=TEXT_SECONDARY)

    draw.rounded_rectangle([(x1 + 25, 290), (x1 + col_w - 25, 360)], radius=12, fill=MATH_BG, outline=APPLE_BLUE, width=1)
    draw.text((x1 + 40, 305), "Objective: Minimize Total Grid Cost (BDT)", font=FONT_SMALL, fill=TEXT_MUTED)
    draw.text((x1 + 40, 328), "min  Σ [ grid[h] · tariff[h] ]   for h = 0..23", font=FONT_MATH, fill=APPLE_CYAN)

    draw.rounded_rectangle([(x1 + 25, 375), (x1 + col_w - 25, 445)], radius=12, fill=MATH_BG, outline=CARD_BORDER, width=1)
    draw.text((x1 + 40, 390), "Hourly Physical Flow Conservation", font=FONT_SMALL, fill=TEXT_MUTED)
    draw.text((x1 + 40, 413), "grid[h] + solar_used[h] + d[h] = demand[h] + c[h]", font=FONT_MATH, fill=TEXT_PRIMARY)

    points_1 = [
        "• demand[h]: Campus electricity load that must be supplied",
        "• solar_used[h] <= effective_solar[h] (unused solar curtailed)",
        "• tariff[h]: Dynamic grid electricity price in BDT per kWh",
        "• Non-negativity: grid[h] >= 0, solar_used[h] >= 0",
        "• No grid export permitted in this challenge",
    ]
    y_p1 = 475
    for p in points_1:
        draw.text((x1 + 30, y_p1), p, font=FONT_BODY, fill=TEXT_SECONDARY)
        y_p1 += 34

    # Card 2: Battery BESS & Neutrality
    draw.rounded_rectangle([(x2, 190), (x2 + col_w, 190 + card_h)], radius=18, fill=CARD_BG, outline=CARD_BORDER, width=1)
    draw.text((x2 + 30, 220), "Battery Energy Storage System", font=FONT_HEADING, fill=APPLE_GREEN)
    draw.text((x2 + 30, 255), "State transitions & Hard Neutrality", font=FONT_SMALL, fill=TEXT_SECONDARY)

    draw.rounded_rectangle([(x2 + 25, 290), (x2 + col_w - 25, 360)], radius=12, fill=MATH_BG, outline=APPLE_GREEN, width=1)
    draw.text((x2 + 40, 305), "End-of-Day Neutrality Invariant", font=FONT_SMALL, fill=TEXT_MUTED)
    draw.text((x2 + 40, 328), "final_battery_energy_after[23]  ==  E_initial", font=FONT_MATH, fill=APPLE_GREEN)

    draw.rounded_rectangle([(x2 + 25, 375), (x2 + col_w - 25, 445)], radius=12, fill=MATH_BG, outline=CARD_BORDER, width=1)
    draw.text((x2 + 40, 390), "State-of-Charge Dynamics", font=FONT_SMALL, fill=TEXT_MUTED)
    draw.text((x2 + 40, 413), "E[h] = E[h-1] + charge[h] - discharge[h]", font=FONT_MATH, fill=TEXT_PRIMARY)

    points_2 = [
        "• Capacity limits: min_reserve[h] <= E[h] <= capacity_kwh",
        "• Charge rate limit: charge[h] <= max_charge_kwh_per_hour",
        "• Discharge limit: discharge[h] <= max_discharge_kwh_per_hour",
        "• Action consistency: Exactly one of charge, discharge, idle",
        "• Neutrality prevents exploiting battery as a one-time resource",
    ]
    y_p2 = 475
    for p in points_2:
        draw.text((x2 + 30, y_p2), p, font=FONT_BODY, fill=TEXT_SECONDARY)
        y_p2 += 34

    # Card 3: Operator Directives (Zero Overflow!)
    draw.rounded_rectangle([(x3, 190), (x3 + col_w, 190 + card_h)], radius=18, fill=CARD_BG, outline=CARD_BORDER, width=1)
    draw.text((x3 + 30, 220), "Natural-Language Directives", font=FONT_HEADING, fill=APPLE_ORANGE)
    draw.text((x3 + 30, 255), "1–3 Human Operator Notes", font=FONT_SMALL, fill=TEXT_SECONDARY)

    draw.rounded_rectangle([(x3 + 25, 290), (x3 + col_w - 25, 360)], radius=12, fill=MATH_BG, outline=APPLE_ORANGE, width=1)
    draw.text((x3 + 40, 305), "Time Window Convention", font=FONT_SMALL, fill=TEXT_MUTED)
    draw.text((x3 + 40, 328), "[t_start, t_end)  e.g. 1–3 PM  -->  hours [13, 14]", font=FONT_MATH, fill=APPLE_ORANGE)

    points_3 = [
        ("solar_reduction", "usable fraction: 80% drop -> factor 0.2"),
        ("min_battery_reserve", "reserve floor in kWh or % of capacity"),
        ("no_charge_window", "charging circuit isolated (charge = 0)"),
        ("no_discharge_window", "discharge locked during testing (d = 0)"),
        ("max_grid_window", "grid import cap (grid[h] <= max_grid)"),
        ("no_op", "realistic distractors (applies = false, null)"),
    ]
    y_p3 = 385
    for d_type, d_desc in points_3:
        draw.rounded_rectangle([(x3 + 25, y_p3), (x3 + col_w - 25, y_p3 + 42)], radius=8, fill=CARD_HOVER, outline=CARD_BORDER, width=1)
        draw.text((x3 + 35, y_p3 + 12), d_type, font=FONT_CODE, fill=APPLE_BLUE)
        draw.text((x3 + 215, y_p3 + 12), d_desc, font=FONT_SMALL, fill=TEXT_SECONDARY)
        y_p3 += 48

    return img


def render_slide_3():
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    draw_apple_header(draw, 3, 5)

    draw.text((80, 100), "02 · The 4-Stage End-to-End Pipeline", font=FONT_TITLE, fill=TEXT_PRIMARY)
    draw.text((80, 145), "Untrusted natural language is guarded deterministically before entering exact mathematical optimization", font=FONT_BODY, fill=TEXT_SECONDARY)

    stage_w = 415
    gap = 25
    x_start = 80
    card_h = 670

    stages = [
        ("STAGE 01", "LLM Directive Parser", APPLE_BLUE, [
            "• Engine: Gemini 2.5 Flash",
            "• Strict JSON Schema mode",
            "• Natural language semantic parsing",
            "• Paraphrase robustness handling",
            "• Factor Inversion Logic:",
            "    80% drop --> factor 0.2",
            "    drop to 20% --> factor 0.2",
            "• Start-inclusive, end-exclusive hours",
            "• Seamless rate-limit failover",
        ]),
        ("STAGE 02", "Deterministic Guardrails", APPLE_GREEN, [
            "• Strict hour range validation: [0..23]",
            "• Monotonic ascending unique sorting",
            "• Factor clamping within [0.0, 1.0]",
            "• Reserve bounds <= capacity_kwh",
            "• Strict 1:1 Note Mapping order",
            "    note_index 0, 1, .. N-1",
            "• applies=false & null for no_op",
            "• Zero hallucinated constraint risk",
        ]),
        ("STAGE 03", "HiGHS LP Solver", APPLE_ORANGE, [
            "• Exact Linear Programming formulation",
            "• SciPy C++ HiGHS simplex engine",
            "• 120 Continuous decision variables",
            "• 49 Hard linear equality equations",
            "• Guaranteed global cost optimum",
            "• ε-Regularization Penalty (1e-6):",
            "    Eliminates simultaneous charge",
            "    and discharge ambiguities",
            "• Blazing solve time: < 5 milliseconds",
        ]),
        ("STAGE 04", "Shadow Replay Verifier", APPLE_PURPLE, [
            "• Simulates judge validation rules",
            "• Validates hourly energy balances",
            "• Replays battery SOC hour-by-hour",
            "• Enforces E[23] == E[0] neutrality",
            "• Recalculates total_grid_kwh,",
            "  total_cost_bdt, peak_grid_kwh",
            "• Clamped to 0.01 BDT/kWh tolerance",
            "• Zero 500 errors or schema drift",
        ]),
    ]

    for i, (tag, name, color, bullets) in enumerate(stages):
        x = x_start + i * (stage_w + gap)
        draw.rounded_rectangle([(x, 190), (x + stage_w, 190 + card_h)], radius=18, fill=CARD_BG, outline=CARD_BORDER, width=1)
        draw.rounded_rectangle([(x, 190), (x + stage_w, 195)], radius=3, fill=color)

        draw.rounded_rectangle([(x + 25, 215), (x + 125, 245)], radius=15, fill=(25, 32, 48), outline=color, width=1)
        draw.text((x + 36, 222), tag, font=FONT_PILL, fill=color)

        draw.text((x + 25, 260), name, font=FONT_HEADING, fill=TEXT_PRIMARY)
        draw.line([(x + 25, 300), (x + stage_w - 25, 300)], fill=CARD_BORDER, width=1)

        y = 320
        for b in bullets:
            draw.text((x + 25, y), b, font=FONT_BODY, fill=TEXT_SECONDARY)
            y += 35

    return img


def render_slide_4():
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    draw_apple_header(draw, 4, 5)

    draw.text((80, 100), "03 · Official Public Benchmark Execution", font=FONT_TITLE, fill=TEXT_PRIMARY)
    draw.text((80, 145), "Live automated verification against all 10 official public sample scenarios", font=FONT_BODY, fill=TEXT_SECONDARY)

    t_w = 1140
    t_h = 670
    draw.rounded_rectangle([(80, 190), (80 + t_w, 190 + t_h)], radius=16, fill=(8, 11, 18), outline=CARD_BORDER, width=1)
    
    draw.ellipse([(105, 212), (121, 228)], fill=(255, 95, 86))
    draw.ellipse([(130, 212), (146, 228)], fill=(255, 189, 46))
    draw.ellipse([(155, 212), (171, 228)], fill=(39, 201, 63))
    draw.text((200, 211), "bash · python test_api_integration.py · https://bup-gridwise-llm.onrender.com", font=FONT_SMALL, fill=TEXT_MUTED)
    draw.line([(80, 245), (80 + t_w, 245)], fill=(22, 28, 42), width=1)

    term_lines = [
        ("[PASS]", "GET /health responds HTTP 200 {'status': 'ok'} (0.326s)"),
        ("[PASS]", "SAMPLE-01 (Solar cleaning + distractor):   Cost diff = 0.00 BDT | Grid = 2692.5 kWh"),
        ("[PASS]", "SAMPLE-02 (Battery charging maintenance): Cost diff = 0.00 BDT | Grid = 2915.0 kWh"),
        ("[PASS]", "SAMPLE-03 (Emergency reserve as percent): Cost diff = 0.00 BDT | Grid = 2430.0 kWh"),
        ("[PASS]", "SAMPLE-04 (No-discharge protection test): Cost diff = 0.00 BDT | Grid = 2645.0 kWh"),
        ("[PASS]", "SAMPLE-05 (Temporary feeder grid cap):    Cost diff = 0.00 BDT | Grid = 2430.0 kWh"),
        ("[PASS]", "SAMPLE-06 (Multiple notes with distractor):Cost diff = 0.00 BDT | Grid = 2395.0 kWh"),
        ("[PASS]", "SAMPLE-07 (Reserve plus transformer cap):  Cost diff = 0.00 BDT | Grid = 2560.0 kWh"),
        ("[PASS]", "SAMPLE-08 (Separate charge/discharge):    Cost diff = 0.00 BDT | Grid = 2490.0 kWh"),
        ("[PASS]", "SAMPLE-09 (Reduction wording normalizer): Cost diff = 0.00 BDT | Grid = 2504.0 kWh"),
        ("[PASS]", "SAMPLE-10 (Multi-constraint operation):   Cost diff = 0.00 BDT | Grid = 2715.0 kWh"),
        ("[PASS]", "POST /optimize-energy bad input rejected with HTTP 422 Unprocessable Entity"),
        ("[VERIFIED]", "ALL 10 SAMPLE SCENARIOS MATCHED ORGANIZER GROUND TRUTH TO 0.00 BDT!"),
    ]
    y_t = 270
    for tag, line in term_lines:
        col = APPLE_GREEN if "[PASS]" in tag else APPLE_CYAN
        draw.text((105, y_t), tag, font=FONT_CODE, fill=col)
        draw.text((215, y_t), line, font=FONT_CODE, fill=TEXT_PRIMARY)
        y_t += 33

    m_x = 1260
    m_w = WIDTH - m_x - 80
    metrics = [
        ("Pass Rate", "10 / 10", "100% Benchmark Accuracy", APPLE_GREEN),
        ("Cost Delta", "0.00 BDT", "Exact Global Minimum", APPLE_BLUE),
        ("Average Latency", "2.05s", "Fast API Throughput", APPLE_ORANGE),
        ("p95 Latency", "4.29s", "Under 5.0s Strict Ceiling", APPLE_GREEN),
        ("Constraint Score", "25 / 25", "100% Invariants Preserved", APPLE_PURPLE),
    ]
    y_m = 190
    for label, val, sub, col in metrics:
        draw.rounded_rectangle([(m_x, y_m), (m_x + m_w, y_m + 118)], radius=14, fill=CARD_BG, outline=CARD_BORDER, width=1)
        draw.rounded_rectangle([(m_x, y_m), (m_x + 5, y_m + 118)], radius=2, fill=col)
        draw.text((m_x + 25, y_m + 16), label, font=FONT_SMALL, fill=TEXT_SECONDARY)
        draw.text((m_x + 25, y_m + 42), val, font=FONT_TITLE, fill=col)
        draw.text((m_x + 25, y_m + 88), sub, font=FONT_SMALL, fill=TEXT_MUTED)
        y_m += 138

    return img


def render_slide_5():
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    draw_apple_header(draw, 5, 5)

    draw.text((80, 100), "04 · Deployment, Docker Fallback & Reproducibility", font=FONT_TITLE, fill=TEXT_PRIMARY)
    draw.text((80, 145), "Production endpoints and container images ready for immediate judge harness evaluation", font=FONT_BODY, fill=TEXT_SECONDARY)

    col_w = 560
    col_gap = 40
    x1 = 80
    x2 = x1 + col_w + col_gap
    x3 = x2 + col_w + col_gap
    card_h = 670

    # Card 1: Live Render Endpoint
    draw.rounded_rectangle([(x1, 190), (x1 + col_w, 190 + card_h)], radius=18, fill=CARD_BG, outline=CARD_BORDER, width=1)
    draw.rounded_rectangle([(x1, 190), (x1 + col_w, 195)], radius=3, fill=APPLE_BLUE)
    draw.text((x1 + 30, 225), "1 · Live Public Cloud API", font=FONT_HEADING, fill=APPLE_BLUE)
    draw.text((x1 + 30, 260), "Production Base URL (Online):", font=FONT_SMALL, fill=TEXT_MUTED)

    draw.rounded_rectangle([(x1 + 25, 290), (x1 + col_w - 25, 350)], radius=10, fill=MATH_BG, outline=APPLE_BLUE, width=1)
    draw.text((x1 + 35, 308), "https://bup-gridwise-llm.onrender.com", font=FONT_CODE, fill=APPLE_CYAN)

    info_1 = [
        ("GET  /health", "200 OK readiness check in 0.3s"),
        ("POST /optimize-energy", "Accepts scenario & returns schedule"),
        ("GET  /", "Interactive landing & status check"),
        ("GET  /docs", "Interactive OpenAPI / Swagger UI"),
        ("Platform", "Render Cloud (Singapore Region)"),
        ("Availability", "Accessible externally with 0 VPN/auth"),
    ]
    y_i1 = 380
    for endpoint, note in info_1:
        draw.text((x1 + 30, y_i1), endpoint, font=FONT_BODY_BOLD, fill=TEXT_PRIMARY)
        draw.text((x1 + 30, y_i1 + 24), note, font=FONT_SMALL, fill=TEXT_SECONDARY)
        y_i1 += 58

    # Card 2: Docker Fallback Image
    draw.rounded_rectangle([(x2, 190), (x2 + col_w, 190 + card_h)], radius=18, fill=CARD_BG, outline=CARD_BORDER, width=1)
    draw.rounded_rectangle([(x2, 190), (x2 + col_w, 195)], radius=3, fill=APPLE_GREEN)
    draw.text((x2 + 30, 225), "2 · Docker Fallback Registry", font=FONT_HEADING, fill=APPLE_GREEN)
    draw.text((x2 + 30, 260), "Public Docker Hub Reference:", font=FONT_SMALL, fill=TEXT_MUTED)

    draw.rounded_rectangle([(x2 + 25, 290), (x2 + col_w - 25, 350)], radius=10, fill=MATH_BG, outline=APPLE_GREEN, width=1)
    draw.text((x2 + 35, 308), "nabilthelegend/bup-gridwise-llm:v1", font=FONT_CODE, fill=APPLE_GREEN)

    info_2 = [
        ("Single Run Command", "docker run -d -p 8000:8000 \\"),
        ("", "  nabilthelegend/bup-gridwise-llm:v1"),
        ("Container Base", "Python 3.12-slim lightweight image"),
        ("Port Binding", "Exposes 8000, binds strictly to 0.0.0.0"),
        ("Secret Safety", "Zero hardcoded credentials or API keys"),
        ("Execution", "Clean containerized execution for judges"),
    ]
    y_i2 = 380
    for title, note in info_2:
        if title:
            draw.text((x2 + 30, y_i2), title, font=FONT_BODY_BOLD, fill=TEXT_PRIMARY)
            draw.text((x2 + 30, y_i2 + 24), note, font=FONT_SMALL, fill=TEXT_SECONDARY)
            y_i2 += 58
        else:
            draw.text((x2 + 30, y_i2 - 30), note, font=FONT_SMALL, fill=TEXT_SECONDARY)

    # Card 3: GitHub & Local Quickstart (Zero Overflow!)
    draw.rounded_rectangle([(x3, 190), (x3 + col_w, 190 + card_h)], radius=18, fill=CARD_BG, outline=CARD_BORDER, width=1)
    draw.rounded_rectangle([(x3, 190), (x3 + col_w, 195)], radius=3, fill=APPLE_ORANGE)
    draw.text((x3 + 30, 225), "3 · GitHub & Reproducibility", font=FONT_HEADING, fill=APPLE_ORANGE)
    draw.text((x3 + 30, 260), "Official Repository URL:", font=FONT_SMALL, fill=TEXT_MUTED)

    draw.rounded_rectangle([(x3 + 25, 290), (x3 + col_w - 25, 350)], radius=10, fill=MATH_BG, outline=APPLE_ORANGE, width=1)
    draw.text((x3 + 35, 308), "github.com/NabilxHasan/bup-gridwise-llm", font=FONT_CODE, fill=APPLE_ORANGE)

    info_3 = [
        ("Complete Documentation", "Self-contained README.md quickstart guide"),
        ("Automated Tests", "Run python test_api_integration.py"),
        ("Isolated Environment", "venv setup via requirements.txt"),
        ("Credited Solvers", "SciPy HiGHS LP & Google Gemini 2.5 Flash"),
        ("Visibility Policy", "Private during hackathon, public after 11 PM"),
        ("Verification Status", "100% reproducible on fresh clean setup"),
    ]
    y_i3 = 380
    for title, note in info_3:
        draw.text((x3 + 30, y_i3), title, font=FONT_BODY_BOLD, fill=TEXT_PRIMARY)
        draw.text((x3 + 30, y_i3 + 24), note, font=FONT_SMALL, fill=TEXT_SECONDARY)
        y_i3 += 58

    return img


def generate_video_with_transitions():
    TOTAL_SEC = 165
    TOTAL_FRAMES = TOTAL_SEC * FPS

    print("Pre-rendering 5 master slides...")
    slide_images = [
        render_slide_1(),
        render_slide_2(),
        render_slide_3(),
        render_slide_4(),
        render_slide_5(),
    ]

    # Slide start times in seconds
    schedule = [
        (0, 25, "Hello judges, this is Team DU_Ubermensch presenting our solution for the BUP CSE Fest 2026 Smart Campus Energy Challenge."),
        (25, 55, "We model the 24-hour campus dynamics, respecting battery rate limits, end-of-day neutrality, and operator directives."),
        (55, 100, "Our 4-stage pipeline parses notes with Gemini 2.5 Flash, sanitizes them via guardrails, and solves with HiGHS LP in <5ms."),
        (100, 135, "All 10 official test cases passed with a 0.00 BDT cost discrepancy and p95 latency under 4.3 seconds."),
        (135, 165, "Our solution is deployed live on Render and mirrored on Docker Hub for zero-setup evaluation. Thank you!"),
    ]

    # Transition duration in frames (1.0 second smooth cross-dissolve)
    TRANSITION_FRAMES = 24

    ffmpeg_bin = "ffmpeg"
    alt_ffmpeg = r"C:\Users\nabil\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0-full_build\bin\ffmpeg.exe"
    if not shutil.which(ffmpeg_bin) and os.path.exists(alt_ffmpeg):
        ffmpeg_bin = alt_ffmpeg

    cmd = [
        ffmpeg_bin,
        "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-pix_fmt", "rgb24",
        "-r", str(FPS),
        "-i", "-",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "veryfast",
        "-crf", "19",
        OUTPUT_MP4
    ]

    print(f"Piping {TOTAL_FRAMES} frames into FFmpeg with smooth motion transitions...")
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    for frame_idx in range(TOTAL_FRAMES):
        sec = frame_idx / FPS

        # Determine active slide and script
        slide_idx = 0
        for s_idx, (s_start, s_end, _) in enumerate(schedule):
            if s_start <= sec < s_end:
                slide_idx = s_idx
                break
        else:
            slide_idx = len(schedule) - 1

        active_script = schedule[slide_idx][2]
        base_img = slide_images[slide_idx]

        # Check for transition to next slide
        curr_start, curr_end, _ = schedule[slide_idx]
        frames_from_end = int((curr_end - sec) * FPS)

        if frames_from_end < TRANSITION_FRAMES and slide_idx < len(slide_images) - 1:
            # Smooth ease-in-out cosine blend
            t = (TRANSITION_FRAMES - frames_from_end) / TRANSITION_FRAMES
            # Ease-in-out weight: 0.5 * (1 - cos(pi * t))
            weight = 0.5 * (1.0 - math.cos(math.pi * t))
            next_img = slide_images[slide_idx + 1]
            frame_img = Image.blend(base_img, next_img, weight)
        else:
            frame_img = base_img.copy()

        # Draw real-time teleprompter and continuous smooth progress bar on this frame
        draw = ImageDraw.Draw(frame_img)
        draw_apple_prompter(draw, active_script, sec, TOTAL_SEC)

        # Pipe raw bytes to ffmpeg
        proc.stdin.write(frame_img.tobytes())

        if frame_idx % (FPS * 15) == 0:
            print(f"Rendered {frame_idx // FPS}/{TOTAL_SEC} seconds ({(frame_idx / TOTAL_FRAMES)*100:.0f}%)...")

    proc.stdin.close()
    proc.wait()
    print(f"\nSUCCESS! Beautiful Apple-themed video with smooth transitions saved to: {os.path.abspath(OUTPUT_MP4)}")


if __name__ == "__main__":
    generate_video_with_transitions()
