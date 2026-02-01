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
        """Analyze draft synergy based on composition patterns."""
        teams = metadata.get("teams", [])
        game = metadata.get("game", "lol")
        if not teams:
            return {}
            
        synergy = {}
        for team in teams:
            team_id = team.get("id")
            draft = team.get("draft", [])
            
            # Base synergy from various archetypes
            score = 70 + (len(draft) * 2) # Base score depends on completed draft
            
            if game == "valorant":
                # Check for roles (Simplified)
                if any(agent in ["Jett", "Raze", "Neon"] for agent in draft): score += 5 # Entry
                if any(agent in ["Omen", "Brimstone", "Astra", "Viper"] for agent in draft): score += 5 # Smokes
                if any(agent in ["Killjoy", "Cypher", "Sage"] for agent in draft): score += 5 # Sentinel
                
                # Known combos
                if "Viper" in draft and "Astra" in draft: score += 5 # Double controller
                if "Jett" in draft and "Sova" in draft: score += 5 # Classic combo
            else:
                # LoL archetypes
                if any(hero in ["Ornn", "Malphite", "Sejuani"] for hero in draft): score += 5 # Tank
                if any(hero in ["Azir", "Kassadin", "Kayle", "Jinx"] for hero in draft): score += 5 # Scaling
                
                # Synergies
                if "Yasuo" in draft and any(h in ["Gragas", "Malphite", "Diana"] for h in draft): score += 10 # Wombo combo
                if "Lucian" in draft and "Nami" in draft: score += 10 # Strong lane
            
            # Determine power spike based on composition
            spike = "Balanced"
            if game == "lol":
                if any(h in ["Azir", "Kassadin", "Jinx"] for h in draft): spike = "Late Game"
                elif any(h in ["Lee Sin", "Renekton", "Lucian"] for hero in draft): spike = "Early Game"
                else: spike = "Mid Game"
            else:
                spike = "Late Round" if "Killjoy" in draft or "Cypher" in draft else "Early Aggression"

            synergy[str(team_id)] = {
                "team_name": team.get("name"),
                "synergy_score": min(100, score),
                "power_spike": spike,
                "win_rate_prediction": 0.50 + (score - 80) / 100
            }
        return synergy

macro_analytics = MacroAnalyticsEngine()
