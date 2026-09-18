import os
import sys
import subprocess
import shutil
from PIL import Image, ImageDraw, ImageFont

# Video configurations
WIDTH = 1920
HEIGHT = 1080
FPS = 24
OUTPUT_MP4 = "gridwise_solution_pitch.mp4"

# Color Palette (Dark high-tech theme)
BG_COLOR = (10, 15, 29)          # #0a0f1d
CARD_BG = (17, 24, 39)           # #111827
CARD_BORDER = (31, 41, 55)       # #1f2937
CYAN = (0, 210, 255)             # #00d2ff
EMERALD = (16, 185, 129)         # #10b981
AMBER = (245, 158, 11)           # #f59e0b
TEXT_WHITE = (243, 244, 246)     # #f3f4f6
TEXT_MUTED = (156, 163, 175)     # #9ca3af
TERMINAL_BG = (5, 8, 16)         # #050810

# Find system fonts
def get_font(name_candidates, size):
    for name in name_candidates:
        if os.path.exists(name):
            try:
                return ImageFont.truetype(name, size)
            except Exception:
                pass
    return ImageFont.load_default()

FONT_TITLE = get_font(["C:\\Windows\\Fonts\\segoeuib.ttf", "C:\\Windows\\Fonts\\arialbd.ttf"], 44)
FONT_SUBTITLE = get_font(["C:\\Windows\\Fonts\\segoeui.ttf", "C:\\Windows\\Fonts\\arial.ttf"], 26)
FONT_HEADING = get_font(["C:\\Windows\\Fonts\\segoeuib.ttf", "C:\\Windows\\Fonts\\arialbd.ttf"], 28)
FONT_BODY = get_font(["C:\\Windows\\Fonts\\segoeui.ttf", "C:\\Windows\\Fonts\\arial.ttf"], 20)
FONT_BODY_BOLD = get_font(["C:\\Windows\\Fonts\\segoeuib.ttf", "C:\\Windows\\Fonts\\arialbd.ttf"], 20)
FONT_CODE = get_font(["C:\\Windows\\Fonts\\consola.ttf", "C:\\Windows\\Fonts\\lucon.ttf"], 18)
FONT_PROMPTER = get_font(["C:\\Windows\\Fonts\\segoeuib.ttf", "C:\\Windows\\Fonts\\arialbd.ttf"], 22)
FONT_SMALL = get_font(["C:\\Windows\\Fonts\\segoeui.ttf", "C:\\Windows\\Fonts\\arial.ttf"], 16)


def draw_header(draw, title_text, slide_num, total_slides):
    # Top bar
    draw.rectangle([(0, 0), (WIDTH, 80)], fill=(13, 20, 36))
    draw.line([(0, 80), (WIDTH, 80)], fill=(30, 41, 59), width=2)
    
    # Event badge
    draw.text((60, 24), "BUP CSE FEST 2026", font=FONT_HEADING, fill=CYAN)
    draw.text((360, 28), "· Smart Campus Energy Optimization Challenge", font=FONT_SUBTITLE, fill=TEXT_MUTED)
    
    # Slide badge
    badge_text = f"Slide {slide_num}/{total_slides}"
    draw.text((WIDTH - 180, 26), badge_text, font=FONT_SUBTITLE, fill=EMERALD)


def draw_prompter(draw, script_text, current_sec, total_sec):
    # Bottom teleprompter container
    prompter_y = HEIGHT - 130
    draw.rectangle([(0, prompter_y), (WIDTH, HEIGHT)], fill=(13, 20, 36))
    draw.line([(0, prompter_y), (WIDTH, prompter_y)], fill=(30, 41, 59), width=2)
    
    # Label
    draw.text((60, prompter_y + 14), "VOICEOVER SCRIPT / TELEPROMPTER:", font=FONT_SMALL, fill=AMBER)
    
    # Time counter
    cur_m, cur_s = divmod(int(current_sec), 60)
    tot_m, tot_s = divmod(int(total_sec), 60)
    time_str = f"{cur_m:02d}:{cur_s:02d} / {tot_m:02d}:{tot_s:02d}"
    draw.text((WIDTH - 180, prompter_y + 14), time_str, font=FONT_SMALL, fill=TEXT_MUTED)
    
    # Script lines
    draw.text((60, prompter_y + 40), script_text, font=FONT_PROMPTER, fill=TEXT_WHITE)
    
    # Progress bar
    bar_width = int((current_sec / total_sec) * WIDTH)
    draw.line([(0, HEIGHT - 4), (bar_width, HEIGHT - 4)], fill=CYAN, width=4)


