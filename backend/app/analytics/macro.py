import pandas as pd
from typing import Dict, List, Any

class MacroAnalyticsEngine:
    @staticmethod
    def identify_strategic_inflections(snapshots_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Identify moments where win probability or gold lead shifted significantly.
        """
        inflections = []
        if snapshots_df.empty:
            return inflections
            
        # Calculate gold diff delta
        # Since snapshots might be every 1 min, diff() is gold change per minute
        snapshots_df['gold_diff_delta'] = snapshots_df['gold_diff'].diff()
        
        # Threshold for a "significant" shift (e.g., 800 gold in a minute)
        threshold = 800
        
        significant_shifts = snapshots_df[snapshots_df['gold_diff_delta'].abs() > threshold]
        
        for _, shift in significant_shifts.iterrows():
            direction = "Team 100 Advantage" if shift['gold_diff_delta'] > 0 else "Team 200 Advantage"
            inflections.append({
                "timestamp": shift['timestamp'],
                "type": "Gold Swing",
                "magnitude": shift['gold_diff_delta'],
                "description": f"Significant gold swing of {abs(shift['gold_diff_delta']):.0f} towards {direction}"
            })
            
        return inflections

    @staticmethod
    def evaluate_objective_control(events_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Analyze dragon/baron/tower control efficiency."""
        objectives = []
        if events_df.empty:
            return objectives
            
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

macro_analytics = MacroAnalyticsEngine()
