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
        
        # Fallback: If very few frames found, try to synthesize a trend from stats
        if len(frames) < 2:
            logger.info(f"Only {len(frames)} frames found in timeline, checking stats for trend synthesis")
            stats = timeline_data.get("stats", {})
            stats_games = stats.get("games", []) if isinstance(stats, dict) else []
            
            if stats_games:
                latest = stats_games[-1]
                team_stats = latest.get("teamStats", [])
                
                blue_gold = 0
                red_gold = 0
                for ts in team_stats:
                    # Common blue team IDs/names
                    tid = str(ts.get("teamId"))
                    if tid in [100, "100", "blue", "team-blue", 340]:
                        blue_gold = ts.get("goldEarned", 0)
                    else:
                        red_gold = ts.get("goldEarned", 0)
                
                # Create multiple snapshots to show a trend
                raw_duration = latest.get("duration", 0)
                if isinstance(raw_duration, str) and "PT" in raw_duration:
                    import re
                    m = re.search(r'PT(?:(\d+)M)?(?:([\d.]+)S)?', raw_duration)
                    duration_secs = (float(m.group(1) or 0) * 60 + float(m.group(2) or 0)) if m else 1200
                else:
                    duration_secs = float(raw_duration or 1200)
                
                duration = duration_secs * 1000
                logger.info(f"Synthesizing trend from stats for {game} (Duration: {duration}ms)")
                
                # If we had one frame, preserve its timestamp if possible
                base_ts = frames[0].get("timestamp") or (duration * 0.5) if frames else (duration * 0.5)

                synthetic_frames = []
                num_points = 6
                for i in range(num_points):
                    progress = (i + 1) / num_points
                    # Add some non-linearity/variance to gold/xp
                    gold_progress = progress ** 1.2
                    
                    frame = {
                        "timestamp": duration * progress,
                        "gold_diff": (blue_gold - red_gold) * gold_progress,
                        "xp_diff": (blue_gold - red_gold) * gold_progress * 0.8,
                        "team100_gold": blue_gold * gold_progress + 500,
                        "team200_gold": red_gold * gold_progress + 500,
                        "dragons_diff": int(progress * 2) if blue_gold > red_gold else -int(progress * 2),
                        "towers_diff": int(progress * 3) if blue_gold > red_gold else -int(progress * 3),
                        "barons_diff": 0,
                        "team100_kills": int(progress * 10) if blue_gold > red_gold else int(progress * 5),
                        "team200_kills": int(progress * 10) if red_gold > blue_gold else int(progress * 5),
                        "participantFrames": {str(p.get("playerId")): p for p in latest.get("playerStats", [])}
                    }
                    synthetic_frames.append(frame)
                
                # If we had one real frame, merge it
                if frames:
                    # Sort by timestamp
                    frames = sorted(synthetic_frames + [frames[0]], key=lambda x: x['timestamp'])
                else:
                    frames = synthetic_frames
            elif frames:
                # We have at least one real frame, but let's make sure we have a trend
                pass
            else:
                # No stats and no frames. Create a baseline snapshot from metadata if possible.
                logger.info("No timeline or stats data found, creating baseline snapshot")
                metadata = timeline_data.get("metadata", {})
                teams = metadata.get("teams", [])
                
                baseline_frame = {
                    "timestamp": 0,
                    "gold_diff": 0,
                    "xp_diff": 0,
                    "team100_gold": 2500,
                    "team200_gold": 2500,
                    "dragons_diff": 0, "towers_diff": 0, "barons_diff": 0,
                    "team100_kills": 0, "team200_kills": 0,
                    "participantFrames": {}
                }
                
                for team in teams:
                    tid = team.get("id")
                    for p in team.get("roster", []):
                        pid = str(p.get("id"))
                        baseline_frame["participantFrames"][pid] = {
                            "teamId": tid,
                            "totalGold": 500,
                            "xp": 0,
                            "credits": 800,
                            "position": {"x": 0, "y": 0}
                        }
                frames = [baseline_frame]

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

                    def get_val(d, keys):
                        for k in keys:
                            v = d.get(k)
                            if v is not None:
                                if isinstance(v, (int, float)):
                                    return v
                                if isinstance(v, dict):
                                    # Try common subkeys
                                    for subk in ["total", "amount", "value", "current", "count", "netWorth", "money"]:
                                        subv = v.get(subk)
                                        if isinstance(subv, (int, float)):
                                            return subv
                                    # Last resort: first numeric value
                                    for subv in v.values():
                                        if isinstance(subv, (int, float)):
                                            return subv
                                    return 0
                        return 0

                    primary_val = get_val(data, ["credits", "money", "netWorth"]) or get_val(data.get("stats", {}), ["credits"])
                    secondary_val = get_val(data, ["loadoutValue"]) or get_val(data.get("stats", {}), ["loadoutValue"])
                    
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

                    def get_val(d, keys):
                        for k in keys:
                            v = d.get(k)
                            if v is not None:
                                if isinstance(v, (int, float)):
                                    return v
                                if isinstance(v, dict):
                                    for subk in ["total", "amount", "value", "current", "count", "netWorth", "money"]:
                                        subv = v.get(subk)
                                        if isinstance(subv, (int, float)):
                                            return subv
                                    for subv in v.values():
                                        if isinstance(subv, (int, float)):
                                            return subv
                                    return 0
                        return 0
                            
                    primary_val = get_val(data, ["totalGold", "netWorth", "money", "gold"]) or get_val(data.get("stats", {}), ["gold"])
                    secondary_val = get_val(data, ["xp", "experiencePoints"]) or get_val(data.get("stats", {}), ["xp"])
                    
                    snapshot[f"p{pid}_gold"] = primary_val
                    snapshot[f"p{pid}_xp"] = secondary_val
                    snapshot[f"p{pid}_minionsKilled"] = get_val(data, ["minionsKilled", "unitKills"]) or get_val(data.get("stats", {}), ["minionsKilled"])
                    snapshot[f"p{pid}_jungleMinionsKilled"] = get_val(data, ["jungleMinionsKilled"]) or get_val(data.get("stats", {}), ["jungleMinionsKilled"])
                    snapshot[f"p{pid}_wardsPlaced"] = get_val(data, ["wardsPlaced", "visionScore"]) or get_val(data.get("stats", {}), ["wardsPlaced"])
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
            logger.info("No events found in timeline, checking games and stats for fallback events")
            
            # 1. Try to find summary data in timeline 'games'
            state = timeline_data.get("seriesState") or (timeline_data if "games" in timeline_data else {})
            games_list = state.get("games", [])
            
            # 2. Try 'stats' as alternative source
            stats = timeline_data.get("stats", {})
            stats_games = stats.get("games", []) if isinstance(stats, dict) else []
            
            # Pick best summary source
            summary_game = None
            if games_list: summary_game = games_list[-1]
            elif stats_games: summary_game = stats_games[-1]
            
            if summary_game:
                # Safe duration extraction
                raw_duration = summary_game.get("duration", 0)
                if isinstance(raw_duration, str) and "PT" in raw_duration:
                    import re
                    m = re.search(r'PT(?:(\d+)M)?(?:([\d.]+)S)?', raw_duration)
                    duration_secs = (float(m.group(1) or 0) * 60 + float(m.group(2) or 0)) if m else 1200
                else:
                    duration_secs = float(raw_duration or 1200)
                
                duration = duration_secs * 1000
                metadata = timeline_data.get("metadata", {})
                game = metadata.get("game", "lol")
                
                # Extract player summaries
                player_summaries = []
                if "teams" in summary_game:
                    for team in summary_game["teams"]:
                        team_id = team.get("id")
                        for p in team.get("players", []):
                            p["teamId"] = team_id
                            player_summaries.append(p)
                elif "playerStats" in summary_game:
                    player_summaries = summary_game["playerStats"]
                
                team100_pids = [str(p.get("playerId") or p.get("id")) for p in player_summaries if str(p.get("teamId")) in ["100", "blue", "team-blue", "340"]]
                team200_pids = [str(p.get("playerId") or p.get("id")) for p in player_summaries if str(p.get("teamId")) not in ["100", "blue", "team-blue", "340"]]
                
                # Synthesize kills
                for p in player_summaries:
                    pid = str(p.get("playerId") or p.get("id"))
                    kills = p.get("kills", 0)
                    tid = str(p.get("teamId"))
                    is_team100 = tid in ["100", "blue", "team-blue", "340"]
                    opponents = team200_pids if is_team100 else team100_pids
                    
                    for i in range(kills):
                        victim = opponents[i % len(opponents)] if opponents else "0"
                        events.append({
                            "type": "CHAMPION_KILL" if game == "lol" else "KILL",
                            "timestamp": duration * (0.1 + 0.8 * (i/max(kills, 1))),
                            "killerId": pid,
                            "victimId": victim,
                            "headshot": (i % 3 == 0) if game == "valorant" else False
                        })
                
                # Synthesize objectives
                team_summaries = summary_game.get("teams") or summary_game.get("teamStats") or []
                for ts in team_summaries:
                    tid = ts.get("teamId") or ts.get("id")
                    
                    # Towers/Structures
                    num_towers = ts.get("towersDestroyed", 0) or ts.get("structuresDestroyed", 0)
                    for i in range(num_towers):
                        events.append({
                            "type": "BUILDING_KILL",
                            "buildingType": "TOWER",
                            "timestamp": duration * (0.2 + 0.7 * (i/max(num_towers, 1))),
                            "teamId": tid
                        })
                        
                    # Dragons/Spikes/Elite Monsters
                    num_obj = ts.get("dragonsKilled", 0) or ts.get("baronsKilled", 0) or (ts.get("roundsWon", 0) // 3 if game == "valorant" else 0)
                    for i in range(num_obj):
                        events.append({
                            "type": "ELITE_MONSTER_KILL" if game == "lol" else "SPIKE_PLANTED",
                            "monsterType": "DRAGON" if i % 2 == 0 else "BARON",
                            "timestamp": duration * (0.3 + 0.6 * (i/max(num_obj, 1))),
                            "teamId": tid,
                            "planterId": team100_pids[0] if str(tid) in ["100", "blue"] and team100_pids else team200_pids[0] if team200_pids else "0"
                        })

        if not events:
            return pd.DataFrame(columns=["type", "timestamp", "killerId", "victimId", "headshot"])
            
        return pd.DataFrame(events)

# Singleton instance
normalizer = Normalizer()
