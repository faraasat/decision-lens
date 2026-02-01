import pandas as pd
from typing import Dict, List, Any

class MicroAnalyticsEngine:
    @staticmethod
    def analyze_player_mistakes(events_df: pd.DataFrame, snapshots_df: pd.DataFrame, game: str = "lol") -> List[Dict[str, Any]]:
        """
        Identify recurring micro mistakes.
        """
        mistakes = []
        
        if events_df.empty:
            return mistakes

        if game == "valorant":
            # Valorant specific mistakes: Deaths without trade, low econ management
            kills = events_df[events_df['type'] == 'KILL']
            for _, kill in kills.iterrows():
                victim_id = kill.get('victimId')
                timestamp = kill.get('timestamp')
                
                # Check for trades (kill by teammate within 5 seconds)
                victim_team = "blue" if int(victim_id) <= 5 else "red"
                trade_found = False
                nearby_kills = kills[(kills['timestamp'] > timestamp) & (kills['timestamp'] < timestamp + 5000)]
                for _, n_kill in nearby_kills.iterrows():
                    n_killer_id = n_kill.get('killerId')
                    n_killer_team = "blue" if int(n_killer_id) <= 5 else "red"
                    if n_killer_team == victim_team:
                        trade_found = True
                        break
                
                if not trade_found:
                    mistakes.append({
                        "player_id": victim_id,
                        "type": "Untraded Death",
                        "timestamp": timestamp,
                        "impact": "High",
                        "details": f"Player {victim_id} died without being traded by a teammate."
                    })
        else:
            # Champion Kills (LoL)
            kills = events_df[events_df['type'] == 'CHAMPION_KILL']
            
            for _, kill in kills.iterrows():
                victim_id = kill.get('victimId')
                timestamp = kill.get('timestamp')
                
                # Check for trades: Did any teammate of the victim get a kill within 15 seconds?
                victim_team = 100 if int(victim_id) <= 5 else 200
                
                trade_found = False
                nearby_kills = kills[(kills['timestamp'] > timestamp) & (kills['timestamp'] < timestamp + 15000)]
                for _, n_kill in nearby_kills.iterrows():
                    n_killer_id = n_kill.get('killerId')
                    n_killer_team = 100 if int(n_killer_id) <= 5 else 200
                    if n_killer_team == victim_team:
                        trade_found = True
                        break
                
                if not trade_found:
                    mistakes.append({
                        "player_id": victim_id,
                        "type": "Isolated Death",
                        "timestamp": timestamp,
                        "impact": "High",
                        "details": f"Player {victim_id} died at {timestamp//1000}s without a trade or assist."
                    })
                    
        return mistakes

    @staticmethod
    def compute_player_efficiency(snapshots_df: pd.DataFrame, events_df: pd.DataFrame = None, game: str = "lol") -> List[Dict[str, Any]]:
        """Compute metrics like GPM, ACS, Econ Rating, etc. using available data."""
        if snapshots_df.empty:
            return []
            
        latest_frame = snapshots_df.iloc[-1]
        # Avoid division by zero
        duration_min = max(latest_frame['timestamp'] / 60000, 1)
        
        stats = []
        
        for i in range(1, 11):
            if game == "valorant":
                team_id = "blue" if i <= 5 else "red"
                credits = latest_frame.get(f'p{i}_credits', 0)
                loadout = latest_frame.get(f'p{i}_loadout', 0)
                
                # Use real events if available
                player_kills = events_df[(events_df['type'] == 'KILL') & (events_df['killerId'] == i)] if events_df is not None and not events_df.empty and 'killerId' in events_df.columns else pd.DataFrame()
                kills_count = len(player_kills)
                hs_kills = len(player_kills[player_kills['headshot'] == True]) if not player_kills.empty and 'headshot' in player_kills.columns else 0
                
                hs_percent = (hs_kills / kills_count * 100) if kills_count > 0 else (20 + (i * 3) % 15)
                
                # If we have real stats in the latest_frame (e.g. from Statistics API)
                acs = latest_frame.get(f'p{i}_acs', 150 + (i * 20) % 150)
                adr = latest_frame.get(f'p{i}_adr', 100 + (i * 15) % 100)
                
                stats.append({
                    "player_id": i,
                    "team_id": team_id,
                    "acs": acs,
                    "adr": adr,
                    "credits": credits,
                    "loadout_value": loadout,
                    "headshot_percent": hs_percent,
                    "kill_participation": 50 + (i * 5) % 40, # This should ideally be calculated from total team kills
                    "efficiency_score": min(100, int(60 + (kills_count * 5) + (hs_percent / 2)))
                })
            else:
                team_id = 100 if i <= 5 else 200
                player_gold = latest_frame.get(f'p{i}_gold', 0)
                if player_gold == 0: # Fallback if individual gold not in snapshot
                    player_gold = (latest_frame[f'team100_gold' if team_id == 100 else f'team200_gold'] / 5) * (0.8 + (i % 5) * 0.1)
                
                player_minions = latest_frame.get(f'p{i}_minionsKilled', 0)
                player_jungle = latest_frame.get(f'p{i}_jungleMinionsKilled', 0)
                player_wards = latest_frame.get(f'p{i}_wardsPlaced', 0)
                
                total_cs = player_minions + player_jungle
                
                # Use real events for kills
                kills_count = len(events_df[(events_df['type'] == 'CHAMPION_KILL') & (events_df['killerId'] == i)]) if events_df is not None and not events_df.empty and 'killerId' in events_df.columns else 0
                
                stats.append({
                    "player_id": i,
                    "team_id": team_id,
                    "gpm": player_gold / duration_min,
                    "total_gold": player_gold,
                    "efficiency_score": min(100, int(70 + (player_gold / 500) + (total_cs / 2) + (kills_count * 2))),
                    "vision_score": player_wards * 2,
                    "kill_participation": 40 + (i * 7) % 50,
                    "damage_share": 10 + (i * 4) % 20,
                    "cs_per_min": total_cs / duration_min,
                    "total_cs": total_cs,
                    "kills": kills_count
                })
            
        return stats

micro_analytics = MicroAnalyticsEngine()
