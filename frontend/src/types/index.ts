export interface MatchReview {
  match_id: str;
  micro_insights: MicroInsight[];
  macro_insights: MacroInsight[];
  decision_analysis: DecisionAnalysis;
  ai_coach_summary: string;
}

export interface MicroInsight {
  player_id: number;
  type: string;
  timestamp: number;
  impact: string;
}

export interface MacroInsight {
  timestamp: number;
  type: string;
  magnitude: number;
  description: string;
}

export interface DecisionAnalysis {
  current_probability: number;
  modified_probability: number;
  delta: number;
}
