import logging
import math
from typing import Dict, List, Any
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Response, Body
from fastapi.middleware.cors import CORSMiddleware
from app.services.grid_service import grid_service
from app.core.normalization import normalizer
from app.analytics.micro import micro_analytics
from app.analytics.macro import macro_analytics
from app.core.decision_engine import decision_engine
from app.services.ai_insight_service import ai_insight_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("decision-lens")

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
    logger.info("Root endpoint hit")
    return {"message": "Welcome to DecisionLens AI Assistant Coach API"}

@app.get("/health")
async def health():
    logger.info("Health check endpoint hit")
    return {"status": "healthy"}

@app.post("/api/simulate")
async def simulate_state(payload: Dict[str, Any] = Body(...)):
    logger.info("Simulation request received")
    try:
        current_state = payload.get("current_state", {})
        modifications = payload.get("modifications", {})
        
        modified_state = current_state.copy()
        modified_state.update(modifications)
        
        prob = decision_engine.predict_win_probability(modified_state)
        shap_values = decision_engine.explain_decision(modified_state)
        
        return {
            "win_probability": prob,
            "shap_explanations": shap_values,
            "modified_state": modified_state
        }
    except Exception as e:
        logger.error(f"Simulation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/match/{match_id}/review")
async def get_match_review(match_id: str):
    logger.info(f"Fetching review for match_id: {match_id}")
    try:
        # Simulate delay for realism
        import asyncio
        await asyncio.sleep(0.5)
        
        # 1. Fetch data from GRID
        logger.info(f"Requesting data from GRID for match: {match_id}")
        timeline = await grid_service.get_match_timeline(match_id)
        match_details = await grid_service.get_match_details(match_id)
        
        metadata = match_details.get("metadata", {})
        game = metadata.get("game", "lol")
        
        # 2. Normalize
        logger.info(f"Normalizing {game} timeline data")
        snapshots = normalizer.normalize_timeline(match_details).fillna(0) # Note: match_details contains frames in mock
        # Extract multiple event types
        event_types = ["KILL", "SPIKE_PLANTED", "SPIKE_DEFUSED"] if game == "valorant" else ["CHAMPION_KILL", "ELITE_MONSTER_KILL", "BUILDING_KILL"]
        events = normalizer.extract_events(match_details, event_types).fillna(0)
        logger.info(f"Extracted {len(events)} events and {len(snapshots)} snapshots")
        
        # 3. Analyze
        logger.info(f"Running micro and macro analytics for {game}")
        micro = micro_analytics.analyze_player_mistakes(events, snapshots, game=game)
        player_stats = micro_analytics.compute_player_efficiency(snapshots, events, game=game)
        macro_shifts = macro_analytics.identify_strategic_inflections(snapshots, game=game)
        objectives = macro_analytics.evaluate_objective_control(events, game=game)
        draft_analysis = macro_analytics.analyze_draft_synergy(metadata)
        
        # 4. Decision Engine (Get latest state for analysis)
        if not snapshots.empty:
            logger.info("Preparing current state for decision engine")
            
            # Prepare feature sets for all snapshots
            all_states = []
            for idx, row in snapshots.iterrows():
                row_dict = row.to_dict()
                
                # We need to approximate objective counts for historical snapshots
                # In a real system, we'd have this data properly indexed.
                # For this mock, we'll use a cumulative count of events up to that timestamp.
                ts = row_dict.get("timestamp", 0)
                past_events = events[events['timestamp'] <= ts]
                
                if game == "valorant":
                    state = {
                        "gold_diff": row_dict.get("gold_diff", 0),
                        "xp_diff": row_dict.get("xp_diff", 0),
                        "time_seconds": ts / 1000,
                        "dragons_diff": len(past_events[past_events['type'] == 'SPIKE_PLANTED']),
                        "towers_diff": len(past_events[past_events['type'] == 'SPIKE_DEFUSED']),
                        "barons_diff": 0,
                        "team100_kills": len(past_events[(past_events['type'] == 'KILL') & (past_events['killerId'] <= 5)]),
                        "team200_kills": len(past_events[(past_events['type'] == 'KILL') & (past_events['killerId'] > 5)])
                    }
                else:
                    state = {
                        "gold_diff": row_dict.get("gold_diff", 0),
                        "xp_diff": row_dict.get("xp_diff", 0),
                        "time_seconds": ts / 1000,
                        "dragons_diff": len(past_events[(past_events['type'] == 'ELITE_MONSTER_KILL') & (past_events['monsterType'] == 'DRAGON')]),
                        "towers_diff": len(past_events[(past_events['type'] == 'BUILDING_KILL') & (past_events['buildingType'] == 'TOWER')]),
                        "barons_diff": len(past_events[(past_events['type'] == 'ELITE_MONSTER_KILL') & (past_events['monsterType'] == 'BARON')]),
                        "team100_kills": len(past_events[(past_events['type'] == 'CHAMPION_KILL') & (past_events['killerId'] <= 5)]),
                        "team200_kills": len(past_events[(past_events['type'] == 'CHAMPION_KILL') & (past_events['killerId'] > 5)])
                    }
                all_states.append(state)

            # Bulk predict win probabilities
            logger.info(f"Predicting win probabilities for {len(all_states)} snapshots")
            probs = decision_engine.predict_bulk_probabilities(all_states)
            
            # Enrich snapshots with probabilities and player stats
            enriched_snapshots = []
            for idx, p in enumerate(probs):
                snapshot_row = snapshots.iloc[idx].to_dict()
                snapshot_row['win_prob'] = p
                
                # We filter events up to this snapshot
                snap_ts = snapshot_row.get("timestamp", 0)
                snap_events = events[events['timestamp'] <= snap_ts]
                
                # Compute player stats
                snap_df = pd.DataFrame([snapshots.iloc[idx]])
                snapshot_row['player_stats'] = micro_analytics.compute_player_efficiency(snap_df, snap_events, game=game)
                
                # Compute SHAP for each snapshot for true dynamic analysis
                snapshot_row['shap_explanations'] = decision_engine.explain_decision(all_states[idx])
                
                enriched_snapshots.append(snapshot_row)

            current_state = all_states[-1]
            shap_explanations = enriched_snapshots[-1]['shap_explanations']
            player_stats = enriched_snapshots[-1]['player_stats']
        else:
            logger.warning("Snapshots are empty, returning default state")
            current_state = {
                "gold_diff": 0, "dragons_diff": 0, "time_seconds": 0,
                "xp_diff": 0, "towers_diff": 0, "barons_diff": 0,
                "team100_kills": 0, "team200_kills": 0
            }
            player_stats = []
            enriched_snapshots = []
            shap_explanations = {}
            
        logger.info("Performing what-if analysis")
        what_if = decision_engine.what_if_analysis(current_state, {"dragons_diff": current_state["dragons_diff"] + 1})
        
        # 5. Generate Insights
        logger.info("Generating AI insights")
        ai_summary = ai_insight_service.generate_coach_summary(micro, macro_shifts, [
            {
                "what_if": f"Better performance on {('site entries' if game == 'valorant' else 'objective setup')}", 
                "delta": what_if["delta"] * 100,
                "current_probability": what_if["current_probability"]
            }
        ], game=game)
        
        logger.info("Successfully processed match review")
        response_data = {
            "match_id": match_id,
            "game": game,
            "metadata": metadata,
            "micro_insights": micro,
            "macro_insights": macro_shifts,
            "objectives": objectives,
            "decision_analysis": what_if,
            "shap_explanations": shap_explanations,
            "ai_coach_summary": ai_summary,
            "current_state": current_state,
            "player_stats": player_stats,
            "draft_analysis": draft_analysis,
            "timeline_snapshots": enriched_snapshots
        }
        
        # Final safety check for NaN in the whole structure
        def clean_nans(obj):
            if isinstance(obj, float):
                if math.isnan(obj) or math.isinf(obj):
                    return 0
                return float(obj)
            if isinstance(obj, (np.integer, int)):
                return int(obj)
            if isinstance(obj, (np.floating, float)):
                if math.isnan(obj) or math.isinf(obj):
                    return 0
                return float(obj)
            if isinstance(obj, dict):
                return {str(k): clean_nans(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [clean_nans(x) for x in obj]
            return obj

        try:
            cleaned_response = clean_nans(response_data)
            
            import json
            return Response(content=json.dumps(cleaned_response), media_type="application/json")
        except Exception as json_err:
            logger.error(f"Serialization error: {str(json_err)}", exc_info=True)
            raise HTTPException(status_code=500, detail="Error serializing match review data")
    except Exception as e:
        logger.error(f"Error processing match review: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
