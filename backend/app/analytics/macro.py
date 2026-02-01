import pandas as pd
from typing import Dict, List, Any

class MacroAnalyticsEngine:
    @staticmethod
    def identify_strategic_inflections(snapshots_df: pd.DataFrame, game: str = "lol", events_df: pd.DataFrame = None) -> List[Dict[str, Any]]:
        """
        Identify moments where win probability, gold lead, or objectives shifted significantly.
        """
        inflections = []
        if snapshots_df.empty:
            return inflections
            
        # 1. Gold diff delta
        snapshots_df['gold_diff_delta'] = snapshots_df['gold_diff'].diff()
        
        # Threshold for a "significant" shift
        threshold = 1000 if game == "valorant" else 500
        # Lower threshold if we have very few snapshots to ensure we show SOMETHING
        if len(snapshots_df) < 10:
            threshold = threshold // 2
        
        significant_shifts = snapshots_df[snapshots_df['gold_diff_delta'].abs() > threshold]
        
        for _, shift in significant_shifts.iterrows():
            direction = "Team Blue" if shift['gold_diff_delta'] > 0 else "Team Red"
            inflections.append({
                "timestamp": shift['timestamp'],
                "type": "Economy Swing" if game == "valorant" else "Gold Swing",
                "magnitude": shift['gold_diff_delta'],
                "description": f"Significant {('econ' if game == 'valorant' else 'gold')} swing towards {direction}"
            })
        
        # 2. Objective-based inflections
        if events_df is not None and not events_df.empty:
            if game == "lol":
                # Significant LoL objectives
                obj_events = events_df[events_df['type'].isin(['ELITE_MONSTER_KILL', 'BUILDING_KILL'])]
                for _, event in obj_events.iterrows():
                    etype = event.get('monsterType') or event.get('buildingType') or event.get('type')
                    if etype in ['BARON', 'DRAGON', 'INHIBITOR', 'TOWER']:
                        team_id = event.get('teamId')
                        team_label = "Blue" if str(team_id) in ["100", "blue", "team-blue"] else "Red"
                        inflections.append({
                            "timestamp": event.get('timestamp'),
                            "type": "Objective Take",
                            "description": f"{etype} secured by Team {team_label}"
                        })
            elif game == "valorant":
                # Significant Valorant events
                val_events = events_df[events_df['type'].isin(['SPIKE_PLANTED', 'SPIKE_DEFUSED', 'ROUND_END'])]
                for _, event in val_events.iterrows():
                    etype = event.get('type')
                    inflections.append({
                        "timestamp": event.get('timestamp'),
                        "type": "Tactical Event",
                        "description": f"Critical {etype.replace('_', ' ').lower()} observed"
                    })
        
        # 3. Baseline fallback if still empty
        if not inflections:
            inflections.append({
                "timestamp": 0,
                "type": "Strategic Baseline",
                "description": f"Analyzing initial {game} team compositions and positioning."
            })
            if not snapshots_df.empty:
                last_snap = snapshots_df.iloc[-1]
                lead_team = "Blue" if last_snap['gold_diff'] > 0 else "Red"
                inflections.append({
                    "timestamp": last_snap['timestamp'],
                    "type": "Current Momentum",
                    "description": f"Overall momentum favors Team {lead_team} based on resource accumulation."
                })
            
        return sorted(inflections, key=lambda x: x['timestamp'])

    @staticmethod
    def evaluate_objective_control(events_df: pd.DataFrame, game: str = "lol") -> List[Dict[str, Any]]:
        """Analyze objectives (Towers/Dragons for LoL, Spike for Val)."""
        objectives = []
        if events_df.empty:
            return objectives
            
        if game == "valorant":
            # Better Valorant objective mapping
            obj_events = events_df[events_df['type'].str.contains('SPIKE', case=False, na=False)]
            for _, event in obj_events.iterrows():
                objectives.append({
                    "timestamp": event.get('timestamp'),
                    "type": event.get('type'),
                    "site": event.get('site', 'Unknown'),
                    "team_id": "blue" if event.get('planterId', '').startswith('blue') or event.get('defuserId', '').startswith('blue') else "red",
                    "player_id": event.get('planterId') or event.get('defuserId')
                })
        else:
            # Better LoL objective mapping
            obj_events = events_df[events_df['type'].isin(['ELITE_MONSTER_KILL', 'BUILDING_KILL', 'monsterKilled', 'buildingKilled'])]
            for _, event in obj_events.iterrows():
                obj_type = event.get('monsterType') or event.get('buildingType') or event.get('type')
                team_id = event.get('teamId')
                if team_id is None:
                    # Try to infer from killerId
                    kid = str(event.get('killerId', '0'))
                    team_id = 100 if kid.isdigit() and int(kid) <= 5 else 200

                objectives.append({
                    "timestamp": event.get('timestamp'),
                    "type": str(obj_type).upper(),
                    "team_id": team_id,
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
            
            draft_lower = [a.lower() for a in draft]
            
            if game == "valorant":
                # Check for roles (Simplified)
                if any(a in draft_lower for a in ["jett", "raze", "neon"]): score += 5 # Entry
                if any(a in draft_lower for a in ["omen", "brimstone", "astra", "viper"]): score += 5 # Smokes
                if any(a in draft_lower for a in ["killjoy", "cypher", "sage"]): score += 5 # Sentinel
                
                # Known combos
                if "viper" in draft_lower and "astra" in draft_lower: score += 5 # Double controller
                if "jett" in draft_lower and "sova" in draft_lower: score += 5 # Classic combo
            else:
                # LoL archetypes
                if any(a in draft_lower for a in ["ornn", "malphite", "sejuani"]): score += 5 # Tank
                if any(a in draft_lower for a in ["azir", "kassadin", "kayle", "jinx"]): score += 5 # Scaling
                
                # Synergies
                if "yasuo" in draft_lower and any(a in draft_lower for a in ["gragas", "malphite", "diana"]): score += 10 # Wombo combo
                if "lucian" in draft_lower and "nami" in draft_lower: score += 10 # Strong lane
            
            # Determine power spike based on composition
            spike = "Balanced"
            if game == "lol":
                if any(a in draft_lower for a in ["azir", "kassadin", "jinx"]): spike = "Late Game"
                elif any(a in draft_lower for a in ["lee sin", "renekton", "lucian"]): spike = "Early Game"
                else: spike = "Mid Game"
            else:
                spike = "Late Round" if "killjoy" in draft_lower or "cypher" in draft_lower else "Early Aggression"

            synergy[str(team_id)] = {
                "team_name": team.get("name"),
                "synergy_score": min(100, score),
                "power_spike": spike,
                "win_rate_prediction": 0.50 + (score - 80) / 100
            }
        return synergy

macro_analytics = MacroAnalyticsEngine()
