import asyncio
import json
import logging
import os
from typing import List, Dict, Any, Optional
from fastapi import WebSocket
import httpx
from .grid_service import grid_service
from ..core.normalization import normalizer
from ..core.decision_engine import decision_engine
from ..analytics.micro import micro_analytics
from ..analytics.macro import macro_analytics
from ..core.utils import clean_json_data
import pandas as pd

logger = logging.getLogger("decision-lens.live")

class LiveStreamService:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.is_running = False
        self.current_match_id = None
        self.state_history = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        if not self.active_connections:
            logger.debug("No active connections to broadcast to")
            return
        logger.info(f"Broadcasting {message.get('type')} to {len(self.active_connections)} clients")
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")

    async def start_live_stream(self, match_id: str):
        """
        In a real production app, this would connect to GRID WebSocket.
        For this hackathon, we simulate the real-time feed by fetching 
        the full timeline and streaming it snapshot by snapshot if real 
        WebSocket is unavailable.
        """
        self.current_match_id = match_id
        self.is_running = True
        self.state_history = []
        
        logger.info(f"Starting live stream for match: {match_id}")
        
        try:
            # 1. Try to get initial state/timeline
            full_data = await grid_service.get_match_timeline(match_id)
            snapshots = normalizer.normalize_timeline(full_data)
            game = full_data.get("metadata", {}).get("game", "lol")
            
            # Extract events for micro analytics
            event_types = ["KILL", "SPIKE_PLANTED", "SPIKE_DEFUSED"] if game == "valorant" else ["CHAMPION_KILL", "ELITE_MONSTER_KILL", "BUILDING_KILL"]
            all_events = normalizer.extract_events(full_data, event_types)

            if snapshots.empty:
                logger.warning(f"No snapshots found for match {match_id}. Cannot start live stream.")
                self.is_running = False
                return

            # 2. Stream snapshots one by one to simulate real-time
            for _, row in snapshots.iterrows():
                if not self.is_running:
                    break
                    
                state = row.to_dict()
                ts = state.get("timestamp", 0)
                
                # Enrich with AI predictions in real-time
                features = self._extract_features(state)
                win_prob = decision_engine.predict_win_probability(features)
                state['win_prob'] = win_prob
                state['shap_explanations'] = decision_engine.explain_decision(features)
                
                # Filter events up to current timestamp
                current_events = all_events[all_events['timestamp'] <= ts] if not all_events.empty else pd.DataFrame()
                
                # Dynamic Analytics
                current_df = pd.DataFrame(self.state_history + [state])
                state['macro_insights'] = macro_analytics.identify_strategic_inflections(current_df, game=game, events_df=current_events)
                state['player_stats'] = micro_analytics.compute_player_efficiency(current_df, current_events, game=game)
                state['micro_insights'] = micro_analytics.analyze_player_mistakes(current_events, current_df, game=game)
                state['objectives'] = macro_analytics.evaluate_objective_control(current_events, game=game)
                state['draft_analysis'] = macro_analytics.analyze_draft_synergy(full_data.get("metadata", {}))
                
                self.state_history.append(state)
                
                await self.broadcast(clean_json_data({
                    "type": "STATE_UPDATE",
                    "match_id": match_id,
                    "game": game,
                    "data": state,
                    "history_count": len(self.state_history)
                }))
                
                # Simulate the delay between real-game snapshots (usually 1-5 seconds)
                await asyncio.sleep(2)
                
        except Exception as e:
            logger.error(f"Error in live stream: {e}", exc_info=True)
            self.is_running = False

    def _extract_features(self, state: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "gold_diff": state.get("gold_diff", 0),
            "xp_diff": state.get("xp_diff", 0),
            "time_seconds": state.get("timestamp", 0) / 1000,
            "dragons_diff": state.get("dragons_diff", 0),
            "towers_diff": state.get("towers_diff", 0),
            "barons_diff": state.get("barons_diff", 0),
            "team100_kills": state.get("team100_kills", 0),
            "team200_kills": state.get("team200_kills", 0)
        }

    async def _run_mock_stream(self, match_id: str, game: str = "lol"):
        """Generates realistic mock data if real match data is unavailable."""
        gold_diff = 0
        team100_kills = 0
        team200_kills = 0
        dragons_diff = 0
        
        # Mock events for analytics
        mock_events = []
        
        for i in range(200):
            if not self.is_running:
                break
                
            # Simulate a dynamic game
            gold_diff += (i * 2) + (i % 7 * 50) - (i % 5 * 40)
            
            # Create mock events
            if i % 10 == 0: 
                team100_kills += 1
                mock_events.append({"type": "KILL" if game == "valorant" else "CHAMPION_KILL", "timestamp": i * 5000, "killerId": "blue1" if game == "valorant" else 1, "victimId": "red1" if game == "valorant" else 6})
            if i % 12 == 0: 
                team200_kills += 1
                mock_events.append({"type": "KILL" if game == "valorant" else "CHAMPION_KILL", "timestamp": i * 5000, "killerId": "red2" if game == "valorant" else 7, "victimId": "blue2" if game == "valorant" else 2})
            if i % 50 == 0: 
                dragons_diff += 1
                mock_events.append({"type": "SPIKE_PLANTED" if game == "valorant" else "ELITE_MONSTER_KILL", "timestamp": i * 5000, "monsterType": "DRAGON", "teamId": 100})
            
            timestamp = i * 5000
            state = {
                "timestamp": timestamp,
                "gold_diff": gold_diff,
                "xp_diff": gold_diff * 0.85,
                "team100_gold": 5000 + (i * 400) + gold_diff,
                "team200_gold": 5000 + (i * 400),
                "dragons_diff": dragons_diff,
                "towers_diff": int(gold_diff / 2000),
                "barons_diff": 1 if i > 100 and gold_diff > 5000 else 0,
                "team100_kills": team100_kills,
                "team200_kills": team200_kills,
                "participantFrames": {
                    str(p): {
                        "position": {"x": 5000 + (i * 10) + (p * 100), "y": 5000 + (i * 10) + (p * 100)},
                        "totalGold" if game == "lol" else "credits": 1000 + (i * 100),
                        "xp" if game == "lol" else "loadoutValue": 800 + (i * 80),
                        "wardsPlaced": 2 + (i // 10),
                        "minionsKilled": 10 + (i * 8)
                    } for p in range(1, 11)
                }
            }
            
            # Enrich with AI
            features = self._extract_features(state)
            state['win_prob'] = decision_engine.predict_win_probability(features)
            state['shap_explanations'] = decision_engine.explain_decision(features)
            
            # Dynamic Analytics for Mock
            current_df = pd.DataFrame(self.state_history + [state])
            events_df = pd.DataFrame(mock_events)
            state['macro_insights'] = macro_analytics.identify_strategic_inflections(current_df, game=game, events_df=events_df)
            state['player_stats'] = micro_analytics.compute_player_efficiency(current_df, events_df, game=game)
            state['micro_insights'] = micro_analytics.analyze_player_mistakes(events_df, current_df, game=game)
            state['objectives'] = macro_analytics.evaluate_objective_control(events_df, game=game)
            state['draft_analysis'] = {}
            
            self.state_history.append(state)
            
            await self.broadcast(clean_json_data({
                "type": "STATE_UPDATE",
                "match_id": match_id,
                "game": game,
                "data": state,
                "is_mock": True,
                "history_count": len(self.state_history)
            }))
            await asyncio.sleep(2)

    def stop_stream(self):
        self.is_running = False
        logger.info("Live stream stopped")

live_stream_service = LiveStreamService()
