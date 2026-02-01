import logging
import math
import asyncio
import json
from typing import Dict, List, Any
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Response, Body, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.services.grid_service import grid_service
from app.services.live_stream_service import live_stream_service
from app.core.normalization import normalizer
from app.analytics.micro import micro_analytics
from app.analytics.macro import macro_analytics
from app.core.decision_engine import decision_engine
from app.services.ai_insight_service import ai_insight_service
from app.core.utils import clean_json_data

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

@app.get("/api/matches/live")
async def get_live_matches(game: str = "lol"):
    try:
        matches = await grid_service.get_live_matches(game)
        return matches
    except Exception as e:
        logger.error(f"Error fetching live matches: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await live_stream_service.connect(websocket)
    try:
        while True:
            # Keep connection alive and listen for any client messages
            data = await websocket.receive_text()
            logger.info(f"Received message from client: {data}")
    except WebSocketDisconnect:
        live_stream_service.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        live_stream_service.disconnect(websocket)

@app.post("/api/live/start/{match_id}")
async def start_live_stream(match_id: str):
    import asyncio
    # Run the stream in the background
    asyncio.create_task(live_stream_service.start_live_stream(match_id))
    return {"status": "started", "match_id": match_id}

@app.post("/api/live/stop")
async def stop_live_stream():
    live_stream_service.stop_stream()
    return {"status": "stopped"}

@app.post("/api/simulate")
async def simulate_state(payload: Dict[str, Any] = Body(...)):
    logger.info("Simulation request received")
    try:
        current_state = payload.get("current_state", {})
        modifications = payload.get("modifications", {})
        
        # Use what_if_analysis for comprehensive XAI
        result = decision_engine.what_if_analysis(current_state, modifications)
        
        # Also include SHAP for the new state
        shap_values = decision_engine.explain_decision(result["modified_state"])
        
        return clean_json_data({
            "win_probability": result["modified_probability"],
            "shap_explanations": shap_values,
            "modified_state": result["modified_state"],
            "explanation": result["explanation"],
            "delta": result["delta"]
        })
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
        match_data = await grid_service.get_match_timeline(match_id)
        
        metadata = match_data.get("metadata", {})
        game = metadata.get("game", "lol")
        
        # 2. Normalize
        logger.info(f"Normalizing {game} timeline data")
        snapshots = normalizer.normalize_timeline(match_data).fillna(0) 
        
        # Extract multiple event types
        event_types = ["KILL", "SPIKE_PLANTED", "SPIKE_DEFUSED"] if game == "valorant" else ["CHAMPION_KILL", "ELITE_MONSTER_KILL", "BUILDING_KILL"]
        events = normalizer.extract_events(match_data, event_types).fillna(0)
        logger.info(f"Extracted {len(events)} events and {len(snapshots)} snapshots")
        
        # If events are still empty and we have no snapshots, don't create mock events
        if events.empty and snapshots.empty:
            logger.info("No events or snapshots found in GRID data")
            events = pd.DataFrame(columns=["type", "timestamp", "killerId", "victimId", "headshot"])
        
        # 3. Analyze
        logger.info(f"Running micro and macro analytics for {game}")
        micro = micro_analytics.analyze_player_mistakes(events, snapshots, game=game)
        player_stats = micro_analytics.compute_player_efficiency(snapshots, events, game=game)
        macro_shifts = macro_analytics.identify_strategic_inflections(snapshots, game=game, events_df=events)
        objectives = macro_analytics.evaluate_objective_control(events, game=game)
        draft_analysis = macro_analytics.analyze_draft_synergy(metadata)
        
        # 4. Decision Engine (Get latest state for analysis)
        if not snapshots.empty:
            logger.info("Preparing current state for decision engine")
            
            # Prepare feature sets for all snapshots
            all_states = []
            for idx, row in snapshots.iterrows():
                row_dict = row.to_dict()
                ts = row_dict.get("timestamp", 0)
                past_events = events[events['timestamp'] <= ts] if not events.empty else pd.DataFrame()
                
                if game == "valorant":
                    state = {
                        "gold_diff": row_dict.get("gold_diff", 0),
                        "xp_diff": row_dict.get("xp_diff", 0),
                        "time_seconds": ts / 1000,
                        "dragons_diff": len(past_events[past_events['type'] == 'SPIKE_PLANTED']) if not past_events.empty else 0,
                        "towers_diff": len(past_events[past_events['type'] == 'SPIKE_DEFUSED']) if not past_events.empty else 0,
                        "barons_diff": 0,
                        "team100_kills": len(past_events[(past_events['type'] == 'KILL') & (past_events['killerId'] <= 5)]) if not past_events.empty else 0,
                        "team200_kills": len(past_events[(past_events['type'] == 'KILL') & (past_events['killerId'] > 5)]) if not past_events.empty else 0
                    }
                else:
                    state = {
                        "gold_diff": row_dict.get("gold_diff", 0),
                        "xp_diff": row_dict.get("xp_diff", 0),
                        "time_seconds": ts / 1000,
                        "dragons_diff": len(past_events[(past_events['type'] == 'ELITE_MONSTER_KILL') & (past_events['monsterType'] == 'DRAGON')]) if not past_events.empty else 0,
                        "towers_diff": len(past_events[(past_events['type'] == 'BUILDING_KILL') & (past_events['buildingType'] == 'TOWER')]) if not past_events.empty else 0,
                        "barons_diff": len(past_events[(past_events['type'] == 'ELITE_MONSTER_KILL') & (past_events['monsterType'] == 'BARON')]) if not past_events.empty else 0,
                        "team100_kills": len(past_events[(past_events['type'] == 'CHAMPION_KILL') & (past_events['killerId'] <= 5)]) if not past_events.empty else 0,
                        "team200_kills": len(past_events[(past_events['type'] == 'CHAMPION_KILL') & (past_events['killerId'] > 5)]) if not past_events.empty else 0
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
        ], game=game, player_stats=player_stats)
        
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
        
        try:
            cleaned_response = clean_json_data(response_data)
            
            import json
            return Response(content=json.dumps(cleaned_response), media_type="application/json")
        except Exception as json_err:
            logger.error(f"Serialization error: {str(json_err)}", exc_info=True)
            raise HTTPException(status_code=500, detail="Error serializing match review data")
    except Exception as e:
        logger.error(f"Error processing match review: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
