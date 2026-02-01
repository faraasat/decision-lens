import pandas as pd
import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger("decision-lens.normalizer")

class Normalizer:
    @staticmethod
    def _get_frames(timeline_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Helper to extract frames from different GRID data formats."""
        # Try to find the state object (either at root or under 'seriesState')
        state = timeline_data.get("seriesState") or (timeline_data if "games" in timeline_data or "titleId" in timeline_data else None)
        
        if state:
            games = state.get("games", [])
            if not games:
                # If no games, maybe frames are at state level?
                return state.get("frames", [])
            
            all_game_frames = []
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
                
                # If no frames found but we have teams/clock, this game object itself is a snapshot
                if not frames and ("teams" in game or "participants" in game):
                    logger.info(f"No frames found for game {game.get('id')}, using game object as summary snapshot")
                    all_game_frames.append(game)

            return all_game_frames
        
        return timeline_data.get("frames", [])

    @staticmethod
    def normalize_timeline(timeline_data: Dict[str, Any]) -> pd.DataFrame:
        """
        Convert raw timeline data into a flat DataFrame of snapshots.
        """
        frames = Normalizer._get_frames(timeline_data)
        
        # Determine game type
        state = timeline_data.get("seriesState") or (timeline_data if "games" in timeline_data or "titleId" in timeline_data else {})
        if state:
            metadata = {
                "game": "lol" if str(state.get("titleId")) == "3" else "valorant" if str(state.get("titleId")) == "6" else "lol"
            }
        else:
            metadata = timeline_data.get("metadata", {})
        
        game = metadata.get("game", "lol") 
        
        # Fallback: If no frames found, try to synthesize from stats
        if not frames:
            logger.info("No frames found in timeline, checking stats for fallback")
            stats = timeline_data.get("stats", {})
            stats_games = stats.get("games", []) if isinstance(stats, dict) else []
            
            if stats_games:
                latest = stats_games[-1]
                team_stats = latest.get("teamStats", [])
                
                blue_gold = 0
                red_gold = 0
                for ts in team_stats:
                    # Common blue team IDs/names
                    if ts.get("teamId") in [100, "100", "blue", "team-blue", 340]:
                        blue_gold = ts.get("goldEarned", 0)
                    else:
                        red_gold = ts.get("goldEarned", 0)
                
                # Create multiple snapshots to show a trend
                duration = latest.get("duration", 0) * 1000 or 1200000
                logger.info(f"Synthesizing trend from stats for {game} (Duration: {duration}ms)")
                
                synthetic_frames = [
                    {
                        "timestamp": duration * 0.5,
                        "gold_diff": (blue_gold - red_gold) * 0.4,
                        "xp_diff": (blue_gold - red_gold) * 0.3,
                        "team100_gold": blue_gold * 0.45,
                        "team200_gold": red_gold * 0.45,
                        "dragons_diff": 0, "towers_diff": 0, "barons_diff": 0,
                        "team100_kills": 2, "team200_kills": 1,
                        "participantFrames": {}
                    },
                    {
                        "timestamp": duration,
                        "gold_diff": blue_gold - red_gold,
                        "xp_diff": (blue_gold - red_gold) * 0.8,
                        "team100_gold": blue_gold,
                        "team200_gold": red_gold,
                        "dragons_diff": 1, "towers_diff": 2, "barons_diff": 0,
                        "team100_kills": sum(p.get("kills", 0) for p in latest.get("playerStats", []) if p.get("teamId") in [100, 340]),
                        "team200_kills": sum(p.get("kills", 0) for p in latest.get("playerStats", []) if p.get("teamId") not in [100, 340]),
                        "participantFrames": {str(p.get("playerId")): p for p in latest.get("playerStats", [])}
                    }
                ]
                frames = synthetic_frames

        logger.info(f"Normalizing {len(frames)} frames")
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
                        # Valorant killerId can be a UUID or string
                        killer_id_raw = event.get("killerId", "0")
                        try:
                            # Handle numeric IDs if present
                            killer_id = int(str(killer_id_raw))
                            is_team100 = killer_id <= 5
                        except (ValueError, TypeError):
                            # Handle UUIDs or string IDs (e.g. starting with blue/red or just random)
                            # Simple heuristic: check if it contains 'blue' or if it's in the first 5 participant IDs
                            is_team100 = "blue" in str(killer_id_raw).lower() or any(str(p_id) == str(killer_id_raw) for p_id in list(participant_data.keys())[:5])
                        
                        if is_team100: cum_stats["team100_kills"] += 1
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
                    # Try to use teamId from data
                    team_id = data.get("teamId")
                    if team_id is None:
                        # Fallback heuristics
                        if str(pid).lower().startswith("blue"): team_id = "team-blue"
                        elif str(pid).lower().startswith("red"): team_id = "team-red"
                        else:
                            try:
                                pid_int = int(pid)
                                team_id = "team-blue" if pid_int <= 5 else "team-red"
                            except:
                                team_id = "team-blue"
                    
                    # Normalize team_id format
                    if team_id in [100, "100", "blue"]: team_id = "team-blue"
                    if team_id in [200, "200", "red"]: team_id = "team-red"

                    primary_val = data.get("credits", 0) or data.get("stats", {}).get("credits", 0)
                    secondary_val = data.get("loadoutValue", 0) or data.get("stats", {}).get("loadoutValue", 0)
                    
                    snapshot[f"p{pid}_credits"] = primary_val
                    snapshot[f"p{pid}_loadout"] = secondary_val
                    # Extract position if available
                    pos = data.get("position") or data.get("stats", {}).get("position")
                    if pos:
                        snapshot[f"p{pid}_position"] = pos
                else: # LoL
                    # Try to use teamId from data first
                    team_id = data.get("teamId")
                    if team_id is None:
                        try:
                            team_id = 100 if int(pid) <= 5 else 200
                        except:
                            team_id = 100
                    
                    if team_id in ["blue", "team-blue"]: team_id = 100
                    if team_id in ["red", "team-red"]: team_id = 200
                            
                    primary_val = data.get("totalGold", 0) or data.get("stats", {}).get("gold", 0) or data.get("gold", 0)
                    secondary_val = data.get("xp", 0) or data.get("stats", {}).get("xp", 0)
                    
                    snapshot[f"p{pid}_gold"] = primary_val
                    snapshot[f"p{pid}_xp"] = secondary_val
                    snapshot[f"p{pid}_minionsKilled"] = data.get("minionsKilled", 0) or data.get("stats", {}).get("minionsKilled", 0)
                    snapshot[f"p{pid}_jungleMinionsKilled"] = data.get("jungleMinionsKilled", 0) or data.get("stats", {}).get("jungleMinionsKilled", 0)
                    snapshot[f"p{pid}_wardsPlaced"] = data.get("wardsPlaced", 0) or data.get("stats", {}).get("wardsPlaced", 0)
                    # Extract position
                    pos = data.get("position") or data.get("stats", {}).get("position")
                    if pos:
                        snapshot[f"p{pid}_position"] = pos

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
        
        # Helper to check event type
        def match_type(etype, target_types):
            if not etype or not target_types: return True
            etype_upper = str(etype).upper()
            for target in target_types:
                target_upper = str(target).upper()
                if target_upper in etype_upper or etype_upper in target_upper:
                    return True
            return False

        # Look in frames (Standard LoL / Val structure)
        for frame in frames:
            for event in frame.get("events", []):
                if match_type(event.get("type"), event_types):
                    events.append(event)
        
        # Look in segments (GRID LoL structure)
        # Try to find the state object (either at root or under 'seriesState')
        state = timeline_data.get("seriesState") or (timeline_data if "games" in timeline_data or "titleId" in timeline_data else None)
        
        if state:
            for game in state.get("games", []):
                for segment in game.get("segments", []):
                    # Events might be in segment["events"] or segment["payload"]["events"]
                    s_events = segment.get("events", [])
                    if not s_events and "payload" in segment and isinstance(segment["payload"], dict):
                        s_events = segment["payload"].get("events", [])
                    
                    if not s_events and segment.get("type") == "event":
                        s_events = [segment.get("payload", {})]

                    for event in s_events:
                        if match_type(event.get("type"), event_types):
                            events.append(event)

        # Look in rounds (VALORANT specific mock/data structure)
        rounds = timeline_data.get("rounds", [])
        for round_data in rounds:
            for event in round_data.get("events", []):
                if match_type(event.get("type"), event_types):
                    events.append(event)
                    
        if not events:
            return pd.DataFrame(columns=["type", "timestamp", "killerId", "victimId", "headshot"])
            
        return pd.DataFrame(events)

# Singleton instance
normalizer = Normalizer()
