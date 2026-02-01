import xgboost as xgb
import pandas as pd
import numpy as np
from typing import Dict, Any, List
import shap

class DecisionEngine:
    def __init__(self):
        self.model = None
        self.explainer = None
        # Mock features that would be used in a real LoL model
        self.feature_names = [
            "gold_diff", "xp_diff", "towers_diff", "dragons_diff", 
            "barons_diff", "time_seconds", "team100_kills", "team200_kills"
        ]

    def train_mock_model(self):
        """Train a model on synthetic data for demonstration purposes."""
        # Generate synthetic data
        n_samples = 1000
        X = pd.DataFrame(np.random.randn(n_samples, len(self.feature_names)), columns=self.feature_names)
        
        # Simple heuristic: gold_diff and dragons_diff highly correlate with win
        y = (X["gold_diff"] * 2 + X["dragons_diff"] * 3 + np.random.randn(n_samples) > 0).astype(int)
        
        self.model = xgb.XGBClassifier()
        self.model.fit(X, y)
        self.explainer = shap.TreeExplainer(self.model)

    def predict_win_probability(self, game_state: Dict[str, Any]) -> float:
        if self.model is None:
            self.train_mock_model()
            
        df = pd.DataFrame([game_state], columns=self.feature_names).fillna(0)
        prob = self.model.predict_proba(df)[0][1]
        return float(prob)

    def explain_decision(self, game_state: Dict[str, Any]) -> Dict[str, float]:
        """Use SHAP to explain why the win probability is what it is."""
        if self.explainer is None:
            self.train_mock_model()
            
        df = pd.DataFrame([game_state], columns=self.feature_names).fillna(0)
        shap_values = self.explainer.shap_values(df)
        
        # Return feature contributions
        explanations = dict(zip(self.feature_names, shap_values[0]))
        return explanations

    def what_if_analysis(self, current_state: Dict[str, Any], modification: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare current win probability with a modified state.
        Example modification: {"dragons_diff": current_state["dragons_diff"] + 1}
        """
        current_prob = self.predict_win_probability(current_state)
        
        modified_state = current_state.copy()
        modified_state.update(modification)
        
        modified_prob = self.predict_win_probability(modified_state)
        
        return {
            "current_probability": current_prob,
            "modified_probability": modified_prob,
            "delta": modified_prob - current_prob
        }

# Singleton instance
decision_engine = DecisionEngine()
