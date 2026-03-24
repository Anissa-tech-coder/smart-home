import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from config import ROOMS

class UserPreferencesManager:
    """Gère les préférences - L'utilisateur CHOISIT ses paramètres!"""
    
    def __init__(self, preferences_file: str = "data/user_preferences.json"):
        self.preferences_file = preferences_file
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        dir_path = os.path.dirname(self.preferences_file)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        if not os.path.exists(self.preferences_file):
            default_data = {"users": [], "created_at": datetime.now().isoformat()}
            self._save_to_file(default_data)
    
    def _load_from_file(self) -> Dict[str, Any]:
        try:
            with open(self.preferences_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {"users": []}
    
    def _save_to_file(self, data: Dict[str, Any]):
        with open(self.preferences_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def create_user_profile(self, user_id: str, name: str, email: str = "") -> Dict[str, Any]:
        """Crée un profil utilisateur avec les préférences (user_target inclus)"""
        data = self._load_from_file()
        
        if any(u["user_id"] == user_id for u in data["users"]):
            return None
        
        # ✅ CORRECTION: email optionnel
        user_profile = {
            "user_id": user_id,
            "name": name,
            "email": email or f"{user_id}@default.local",
            "created_at": datetime.now().isoformat(),
            "preferences": {
                "global_comfort_level": "normal",
                "user_target": 22.0,  # ✅ Température cible globale
                "rooms": {room: {
                    "desired_temperature": 22,
                    "desired_brightness": 80,
                    "appliances_allowed": True,
                    "priority": "comfort"
                } for room in ROOMS}
            },
            "preferences_configured": False,
            "action_history": []
        }
        
        data["users"].append(user_profile)
        self._save_to_file(data)
        print(f"✅ Profil créé pour {name} ({user_id})")
        return user_profile
    
    def setup_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """L'UTILISATEUR configure ses préférences"""
        data = self._load_from_file()
        
        for user in data["users"]:
            if user["user_id"] == user_id:
                user["preferences"] = preferences
                user["preferences_configured"] = True
                user["preferences_configured_at"] = datetime.now().isoformat()
                self._save_to_file(data)
                print(f"✅ Préférences configurées pour {user_id}")
                return True
        
        return False
    
    def get_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Récupère le profil complet d'un utilisateur"""
        data = self._load_from_file()
        for user in data["users"]:
            if user["user_id"] == user_id:
                return user
        return None
    
    def get_user_preferences_summary(self, user_id: str) -> Dict[str, Any]:
        """Récupère un résumé des préférences"""
        user = self.get_user_preferences(user_id)
        if not user:
            return {}
        prefs = user["preferences"]
        return {
            "global_comfort_level": prefs.get("global_comfort_level"),
            "user_target": prefs.get("user_target", 22.0),  # ✅ Inclure user_target
            "rooms": prefs.get("rooms", {}),
            "configured": user.get("preferences_configured", False)
        }
    
    def update_user_target(self, user_id: str, target_temp: float) -> bool:
        """Met à jour la température cible globale de l'utilisateur"""
        data = self._load_from_file()
        for user in data["users"]:
            if user["user_id"] == user_id:
                user["preferences"]["user_target"] = float(target_temp)
                self._save_to_file(data)
                return True
        return False
    
    def update_global_comfort_level(self, user_id: str, level: str) -> bool:
        """Met à jour le niveau de confort global"""
        data = self._load_from_file()
        for user in data["users"]:
            if user["user_id"] == user_id:
                user["preferences"]["global_comfort_level"] = level
                self._save_to_file(data)
                return True
        return False
    
    def log_action(self, user_id: str, action: Dict[str, Any], accepted: bool, reason: str = "") -> bool:
        """Enregistre une action dans l'historique"""
        data = self._load_from_file()
        for user in data["users"]:
            if user["user_id"] == user_id:
                action_record = {
                    "timestamp": datetime.now().isoformat(),
                    "action": action,
                    "accepted": accepted,
                    "reason": reason
                }
                user["action_history"].append(action_record)
                self._save_to_file(data)
                return True
        return False
    
    def get_action_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Récupère l'historique des actions d'un utilisateur"""
        user = self.get_user_preferences(user_id)
        if user:
            return user.get("action_history", [])
        return []
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Récupère tous les utilisateurs"""
        data = self._load_from_file()
        return data.get("users", [])
