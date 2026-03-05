"""
Calculateur d'énergie SIMPLIFIÉ pour Tasnim
⭐ Le calcul PRÉCIS sera fait par Lina et Selsabila
⭐ Ici on donne juste des INDICATIONS
"""

from typing import List, Dict, Any
from actions import Action

class EnergyCalculator:
    """
    Version simplifiée pour Tasnim
    Donne des INDICATIONS d'économie (pas les valeurs exactes)
    """
    
    def __init__(self):
        """Initialisation simple"""
        pass
    
    def estimate_savings(self, actions: List[Action]) -> Dict[str, Any]:
        """
        Donne une ESTIMATION des économies
        (pour l'affichage, pas pour le calcul réel)
        """
        total_high = sum(1 for a in actions if a.energy_saving_potential == "high")
        total_medium = sum(1 for a in actions if a.energy_saving_potential == "medium")
        total_low = sum(1 for a in actions if a.energy_saving_potential == "low")
        
        return {
            "high_potential": total_high,
            "medium_potential": total_medium,
            "low_potential": total_low,
            "total_actions": len(actions),
            "note": "Calcul précis de l'énergie fait par Lina et Selsabila"
        }
    
    def get_saving_indicator(self, action: Action) -> str:
        """
        Retourne un indicateur visuel d'économie
        """
        indicators = {
            "high": "🔴 Élevé",
            "medium": "🟡 Moyen",
            "low": "🟢 Faible"
        }
        return indicators.get(action.energy_saving_potential, "⚪ Inconnu")