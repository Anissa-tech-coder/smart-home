"""
Module d'adaptation comportementale
Analyse les habitudes des utilisateurs pour mieux recommander
"""

from typing import List, Dict, Any
from datetime import datetime
from collections import defaultdict
import json

class AdaptiveUserProfiler:
    """
    Crée des profils utilisateur basés sur l'historique
    ⭐ S'adapte automatiquement aux habitudes
    """
    
    def __init__(self, data_file: str = "data/user_profiles.json"):
        self.data_file = data_file
        self.profiles = self._load_profiles()
    
    def _load_profiles(self) -> Dict:
        """Charge les profils existants"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def _save_profiles(self):
        """Sauvegarde les profils"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.profiles, f, indent=2, ensure_ascii=False)
    
    def analyze_history(self, user_id: str, action_history: List[Dict]) -> Dict:
        """
        Analyse l'historique pour créer un profil comportemental
        À appeler après chaque feedback
        """
        if not action_history:
            return self._get_default_profile()
        
        # Regrouper par heure
        hourly_acceptance = defaultdict(list)
        actions_by_type = defaultdict(list)
        
        for action in action_history:
            try:
                timestamp = datetime.fromisoformat(action['timestamp'])
                hour = timestamp.hour
                accepted = action.get('accepted', False)
                action_type = str(action.get('action', {}).get('action_type', 'unknown'))
                
                hourly_acceptance[hour].append(1 if accepted else 0)
                actions_by_type[action_type].append(1 if accepted else 0)
            except:
                continue
        
        # Calculer les taux par heure
        time_patterns = {}
        for hour in range(24):
            if hourly_acceptance[hour]:
                time_patterns[str(hour)] = sum(hourly_acceptance[hour]) / len(hourly_acceptance[hour])
            else:
                time_patterns[str(hour)] = 0.5  # Valeur par défaut
        
        # Calculer les préférences par type d'action
        action_preferences = {}
        for action_type, accepts in actions_by_type.items():
            if accepts:
                action_preferences[action_type] = sum(accepts) / len(accepts)
        
        # Calculer le profil global
        profile = {
            "user_id": user_id,
            "last_updated": datetime.now().isoformat(),
            "total_actions": len(action_history),
            "global_acceptance_rate": sum(1 for a in action_history if a.get('accepted')) / len(action_history),
            "hourly_patterns": time_patterns,
            "action_preferences": action_preferences,
            "preferred_hours": self._get_preferred_hours(time_patterns),
            "eco_sensitivity": self._calculate_eco_sensitivity(action_history),
            "comfort_priority": self._calculate_comfort_priority(action_history)
        }
        
        self.profiles[user_id] = profile
        self._save_profiles()
        return profile
    
    def _get_default_profile(self) -> Dict:
        """Profil par défaut pour les nouveaux utilisateurs"""
        return {
            "global_acceptance_rate": 0.7,
            "hourly_patterns": {str(h): 0.5 for h in range(24)},
            "action_preferences": {},
            "preferred_hours": [8, 9, 10, 18, 19, 20],  # Matin et soir
            "eco_sensitivity": 0.5,
            "comfort_priority": 0.5
        }
    
    def _get_preferred_hours(self, patterns: Dict) -> List[int]:
        """Identifie les heures où l'utilisateur accepte le plus"""
        sorted_hours = sorted(patterns.items(), key=lambda x: x[1], reverse=True)
        return [int(h) for h, _ in sorted_hours[:6]]  # Top 6 heures
    
    def _calculate_eco_sensitivity(self, history: List[Dict]) -> float:
        """
        Calcule la sensibilité aux économies (0-1)
        0 = n'aime pas économiser, 1 = adore économiser
        """
        eco_actions = []
        for action in history:
            action_data = action.get('action', {})
            if action_data.get('energy_saving_potential') == 'high':
                eco_actions.append(1 if action.get('accepted') else 0)
        
        if not eco_actions:
            return 0.5
        return sum(eco_actions) / len(eco_actions)
    
    def _calculate_comfort_priority(self, history: List[Dict]) -> float:
        """
        Calcule la priorité confort (0-1)
        0 = préfère économies, 1 = préfère confort
        """
        comfort_actions = []
        for action in history:
            action_data = action.get('action', {})
            if action_data.get('impact_on_comfort') == 'positive':
                comfort_actions.append(1 if action.get('accepted') else 0)
        
        if not comfort_actions:
            return 0.5
        return sum(comfort_actions) / len(comfort_actions)
    
    def get_action_score(self, user_id: str, action_type: str, hour: int) -> float:
        """
        Donne un score de pertinence pour une action
        Utilisé par le moteur de recommandation
        """
        profile = self.profiles.get(user_id, self._get_default_profile())
        
        # Score basé sur l'heure
        hour_score = profile['hourly_patterns'].get(str(hour), 0.5)
        
        # Score basé sur le type d'action
        action_score = profile['action_preferences'].get(action_type, 0.5)
        
        # Score global (moyenne pondérée)
        return (hour_score * 0.4 + action_score * 0.6)
    
    def should_be_aggressive(self, user_id: str) -> bool:
        """Détermine si on peut proposer des actions agressives"""
        profile = self.profiles.get(user_id, self._get_default_profile())
        return profile['eco_sensitivity'] > 0.6