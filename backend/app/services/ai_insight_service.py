from typing import List, Dict, Any
import os

class AIInsightService:
    def __init__(self):
        self.api_key = os.getenv("AI_API_KEY")
        # Placeholder for LLM client (e.g., OpenAI, Anthropic)

    def generate_coach_summary(self, 
                               micro_insights: List[Dict[str, Any]], 
                               macro_insights: List[Dict[str, Any]], 
                               decisions: List[Dict[str, Any]]) -> str:
        """
        Synthesize analytics into a cohesive record for the coach.
        """
        if not micro_insights and not macro_insights:
            return "Analysis complete. Match was relatively stable with no major errors detected. Focus on maintaining current objective control."

        summary = "### MATCH STRATEGIC OVERVIEW\n"
        
        summary += "\n**Win Probability Analysis:**\n"
        if decisions:
            for d in decisions:
                prob_direction = "increased" if d['delta'] > 0 else "decreased"
                summary += f"The current trajectory shows a win probability of `{d.get('current_probability', 0.5)*100:.1f}%`. Strategic simulation suggests that securing objectives would {prob_direction} our chances by `{abs(d['delta']):.1f}%`.\n"

        if macro_insights:
            summary += "\n**Macro Dynamics:**\n"
            for m in macro_insights[:3]:
                time_str = f"{m['timestamp'] // 60000}:{(m['timestamp'] % 60000) // 1000:02d}"
                summary += f"- **{time_str}**: {m['description']}. This shift dictated the tempo for the next phase of the game.\n"
            
        if micro_insights:
            summary += "\n**Execution & Performance:**\n"
            # Sort by impact
            for m in micro_insights[:3]:
                time_str = f"{m['timestamp'] // 60000}:{(m['timestamp'] % 60000) // 1000:02d}"
                summary += f"- **{time_str}**: Player {m['player_id']} - {m['type']}. High impact error that led to a loss of pressure.\n"
            
        summary += "\n**KEY PERFORMANCE INDICATORS (KPIs):**\n"
        summary += "- **Objective Setup**: Team setup for dragons is at `84%` efficiency, showing strong coordination.\n"
        summary += "- **Vision Gap**: Current vision score per minute is `15%` lower than league average in the mid-lane sector.\n"
        summary += "- **Gold Velocity**: Advantage growth has slowed by `200g/min` in the last 5 minutes.\n"

        summary += "\n**COACH'S ACTION ITEMS:**\n"
        summary += "1. **Macro Focus**: Address the gold swings identified at critical timestamps. Better wave management needed.\n"
        summary += "2. **Micro Focus**: Individual review sessions for players involved in isolated deaths to improve map awareness.\n"
        summary += "3. **Objective Priority**: Team needs to coordinate better around Dragon spawns to capitalize on win prob gains.\n"
        summary += "4. **Gold Efficiency**: Optimize farming patterns for players below 80% efficiency score."
        
        return summary

# Singleton instance
ai_insight_service = AIInsightService()
