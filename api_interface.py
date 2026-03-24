"""
Interface API simplifiée
Version compatible avec Naila
"""

from typing import Dict, Any, List, Optional, Callable
import json
from datetime import datetime
import time

from authentication import AuthenticationManager
from user_preferences import UserPreferencesManager
from actions import ActionGenerator
from mqtt_interface import MQTTInterface

class RecommendationAPI:
    """
    API pour l'application mobile (Nadine) + MQTT pour Naila
    Version compatible avec l'environnement de Naila
    """
    
    def __init__(self):
        print("🔄 Initialisation API...")
        self.auth = AuthenticationManager()
        self.prefs_manager = UserPreferencesManager("data/user_preferences.json")
        self.action_generator = ActionGenerator()
        
        # Cache
        self.preferences_cache = {}
        self.cache_timeout = 60
        
        # MQTT
        self.mqtt = MQTTInterface("tasnim_api")
        self.mqtt.connect()
        
        # Enregistrer les callbacks
        self._register_callbacks()
        
        print("✅ API initialisée!")
    
    def _register_callbacks(self):
        """Enregistre tous les callbacks MQTT"""
        self.mqtt.register_feedback_callback("default", self.handle_feedback)
        self.mqtt.register_naila_callback("demande", self.handle_naila_demande)
        print("📝 Callbacks enregistrés:")
        print("   - Feedback (default)")
        print("   - Demande Naila")
    
    # ========== CALLBACKS MQTT ==========
    
    def handle_naila_demande(self, user_id: str, etat: Dict):
        """
        Naila demande des actions
        """
        print(f"\n📢 [NAILA] Demande d'actions pour {user_id}")
        print(f"   État reçu: {etat}")
        result = self.generate_and_publish_actions(user_id, etat)
        if result["success"]:
            print(f"   ✅ {result['num_actions']} actions envoyées")
        else:
            print(f"   ❌ {result.get('error')}")
    
    def handle_feedback(self, user_id: str, action_id: str, accepted: bool, reward: float):
        """
        Reçoit les feedbacks de Naila
        """
        print(f"\n💬 [NAILA] Feedback reçu pour {user_id}")
        print(f"   Action: {action_id}")
        print(f"   Accepté: {'✅' if accepted else '❌'}")
        print(f"   Reward: {reward:.3f}")
        
        # Sauvegarder dans l'historique
        self.prefs_manager.log_action(
            user_id=user_id,
            action={"action_id": action_id},
            accepted=accepted,
            reason=f"Reward: {reward:.3f}"
        )
    
    # ========== MÉTHODES D'AUTH ==========
    
    def register_user(self, email, name, password):
        result = self.auth.register_user(email, name, password)
        if result["success"]:
            self.prefs_manager.create_user_profile(result["user_id"], name, email)
        return result
    
    def login_user(self, email, password):
        return self.auth.login_user(email, password)
    
    def setup_preferences(self, user_id, preferences):
        result = self.prefs_manager.setup_user_preferences(user_id, preferences)
        if result:
            self.preferences_cache.pop(user_id, None)
        return {"success": result, "message": "✅ Préférences enregistrées" if result else "❌ Erreur"}
    
    def get_preferences(self, user_id):
        try:
            prefs = self.prefs_manager.get_user_preferences_summary(user_id)
            if prefs:
                return {"success": True, "data": prefs}
            return {"success": False, "error": "Utilisateur non trouvé"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ========== GESTION UTILISATEUR ==========
    
    def _get_or_create_user(self, user_id: str) -> Dict:
        """Récupère ou crée un utilisateur"""
        user = self.prefs_manager.get_user_preferences(user_id)
        if not user:
            print(f"   👤 Création auto de l'utilisateur {user_id}")
            self.prefs_manager.create_user_profile(
                user_id, 
                f"User_{user_id}", 
                f"{user_id}@example.com"
            )
            default_prefs = {
                "global_comfort_level": "normal",
                "rooms": {
                    "salon": {"desired_temperature": 22, "desired_brightness": 80},
                    "cuisine": {"desired_temperature": 21, "desired_brightness": 90}
                }
            }
            self.prefs_manager.setup_user_preferences(user_id, default_prefs)
            user = self.prefs_manager.get_user_preferences(user_id)
        return user
    
    def _get_user_preferences_cached(self, user_id: str) -> Optional[Dict]:
        """Récupère les préférences avec cache"""
        now = time.time()
        
        if user_id in self.preferences_cache:
            cached_time, prefs = self.preferences_cache[user_id]
            if now - cached_time < self.cache_timeout:
                return prefs
        
        user = self._get_or_create_user(user_id)
        if user:
            self.preferences_cache[user_id] = (now, user["preferences"])
            return user["preferences"]
        return None
    
    # ========== CŒUR DE LA COMMUNICATION ==========
    
    def generate_and_publish_actions(self, user_id: str, current_state: Dict) -> Dict:
        """
        Génère les actions et les envoie à Naila
        """
        try:
            # Récupérer les préférences
            user_prefs = self._get_user_preferences_cached(user_id)
            if not user_prefs:
                return {"success": False, "error": "Préférences non trouvées"}
            
            # Générer les actions
            actions = self.action_generator.generate_all_actions(
                user_id=user_id,
                current_state=current_state,
                user_prefs=user_prefs
            )
            
            # Préparer le format pour Naila
            actions_dict = [a.to_mqtt_message() for a in actions]
            
            # Vérifier que user_id est bien présent
            print(f"   📤 Envoi pour user_id: {user_id}")
            
            # Publier
            mqtt_success = self.mqtt.publish_actions(
                user_id=user_id,
                actions=actions_dict,
                current_state=current_state
            )
            
            if mqtt_success:
                print(f"📤 [MQTT] {len(actions)} actions envoyées")
                # Afficher les 3 premières
                for i, action in enumerate(actions_dict[:3]):
                    print(f"   {i+1}. {action.get('description', 'Action')} (index {action.get('naila_index', -1)})")
            
            return {
                "success": mqtt_success,
                "num_actions": len(actions),
                "actions": actions_dict,
                "user_id": user_id
            }
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return {"success": False, "error": str(e)}
    
    # ========== FERMETURE ==========
    
    def close(self):
        """Ferme les connexions"""
        self.mqtt.disconnect()
        print("👋 API fermée")        """Inscription utilisateur"""
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
