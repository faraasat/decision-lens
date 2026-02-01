import pandas as pd
from typing import Dict, List, Any

class MicroAnalyticsEngine:
    @staticmethod
    def analyze_player_mistakes(events_df: pd.DataFrame, snapshots_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Identify recurring micro mistakes.
        Example: Deaths without KAST, isolated deaths.
        """
        mistakes = []
        
        if events_df.empty:
            return mistakes

        # Champion Kills
        kills = events_df[events_df['type'] == 'CHAMPION_KILL']
        
        for _, kill in kills.iterrows():
            victim_id = kill.get('victimId')
            killer_id = kill.get('killerId')
            assisting_participants = kill.get('assistingParticipantIds', [])
            timestamp = kill.get('timestamp')
            
            # Isolated Death Logic:
            # 1. Victim had no assisting teammates in their own death (wait, that's not right for victim)
            # 2. Re-read: "C9 loses nearly 4 out of 5 rounds when OXY dies 'for free' (without a KAST)"
            # In LoL, if you die and your team gets nothing back, it's an isolated death.
            
            # Check for trades: Did any teammate of the victim get a kill within 15 seconds?
            victim_team = 100 if victim_id <= 5 else 200
            
            trade_found = False
            nearby_kills = kills[(kills['timestamp'] > timestamp) & (kills['timestamp'] < timestamp + 15000)]
            for _, n_kill in nearby_kills.iterrows():
                n_killer_id = n_kill.get('killerId')
                n_killer_team = 100 if n_killer_id <= 5 else 200
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
    def compute_player_efficiency(snapshots_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Compute metrics like Gold Per Minute (GPM), XP Per Minute, etc."""
        if snapshots_df.empty:
            return []
            
        latest_frame = snapshots_df.iloc[-1]
        duration_min = max(latest_frame['timestamp'] / 60000, 1)
        
        stats = []
        # In a real scenario, we'd have participant-level snapshots.
        # Since we only have team-level in snapshots_df currently, 
        # let's simulate individual stats based on team gold for the demo.
        # Ideally, normalizer should keep participant frames.
        
        for i in range(1, 11):
            team_id = 100 if i <= 5 else 200
            team_gold = latest_frame[f'team{team_id}_gold']
            # Distribute team gold with some variance for demo
            player_gold = (team_gold / 5) * (0.8 + (i % 5) * 0.1)
            
            stats.append({
                "player_id": i,
                "team_id": team_id,
                "gpm": player_gold / duration_min,
                "total_gold": player_gold,
                "efficiency_score": 70 + (i * 2) % 25, # Mock score
                "vision_score": 10 + (i * 3) % 40,
                "kill_participation": 40 + (i * 7) % 50,
                "damage_share": 10 + (i * 4) % 20,
                "cs_per_min": 5 + (i * 0.5) % 5 if i % 5 != 0 else 1.2 # Support has low CS
            })
            
        return stats

micro_analytics = MicroAnalyticsEngine()
