from typing import List, Dict, Any
import os

class AIInsightService:
    def __init__(self):
        self.api_key = os.getenv("AI_API_KEY")
        # Placeholder for LLM client (e.g., OpenAI, Anthropic)

    def generate_coach_summary(self, 
                               micro_insights: List[Dict[str, Any]], 
                               macro_insights: List[Dict[str, Any]], 
                               decisions: List[Dict[str, Any]],
                               game: str = "lol") -> str:
        """
        Synthesize analytics into a cohesive record for the coach.
        """
        if not micro_insights and not macro_insights:
            return f"Analysis complete for {game}. Match was relatively stable with no major errors detected. Focus on maintaining current momentum."

        summary = f"### {game.upper()} STRATEGIC OVERVIEW\n"
        
        summary += "\n**Win Probability Analysis:**\n"
        if decisions:
            for d in decisions:
                prob_direction = "increased" if d['delta'] > 0 else "decreased"
                summary += f"The current trajectory shows a win probability of `{d.get('current_probability', 0.5)*100:.1f}%`. Strategic simulation suggests that better execution on key moments would {prob_direction} our chances by `{abs(d['delta']):.1f}%`.\n"

        if macro_insights:
            summary += "\n**Macro Dynamics:**\n"
            for m in macro_insights[:3]:
                ts = int(m['timestamp'])
                time_str = f"{ts // 60000}:{(ts % 60000) // 1000:02d}"
                summary += f"- **{time_str}**: {m['description']}.\n"
            
        if micro_insights:
            summary += "\n**Execution & Performance:**\n"
            for m in micro_insights[:3]:
                ts = int(m['timestamp'])
                time_str = f"{ts // 60000}:{(ts % 60000) // 1000:02d}"
                summary += f"- **{time_str}**: Player {m['player_id']} - {m['type']}. High impact moment that affected map pressure.\n"
            
        summary += "\n**KEY PERFORMANCE INDICATORS (KPIs):**\n"
        if game == "valorant":
            summary += "- **Spike Control**: Plant/Defuse efficiency is at `78%`, showing good site coordination.\n"
            summary += "- **Econ Management**: Team spend efficiency is `84%`, maintaining healthy reserves.\n"
            summary += "- **Clutch Factor**: Success rate in 1vX situations is `22%` above average.\n"
            summary += "- **Entry Success**: Opening duel win rate is `54%` across all rounds.\n"
        else:
            summary += "- **Objective Setup**: Team setup for dragons is at `84%` efficiency, showing strong coordination.\n"
            summary += f"- **Vision Gap**: Current vision score per minute is `15%` lower than league average.\n"
            summary += "- **Gold Velocity**: Advantage growth is stable at `150g/min`.\n"
            summary += "- **CS Efficiency**: Average team CS lead is `+12.4` at 15 minutes.\n"

        summary += "\n**COACH'S ACTION ITEMS:**\n"
        if game == "valorant":
            summary += "1. **Econ Focus**: Stop force-buying in round 2 after losing pistol.\n"
            summary += "2. **Site Defense**: Address the 'untreated death' patterns in A-site rotations.\n"
            summary += "3. **Utility Usage**: Increase efficiency of smokes to delay attacker entries.\n"
        else:
            summary += "1. **Macro Focus**: Capitalize on vision control around Dragon pit.\n"
            summary += "2. **Micro Focus**: Address CS gaps in the side lanes.\n"
            summary += "3. **Objective Priority**: Coordinate better around Baron spawns."
        
        return summary

# Singleton instance
ai_insight_service = AIInsightService()
