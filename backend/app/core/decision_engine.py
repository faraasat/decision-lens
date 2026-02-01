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
        n_samples = 2000
        # Creating features with realistic ranges
        data = {
            "gold_diff": np.random.normal(0, 3000, n_samples),
            "xp_diff": np.random.normal(0, 2000, n_samples),
            "towers_diff": np.random.randint(-11, 11, n_samples),
            "dragons_diff": np.random.randint(-5, 5, n_samples),
            "barons_diff": np.random.randint(-3, 3, n_samples),
            "time_seconds": np.random.randint(0, 2400, n_samples),
            "team100_kills": np.random.randint(0, 40, n_samples),
            "team200_kills": np.random.randint(0, 40, n_samples)
        }
        X = pd.DataFrame(data)
        
        # Simple win probability heuristic
        logit = (X["gold_diff"] * 0.001 + 
                 X["towers_diff"] * 0.5 + 
                 X["dragons_diff"] * 0.8 + 
                 X["barons_diff"] * 1.5 + 
                 (X["team100_kills"] - X["team200_kills"]) * 0.1)
        
        prob = 1 / (1 + np.exp(-logit))
        y = (prob > np.random.rand(n_samples)).astype(int)
        
        self.model = xgb.XGBClassifier(n_estimators=50, max_depth=3)
        self.model.fit(X, y)
        self.explainer = shap.TreeExplainer(self.model)

    def predict_win_probability(self, game_state: Dict[str, Any]) -> float:
        if self.model is None:
            self.train_mock_model()
            
        df = pd.DataFrame([game_state], columns=self.feature_names).fillna(0)
        prob = self.model.predict_proba(df)[0][1]
        return float(prob)

    def predict_bulk_probabilities(self, game_states: List[Dict[str, Any]]) -> List[float]:
        if self.model is None:
            self.train_mock_model()
        if not game_states:
            return []
        df = pd.DataFrame(game_states, columns=self.feature_names).fillna(0)
        probs = self.model.predict_proba(df)[:, 1]
        return [float(p) for p in probs]

    def explain_decision(self, game_state: Dict[str, Any]) -> Dict[str, float]:
        """Use SHAP to explain why the win probability is what it is."""
        if self.explainer is None:
            self.train_mock_model()
            
        df = pd.DataFrame([game_state], columns=self.feature_names).fillna(0)
        shap_values = self.explainer.shap_values(df)
        
        # In newer SHAP versions for binary classification, shap_values might be a list
        if isinstance(shap_values, list):
            # For binary classification, index 1 is for the positive class
            current_shap = shap_values[1][0] if len(shap_values) > 1 else shap_values[0][0]
        else:
            # If it's a single array, it might be (n_samples, n_features) or (n_samples, n_features, n_classes)
            if len(shap_values.shape) == 3:
                current_shap = shap_values[0, :, 1]
            else:
                current_shap = shap_values[0]

        # Return feature contributions
        explanations = {k: float(v) for k, v in zip(self.feature_names, current_shap)}
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
            "delta": modified_prob - current_prob,
            "modified_state": modified_state,
            "explanation": self._explain_delta(current_state, modified_state)
        }

    def _explain_delta(self, before: Dict[str, Any], after: Dict[str, Any]) -> str:
        """Generate a natural language explanation of the probability shift."""
        # This is a simplified XAI heuristic
        prob_before = self.predict_win_probability(before)
        prob_after = self.predict_win_probability(after)
        delta = prob_after - prob_before
        
        shap_before = self.explain_decision(before)
        shap_after = self.explain_decision(after)
        
        # Find which feature shifted the most in impact
        impact_shifts = {}
        for feature in self.feature_names:
            impact_shifts[feature] = shap_after.get(feature, 0) - shap_before.get(feature, 0)
        
        top_driver = max(impact_shifts.items(), key=lambda x: abs(x[1]))
        
        direction = "increase" if delta > 0 else "decrease"
        magnitude = abs(delta) * 100
        
        feature_readable = top_driver[0].replace("_diff", "").replace("_", " ").title()
        
        explanation = f"The {magnitude:.1f}% {direction} in win probability is primarily driven by "
        explanation += f"the shift in {feature_readable} impact. "
        
        if abs(top_driver[1]) > 0.05:
            explanation += f"This modification heavily optimized the {feature_readable} contribution to the XGBoost outcome."
        else:
            explanation += "The cumulative effect of minor stat improvements reached a neural tipping point."
            
        return explanation

# Singleton instance
decision_engine = DecisionEngine()
