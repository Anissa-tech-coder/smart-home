"""
Interface API simplifiée
Utilise MQTT pour communiquer avec Naila
"""

import json
from typing import Dict, Any, List, Optional, Callable  # IMPORT AJOUTÉ
from datetime import datetime

from authentication import AuthenticationManager
from user_preferences import UserPreferencesManager
from actions import ActionGenerator
from mqtt_interface import MQTTInterface


class RecommendationAPI:
    """
    API RESTful pour l'application mobile (Nadine)
    + MQTT pour Naila
    """
    
    def __init__(self):
        print("🔄 Initialisation API...")
        self.auth = AuthenticationManager()
        self.prefs_manager = UserPreferencesManager("data/user_preferences.json")
        self.action_generator = ActionGenerator()
        
        # MQTT pour Naila
        self.mqtt = MQTTInterface("tasnim_api")
        self.mqtt.connect()
        
        print("✅ API initialisée!")
    
    # ========== AUTHENTIFICATION (pour Nadine) ==========
    
    def register_user(self, email: str, name: str, password: str) -> Dict:
        """Inscription utilisateur"""
        try:
            auth_result = self.auth.register_user(email, name, password)
            if not auth_result["success"]:
                return auth_result
            
            user_id = auth_result["user_id"]
            self.prefs_manager.create_user_profile(user_id, name, email)
            
            return {
                "success": True,
                "user_id": user_id,
                "name": name,
                "message": "✅ Compte créé!"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def login_user(self, email: str, password: str) -> Dict:
        """Connexion utilisateur"""
        try:
            return self.auth.login_user(email, password)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ========== PRÉFÉRENCES (pour Nadine) ==========
    
    def setup_preferences(self, user_id: str, preferences: Dict) -> Dict:
        """Configuration des préférences"""
        try:
            success = self.prefs_manager.setup_user_preferences(user_id, preferences)
            if success:
                return {"success": True, "message": "✅ Préférences enregistrées"}
            return {"success": False, "error": "Erreur enregistrement"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_preferences(self, user_id: str) -> Dict:
        """Récupère les préférences"""
        try:
            prefs = self.prefs_manager.get_user_preferences_summary(user_id)
            if prefs:
                return {"success": True, "data": prefs}
            return {"success": False, "error": "Utilisateur non trouvé"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ========== ACTIONS ET MQTT (pour Naila) ==========
    
    def generate_and_publish_actions(self, user_id: str, 
                                     current_state: Dict) -> Dict:
        """
        Génère les actions ET les publie sur MQTT pour Naila
        """
        try:
            # 1. Récupérer l'utilisateur
            user = self.prefs_manager.get_user_preferences(user_id)
            if not user:
                return {"success": False, "error": "Utilisateur non trouvé"}
            
            if not user.get("preferences_configured"):
                return {"success": False, "error": "Préférences non configurées"}
            
            # 2. Générer les actions
            actions = self.action_generator.generate_all_actions(
                user_id=user_id,  # AJOUTÉ
                current_state=current_state,
                user_prefs=user["preferences"]
            )
            
            actions_dict = [a.to_mqtt_message() for a in actions]
            
            # 3. Publier sur MQTT pour Naila
            mqtt_success = self.mqtt.publish_actions(
                user_id=user_id,
                actions=actions_dict,
                current_state=current_state
            )
            
            return {
                "success": True,
                "num_actions": len(actions),
                "actions": [a.to_dict() for a in actions[:5]],  # Top 5 pour l'affichage
                "mqtt_published": mqtt_success,
                "message": f"✅ {len(actions)} actions publiées sur MQTT"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ========== FEEDBACK (via MQTT) ==========
    
    def register_feedback_handler(self, user_id: str, 
                                  callback: Optional[Callable] = None):
        """
        Enregistre un handler pour les feedbacks de Naila
        """
        def default_handler(uid, action_id, accepted, reward):
            # Sauvegarde dans l'historique
            self.prefs_manager.log_action(
                user_id=uid,
                action={"action_id": action_id},
                accepted=accepted,
                reason=f"Reward SAC: {reward}"
            )
            print(f"📝 Feedback enregistré: {action_id} -> {'✅' if accepted else '❌'}")
        
        handler = callback if callback else default_handler
        self.mqtt.register_feedback_callback(user_id, handler)
        
        return {"success": True, "message": "Handler enregistré"}
    
    # ========== FERMETURE ==========
    
    def close(self):
        """Ferme les connexions"""
        self.mqtt.disconnect()
        print("👋 API fermée")