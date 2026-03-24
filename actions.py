"""
Module de génération d'actions
Version compatible avec la nouvelle structure de Naila
⭐ VERSION CORRIGÉE - Génération intelligente + validation
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import uuid
from adaptive_profiler import AdaptiveUserProfiler

class ActionType(Enum):
    # Salon
    ACTIVER_CHAUFFAGE_SALON = "activer_chauffage_salon"        # 0
    ACTIVER_REFROIDISSEMENT_SALON = "activer_refroidissement_salon"  # 1
    ETEINDRE_CLIMAT_SALON = "eteindre_climat_salon"            # 2
    AUGMENTER_TEMP_SALON = "augmenter_temp_salon"              # 3
    DIMINUER_TEMP_SALON = "diminuer_temp_salon"                # 4
    ALLUMER_LUMIERE_SALON = "allumer_lumiere_salon"            # 5
    ETEINDRE_LUMIERE_SALON = "eteindre_lumiere_salon"          # 6
    AUGMENTER_LUMIERE_SALON = "augmenter_lumiere_salon"        # 7
    DIMINUER_LUMIERE_SALON = "diminuer_lumiere_salon"          # 8
    ALLUMER_TV_SALON = "allumer_tv_salon"                      # 9
    ETEINDRE_TV_SALON = "eteindre_tv_salon"                    # 10
    
    # Cuisine
    ALLUMER_CHAUFFAGE_CUISINE = "allumer_chauffage_cuisine"    # 11
    ETEINDRE_CHAUFFAGE_CUISINE = "eteindre_chauffage_cuisine"  # 12
    AUGMENTER_TEMP_CUISINE = "augmenter_temp_cuisine"          # 13
    DIMINUER_TEMP_CUISINE = "diminuer_temp_cuisine"            # 14
    ALLUMER_LUMIERE_CUISINE = "allumer_lumiere_cuisine"        # 15
    ETEINDRE_LUMIERE_CUISINE = "eteindre_lumiere_cuisine"      # 16
    AUGMENTER_LUMIERE_CUISINE = "augmenter_lumiere_cuisine"    # 17
    DIMINUER_LUMIERE_CUISINE = "diminuer_lumiere_cuisine"      # 18
    ALLUMER_HOTTE_CUISINE = "allumer_hotte_cuisine"            # 19
    ETEINDRE_HOTTE_CUISINE = "eteindre_hotte_cuisine"          # 20
    ALLUMER_FOUR = "allumer_four"                               # 21
    ETEINDRE_FOUR = "eteindre_four"                             # 22

@dataclass
class Action:
    """Action discrète pour le système"""
    action_id: str
    action_type: ActionType
    room: str
    description: str
    current_value: Any
    recommended_value: Any
    energy_saving_potential: str  # "high", "medium", "low"
    impact_on_comfort: str  # "positive", "neutral", "negative"
    priority: int  # 1 (urgent) à 3 (normal)
    confidence_score: float = 0.5
    
    # Mapping des actions vers les index Naila
    _NAILA_INDEX_MAP = {
        "activer_chauffage_salon": 0,
        "activer_refroidissement_salon": 1,
        "eteindre_climat_salon": 2,
        "augmenter_temp_salon": 3,
        "diminuer_temp_salon": 4,
        "allumer_lumiere_salon": 5,
        "eteindre_lumiere_salon": 6,
        "augmenter_lumiere_salon": 7,
        "diminuer_lumiere_salon": 8,
        "allumer_tv_salon": 9,
        "eteindre_tv_salon": 10,
        "allumer_chauffage_cuisine": 11,
        "eteindre_chauffage_cuisine": 12,
        "augmenter_temp_cuisine": 13,
        "diminuer_temp_cuisine": 14,
        "allumer_lumiere_cuisine": 15,
        "eteindre_lumiere_cuisine": 16,
        "augmenter_lumiere_cuisine": 17,
        "diminuer_lumiere_cuisine": 18,
        "allumer_hotte_cuisine": 19,
        "eteindre_hotte_cuisine": 20,
        "allumer_four": 21,
        "eteindre_four": 22
    }
    
    def get_naila_index(self) -> int:
        """Retourne l'index de l'action pour Naila"""
        return self._NAILA_INDEX_MAP.get(self.action_type.value, -1)
    
    def to_dict(self) -> Dict:
        """Format pour affichage / Nadine (sans amplitude)"""
        return {
            "action_id": self.action_id,
            "action_type": self.action_type.value,
            "room": self.room,
            "description": self.description,
            "current_value": self.current_value,
            "recommended_value": self.recommended_value,
            "energy_saving_potential": self.energy_saving_potential,
            "impact_on_comfort": self.impact_on_comfort,
            "priority": self.priority,
            "confidence_score": self.confidence_score,
            "naila_index": self.get_naila_index()
        }
    
    def to_mqtt_message(self) -> Dict:
        """Format pour Naila (SAC) avec index"""
        return {
            "action_id": self.action_id,
            "action_type": self.action_type.value,
            "naila_index": self.get_naila_index(),
            "room": self.room,
            "description": self.description,
            "parameters": {
                "current": self.current_value,
                "target": self.recommended_value
            },
            "energy_potential": self.energy_saving_potential,
            "comfort_impact": self.impact_on_comfort,
            "priority": self.priority,
            "confidence": self.confidence_score
        }


class ActionGenerator:
    """
    Génère des actions adaptées au profil utilisateur
    ⭐ VERSION CORRIGÉE - Validation d'état intégrée
    """
    
    def __init__(self, profiler: AdaptiveUserProfiler = None):
        self.actions_counter = 0
        self.profiler = profiler or AdaptiveUserProfiler()
    
    def _generate_action_id(self) -> str:
        self.actions_counter += 1
        return f"act_{self.actions_counter:04d}_{uuid.uuid4().hex[:4]}"
    
    def _calculate_confidence(self, user_id: str, action_type: str, 
                             hour: int, base_score: float) -> float:
        """Calcule la confiance dans la recommandation"""
        if not self.profiler:
            return base_score
        
        profile_score = self.profiler.get_action_score(user_id, action_type, hour)
        return (base_score + profile_score) / 2
    
    def _is_value_on(self, value: Any) -> bool:
        """Convertit n'importe quel format de valeur en booléen"""
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value > 0.5  # Seuil 0.5 pour 0.0-1.0
        return bool(value)
    
    def _normalize_value(self, value: Any) -> float:
        """Normalise une valeur en float 0.0-1.0"""
        if isinstance(value, bool):
            return 1.0 if value else 0.0
        if isinstance(value, (int, float)):
            return float(max(0.0, min(1.0, value)))
        return 0.0
    
    # ========== GÉNÉRATION DES ACTIONS SALON ==========
    
    def generate_temperature_actions_salon(self, user_id: str,
                                          current_temp: float,
                                          user_target: float,
                                          hour: int) -> List[Action]:
        """Génère des actions de température pour le salon"""
        actions = []
        
        # Éviter les actions inutiles (écart trop faible)
        ecart = current_temp - user_target
        if abs(ecart) < 0.5:  # ✅ CORRECTION: Pas d'action si écart < 0.5°C
            return actions
        
        is_aggressive = self.profiler.should_be_aggressive(user_id) if self.profiler else False
        
        if ecart > 1.0:  # Trop chaud
            # Option 1: Activer la clim
            confidence = self._calculate_confidence(user_id, "activer_clim", hour, 0.9)
            actions.append(Action(
                action_id=self._generate_action_id(),
                action_type=ActionType.ACTIVER_REFROIDISSEMENT_SALON,
                room="salon",
                description=f"Réduire température salon ({current_temp:.1f}°C → {user_target:.1f}°C)",
                current_value=current_temp,
                recommended_value=user_target,
                energy_saving_potential="medium",
                impact_on_comfort="positive",
                priority=1,
                confidence_score=confidence
            ))
            
        elif ecart < -1.0:  # Trop froid
            # Option 1: Activer le chauffage
            confidence = self._calculate_confidence(user_id, "activer_chauffage", hour, 0.9)
            actions.append(Action(
                action_id=self._generate_action_id(),
                action_type=ActionType.ACTIVER_CHAUFFAGE_SALON,
                room="salon",
                description=f"Augmenter température salon ({current_temp:.1f}°C → {user_target:.1f}°C)",
                current_value=current_temp,
                recommended_value=user_target,
                energy_saving_potential="medium",
                impact_on_comfort="positive",
                priority=1,
                confidence_score=confidence
            ))
        
        return actions
    
    def generate_light_actions_salon(self, user_id: str,
                                    current_light: Any,
                                    presence: bool,
                                    hour: int) -> List[Action]:
        """Génère des actions d'éclairage pour le salon"""
        actions = []
        
        # ✅ CORRECTION: Normaliser la valeur
        light_value = self._normalize_value(current_light)
        light_on = self._is_value_on(current_light)
        
        # Pas de présence → éteindre si allumé
        if not presence and light_on:
            confidence = self._calculate_confidence(user_id, "eteindre_lumiere", hour, 0.95)
            actions.append(Action(
                action_id=self._generate_action_id(),
                action_type=ActionType.ETEINDRE_LUMIERE_SALON,
                room="salon",
                description="Éteindre lumière salon (pièce vide)",
                current_value=light_value,
                recommended_value=0.0,
                energy_saving_potential="high",
                impact_on_comfort="neutral",
                priority=1,
                confidence_score=confidence
            ))
        
        # Présence la nuit → allumer si éteint
        elif presence and (hour < 6 or hour > 20) and not light_on:
            confidence = self._calculate_confidence(user_id, "allumer_lumiere", hour, 0.85)
            actions.append(Action(
                action_id=self._generate_action_id(),
                action_type=ActionType.ALLUMER_LUMIERE_SALON,
                room="salon",
                description="Allumer lumière salon (nuit, présence détectée)",
                current_value=light_value,
                recommended_value=0.8,
                energy_saving_potential="low",
                impact_on_comfort="positive",
                priority=2,
                confidence_score=confidence
            ))
        
        return actions
    
    def generate_tv_actions(self, user_id: str,
                           tv_on: Any,
                           presence_salon: bool,
                           hour: int) -> List[Action]:
        """Génère des actions pour la TV"""
        actions = []
        
        # ✅ CORRECTION: Normaliser et vérifier
        tv_value = self._normalize_value(tv_on)
        tv_is_on = self._is_value_on(tv_on)
        
        # Pas de présence et TV allumée → éteindre
        if not presence_salon and tv_is_on:
            confidence = self._calculate_confidence(user_id, "eteindre_tv", hour, 0.95)
            actions.append(Action(
                action_id=self._generate_action_id(),
                action_type=ActionType.ETEINDRE_TV_SALON,
                room="salon",
                description="Éteindre TV (personne partie du salon)",
                current_value=tv_value,
                recommended_value=0.0,
                energy_saving_potential="medium",
                impact_on_comfort="neutral",
                priority=1,
                confidence_score=confidence
            ))
        
        return actions
    
    # ========== GÉNÉRATION DES ACTIONS CUISINE ==========
    
    def generate_temperature_actions_cuisine(self, user_id: str,
                                            current_temp: float,
                                            user_target: float,
                                            hour: int) -> List[Action]:
        """Génère des actions de température pour la cuisine"""
        actions = []
        
        # ✅ CORRECTION: Éviter les actions inutiles
        ecart = current_temp - user_target
        if abs(ecart) < 0.5:
            return actions
        
        if ecart > 1.0:  # Trop chaud
            confidence = self._calculate_confidence(user_id, "eteindre_chauffage_cuisine", hour, 0.85)
            actions.append(Action(
                action_id=self._generate_action_id(),
                action_type=ActionType.ETEINDRE_CHAUFFAGE_CUISINE,
                room="cuisine",
                description=f"Réduire température cuisine ({current_temp:.1f}°C → {user_target:.1f}°C)",
                current_value=current_temp,
                recommended_value=user_target,
                energy_saving_potential="medium",
                impact_on_comfort="neutral",
                priority=1,
                confidence_score=confidence
            ))
            
        elif ecart < -1.0:  # Trop froid
            confidence = self._calculate_confidence(user_id, "allumer_chauffage_cuisine", hour, 0.85)
            actions.append(Action(
                action_id=self._generate_action_id(),
                action_type=ActionType.ALLUMER_CHAUFFAGE_CUISINE,
                room="cuisine",
                description=f"Augmenter température cuisine ({current_temp:.1f}°C → {user_target:.1f}°C)",
                current_value=current_temp,
                recommended_value=user_target,
                energy_saving_potential="medium",
                impact_on_comfort="positive",
                priority=1,
                confidence_score=confidence
            ))
        
        return actions
    
    def generate_light_actions_cuisine(self, user_id: str,
                                      current_light: Any,
                                      presence: bool,
                                      hour: int) -> List[Action]:
        """Génère des actions d'éclairage pour la cuisine"""
        actions = []
        
        # ✅ CORRECTION: Normaliser la valeur
        light_value = self._normalize_value(current_light)
        light_on = self._is_value_on(current_light)
        
        # Pas de présence → éteindre si allumé
        if not presence and light_on:
            confidence = self._calculate_confidence(user_id, "eteindre_lumiere_cuisine", hour, 0.9)
            actions.append(Action(
                action_id=self._generate_action_id(),
                action_type=ActionType.ETEINDRE_LUMIERE_CUISINE,
                room="cuisine",
                description="Éteindre lumière cuisine (pièce vide)",
                current_value=light_value,
                recommended_value=0.0,
                energy_saving_potential="high",
                impact_on_comfort="neutral",
                priority=1,
                confidence_score=confidence
            ))
        
        # Présence → allumer si éteint
        elif presence and not light_on:
            confidence = self._calculate_confidence(user_id, "allumer_lumiere_cuisine", hour, 0.8)
            actions.append(Action(
                action_id=self._generate_action_id(),
                action_type=ActionType.ALLUMER_LUMIERE_CUISINE,
                room="cuisine",
                description="Allumer lumière cuisine (présence détectée)",
                current_value=light_value,
                recommended_value=0.8,
                energy_saving_potential="low",
                impact_on_comfort="positive",
                priority=2,
                confidence_score=confidence
            ))
        
        return actions
    
    def generate_hotte_actions(self, user_id: str,
                              hotte_on: Any,
                              temp_cuisine: float,
                              temp_precedente: Optional[float],
                              presence: bool,
                              hour: int) -> List[Action]:
        """Génère des actions pour la hotte"""
        actions = []
        
        # ✅ CORRECTION: Normaliser
        hotte_value = self._normalize_value(hotte_on)
        hotte_is_on = self._is_value_on(hotte_on)
        
        hausse_temp = (temp_cuisine - temp_precedente) if temp_precedente else 0
        
        # Détection de cuisson (hausse temp + présence) → allumer si éteint
        if presence and hausse_temp > 1.0 and not hotte_is_on:
            confidence = self._calculate_confidence(user_id, "allumer_hotte", hour, 0.85)
            actions.append(Action(
                action_id=self._generate_action_id(),
                action_type=ActionType.ALLUMER_HOTTE_CUISINE,
                room="cuisine",
                description="Allumer hotte (augmentation température détectée)",
                current_value=hotte_value,
                recommended_value=1.0,
                energy_saving_potential="low",
                impact_on_comfort="positive",
                priority=2,
                confidence_score=confidence
            ))
        
        # Pas de présence → éteindre si allumé
        if not presence and hotte_is_on:
            confidence = self._calculate_confidence(user_id, "eteindre_hotte", hour, 0.9)
            actions.append(Action(
                action_id=self._generate_action_id(),
                action_type=ActionType.ETEINDRE_HOTTE_CUISINE,
                room="cuisine",
                description="Éteindre hotte (plus personne en cuisine)",
                current_value=hotte_value,
                recommended_value=0.0,
                energy_saving_potential="medium",
                impact_on_comfort="neutral",
                priority=1,
                confidence_score=confidence
            ))
        
        return actions
    
    def generate_four_actions(self, user_id: str,
                             four_on: Any,
                             presence: bool,
                             hour: int) -> List[Action]:
        """Génère des actions pour le four"""
        actions = []
        
        # ✅ CORRECTION: Normaliser
        four_value = self._normalize_value(four_on)
        four_is_on = self._is_value_on(four_on)
        
        # Pas de présence → éteindre si allumé (SÉCURITÉ!)
        if not presence and four_is_on:
            confidence = self._calculate_confidence(user_id, "eteindre_four", hour, 0.99)
            actions.append(Action(
                action_id=self._generate_action_id(),
                action_type=ActionType.ETEINDRE_FOUR,
                room="cuisine",
                description="Éteindre four (SÉCURITÉ: pièce vide)",
                current_value=four_value,
                recommended_value=0.0,
                energy_saving_potential="high",
                impact_on_comfort="neutral",
                priority=1,  # URGENT pour sécurité
                confidence_score=confidence
            ))
        
        return actions
    
    def generate_all_actions(self, user_id: str,
                           current_state: Dict[str, Any],
                           user_prefs: Dict[str, Any]) -> List[Action]:
        """
        Génère UNIQUEMENT les actions pertinentes
        ⭐ VERSION CORRIGÉE - Filtre intelligent
        """
        all_actions = []
        
        # Extraire l'état avec valeurs par défaut sûres
        temp_salon = float(current_state.get('temp_salon', 22.0))
        temp_cuisine = float(current_state.get('temp_cuisine', 22.0))
        user_target = float(current_state.get('user_target', 22.0))
        presence_salon = bool(current_state.get('presence_salon', False))
        presence_cuisine = bool(current_state.get('presence_cuisine', False))
        lumiere_salon = current_state.get('lumiere_salon', 0.0)
        lumiere_cuisine = current_state.get('lumiere_cuisine', 0.0)
        tv_on = current_state.get('tv_on', 0.0)
        four_on = current_state.get('four_on', 0.0)
        hotte_on = current_state.get('hotte_on', 0.0)
        temp_cuisine_precedente = current_state.get('temp_cuisine_precedente', None)
        heure = int(current_state.get('heure', 12))
        
        # Actions Salon
        all_actions.extend(self.generate_temperature_actions_salon(
            user_id, temp_salon, user_target, heure
        ))
        all_actions.extend(self.generate_light_actions_salon(
            user_id, lumiere_salon, presence_salon, heure
        ))
        all_actions.extend(self.generate_tv_actions(
            user_id, tv_on, presence_salon, heure
        ))
        
        # Actions Cuisine
        all_actions.extend(self.generate_temperature_actions_cuisine(
            user_id, temp_cuisine, user_target, heure
        ))
        all_actions.extend(self.generate_light_actions_cuisine(
            user_id, lumiere_cuisine, presence_cuisine, heure
        ))
        all_actions.extend(self.generate_hotte_actions(
            user_id, hotte_on, temp_cuisine, temp_cuisine_precedente, presence_cuisine, heure
        ))
        all_actions.extend(self.generate_four_actions(
            user_id, four_on, presence_cuisine, heure
        ))
        
        return all_actions
