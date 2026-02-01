from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.services.grid_service import grid_service
from app.core.normalization import normalizer
from app.analytics.micro import micro_analytics
from app.analytics.macro import macro_analytics
from app.core.decision_engine import decision_engine
from app.services.ai_insight_service import ai_insight_service

app = FastAPI(title="DecisionLens API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to DecisionLens AI Assistant Coach API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/match/{match_id}/review")
async def get_match_review(match_id: str):
    try:
        # 1. Fetch data from GRID
        # timeline = await grid_service.get_match_timeline(match_id)
        # Mocking timeline for the demo if API key is missing
        timeline = {"frames": []} 
        
        # 2. Normalize
        snapshots = normalizer.normalize_timeline(timeline)
        events = normalizer.extract_events(timeline, "CHAMPION_KILL")
        
        # 3. Analyze
        micro = micro_analytics.analyze_player_mistakes(events, snapshots)
        macro = macro_analytics.identify_strategic_inflections(snapshots)
        
        # 4. Decision Engine (Mock state for demo)
        current_state = {
            "gold_diff": 500, "dragons_diff": 1, "time_seconds": 1200,
            "xp_diff": 200, "towers_diff": 0, "barons_diff": 0,
            "team100_kills": 5, "team200_kills": 4
        }
        what_if = decision_engine.what_if_analysis(current_state, {"dragons_diff": 2})
        
        # 5. Generate Insights
        ai_summary = ai_insight_service.generate_coach_summary(micro, macro, [
            {"what_if": "We secured the second dragon", "delta": what_if["delta"] * 100}
        ])
        
        return {
            "match_id": match_id,
            "micro_insights": micro,
            "macro_insights": macro,
            "decision_analysis": what_if,
            "ai_coach_summary": ai_summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
