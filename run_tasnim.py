import time
import threading
import json
from typing import Dict
from api_interface import RecommendationAPI

class TasnimAutomatique:
    def __init__(self):
        self.running = True
        self.dernier_etat = None
        self.premiere_donnee_recue = False
        
        # --- CONFIGURATION CRITIQUE ---
        # On utilise l'ID exact que Naila et l'App attendent
        self.user_id = "69aced61ef5d125fc18e5fac" 
        
        # ✅ Initialisation des attributs manquants
        self.last_send_time = time.time()
        self.min_interval_between_sends = 10  # 10 secondes pour les tests
        
        print("="*60)
        print(f"🚀 TASNIM DÉMARRÉ - CIBLE : {self.user_id}")
        print("="*60)
        
        # ✅ Initialisation de l'API avec gestion d'erreur
        self.api = None
        try:
            self.api = RecommendationAPI()
            # Enregistrer le callback pour Home Assistant
            self.api.mqtt.register_state_callback("state_update", self.on_state_update)
        except Exception as e:
            print(f"❌ Erreur Initialisation API : {e}")
            return

        # ✅ Initialisation du thread
        self.thread = threading.Thread(target=self._verification_periodique)
        self.thread.daemon = True

    def on_state_update(self, etat: Dict):
        """
        Cette fonction se déclenche dès que Home Assistant envoie une donnée.
        """
        # ✅ Vérifier que l'API est bien initialisée
        if self.api is None:
            print("⚠️ API non initialisée, impossible d'envoyer")
            return
            
        self.premiere_donnee_recue = True
        self.dernier_etat = etat.copy()
        
        # ✅ Vérifier que les données ne sont pas fausses
        # Si les données sont manifestement fausses (température 0°C), on attend
        if etat.get('temp_salon', 0) == 0 and etat.get('temp_cuisine', 0) == 0:
            print("⚠️ Données HA suspectes (température 0°C) - Attente de vraies données...")
            return
        
        current_time = time.time()
        # On vérifie si on a attendu assez longtemps depuis le dernier envoi
        if current_time - self.last_send_time >= self.min_interval_between_sends:
            self.last_send_time = current_time
            
            print(f"\n📡 DONNÉES REÇUES -> ENVOI À NAILA")
            print(f"   🌡️ Salon: {etat.get('temp_salon')}°C | 👤 Présence: {etat.get('presence_salon')}")
            print(f"   🌡️ Cuisine: {etat.get('temp_cuisine')}°C | 👤 Présence: {etat.get('presence_cuisine')}")
            print(f"   ⏰ Heure: {etat.get('heure')}h")

            # ✅ ENVOI UNIQUEMENT À NAILA (via MQTT)
            result = self.api.generate_and_publish_actions(self.user_id, etat)
            
            if result.get("success"):
                print(f"✅ Menu envoyé à Naila ({result.get('num_actions')} actions).")
                # Afficher les actions envoyées (sans amplitude)
                for i, action in enumerate(result.get('actions', [])[:3], 1):
                    print(f"   {i}. {action.get('description')}")
            else:
                print(f"❌ Erreur lors de l'envoi : {result.get('error')}")

    def _force_first_send(self):
        """ Force un envoi immédiat pour tester la chaîne complète """
        if self.api is None:
            print("⚠️ API non initialisée")
            return
            
        print("\n⚡ TEST DE CONNEXION : Envoi d'un état simulé...")
        etat_test = {
            'temp_salon': 25.5, 
            'temp_cuisine': 22.0, 
            'temp_ext': 20.0,
            'user_target': 22.0,
            'presence_salon': True, 
            'presence_cuisine': False, 
            'heure': 19,
            'jour_nuit': 0.0,
            'lumiere_salon': 0.0,
            'lumiere_cuisine': 0.0,
            'tv_on': 1.0,
            'four_on': 0.0,
            'hotte_on': 0.0,
            'clim_salon_power': 0.0,
            'chauffage_cuisine_power': 0.0
        }
        result = self.api.generate_and_publish_actions(self.user_id, etat_test)
        if result.get("success"):
            print(f"✅ Test réussi : {result.get('num_actions')} actions envoyées")

    def _verification_periodique(self):
        """Vérifie périodiquement si on a reçu des données"""
        while self.running:
            if not self.premiere_donnee_recue:
                print("⏳ En attente de données provenant de Home Assistant...")
            time.sleep(15)

    def run(self):
        """Lance le système"""
        if self.api is None:
            print("❌ API non initialisée, impossible de démarrer")
            return

        print(f"\n📡 Écoute des topics Home Assistant...")
        print(f"📤 Envoi des menus sur : pfe_smart_home/tasnim/reco/menu")
        print(f"   (les actions sont envoyées UNIQUEMENT à Naila)")
        
        # ✅ Lance un envoi de test au démarrage pour réveiller Naila
        self._force_first_send()
        
        # ✅ Démarrer le thread de vérification
        self.thread.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Arrêt de Tasnim...")
            self.running = False
            if self.api:
                self.api.close()
            print("✅ Tasnim arrêté proprement")

if __name__ == "__main__":
    tasnim = TasnimAutomatique()
    tasnim.run()