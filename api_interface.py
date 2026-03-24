"""
Interface API simplifiée
⭐ VERSION CORRIGÉE - Validation stricte + filtrage des actions
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
    ⭐ VERSION CORRIGÉE
    """

    def __init__(self):
        print("🔄 Initialisation API...")
        self.auth = AuthenticationManager()
        self.prefs_manager = UserPreferencesManager("data/user_preferences.json")
        self.action_generator = ActionGenerator()

        # Cache
        self.preferences_cache = {}
        self.cache_timeout = 60
        
        # ✅ NOUVEAU: Limiter les actions
        self.max_actions_per_request = 5

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
        """Naila demande des actions"""
        print(f"\n📢 [NAILA] Demande d'actions pour {user_id}")
        print(f"   État reçu: {json.dumps(etat, indent=2)}")
        result = self.generate_and_publish_actions(user_id, etat)
        if result["success"]:
            print(f"   ✅ {result['num_actions']} actions envoyées")
        else:
            print(f"   ❌ {result.get('error')}")

    def handle_feedback(self, user_id: str, action_id: str, accepted: bool, reward: float):
        """Reçoit les feedbacks de Naila"""
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

    # ========== PRÉFÉRENCES ==========

    def setup_preferences(self, user_id: str, preferences: Dict) -> Dict:
        """Configuration des préférences"""
        try:
            success = self.prefs_manager.setup_user_preferences(user_id, preferences)
            if success:
                self.preferences_cache.pop(user_id, None)
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
                "user_target": 22.0,  # ✅ NOUVEAU
                "rooms": {
                    "salon": {"desired_temperature": 22, "desired_brightness": 80},
                    "cuisine": {"desired_temperature": 21, "desired_brightness": 90}
                }
            }
            self.prefs_manager.setup_user_preferences(user_id, default_prefs)
            user = self.prefs_manager.get_user_preferences(user_id)
        return user

    # ========== CŒUR DE LA COMMUNICATION ==========

    def generate_and_publish_actions(self, user_id: str, current_state: Dict) -> Dict:
        """
        Génère les actions ET les publie sur MQTT pour Naila
        ⭐ VERSION CORRIGÉE - Validation + filtrage
        """
        try:
            # 1. Vérifier que l'état n'est pas vide ou invalide
            if not current_state:
                return {"success": False, "error": "État vide reçu"}
            
            print(f"\n📊 État reçu:")
            print(f"   Clés: {list(current_state.keys())}")
            print(f"   Valeurs: {current_state}")

            # 2. Récupérer l'utilisateur
            user = self._get_or_create_user(user_id)
            if not user:
                return {"success": False, "error": "Utilisateur non trouvé"}

            user_prefs = user.get("preferences", {})

            # 3. Générer les actions
            actions = self.action_generator.generate_all_actions(
                user_id=user_id,
                current_state=current_state,
                user_prefs=user_prefs
            )

            print(f"\n📋 Actions générées: {len(actions)}")
            for i, action in enumerate(actions, 1):
                print(f"   {i}. [{action.action_type.value}] {action.description}")

            # 4. ✅ CORRECTION: Valider et filtrer les actions
            validated_actions = self._filter_and_validate_actions(
                actions, current_state
            )

            print(f"\n✅ Actions validées: {len(validated_actions)}")
            for i, action in enumerate(validated_actions, 1):
                print(f"   {i}. {action.description}")

            # 5. ✅ CORRECTION: Limiter le nombre d'actions
            limited_actions = validated_actions[:self.max_actions_per_request]

            if not limited_actions:
                print("⚠️ Aucune action valide générée")
                return {
                    "success": True,
                    "num_actions": 0,
                    "actions": [],
                    "message": "Aucune action recommandée pour l'état actuel"
                }

            actions_dict = [a.to_mqtt_message() for a in limited_actions]

            # 6. Publier sur MQTT pour Naila
            mqtt_success = self.mqtt.publish_actions(
                user_id=user_id,
                actions=actions_dict,
                current_state=current_state,
                user_prefs=user_prefs
            )

            return {
                "success": mqtt_success,
                "num_actions": len(limited_actions),
                "actions": [a.to_dict() for a in limited_actions],
                "mqtt_published": mqtt_success,
                "message": f"✅ {len(limited_actions)} actions valides publiées"
            }

        except Exception as e:
            print(f"❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}

    def _filter_and_validate_actions(self, actions: List, current_state: Dict) -> List:
        """
        ✅ NOUVEAU: Filtre et valide les actions
        - Supprime les actions incohérentes
        - Limite le nombre d'actions par catégorie
        """
        validated = []
        action_counts = {}  # Compter par type
        
        print(f"\n🔍 Validation des {len(actions)} actions...")
        
        for action in actions:
            action_type = action.action_type.value
            
            # ✅ Compter par type
            action_counts[action_type] = action_counts.get(action_type, 0) + 1
            
            # ✅ Rejeter les doublons du même type
            if action_counts[action_type] > 1:
                print(f"   ⛔ REJET DOUBLON: {action_type}")
                continue
            
            # ✅ Validation: Éteindre quelque chose déjà éteint?
            if action_type == "eteindre_lumiere_salon":
                light = current_state.get('lumiere_salon', 0.0)
                if light <= 0.1:  # Déjà éteint
                    print(f"   ⛔ REJET INCOHÉRENT: {action_type} (déjà OFF)")
                    continue
            
            if action_type == "eteindre_lumiere_cuisine":
                light = current_state.get('lumiere_cuisine', 0.0)
                if light <= 0.1:
                    print(f"   ⛔ REJET INCOHÉRENT: {action_type} (déjà OFF)")
                    continue
            
            if action_type == "eteindre_tv_salon":
                tv = current_state.get('tv_on', 0.0)
                if tv <= 0.1:
                    print(f"   ⛔ REJET INCOHÉRENT: {action_type} (déjà OFF)")
                    continue
            
            if action_type == "eteindre_hotte_cuisine":
                hotte = current_state.get('hotte_on', 0.0)
                if hotte <= 0.1:
                    print(f"   ⛔ REJET INCOHÉRENT: {action_type} (déjà OFF)")
                    continue
            
            if action_type == "eteindre_four":
                four = current_state.get('four_on', 0.0)
                if four <= 0.1:
                    print(f"   ⛔ REJET INCOHÉRENT: {action_type} (déjà OFF)")
                    continue
            
            # ✅ Validation: Allumer quelque chose déjà allumé?
            if action_type == "allumer_lumiere_salon":
                light = current_state.get('lumiere_salon', 0.0)
                if light > 0.5:
                    print(f"   ⛔ REJET INCOHÉRENT: {action_type} (déjà ON)")
                    continue
            
            if action_type == "allumer_lumiere_cuisine":
                light = current_state.get('lumiere_cuisine', 0.0)
                if light > 0.5:
                    print(f"   ⛔ REJET INCOHÉRENT: {action_type} (déjà ON)")
                    continue
            
            # ✅ Action valide
            print(f"   ✅ ACCEPTÉ: {action_type}")
            validated.append(action)
        
        return validated

    def close(self):
        """Ferme les connexions"""
        self.mqtt.disconnect()
        print("👋 API fermée")
