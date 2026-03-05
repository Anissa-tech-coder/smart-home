"""
Moteur de recommandation adaptatif
Utilise le profilage pour personnaliser les recommandations
"""

from typing import List, Dict, Any
from datetime import datetime
from actions import Action, ActionGenerator
from user_preferences import UserPreferencesManager
from adaptive_profiler import AdaptiveUserProfiler

class RecommendationEngine:
    """
    Moteur intelligent avec adaptation comportementale
    """
    
    def __init__(self, preferences_manager: UserPreferencesManager,
                 action_generator: ActionGenerator,
                 profiler: AdaptiveUserProfiler):
        self.preferences_manager = preferences_manager
        self.action_generator = action_generator
        self.profiler = profiler
    
    def score_action(self, action: Action, user_profile: Dict, hour: int) -> float:
        """
        Calcule un score personnalisé pour une action
        """
        score = 0.0
        
        # 1. Potentiel d'économie
        if action.energy_saving_potential == "high":
            score += 3.0
        elif action.energy_saving_potential == "medium":
            score += 1.5
        elif action.energy_saving_potential == "low":
            score += 0.5
        
        # 2. Impact confort (pondéré par les préférences)
        comfort_weight = user_profile.get('comfort_priority', 0.5)
        if action.impact_on_comfort == "positive":
            score += 2.0 * comfort_weight
        elif action.impact_on_comfort == "negative":
            score -= 1.0 * (1 - comfort_weight)
        
        # 3. Priorité de base
        score += (4 - action.priority)
        
        # 4. Confiance du profiler
        score += action.confidence_score * 2
        
        # 5. Bonus horaire
        hour_score = user_profile.get('hourly_patterns', {}).get(str(hour), 0.5)
        score += hour_score * 1.5
        
        return score
    
    def generate_recommendations(self, user_id: str,
                                current_state: Dict[str, Any],
                                max_recommendations: int = 5) -> Dict[str, Any]:
        """
        Génère des recommandations personnalisées
        """
        # 1. Récupérer l'utilisateur
        user = self.preferences_manager.get_user_preferences(user_id)
        if not user:
            return {"error": f"Utilisateur {user_id} non trouvé"}
        
        # 2. Récupérer/Mettre à jour le profil
        history = self.preferences_manager.get_action_history(user_id)
        user_profile = self.profiler.analyze_history(user_id, history)
        
        # 3. Générer toutes les actions
        all_actions = self.action_generator.generate_all_actions(
            user_id=user_id,
            current_state=current_state,
            user_prefs=user["preferences"]
        )
        
        # 4. Calculer les scores
        hour = current_state.get('heure', 12)
        scored_actions = [(self.score_action(a, user_profile, hour), a) 
                         for a in all_actions]
        
        # 5. Trier et sélectionner
        scored_actions.sort(key=lambda x: x[0], reverse=True)
        best_actions = [a for score, a in scored_actions[:max_recommendations]]
        
        # 6. Générer le rapport
        return {
            "user_id": user_id,
            "user_name": user["name"],
            "timestamp": datetime.now().isoformat(),
            "comfort_level": user["preferences"]["global_comfort_level"],
            "recommendations": [a.to_dict() for a in best_actions],
            "num_recommendations": len(best_actions),
            "user_profile_summary": {
                "eco_sensitivity": round(user_profile.get('eco_sensitivity', 0.5), 2),
                "comfort_priority": round(user_profile.get('comfort_priority', 0.5), 2),
                "total_actions_analyzed": user_profile.get('total_actions', 0)
            }
        }