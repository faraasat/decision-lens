import pandas as pd
from typing import Dict, List, Any

class MacroAnalyticsEngine:
    @staticmethod
    def identify_strategic_inflections(snapshots_df: pd.DataFrame, game: str = "lol") -> List[Dict[str, Any]]:
        """
        Identify moments where win probability or gold lead shifted significantly.
        """
        inflections = []
        if snapshots_df.empty:
            return inflections
            
        # Calculate gold diff delta
        snapshots_df['gold_diff_delta'] = snapshots_df['gold_diff'].diff()
        
        # Threshold for a "significant" shift
        threshold = 1500 if game == "valorant" else 800
        
        significant_shifts = snapshots_df[snapshots_df['gold_diff_delta'].abs() > threshold]
        
        for _, shift in significant_shifts.iterrows():
            direction = "Team Blue" if shift['gold_diff_delta'] > 0 else "Team Red"
            inflections.append({
                "timestamp": shift['timestamp'],
                "type": "Economy Swing" if game == "valorant" else "Gold Swing",
                "magnitude": shift['gold_diff_delta'],
                "description": f"Significant {('econ' if game == 'valorant' else 'gold')} swing towards {direction}"
            })
            
        return inflections

    @staticmethod
    def evaluate_objective_control(events_df: pd.DataFrame, game: str = "lol") -> List[Dict[str, Any]]:
        """Analyze objectives (Towers/Dragons for LoL, Spike for Val)."""
        objectives = []
        if events_df.empty:
            return objectives
            
        if game == "valorant":
            obj_events = events_df[events_df['type'].isin(['SPIKE_PLANTED', 'SPIKE_DEFUSED', 'SPIKE_EXPLODED'])]
            for _, event in obj_events.iterrows():
                objectives.append({
                    "timestamp": event.get('timestamp'),
                    "type": event.get('type'),
                    "site": event.get('site'),
                    "player_id": event.get('planterId') or event.get('defuserId')
                })
        else:
            obj_events = events_df[events_df['type'].isin(['ELITE_MONSTER_KILL', 'BUILDING_KILL'])]
            for _, event in obj_events.iterrows():
                obj_type = event.get('monsterType') or event.get('buildingType')
                objectives.append({
                    "timestamp": event.get('timestamp'),
                    "type": obj_type,
                    "team_id": event.get('teamId'),
                    "killer_id": event.get('killerId')
                })
            
        return objectives

    @staticmethod
    def analyze_draft_synergy(metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate draft synergy and power spikes."""
        teams = metadata.get("teams", [])
        game = metadata.get("game", "lol")
        if not teams:
            return {}
            
        synergy = {}
        for team in teams:
            team_id = team.get("id")
            draft = team.get("draft", [])
            
            score = 75
            if game == "valorant":
                if "Jett" in draft and "Omen" in draft: score += 10
                if "Killjoy" in draft: score += 5 # Good defense
            else:
                if "Vi" in draft and "Azir" in draft: score += 15 
                if "Jayce" in draft and "Lee Sin" in draft: score += 10
            
            synergy[str(team_id)] = {
                "team_name": team.get("name"),
                "synergy_score": score,
                "power_spike": "Late Round" if game == "valorant" else ("Mid Game" if team_id == 100 else "Early Game"),
                "win_rate_prediction": 0.50 + (score - 75) / 100
            }
        return synergy

macro_analytics = MacroAnalyticsEngine()
