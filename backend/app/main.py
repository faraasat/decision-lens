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
        # Simulate delay for realism
        import asyncio
        await asyncio.sleep(0.5)
        
        # 1. Fetch data from GRID
        timeline = await grid_service.get_match_timeline(match_id)
        
        # 2. Normalize
        snapshots = normalizer.normalize_timeline(timeline)
        # Extract multiple event types
        events = normalizer.extract_events(timeline, ["CHAMPION_KILL", "ELITE_MONSTER_KILL", "BUILDING_KILL"])
        
        # 3. Analyze
        micro = micro_analytics.analyze_player_mistakes(events, snapshots)
        player_stats = micro_analytics.compute_player_efficiency(snapshots)
        macro_shifts = macro_analytics.identify_strategic_inflections(snapshots)
        objectives = macro_analytics.evaluate_objective_control(events)
        
        # 4. Decision Engine (Get latest state for analysis)
        if not snapshots.empty:
            latest = snapshots.iloc[-1].to_dict()
            
            # Count objectives from events
            dragons = len([o for o in objectives if o['type'] == 'DRAGON'])
            barons = len([o for o in objectives if o['type'] == 'BARON'])
            towers = len([o for o in objectives if o['type'] == 'TOWER'])
            kills_100 = len(events[(events['type'] == 'CHAMPION_KILL') & (events['killerId'] <= 5)])
            kills_200 = len(events[(events['type'] == 'CHAMPION_KILL') & (events['killerId'] > 5)])

            current_state = {
                "gold_diff": latest.get("gold_diff", 0),
                "xp_diff": latest.get("xp_diff", 0),
                "time_seconds": latest.get("timestamp", 0) / 1000,
                "dragons_diff": dragons, # Simplified
                "towers_diff": towers,
                "barons_diff": barons,
                "team100_kills": kills_100,
                "team200_kills": kills_200
            }
        else:
            current_state = {
                "gold_diff": 0, "dragons_diff": 0, "time_seconds": 0,
                "xp_diff": 0, "towers_diff": 0, "barons_diff": 0,
                "team100_kills": 0, "team200_kills": 0
            }
            player_stats = []
            
        what_if = decision_engine.what_if_analysis(current_state, {"dragons_diff": current_state["dragons_diff"] + 1})
        
        # 5. Generate Insights
        ai_summary = ai_insight_service.generate_coach_summary(micro, macro_shifts, [
            {
                "what_if": "We secured an additional dragon", 
                "delta": what_if["delta"] * 100,
                "current_probability": what_if["current_probability"]
            }
        ])
        
        return {
            "match_id": match_id,
            "micro_insights": micro,
            "macro_insights": macro_shifts,
            "objectives": objectives,
            "decision_analysis": what_if,
            "ai_coach_summary": ai_summary,
            "current_state": current_state,
            "player_stats": player_stats,
            "timeline_snapshots": snapshots.to_dict(orient="records")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
