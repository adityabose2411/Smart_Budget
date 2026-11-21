"""RaastaIQ – Budget Smarts: strategy comparison API (FastAPI).

Run:  pip install fastapi uvicorn pydantic
      uvicorn main:app --reload --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="RaastaIQ API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Road(BaseModel):
    id: str
    name: str
    complaints: int = Field(ge=0)          # open citizen complaints
    condition: float = Field(ge=0, le=100)  # 0 = destroyed, 100 = perfect
    traffic: float = Field(ge=0)            # daily vehicles (thousands)
    repair_cost: float = Field(gt=0)        # Rs lakh to fully repair
    flood_risk: float = Field(ge=0, le=1)   # 0-1, from monsoon simulator


class CompareRequest(BaseModel):
    budget: float = Field(gt=0)  # Rs lakh
    roads: list[Road] | None = None


# Demo data used when the client sends no roads.
DEMO_ROADS = [
    Road(id="r1", name="Ring Road, Sector 4", complaints=140, condition=35, traffic=60, repair_cost=90, flood_risk=0.9),
    Road(id="r2", name="Old Market Link", complaints=210, condition=55, traffic=25, repair_cost=40, flood_risk=0.6),
    Road(id="r3", name="Canal Street", complaints=90, condition=30, traffic=45, repair_cost=70, flood_risk=0.85),
    Road(id="r4", name="Station Approach", complaints=170, condition=62, traffic=80, repair_cost=55, flood_risk=0.3),
    Road(id="r5", name="University Avenue", complaints=40, condition=48, traffic=30, repair_cost=35, flood_risk=0.4),
    Road(id="r6", name="Hospital Road", complaints=75, condition=28, traffic=50, repair_cost=60, flood_risk=0.7),
    Road(id="r7", name="Market Lane", complaints=120, condition=70, traffic=15, repair_cost=20, flood_risk=0.2),
]


def impact(road: Road) -> float:
    """Citizen harm avoided by repairing a road (higher = better)."""
    damage = (100 - road.condition) / 100
    return road.traffic * damage * (1 + road.flood_risk) + road.complaints * 0.05


def fund(roads: list[Road], budget: float) -> list[Road]:
    """Fund roads in the given order, skipping any that no longer fit."""
    chosen, left = [], budget
    for r in roads:
        if r.repair_cost <= left:
            chosen.append(r)
            left -= r.repair_cost
    return chosen


STRATEGIES = {
    "Most complaints first": lambda rs: sorted(rs, key=lambda r: -r.complaints),
    "Worst roads first": lambda rs: sorted(rs, key=lambda r: r.condition),
    # NagarLens plan: best harm avoided per rupee (greedy knapsack by ratio).
    "NagarLens plan": lambda rs: sorted(rs, key=lambda r: -impact(r) / r.repair_cost),
}


@app.post("/api/strategy-comparison")
def compare(req: CompareRequest):
    roads = req.roads or DEMO_ROADS
    total = sum(impact(r) for r in roads) or 1.0
    results = []
    for name, order in STRATEGIES.items():
        chosen = fund(order(roads), req.budget)
        spent = sum(r.repair_cost for r in chosen)
        gained = sum(impact(r) for r in chosen)
        results.append({
            "strategy": name,
            "roads_fixed": [r.name for r in chosen],
            "spent": round(spent, 1),
            "unspent": round(req.budget - spent, 1),
            "harm_avoided_pct": round(100 * gained / total, 1),
            "complaints_resolved": sum(r.complaints for r in chosen),
            "impact_per_lakh": round(gained / spent, 3) if spent else 0,
        })
    best = max(results, key=lambda x: x["harm_avoided_pct"])
    base = max((x for x in results if x["strategy"] != "NagarLens plan"),
               key=lambda x: x["harm_avoided_pct"])
    return {
        "budget": req.budget,
        "results": results,
        "winner": best["strategy"],
        "uplift_vs_best_baseline_pct": round(
            best["harm_avoided_pct"] - base["harm_avoided_pct"], 1),
    }


@app.get("/api/health")
def health():
    return {"ok": True}
