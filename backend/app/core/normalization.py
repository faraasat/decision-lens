import pandas as pd
import json
from typing import List, Dict, Any

class Normalizer:
    @staticmethod
    def normalize_timeline(timeline_data: Dict[str, Any]) -> pd.DataFrame:
        """
        Convert raw timeline data into a flat DataFrame of snapshots.
        Expecting snapshots at regular intervals (e.g., every 1 min).
        """
        frames = timeline_data.get("frames", [])
        snapshot_list = []
        
        for frame in frames:
            timestamp = frame.get("timestamp")
            participant_data = frame.get("participantFrames", {})
            
            # Aggregate team level stats from participant frames
            team_stats = {
                100: {"gold": 0, "xp": 0},
                200: {"gold": 0, "xp": 0}
            }
            
            for pid, data in participant_data.items():
                # GRID participant IDs are 1-10, usually 1-5 for team 100, 6-10 for team 200
                team_id = 100 if int(pid) <= 5 else 200
                team_stats[team_id]["gold"] += data.get("totalGold", 0)
                team_stats[team_id]["xp"] += data.get("xp", 0)
            
            snapshot = {
                "timestamp": timestamp,
                "gold_diff": team_stats[100]["gold"] - team_stats[200]["gold"],
                "xp_diff": team_stats[100]["xp"] - team_stats[200]["xp"],
                "team100_gold": team_stats[100]["gold"],
                "team200_gold": team_stats[200]["gold"],
                "team100_xp": team_stats[100]["xp"],
                "team200_xp": team_stats[200]["xp"]
            }
            snapshot_list.append(snapshot)
            
        return pd.DataFrame(snapshot_list)

    @staticmethod
    def extract_events(timeline_data: Dict[str, Any], event_types: List[str] = None) -> pd.DataFrame:
        """
        Extract specific events (e.g., CHAMPION_KILL, BUILDING_KILL, ELITE_MONSTER_KILL)
        """
        frames = timeline_data.get("frames", [])
        events = []
        
        for frame in frames:
            for event in frame.get("events", []):
                if event_types is None or event.get("type") in event_types:
                    events.append(event)
                    
        return pd.DataFrame(events)

# Singleton instance
normalizer = Normalizer()
