"""
Test complet du système réaliste
1. Inscription utilisateur
2. Configuration des préférences
3. Génération de recommandations
4. Feedback utilisateur
"""

import json
from datetime import datetime
from api_interface import RecommendationAPI
from data_simulator import IoTSimulator

print("\n" + "="*70)
print("🚀 TEST COMPLET - SYSTÈME RÉALISTE")
print("="*70)

api = RecommendationAPI()
simulator = IoTSimulator()

# ============================================
# 1️⃣ INSCRIPTION
# ============================================
print("\n1️⃣ INSCRIPTION D'UN UTILISATEUR")
print("-"*70)

reg = api.register_user(
    email="tasnim@example.com",
    name="Tasnim",
    password="monmotdepasse"
)

if not reg["success"]:
    print(f"❌ {reg['error']}")
    exit()

user_id = reg["user_id"]
print(f"✅ {reg['message']}")
print(f"   ID utilisateur: {user_id}")

# ============================================
# 2️⃣ CONNEXION
# ============================================
print("\n2️⃣ CONNEXION DE L'UTILISATEUR")
print("-"*70)

login = api.login_user("tasnim@example.com", "monmotdepasse")

if not login["success"]:
    print(f"❌ {login['error']}")
    exit()

print(f"✅ {login['message']}")

# ============================================
# 3️⃣ CONFIGURATION DES PRÉFÉRENCES
# ============================================
print("\n3️⃣ L'UTILISATEUR CONFIGURE SES PRÉFÉRENCES")
print("-"*70)

preferences = {
    "global_comfort_level": "normal",
    "rooms": {
        "salon": {
            "desired_temperature": 22,
            "desired_brightness": 80,
            "priority": "comfort"
        },
        "cuisine": {
            "desired_temperature": 21,
            "desired_brightness": 90,
            "priority": "comfort"
        }
    }
}

print("Préférences configurées:")
for room, pref in preferences["rooms"].items():
    print(f"  {room}: {pref['desired_temperature']}°C, {pref['desired_brightness']}%")

setup = api.setup_preferences(user_id, preferences)
print(f"✅ {setup['message']}")

# ============================================
# 4️⃣ ÉTAT ACTUEL SIMULÉ (format Naila)
# ============================================
print("\n4️⃣ ÉTAT ACTUEL (format Naila)")
print("-"*70)

current_state = {
    'temp_salon': 25.0,
    'temp_cuisine': 24.0,
    'temp_ext': 20.0,
    'heure': 14,
    'presence_salon': True,
    'presence_cuisine': False,
    'salon_light_on': 80.0,
    'cuisine_light_on': 0.0,
    'tv_on': 1.0,
    'four_on': 0.0,
    'timer_four': 0,
    'consommation': 2.5
}

print("État simulé:")
for key, value in current_state.items():
    print(f"  {key}: {value}")

# ============================================
# 5️⃣ GÉNÉRATION ET PUBLICATION DES ACTIONS
# ============================================
print("\n5️⃣ GÉNÉRATION ET PUBLICATION DES ACTIONS")
print("-"*70)

result = api.generate_and_publish_actions(
    user_id=user_id,
    current_state=current_state
)

if not result["success"]:
    print(f"❌ {result['error']}")
    exit()

print(f"✅ {result['num_actions']} actions générées!")
print(f"📤 Publication MQTT: {'✅' if result['mqtt_published'] else '❌'}")

print("\n📋 TOP 5 ACTIONS:")
for i, action in enumerate(result['actions'][:5], 1):
    print(f