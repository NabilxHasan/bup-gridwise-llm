import os
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load local environment variables if .env exists
load_dotenv()

from app.models import (
    HealthResponse,
    OptimizeEnergyRequest,
    OptimizeEnergyResponse,
)
from app.interpreter import interpret_operator_notes, LLMUnavailableError
from app.optimizer import solve_energy_schedule
from app.verifier import verify_schedule

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gridwise.main")

app = FastAPI(
    title="GridWise LLM Service",
    description="LLM-Assisted Smart Campus Energy Scheduling Service for BUP CSE Fest 2026",
    version="2.0.0",
)

from fastapi.encoders import jsonable_encoder

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Map malformed JSON / missing structure to 400, and schema violations to 422 per Section 06.1."""
    for err in exc.errors():
        if err.get("type") in ("json_invalid", "missing"):
            return JSONResponse(
                status_code=400,
                content={"detail": "Malformed JSON or structurally invalid request."},
            )
    return JSONResponse(
        status_code=422,
        content={"detail": "Semantically invalid but well-formed request.", "errors": jsonable_encoder(exc.errors())},
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint providing service status and quick links."""
    return {
        "status": "ok",
        "service": "GridWise LLM Service",
        "event": "BUP CSE Fest 2026",
        "health_check": "/health",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Readiness endpoint for the judging harness."""
    return HealthResponse(status="ok")


@app.post("/optimize-energy", response_model=OptimizeEnergyResponse)
async def optimize_energy(req: OptimizeEnergyRequest):
    """
    Main LLM interpretation + 24-hour mathematical optimization endpoint.
    Pipeline:
      1. Interpret operator notes via LLM with deterministic guardrails.
      2. Apply directives to 24-hour Linear Programming model (HiGHS).
      3. Solve for cost-optimal, constraint-satisfying dispatch schedule.
      4. Shadow-replay verification to guarantee 0 constraint violations.
    """
    try:
        # Step 1: LLM semantic interpretation + Guardrails
        directives = await interpret_operator_notes(
            notes=req.operator_notes,
            battery=req.battery,
        )

        # Step 2 & 3: Mathematical Optimization via HiGHS LP Solver
        hourly_plan, total_grid, total_cost, peak_grid = solve_energy_schedule(
            hours=req.hours,
            battery=req.battery,
            directives=directives,
        )

        # Step 4: Shadow Replay Verification (simulates judge checks)
        verified, verif_msg = verify_schedule(
            hours=req.hours,
            battery=req.battery,
            directives=directives,
            hourly_plan=hourly_plan,
        )

        if not verified:
            logger.error(f"Internal schedule verification failed: {verif_msg}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Controlled internal error: schedule failed mathematical verification."},
            )

        # Generate concise plan summary
        applied_types = [d.directive_type for d in directives if d.applies]
        if applied_types:
            dir_text = f"applied directives: {', '.join(applied_types)}"
        else:
            dir_text = "no operational directives applied"

        plan_summary = (
            f"Optimized 24-hour schedule for {req.scenario_id} under {dir_text}. "
            f"Total grid import {total_grid} kWh at total cost {total_cost} BDT "
            f"with peak grid load of {peak_grid} kWh and battery neutrality preserved."
        )

        return OptimizeEnergyResponse(
            scenario_id=req.scenario_id,
            directive_interpretation=directives,
            hourly_plan=hourly_plan,
            total_grid_kwh=total_grid,
            total_cost_bdt=total_cost,
            peak_grid_kwh=peak_grid,
            plan_summary=plan_summary,
        )

    except LLMUnavailableError as le:
        logger.error(f"Controlled LLM error: {le}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Controlled internal error: language model unavailable for operator notes."},
        )
    except ValueError as ve:
        logger.error(f"Controlled optimization solver error: {ve}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Controlled internal optimization solver error."},
        )
    except Exception as e:
        logger.error(f"Controlled server error: {e}", exc_info=True)
        # Never leak secrets or raw traces per Section 06.1
        return JSONResponse(
            status_code=500,
            content={"detail": "Controlled internal processing error."},
        )


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
