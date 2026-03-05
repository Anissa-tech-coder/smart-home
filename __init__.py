# Créer ce fichier pour que Python reconnaisse le package
"""
Package de recommandation énergétique
"""
from .authentication import AuthenticationManager
from .user_preferences import UserPreferencesManager
from .actions import Action, ActionGenerator, ActionType
from .recommendation_engine import RecommendationEngine
from .mqtt_interface import MQTTInterface
from .api_interface import RecommendationAPI