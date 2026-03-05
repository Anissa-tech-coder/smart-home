"""Exceptions personnalisées du système"""

class SmartHomeException(Exception):
    """Classe de base pour toutes les exceptions"""
    pass

class UserNotFoundError(SmartHomeException):
    """L'utilisateur n'existe pas"""
    pass

class InvalidPreferenceError(SmartHomeException):
    """Les préférences sont invalides"""
    pass

class InvalidActionError(SmartHomeException):
    """L'action est invalide"""
    pass

class AuthenticationError(SmartHomeException):
    """Erreur d'authentification"""
    pass