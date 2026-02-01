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
            
            if snapshots.empty:
                logger.warning("No snapshots found for match, using mock generator")
                await self._run_mock_stream(match_id)
                return

            # 2. Stream snapshots one by one to simulate real-time
            for _, row in snapshots.iterrows():
                if not self.is_running:
                    break
                    
                state = row.to_dict()
                
                # Enrich with AI predictions in real-time
                win_prob = decision_engine.predict_win_probability(self._extract_features(state))
                state['win_prob'] = win_prob
                state['shap_explanations'] = decision_engine.explain_decision(self._extract_features(state))
                
                self.state_history.append(state)
                
                await self.broadcast({
                    "type": "STATE_UPDATE",
                    "match_id": match_id,
                    "data": state,
                    "history_count": len(self.state_history)
                })
                
                # Simulate the delay between real-game snapshots (usually 1-5 seconds)
                await asyncio.sleep(2)
                
        except Exception as e:
            logger.error(f"Error in live stream: {e}")
            self.is_running = False

    def _extract_features(self, state: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "gold_diff": state.get("gold_diff", 0),
            "xp_diff": state.get("xp_diff", 0),
            "time_seconds": state.get("timestamp", 0) / 1000,
            "dragons_diff": 0, # Should be calculated from state
            "towers_diff": 0,
            "barons_diff": 0,
            "team100_kills": 0,
            "team200_kills": 0
        }

    async def _run_mock_stream(self, match_id: str):
        """Generates realistic mock data if real match data is unavailable."""
        gold_diff = 0
        for i in range(100):
            if not self.is_running:
                break
                
            gold_diff += (i * 10) + (i % 5 * 100)
            state = {
                "timestamp": i * 5000,
                "gold_diff": gold_diff,
                "xp_diff": gold_diff * 0.8,
                "team100_gold": 5000 + gold_diff,
                "team200_gold": 5000
            }
            
            win_prob = decision_engine.predict_win_probability(self._extract_features(state))
            state['win_prob'] = win_prob
            
            await self.broadcast({
                "type": "STATE_UPDATE",
                "match_id": match_id,
                "data": state,
                "is_mock": True
            })
            await asyncio.sleep(2)

    def stop_stream(self):
        self.is_running = False
        logger.info("Live stream stopped")

live_stream_service = LiveStreamService()
