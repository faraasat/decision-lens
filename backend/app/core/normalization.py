import pandas as pd
import json
from typing import List, Dict, Any

class Normalizer:
    @staticmethod
    def normalize_timeline(timeline_data: Dict[str, Any]) -> pd.DataFrame:
        """
        Convert raw timeline data into a flat DataFrame of snapshots.
        """
        frames = timeline_data.get("frames", [])
        metadata = timeline_data.get("metadata", {})
        game = metadata.get("game", "lol") # Default to lol if not specified
        
        snapshot_list = []
        
        for frame in frames:
            timestamp = frame.get("timestamp")
            participant_data = frame.get("participantFrames", {})
            
            # Aggregate team level stats
            team_stats = {
                100: {"primary": 0, "secondary": 0},
                200: {"primary": 0, "secondary": 0},
                "team-blue": {"primary": 0, "secondary": 0},
                "team-red": {"primary": 0, "secondary": 0}
            }
            
            snapshot = {
                "timestamp": timestamp,
                "participantFrames": participant_data
            }
            for pid, data in participant_data.items():
                if game == "valorant":
                    team_id = "team-blue" if int(pid) <= 5 else "team-red"
                    primary_val = data.get("credits", 0)
                    secondary_val = data.get("loadoutValue", 0)
                    
                    snapshot[f"p{pid}_credits"] = primary_val
                    snapshot[f"p{pid}_loadout"] = secondary_val
                else: # LoL
                    team_id = 100 if int(pid) <= 5 else 200
                    primary_val = data.get("totalGold", 0)
                    secondary_val = data.get("xp", 0)
                    
                    snapshot[f"p{pid}_gold"] = primary_val
                    snapshot[f"p{pid}_xp"] = secondary_val
                    snapshot[f"p{pid}_minionsKilled"] = data.get("minionsKilled", 0)
                    snapshot[f"p{pid}_jungleMinionsKilled"] = data.get("jungleMinionsKilled", 0)
                    snapshot[f"p{pid}_wardsPlaced"] = data.get("wardsPlaced", 0)

                team_stats[team_id]["primary"] += primary_val
                team_stats[team_id]["secondary"] += secondary_val
            
            if game == "valorant":
                snapshot["gold_diff"] = team_stats["team-blue"]["primary"] - team_stats["team-red"]["primary"]
                snapshot["xp_diff"] = team_stats["team-blue"]["secondary"] - team_stats["team-red"]["secondary"]
                snapshot["team100_gold"] = team_stats["team-blue"]["primary"]
                snapshot["team200_gold"] = team_stats["team-red"]["primary"]
            else:
                snapshot["gold_diff"] = team_stats[100]["primary"] - team_stats[200]["primary"]
                snapshot["xp_diff"] = team_stats[100]["secondary"] - team_stats[200]["secondary"]
                snapshot["team100_gold"] = team_stats[100]["primary"]
                snapshot["team200_gold"] = team_stats[200]["primary"]
            
            snapshot_list.append(snapshot)
            
        return pd.DataFrame(snapshot_list)

    @staticmethod
    def extract_events(timeline_data: Dict[str, Any], event_types: List[str] = None) -> pd.DataFrame:
        """
        Extract specific events from frames or rounds.
        """
        events = []
        
        # Look in frames (Standard LoL / Val structure)
        frames = timeline_data.get("frames", [])
        for frame in frames:
            for event in frame.get("events", []):
                if event_types is None or event.get("type") in event_types:
                    events.append(event)
        
        # Look in rounds (VALORANT specific mock/data structure)
        rounds = timeline_data.get("rounds", [])
        for round_data in rounds:
            for event in round_data.get("events", []):
                if event_types is None or event.get("type") in event_types:
                    events.append(event)
                    
        if not events:
            return pd.DataFrame(columns=["type", "timestamp", "killerId", "victimId", "headshot"])
            
        return pd.DataFrame(events)

# Singleton instance
normalizer = Normalizer()