# Slide 1: Title & Overview
def render_slide_1(sec):
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    draw_header(draw, "Title", 1, 5)

    # Hero Card
    draw.rounded_rectangle([(140, 140), (WIDTH - 140, HEIGHT - 180)], radius=16, fill=CARD_BG, outline=CARD_BORDER, width=2)
    
    # Glow title
    draw.text((200, 200), "GridWise LLM", font=ImageFont.truetype("C:\\Windows\\Fonts\\segoeuib.ttf", 68), fill=CYAN)
    draw.text((200, 290), "Autonomous Smart Campus Energy Optimization Engine", font=FONT_TITLE, fill=TEXT_WHITE)
    draw.text((200, 360), "LLM-Assisted Operator Directive Interpretation · Deterministic Guardrails · HiGHS Linear Programming", font=FONT_SUBTITLE, fill=EMERALD)

    # Bullet badges
    badges = [
        ("Event", "BUP CSE Fest 2026 (In association with Poridhi.io)"),
        ("Track", "Preliminary Online Challenge (7:00 PM – 11:00 PM)"),
        ("Live API", "https://bup-gridwise-llm.onrender.com"),
        ("Docker Hub", "nabilthelegend/bup-gridwise-llm:v1"),
        ("GitHub", "https://github.com/NabilxHasan/bup-gridwise-llm"),
        ("Result", "100% Benchmark Pass Rate (0.00 BDT Optimal Cost Delta)"),
    ]
    
    y = 440
    for label, val in badges:
        draw.rectangle([(200, y), (340, y + 36)], fill=(30, 41, 59))
        draw.text((215, y + 6), label, font=FONT_BODY_BOLD, fill=CYAN)
        draw.text((360, y + 6), val, font=FONT_BODY, fill=TEXT_WHITE)
        y += 50

    script = "Hello judges, this is Team GridWise presenting our solution for the BUP CSE Fest 2026 Smart Campus Energy Challenge."
    draw_prompter(draw, script, sec, 165)
    return img


