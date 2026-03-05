import hashlib
import secrets
from datetime import datetime
from typing import Dict, Any, Optional
import json
import os

class AuthenticationManager:
    """🔐 Gère l'inscription, la connexion et l'authentification"""
    
    def __init__(self, auth_file: str = "data/users_auth.json"):
        self.auth_file = auth_file
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        os.makedirs(os.path.dirname(self.auth_file) or ".", exist_ok=True)
        if not os.path.exists(self.auth_file):
            initial_data = {"users": [], "created_at": datetime.now().isoformat()}
            self._save_to_file(initial_data)
    
    def _load_from_file(self) -> Dict[str, Any]:
        try:
            with open(self.auth_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"users": []}
    
    def _save_to_file(self, data: Dict[str, Any]):
        with open(self.auth_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def _generate_user_id() -> str:
        return f"user_{secrets.token_hex(8)}"
    
    def register_user(self, email: str, name: str, password: str) -> Dict[str, Any]:
        data = self._load_from_file()
        
        if any(u["email"].lower() == email.lower() for u in data["users"]):
            return {"success": False, "error": f"❌ Email {email} est déjà utilisé"}
        
        if not name or len(name.strip()) < 2:
            return {"success": False, "error": "❌ Le nom doit contenir au moins 2 caractères"}
        
        if len(password) < 6:
            return {"success": False, "error": "❌ Le mot de passe doit contenir au moins 6 caractères"}
        
        user_id = self._generate_user_id()
        hashed_password = self._hash_password(password)
        
        new_user = {
            "user_id": user_id,
            "email": email.lower(),
            "name": name.strip(),
            "password_hash": hashed_password,
            "registered_at": datetime.now().isoformat(),
            "last_login": None,
            "is_active": True
        }
        
        data["users"].append(new_user)
        self._save_to_file(data)
        
        return {
            "success": True,
            "user_id": user_id,
            "name": name,
            "email": email,
            "message": f"✅ Bienvenue {name}! Compte créé avec succès!"
        }
    
    def login_user(self, email: str, password: str) -> Dict[str, Any]:
        data = self._load_from_file()
        
        user = next((u for u in data["users"] if u["email"].lower() == email.lower()), None)
        
        if not user:
            return {"success": False, "error": "❌ Email ou mot de passe incorrect"}
        
        hashed_input = self._hash_password(password)
        if user["password_hash"] != hashed_input:
            return {"success": False, "error": "❌ Email ou mot de passe incorrect"}
        
        user["last_login"] = datetime.now().isoformat()
        self._save_to_file(data)
        
        return {
            "success": True,
            "user_id": user["user_id"],
            "name": user["name"],
            "email": user["email"],
            "message": f"✅ Bienvenue {user['name']}!"
        }
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        data = self._load_from_file()
        return next((u for u in data["users"] if u["email"].lower() == email.lower()), None)
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        data = self._load_from_file()
        return next((u for u in data["users"] if u["user_id"] == user_id), None)
    
    def user_exists(self, email: str) -> bool:
        return self.get_user_by_email(email) is not None