#  Système de Recommandation Énergétique - TASNIM

##  Ma Tâche

Créer un moteur de recommandation intelligent qui propose des actions pour économiser l'énergie en fonction des vraies préférences de l'utilisateur.

Status: COMPLÉTÉ ET FONCTIONNEL

---

##  Objectif Principal

Recommander des réglages d'énergie basés sur:
- Ce que l'utilisateur a CHOISI (température, luminosité, priorité)
- L'économie d'énergie possible
- L'impact sur le confort

---

##  Mes Fichiers

| Fichier | Rôle |
|---------|------|
| `authentication.py` |  Gestion des comptes (email + mot de passe) |
| `user_preferences.py` |  Stockage des préférences utilisateur |
| `actions.py` |  Génération des actions recommandées |
| `energy_calculator.py` |  Calcul des économies énergétiques |
| `recommendation_engine.py` |  Moteur de recommandation |
| `api_interface.py` |  API pour Nadine et Naila |
| `mqtt_interface.py` |  Communication MQTT pour Naila |
| `metrics.py` |  Métriques de performance |
| `test_demo.py` |  Test complet |

---

##  Fonctionnement Simple

### Étape 1: L'utilisateur s'inscrit (NADINE le fait)
```python
api.register_user(
    email="tasnim@example.com",
    name="Tasnim",
    password="monmotdepasse"
)

Étape 2: L'utilisateur configure ses préférences (NADINE le fait)


Étape 3: MOI je génère les recommandations:

# Je regarde ce qu'il a choisi et je propose des actions

recommendations = api.get_recommendations(
    user_id=user_id,
    current_state={"salon": {"temperature": 23, "brightness": 90}},
    max_recommendations=5
)

# Je propose:
# "La température actuelle est 23°C, vous avez choisi 22°C"
# "→ Réduire de 1°C économiserait 0.05 kWh"


Étape 4: L'utilisateur accepte ou refuse (NADINE le fait)


Étape 5: NAILA apprend de ça

# NAILA récupère l'historique pour son RL
history = api.get_action_history(user_id)
# Elle voit: "L'utilisateur a accepté cette action"
# → Elle apprend


  Ce que je recommande:
 

1.Ajustements de température:

Règle:
- Si température actuelle > température désirée
  → Recommander de réduire
- Si température actuelle < température désirée
  → Recommander d'augmenter


2.Ajustements de luminosité:

Règle:
- Si luminosité actuelle > luminosité désirée
  → Recommander de réduire
- Si luminosité actuelle < luminosité désirée
  → Recommander d'augmenter


3.Mode économie:

Règle:
- Si mode = "eco"
  → Proposer -1°C, -10% luminosité
- Si mode = "normal"
  → Proposer valeurs exactes
- Si mode = "confort"
  → Proposer +0.5°C, +5% luminosité



Calcul des économies:

Pour chaque recommandation, je calcule:
HEURE:
  Énergie = 0.05 kWh
  Coût = 0.05 × 0.15€ = 0.0075€

JOUR (24h):
  Énergie = 0.05 × 24 = 1.2 kWh
  Coût = 1.2 × 0.15€ = 0.18€

MOIS (30j):
  Énergie = 1.2 × 30 = 36 kWh
  Coût = 36 × 0.15€ = 5.4€

AN (365j):
  Énergie = 1.2 × 365 = 438 kWh
  Coût = 438 × 0.15€ = 65.7€



 Mon API (pour Nadine et Naila):

Endpoints que je fournis:

1.Inscription (Nadine l'utilise):

api.register_user(email, name, password)

2. Connexion (Nadine l'utilise):

api.login_user(email, password)

3.Configuration préférences (Nadine l'utilise):

api.setup_user_preferences(user_id, preferences)

4.Générer recommandations (Nadine l'utilise):

api.get_recommendations(user_id, current_state, max_recommendations=5)

5.Enregistrer feedback (Nadine l'utilise):

api.submit_user_feedback(user_id, action_id, accepted, reason="")

6.Récupérer historique (Naila l'utilise):

api.get_action_history(user_id)



Communication avec NAILA (MQTT):

Je publie sur MQTT:

Topic: tasnim/recommendations/{user_id}
Message: Les recommandations générées

Topic: tasnim/action_history/{user_id}
Message: L'historique de toutes les actions

Naila s'abonne à ces topics pour apprendre.



Test de ma tâche:

python test_demo.py

Résultat attendu:

 TEST TERMINÉ AVEC SUCCÈS!

Ce que ça teste:
1. Inscription 
2. Connexion 
3. Configuration des préférences 
4. Génération de recommandations 
5. Feedback utilisateur 
6. Historique pour Naila 



Métriques que j'utilise:

Authentification:
  Email unique (pas de doublon)
  Mot de passe hashé
  Last login
Préférences:
 Température désirée par pièce
 Luminosité désirée par pièce
 Priorité (economy/comfort)
 Niveau confort (eco/normal/confort)
Recommandations:
 Action ID (unique)
 Description claire
 Valeur actuelle vs recommandée
 Énergie économisée (kWh)
 Impact sur confort (positive/neutral/negative)
 Priorité (1-3)
Énergétique:
 kWh par heure
 kWh par jour (×24)
 kWh par mois (×30)
 kWh par an (×365)
 Coût associé (€)
Feedback:
 Acceptée ou refusée
 Raison du choix
 Timestamp



Résumé de ma tâche:
1.Créer système d'authentification
2. Gérer les préférences utilisateur
3. Générer des recommandations intelligentes
4. Calculer les économies
5. Enregistrer le feedback
6. Fournir API pour Nadine
7. Fournir données pour Naila (MQTT)