# Slide 2: Problem Understanding
def render_slide_2(sec):
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    draw_header(draw, "Problem Statement", 2, 5)

    # Section title
    draw.text((100, 110), "01. PROBLEM UNDERSTANDING & DOMAIN CONSTRAINTS", font=FONT_TITLE, fill=CYAN)

    # 3 Column Cards
    col_w = 540
    # Card 1: Energy Dynamics
    draw.rounded_rectangle([(100, 180), (100 + col_w, HEIGHT - 180)], radius=12, fill=CARD_BG, outline=CARD_BORDER, width=2)
    draw.text((130, 210), "Campus Energy System", font=FONT_HEADING, fill=AMBER)
    lines_c1 = [
        "• 24-Hour Planning Horizon (h = 0..23)",
        "• Hourly Campus Demand [kWh]",
        "• Variable Solar PV Generation [kWh]",
        "• Fluctuating Grid Tariffs [BDT/kWh]",
        "• Objective: Minimize total grid cost:",
        "    min Σ (grid[h] * tariff[h])",
        "• Strict energy balance per hour:",
        "    grid + solar + discharge = demand + charge"
    ]
    y = 270
    for l in lines_c1:
        draw.text((130, y), l, font=FONT_BODY, fill=TEXT_WHITE)
        y += 42

    # Card 2: Battery BESS
    draw.rounded_rectangle([(680, 180), (680 + col_w, HEIGHT - 180)], radius=12, fill=CARD_BG, outline=CARD_BORDER, width=2)
    draw.text((710, 210), "Battery Energy Storage (BESS)", font=FONT_HEADING, fill=EMERALD)
    lines_c2 = [
        "• Storage Capacity Limit: capacity_kwh",
        "• Baseline & Dynamic Reserve Bounds",
        "• Hourly Charge/Discharge Rate Limits",
        "• State-of-Charge Dynamics:",
        "    E[h] = E[h-1] + charge[h] - discharge[h]",
        "",
        "• MANDATORY NEUTRALITY CONSTRAINT:",
        "    E[23] = initial_energy_kwh",
        "  (Prevents free one-time energy depletion)"
    ]
    y = 270
    for l in lines_c2:
        draw.text((710, y), l, font=FONT_BODY, fill=TEXT_WHITE if "NEUTRALITY" not in l else CYAN)
        y += 42

    # Card 3: Operator Directives
    draw.rounded_rectangle([(1260, 180), (1260 + col_w, HEIGHT - 180)], radius=12, fill=CARD_BG, outline=CARD_BORDER, width=2)
    draw.text((1290, 210), "Unstructured Directives", font=FONT_HEADING, fill=CYAN)
    lines_c3 = [
        "• 1–3 Natural Language Operator Notes",
        "• 6 Canonical Supported Directives:",
        "    1. solar_reduction (usable fraction)",
        "    2. minimum_battery_reserve",
        "    3. no_charge_window",
        "    4. no_discharge_window",
        "    5. max_grid_window",
        "    6. no_op (realistic distractors)",
        "• Time Convention: Start-inclusive, end-exclusive (e.g. 1-3 PM -> [13, 14])"
    ]
    y = 270
    for l in lines_c3:
        draw.text((1290, y), l, font=FONT_BODY, fill=TEXT_WHITE)
        y += 42

    script = "We model the 24-hour campus dynamics, respecting battery rate limits, end-of-day neutrality, and operator directives."
    draw_prompter(draw, script, sec, 165)
    return img


# Slide 3: 4-Stage Architecture
def render_slide_3(sec):
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    draw_header(draw, "System Architecture", 3, 5)

    draw.text((100, 110), "02. END-TO-END 4-STAGE PIPELINE ARCHITECTURE", font=FONT_TITLE, fill=CYAN)

    # 4 Horizontal Pipeline Stages
    stage_w = 400
    gap = 25
    x_start = 100

    stages = [
        ("STAGE 1", "LLM Semantic Parser", [
            "• Model: Gemini 2.5 Flash",
            "• Strict JSON Schema Mode",
            "• Natural Language Extraction",
            "• Paraphrase Robustness",
            "• Factor Inversion Logic:",
            "  80% drop -> factor 0.2",
            "• Window Normalization",
            "• Zero-Downtime Fallback"
        ], CYAN),
        ("STAGE 2", "Deterministic Guardrails", [
            "• Range Check: [0..23]",
            "• Unique Ascending Sorting",
            "• Clamping: factor in [0, 1]",
            "• Reserve <= Capacity",
            "• Strict 1:1 Mapping Order",
            "  (note_index 0..N-1)",
            "• applies=False for no_op",
            "• Hallucination Isolation"
        ], EMERALD),
        ("STAGE 3", "HiGHS LP Optimizer", [
            "• Exact Linear Programming",
            "• SciPy HiGHS C++ Solver",
            "• 120 Decision Variables",
            "• 49 Hard Equality Constraints",
            "• Guaranteed Global Minimum",
            "• ε-Regularization Penalty:",
            "  Prevents simultaneous",
            "  charge & discharge",
            "• Solve Time: < 5 ms"
        ], AMBER),
        ("STAGE 4", "Shadow Replay Verifier", [
            "• Replays hourly_plan",
            "• Hourly Energy Balance Check",
            "• Battery Limits Hour-by-Hour",
            "• Neutrality Invariant Check",
            "• Recalculates Total Cost,",
            "  Peak Grid, Total Grid",
            "• 0.01 BDT Tolerance Check",
            "• Zero 500 Errors or Drift"
        ], (168, 85, 247)),
    ]

    for i, (tag, name, bullets, color) in enumerate(stages):
        x = x_start + i * (stage_w + gap)
        draw.rounded_rectangle([(x, 180), (x + stage_w, HEIGHT - 180)], radius=12, fill=CARD_BG, outline=color, width=2)
        
        # Tag badge
        draw.rectangle([(x + 20, 200), (x + 120, 230)], fill=color)
        draw.text((x + 28, 206), tag, font=FONT_SMALL, fill=(10, 15, 29))
        
        draw.text((x + 20, 245), name, font=FONT_HEADING, fill=TEXT_WHITE)
        draw.line([(x + 20, 285), (x + stage_w - 20, 285)], fill=CARD_BORDER, width=1)

        y = 305
        for b in bullets:
            draw.text((x + 20, y), b, font=FONT_BODY, fill=TEXT_WHITE)
            y += 38

    script = "Our 4-stage pipeline parses notes with Gemini 2.5 Flash, sanitizes them via guardrails, and solves with HiGHS LP in <5ms."
    draw_prompter(draw, script, sec, 165)
    return img


