"""
Module de génération d'actions
Version améliorée avec profilage adaptatif
"""

from typing import List, Dict, Any
from dataclasses import dataclass
from enum import Enum
import uuid
from adaptive_profiler import AdaptiveUserProfiler  # IMPORT AJOUTÉ

class ActionType(Enum):
    # Chauffage/Climatisation Salon
    ACTIVER_CHAUFFAGE_SALON = "activer_chauffage_salon"
    ACTIVER_REFROIDISSEMENT_SALON = "activer_refroidissement_salon"
    ETEINDRE_CLIMAT_SALON = "eteindre_climat_salon"
    AUGMENTER_TEMP_SALON = "augmenter_temp_salon"
    DIMINUER_TEMP_SALON = "diminuer_temp_salon"
    
    # Lumières Salon
    ALLUMER_LUMIERE_SALON = "allumer_lumiere_salon"
    ETEINDRE_LUMIERE_SALON = "eteindre_lumiere_salon"
    AUGMENTER_LUMIERE_SALON = "augmenter_lumiere_salon"
    DIMINUER_LUMIERE_SALON = "diminuer_lumiere_salon"
    
    # TV Salon
    ALLUMER_TV_SALON = "allumer_tv_salon"
    ETEINDRE_TV_SALON = "eteindre_tv_salon"
    
    # Chauffage Cuisine
    ALLUMER_CHAUFFAGE_CUISINE = "allumer_chauffage_cuisine"
    ETEINDRE_CHAUFFAGE_CUISINE = "eteindre_chauffage_cuisine"
    AUGMENTER_TEMP_CUISINE = "augmenter_temp_cuisine"
    DIMINUER_TEMP_CUISINE = "diminuer_temp_cuisine"
    
    # Lumières Cuisine
    ALLUMER_LUMIERE_CUISINE = "allumer_lumiere_cuisine"
    ETEINDRE_LUMIERE_CUISINE = "eteindre_lumiere_cuisine"
    AUGMENTER_LUMIERE_CUISINE = "augmenter_lumiere_cuisine"
    DIMINUER_LUMIERE_CUISINE = "diminuer_lumiere_cuisine"
    
    # Appareils Cuisine
    ALLUMER_HOTTE_CUISINE = "allumer_hotte_cuisine"
    ETEINDRE_HOTTE_CUISINE = "eteindre_hotte_cuisine"
    ALLUMER_FOUR = "allumer_four"
    ETEINDRE_FOUR = "eteindre_four"

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
    
    def to_dict(self) -> Dict:
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
            "confidence_score": self.confidence_score
        }
    
    def to_mqtt_message(self) -> Dict:
        """Format pour Naila (SAC)"""
        return {
            "action_id": self.action_id,
            "action_type": self.action_type.value,
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
    ⭐ Utilise le profiler pour personnaliser les recommandations
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
    
    def generate_temperature_actions(self, user_id: str, room: str,
                                   current_temp: float,
                                   user_prefs: Dict,
                                   hour: int) -> List[Action]:
        """Génère des actions température avec score de confiance"""
        actions = []
        desired_temp = user_prefs.get(room, {}).get("desired_temperature", 22)
        
        # Vérifier si on peut être agressif
        is_aggressive = self.profiler.should_be_aggressive(user_id) if self.profiler else False
        
        if current_temp < desired_temp - 1:
            # Il fait trop froid
            confidence = self._calculate_confidence(
                user_id, "activer_chauffage", hour, 0.9
            )
            action_type = (ActionType.ACTIVER_CHAUFFAGE_SALON if room == "salon" 
                          else ActionType.ALLUMER_CHAUFFAGE_CUISINE)
            actions.append(Action(
                action_id=self._generate_action_id(),
                action_type=action_type,
                room=room,
                description=f"Activer chauffage {room} ({current_temp}°C → {desired_temp}°C)",
                current_value=current_temp,
                recommended_value=desired_temp,
                energy_saving_potential="medium",
                impact_on_comfort="positive",
                priority=1,
                confidence_score=confidence
            ))
        
        elif current_temp > desired_temp + 1:
            # Il fait trop chaud
            confidence = self._calculate_confidence(
                user_id, "activer_clim", hour, 0.9
            )
            action_type = (ActionType.ACTIVER_REFROIDISSEMENT_SALON if room == "salon" 
                          else ActionType.ETEINDRE_CHAUFFAGE_CUISINE)
            actions.append(Action(
                action_id=self._generate_action_id(),
                action_type=action_type,
                room=room,
                description=f"Activer climatisation {room} ({current_temp}°C → {desired_temp}°C)",
                current_value=current_temp,
                recommended_value=desired_temp,
                energy_saving_potential="medium",
                impact_on_comfort="positive",
                priority=1,
                confidence_score=confidence
            ))
        
        # Ajustements fins (avec possibilité d'être agressif)
        offsets = [-2, -1, 0, 1, 2] if is_aggressive else [-1, 0, 1]
        
        for offset in offsets:
            target = desired_temp + offset
            if 16 <= target <= 26 and abs(current_temp - target) > 0.5:
                if room == "salon":
                    action_type = (ActionType.AUGMENTER_TEMP_SALON if target > current_temp 
                                  else ActionType.DIMINUER_TEMP_SALON)
                else:
                    action_type = (ActionType.AUGMENTER_TEMP_CUISINE if target > current_temp 
                                  else ActionType.DIMINUER_TEMP_CUISINE)
                
                base_confidence = 0.7 if abs(offset) <= 1 else 0.5
                confidence = self._calculate_confidence(
                    user_id, action_type.value, hour, base_confidence
                )
                
                actions.append(Action(
                    action_id=self._generate_action_id(),
                    action_type=action_type,
                    room=room,
                    description=f"{'Augmenter' if target > current_temp else 'Diminuer'} température {room} de {current_temp}°C à {target}°C",
                    current_value=current_temp,
                    recommended_value=target,
                    energy_saving_potential="low" if abs(offset) <= 1 else "medium",
                    impact_on_comfort="neutral" if offset == 0 else "negative" if offset < 0 else "positive",
                    priority=2 if abs(offset) <= 1 else 3,
                    confidence_score=confidence
                ))
        
        return actions
    
    def generate_light_actions(self, user_id: str, room: str,
                              current_light: float, presence: bool,
                              user_prefs: Dict, hour: int) -> List[Action]:
        """Génère des actions lumière avec score de confiance"""
        actions = []
        desired_light = user_prefs.get(room, {}).get("desired_brightness", 80)
        
        if presence:
            # Personne présente
            if current_light < desired_light - 20:
                confidence = self._calculate_confidence(
                    user_id, "allumer_lumiere", hour, 0.8
                )
                action_type = (ActionType.ALLUMER_LUMIERE_SALON if room == "salon" 
                              else ActionType.ALLUMER_LUMIERE_CUISINE)
                actions.append(Action(
                    action_id=self._generate_action_id(),
                    action_type=action_type,
                    room=room,
                    description=f"Allumer lumière {room} (actuelle: {current_light}%)",
                    current_value=current_light,
                    recommended_value=desired_light,
                    energy_saving_potential="low",
                    impact_on_comfort="positive",
                    priority=2,
                    confidence_score=confidence
                ))
        else:
            # Personne absente
            if current_light > 10:  # Seuil plus bas la nuit
                base_confidence = 0.9 if 22 <= hour <= 6 else 0.7
                confidence = self._calculate_confidence(
                    user_id, "eteindre_lumiere", hour, base_confidence
                )
                action_type = (ActionType.ETEINDRE_LUMIERE_SALON if room == "salon"
                              else ActionType.ETEINDRE_LUMIERE_CUISINE)
                actions.append(Action(
                    action_id=self._generate_action_id(),
                    action_type=action_type,
                    room=room,
                    description=f"Éteindre lumière {room} (pièce vide)",
                    current_value=current_light,
                    recommended_value=0,
                    energy_saving_potential="high",
                    impact_on_comfort="neutral",
                    priority=1,
                    confidence_score=confidence
                ))
        
        return actions
    
    def generate_all_actions(self, user_id: str,
                           current_state: Dict[str, Any],
                           user_prefs: Dict[str, Any]) -> List[Action]:
        """
        Génère toutes les actions possibles
        ⭐ Version améliorée avec profilage
        """
        all_actions = []
        
        # Extraire l'état
        temp_salon = current_state.get('temp_salon', 22)
        temp_cuisine = current_state.get('temp_cuisine', 22)
        presence_salon = current_state.get('presence_salon', False)
        presence_cuisine = current_state.get('presence_cuisine', False)
        salon_light = current_state.get('salon_light_on', 0)
        cuisine_light = current_state.get('cuisine_light_on', 0)
        hour = current_state.get('heure', 12)
        
        # Actions Salon
        all_actions.extend(self.generate_temperature_actions(
            user_id, "salon", temp_salon, user_prefs, hour
        ))
        all_actions.extend(self.generate_light_actions(
            user_id, "salon", salon_light, presence_salon, user_prefs, hour
        ))
        
        # Actions Cuisine
        all_actions.extend(self.generate_temperature_actions(
            user_id, "cuisine", temp_cuisine, user_prefs, hour
        ))
        all_actions.extend(self.generate_light_actions(
            user_id, "cuisine", cuisine_light, presence_cuisine, user_prefs, hour
        ))
        
        # Actions TV
        tv_on = current_state.get('tv_on', 0)
        if not presence_salon and tv_on > 0:
            confidence = self._calculate_confidence(
                user_id, "eteindre_tv", hour, 0.95
            )
            all_actions.append(Action(
                action_id=self._generate_action_id(),
                action_type=ActionType.ETEINDRE_TV_SALON,
                room="salon",
                description="Éteindre TV (personne dans le salon)",
                current_value=tv_on,
                recommended_value=0,
                energy_saving_potential="medium",
                impact_on_comfort="neutral",
                priority=1,
                confidence_score=confidence
            ))
        
        # Actions Four
        four_on = current_state.get('four_on', 0)
        timer_four = current_state.get('timer_four', 0)
        if four_on > 0 and timer_four <= 0:  # Four fini
            confidence = self._calculate_confidence(
                user_id, "eteindre_four", hour, 0.98
            )
            all_actions.append(Action(
                action_id=self._generate_action_id(),
                action_type=ActionType.ETEINDRE_FOUR,
                room="cuisine",
                description="Éteindre four (cuisson terminée)",
                current_value=four_on,
                recommended_value=0,
                energy_saving_potential="high",
                impact_on_comfort="neutral",
                priority=1,
                confidence_score=confidence
            ))
        
        return all_actions