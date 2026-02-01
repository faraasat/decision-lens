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
        For now, uses sophisticated template logic (to be replaced by LLM call).
        """
        prompt = "You are a professional League of Legends Assistant Coach. Review the stats below and provide a concise, actionable summary for the Head Coach.\n\n"
        
        prompt += "Micro Insights (Individual Mistakes):\n"
        for m in micro_insights[:3]:
            prompt += f"- Player {m['player_id']} had an '{m['type']}' at {m['timestamp']}. Impact: {m['impact']}\n"
            
        prompt += "\nMacro Insights (Strategic Shifts):\n"
        for m in macro_insights[:3]:
            prompt += f"- {m['description']} at {m['timestamp']}\n"
            
        prompt += "\nDecision Impact Analysis:\n"
        for d in decisions:
            prompt += f"- What if: {d['what_if']}. Probability Shift: {d['delta']:+.2f}%\n"

        prompt += "\nActionable Recommendations:\n"
        # In a real app, this goes to an LLM
        prompt += "1. Review dragon pit positioning at 15:00.\n2. Address isolated deaths in mid-lane.\n3. Prioritize vision around Baron setup."
        
        return prompt

# Singleton instance
ai_insight_service = AIInsightService()