# Slide 4: Benchmark Demonstration
def render_slide_4(sec):
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    draw_header(draw, "Benchmark Execution", 4, 5)

    draw.text((100, 110), "03. BENCHMARK VERIFICATION ON OFFICIAL PUBLIC TEST CASES", font=FONT_TITLE, fill=CYAN)

    # Left: Terminal Output Box
    draw.rounded_rectangle([(100, 180), (1200, HEIGHT - 180)], radius=12, fill=TERMINAL_BG, outline=(55, 65, 81), width=2)
    # Terminal dots
    draw.ellipse([(120, 198), (134, 212)], fill=(239, 68, 68))
    draw.ellipse([(142, 198), (156, 212)], fill=(245, 158, 11))
    draw.ellipse([(164, 198), (178, 212)], fill=(16, 185, 129))
    draw.text((200, 196), "bash: python test_api_integration.py (All 10 Official Sample Scenarios)", font=FONT_SMALL, fill=TEXT_MUTED)

    term_lines = [
        ("[PASS]", "GET /health responds HTTP 200 {'status': 'ok'} (0.326s)"),
        ("[PASS]", "SAMPLE-01 (Solar cleaning + distractor):   Cost diff=0.00 BDT | Grid=2692.5 kWh"),
        ("[PASS]", "SAMPLE-02 (Battery charging maintenance): Cost diff=0.00 BDT | Grid=2915.0 kWh"),
        ("[PASS]", "SAMPLE-03 (Emergency reserve as percent): Cost diff=0.00 BDT | Grid=2430.0 kWh"),
        ("[PASS]", "SAMPLE-04 (No-discharge protection test): Cost diff=0.00 BDT | Grid=2645.0 kWh"),
        ("[PASS]", "SAMPLE-05 (Temporary feeder grid cap):    Cost diff=0.00 BDT | Grid=2430.0 kWh"),
        ("[PASS]", "SAMPLE-06 (Multiple notes with distractor):Cost diff=0.00 BDT | Grid=2395.0 kWh"),
        ("[PASS]", "SAMPLE-07 (Reserve plus transformer cap):  Cost diff=0.00 BDT | Grid=2560.0 kWh"),
        ("[PASS]", "SAMPLE-08 (Separate charge/discharge):    Cost diff=0.00 BDT | Grid=2490.0 kWh"),
        ("[PASS]", "SAMPLE-09 (Reduction wording normalizer): Cost diff=0.00 BDT | Grid=2504.0 kWh"),
        ("[PASS]", "SAMPLE-10 (Multi-constraint operation):   Cost diff=0.00 BDT | Grid=2715.0 kWh"),
        ("[OK]",   "ALL 10 PUBLIC CASES MATCHED ORGANIZER OPTIMAL REFERENCE WITH 100% ACCURACY!"),
    ]

    y = 235
    for status, text in term_lines:
        color = EMERALD if status == "[PASS]" else CYAN
        draw.text((120, y), status, font=FONT_CODE, fill=color)
        draw.text((200, y), text, font=FONT_CODE, fill=TEXT_WHITE)
        y += 34

    # Right: Metric Cards
    metrics = [
        ("Pass Rate", "10 / 10 (100%)", EMERALD),
        ("Cost Discrepancy", "0.00 BDT", CYAN),
        ("Average Latency", "2.05 seconds", AMBER),
        ("p95 Latency", "4.29s (<= 5.0s Limit)", EMERALD),
        ("Schema Validity", "100% Exact Match", CYAN),
    ]
    x_m = 1240
    y_m = 180
    for title, val, col in metrics:
        draw.rounded_rectangle([(x_m, y_m), (WIDTH - 100, y_m + 115)], radius=10, fill=CARD_BG, outline=CARD_BORDER, width=2)
        draw.text((x_m + 25, y_m + 20), title, font=FONT_SUBTITLE, fill=TEXT_MUTED)
        draw.text((x_m + 25, y_m + 55), val, font=FONT_TITLE, fill=col)
        y_m += 138

    script = "All 10 official test cases passed with a 0.00 BDT cost discrepancy and p95 latency under 4.3 seconds."
    draw_prompter(draw, script, sec, 165)
    return img


