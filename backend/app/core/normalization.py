import pandas as pd
import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger("decision-lens.normalizer")

class Normalizer:
    @staticmethod
    def _get_frames(timeline_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Helper to extract frames from different GRID data formats."""
        if "seriesState" in timeline_data:
            state = timeline_data["seriesState"]
            games = state.get("games", [])
            if not games:
                return []
            
            # Try to find frames in games (latest first)
            for game in reversed(games):
                logger.info(f"Checking game {game.get('id')} with keys {list(game.keys())}")
                frames = game.get("frames", [])
                
                if not frames and "segments" in game:
                    logger.info(f"Game {game.get('id')} has {len(game['segments'])} segments")
                    for segment in game["segments"]:
                        # Try different keys for frames/snapshots
                        for key in ["frames", "snapshots", "states"]:
                            if key in segment:
                                s_frames = segment[key]
                                logger.info(f"Found {len(s_frames)} frames in segment {segment.get('type')} using key '{key}'")
                                frames.extend(s_frames)
                        
                        # Some GRID formats have frames in payload
                        if "payload" in segment and isinstance(segment["payload"], dict):
                            for key in ["frames", "snapshots", "states"]:
                                if key in segment["payload"]:
                                    s_frames = segment["payload"][key]
                                    logger.info(f"Found {len(s_frames)} frames in segment payload using key '{key}'")
                                    frames.extend(s_frames)

                if frames:
                    return frames
            return []
        
        return timeline_data.get("frames", [])

    @staticmethod
    def normalize_timeline(timeline_data: Dict[str, Any]) -> pd.DataFrame:
        """
        Convert raw timeline data into a flat DataFrame of snapshots.
        """
        frames = Normalizer._get_frames(timeline_data)
        
        # Determine game type
        if "seriesState" in timeline_data:
            state = timeline_data["seriesState"]
            metadata = {
                "game": "lol" if str(state.get("titleId")) == "3" else "valorant" if str(state.get("titleId")) == "6" else "lol"
            }
        else:
            metadata = timeline_data.get("metadata", {})
        
        logger.info(f"Normalizing {len(frames)} frames")
        game = metadata.get("game", "lol") 
        
        snapshot_list = []
        
        # Cumulative stats
        cum_stats = {
            "dragons_diff": 0,
            "towers_diff": 0,
            "barons_diff": 0,
            "team100_kills": 0,
            "team200_kills": 0
        }
        
        for frame in frames:
            timestamp = frame.get("timestamp") or frame.get("clock", {}).get("timestamp") or 0
            
            # Update cumulative stats from events in this frame
            for event in frame.get("events", []):
                etype = event.get("type")
                if game == "lol":
                    if etype == "CHAMPION_KILL":
                        killer_id = event.get("killerId", 0)
                        if 1 <= killer_id <= 5: cum_stats["team100_kills"] += 1
                        elif 6 <= killer_id <= 10: cum_stats["team200_kills"] += 1
                    elif etype == "ELITE_MONSTER_KILL":
                        mtype = event.get("monsterType")
                        team_id = event.get("teamId")
                        val = 1 if team_id == 100 else -1
                        if mtype == "DRAGON": cum_stats["dragons_diff"] += val
                        elif mtype == "BARON": cum_stats["barons_diff"] += val
                    elif etype == "BUILDING_KILL":
                        team_id = event.get("teamId")
                        val = 1 if team_id == 100 else -1 # Note: teamId is usually the team that KILLED it
                        cum_stats["towers_diff"] += val
                elif game == "valorant":
                    if etype == "KILL":
                        killer_id = int(event.get("killerId", 0))
                        if killer_id <= 5: cum_stats["team100_kills"] += 1
                        else: cum_stats["team200_kills"] += 1
                    elif etype == "SPIKE_PLANTED":
                        cum_stats["dragons_diff"] += 1 # Map Spike to dragons_diff for XGBoost consistency
                    elif etype == "SPIKE_DEFUSED":
                        cum_stats["towers_diff"] += 1

            participant_data = frame.get("participantFrames", {})
            
            # If participantFrames is missing, check if it's in another location
            if not participant_data:
                if "participants" in frame:
                    participant_data = {str(p.get("id") or p.get("participantId")): p for p in frame["participants"]}
                elif "teams" in frame:
                    participant_data = {}
                    for team in frame["teams"]:
                        team_id = team.get("id")
                        for player in team.get("players", []):
                            pid = player.get("id") or player.get("participantId")
                            if pid:
                                # Ensure player has teamId for later use
                                player["teamId"] = team_id
                                participant_data[str(pid)] = player

            # Aggregate team level stats
            team_stats = {
                100: {"primary": 0, "secondary": 0},
                200: {"primary": 0, "secondary": 0},
                "team-blue": {"primary": 0, "secondary": 0},
                "team-red": {"primary": 0, "secondary": 0}
            }
            
            snapshot = {
                "timestamp": timestamp,
                "participantFrames": participant_data,
                **cum_stats
            }
            for pid, data in participant_data.items():
                if game == "valorant":
                    team_id = "team-blue" if str(pid).lower().startswith("blue") or (pid.isdigit() and int(pid) <= 5) else "team-red"
                    primary_val = data.get("credits", 0) or data.get("stats", {}).get("credits", 0)
                    secondary_val = data.get("loadoutValue", 0) or data.get("stats", {}).get("loadoutValue", 0)
                    
                    snapshot[f"p{pid}_credits"] = primary_val
                    snapshot[f"p{pid}_loadout"] = secondary_val
                else: # LoL
                    # Try to use teamId from data first
                    team_id = data.get("teamId")
                    if team_id is None:
                        try:
                            team_id = 100 if int(pid) <= 5 else 200
                        except:
                            team_id = 100
                            
                    primary_val = data.get("totalGold", 0) or data.get("stats", {}).get("gold", 0) or data.get("gold", 0)
                    secondary_val = data.get("xp", 0) or data.get("stats", {}).get("xp", 0)
                    
                    snapshot[f"p{pid}_gold"] = primary_val
                    snapshot[f"p{pid}_xp"] = secondary_val
                    snapshot[f"p{pid}_minionsKilled"] = data.get("minionsKilled", 0) or data.get("stats", {}).get("minionsKilled", 0)
                    snapshot[f"p{pid}_jungleMinionsKilled"] = data.get("jungleMinionsKilled", 0) or data.get("stats", {}).get("jungleMinionsKilled", 0)
                    snapshot[f"p{pid}_wardsPlaced"] = data.get("wardsPlaced", 0) or data.get("stats", {}).get("wardsPlaced", 0)

                if team_id in team_stats:
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
        
        frames = Normalizer._get_frames(timeline_data)
        
        # Look in frames (Standard LoL / Val structure)
        for frame in frames:
            for event in frame.get("events", []):
                if event_types is None or event.get("type") in event_types:
                    events.append(event)
        
        # Look in segments (GRID LoL structure)
        if "seriesState" in timeline_data:
            state = timeline_data["seriesState"]
            for game in state.get("games", []):
                for segment in game.get("segments", []):
                    # Events might be in segment["events"] or segment["payload"]["events"]
                    s_events = segment.get("events", [])
                    if not s_events and "payload" in segment and isinstance(segment["payload"], dict):
                        s_events = segment["payload"].get("events", [])
                    
                    for event in s_events:
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