# Slide 5: Deployment & Reproducibility
def render_slide_5(sec):
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    draw_header(draw, "Deployment & Deliverables", 5, 5)

    draw.text((100, 110), "04. DEPLOYMENT, REPRODUCIBILITY & SUBMISSION PACKAGE", font=FONT_TITLE, fill=CYAN)

    # 3 Large Cards
    w = 540
    # Card 1: Live API
    draw.rounded_rectangle([(100, 180), (100 + w, HEIGHT - 180)], radius=12, fill=CARD_BG, outline=CARD_BORDER, width=2)
    draw.text((130, 210), "1. Live Public Endpoint", font=FONT_HEADING, fill=CYAN)
    draw.text((130, 260), "Base URL (Reachable by Judge):", font=FONT_BODY_BOLD, fill=AMBER)
    draw.text((130, 295), "https://bup-gridwise-llm.onrender.com", font=FONT_CODE, fill=TEXT_WHITE)
    draw.text((130, 350), "Tested Endpoints:", font=FONT_BODY_BOLD, fill=TEXT_MUTED)
    draw.text((130, 385), "• GET  /health (Readiness: OK in 0.3s)", font=FONT_BODY, fill=EMERALD)
    draw.text((130, 425), "• POST /optimize-energy (Full Pipeline)", font=FONT_BODY, fill=EMERALD)
    draw.text((130, 465), "• GET  /docs (Interactive Swagger UI)", font=FONT_BODY, fill=TEXT_WHITE)
    draw.text((130, 520), "Hosting: Render (Singapore Region)", font=FONT_BODY, fill=TEXT_MUTED)

    # Card 2: Docker Fallback
    draw.rounded_rectangle([(680, 180), (680 + w, HEIGHT - 180)], radius=12, fill=CARD_BG, outline=CARD_BORDER, width=2)
    draw.text((710, 210), "2. Docker Fallback Image", font=FONT_HEADING, fill=EMERALD)
    draw.text((710, 260), "Public Registry Reference:", font=FONT_BODY_BOLD, fill=AMBER)
    draw.text((710, 295), "nabilthelegend/bup-gridwise-llm:v1", font=FONT_CODE, fill=TEXT_WHITE)
    draw.text((710, 350), "Single Pull & Run Command:", font=FONT_BODY_BOLD, fill=TEXT_MUTED)
    draw.text((710, 385), "docker run -d -p 8000:8000 \\", font=FONT_CODE, fill=CYAN)
    draw.text((710, 415), "  nabilthelegend/bup-gridwise-llm:v1", font=FONT_CODE, fill=CYAN)
    draw.text((710, 470), "• Binds to 0.0.0.0, Exposes Port 8000", font=FONT_BODY, fill=TEXT_WHITE)
    draw.text((710, 510), "• Python 3.12-slim lightweight base", font=FONT_BODY, fill=TEXT_WHITE)
    draw.text((710, 550), "• No baked-in secrets or credentials", font=FONT_BODY, fill=EMERALD)

    # Card 3: Source Repository
    draw.rounded_rectangle([(1260, 180), (1260 + w, HEIGHT - 180)], radius=12, fill=CARD_BG, outline=CARD_BORDER, width=2)
    draw.text((1290, 210), "3. GitHub & Local Quickstart", font=FONT_HEADING, fill=AMBER)
    draw.text((1290, 260), "Repository URL:", font=FONT_BODY_BOLD, fill=AMBER)
    draw.text((1290, 295), "github.com/NabilxHasan/bup-gridwise-llm", font=FONT_CODE, fill=TEXT_WHITE)
    draw.text((1290, 350), "Reproducibility Features:", font=FONT_BODY_BOLD, fill=TEXT_MUTED)
    draw.text((1290, 385), "• Self-contained README.md", font=FONT_BODY, fill=TEXT_WHITE)
    draw.text((1290, 425), "• 1-Click test script (run_live_test.py)", font=FONT_BODY, fill=TEXT_WHITE)
    draw.text((1290, 465), "• Isolated virtual environment (.venv)", font=FONT_BODY, fill=TEXT_WHITE)
    draw.text((1290, 505), "• Solver & Model Credited in Docs", font=FONT_BODY, fill=TEXT_WHITE)
    draw.text((1290, 560), "Thank you judges! We are ready for Q&A.", font=FONT_HEADING, fill=CYAN)

    script = "Our solution is deployed live on Render and mirrored on Docker Hub for zero-setup evaluation. Thank you!"
    draw_prompter(draw, script, sec, 165)
    return img


def generate_video():
    # Schedule: 165 seconds total (2m 45s)
    # Slide 1: 0 - 25s (25s)
    # Slide 2: 25 - 55s (30s)
    # Slide 3: 55 - 100s (45s)
    # Slide 4: 100 - 135s (35s)
    # Slide 5: 135 - 165s (30s)

    TOTAL_SEC = 165
    print(f"Generating 1080p MP4 Video: {OUTPUT_MP4} ({TOTAL_SEC}s, {FPS} fps)...")

    # Find ffmpeg
    ffmpeg_bin = "ffmpeg"
    alt_ffmpeg = r"C:\Users\nabil\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0-full_build\bin\ffmpeg.exe"
    if not shutil.which(ffmpeg_bin) and os.path.exists(alt_ffmpeg):
        ffmpeg_bin = alt_ffmpeg

    # FFmpeg command writing raw RGB frames to MP4
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
        "-crf", "22",
        OUTPUT_MP4
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    # Pre-render base frames to make generation blazing fast
    print("Pre-rendering slide templates...")
    # Render every second (1 frame per second template, then pipe FPS times)
    for sec in range(TOTAL_SEC):
        if sec < 25:
            frame = render_slide_1(sec)
        elif sec < 55:
            frame = render_slide_2(sec)
        elif sec < 100:
            frame = render_slide_3(sec)
        elif sec < 135:
            frame = render_slide_4(sec)
        else:
            frame = render_slide_5(sec)

        # Write this frame FPS times
        raw_bytes = frame.tobytes()
        for _ in range(FPS):
            proc.stdin.write(raw_bytes)

        if (sec + 1) % 15 == 0:
            print(f"Rendered {sec + 1}/{TOTAL_SEC} seconds ({(sec+1)/TOTAL_SEC*100:.0f}%)...")

    proc.stdin.close()
    proc.wait()
    print(f"\nSUCCESS! Video saved to: {os.path.abspath(OUTPUT_MP4)}")


if __name__ == "__main__":
    generate_video()
