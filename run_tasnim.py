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

        # --- CONFIGURATION ---
        self.user_id = "69aced61ef5d125fc18e5fac"

        self.last_send_time = time.time()
        self.min_interval_between_sends = 10  # 10 secondes pour les tests

        print("=" * 60)
        print(f"🚀 TASNIM DÉMARRÉ - CIBLE : {self.user_id}")
        print("=" * 60)

        # Initialisation de l'API
        self.api = None
        try:
            self.api = RecommendationAPI()
            # Enregistrer le callback pour Home Assistant
            self.api.mqtt.register_state_callback("state_update", self.on_state_update)
        except Exception as e:
            print(f"❌ Erreur Initialisation API : {e}")
            return

        # Thread de vérification
        self.thread = threading.Thread(target=self._verification_periodique)
        self.thread.daemon = True

    def on_state_update(self, etat: Dict):
        """
        Callback déclenché quand Home Assistant envoie de VRAIES données.
        Ne se déclenche PLUS avec des données par défaut.
        """
        if self.api is None:
            print("⚠️ API non initialisée, impossible d'envoyer")
            return

        self.premiere_donnee_recue = True
        self.dernier_etat = etat.copy()

        # Vérifier que les données ne sont pas manifestement fausses
        if etat.get('temp_salon', 0) == 0 and etat.get('temp_cuisine', 0) == 0:
            print("⚠️ Données HA suspectes (température 0°C) - Attente de vraies données...")
            return

        # Vérifier que les données viennent bien de Home Assistant
        data_source = self.api.mqtt.get_state_source()
        if not self.api.mqtt.data_from_ha:
            print(f"⚠️ DONNÉES NON RÉELLES ignorées. Source: {data_source}")
            print("   → L'agent RL ne doit apprendre que sur des données réelles!")
            return

        current_time = time.time()
        if current_time - self.last_send_time >= self.min_interval_between_sends:
            self.last_send_time = current_time

            print(f"\n{'='*60}")
            print(f"📡 DONNÉES RÉELLES HA → ENVOI À NAILA")
            print(f"   Source: {data_source}")
            print(f"   🌡️ Salon: {etat.get('temp_salon')}°C | 👤 Présence: {etat.get('presence_salon')}")
            print(f"   🌡️ Cuisine: {etat.get('temp_cuisine')}°C | 👤 Présence: {etat.get('presence_cuisine')}")
            print(f"   💡 Lumière salon: {etat.get('lumiere_salon')} | cuisine: {etat.get('lumiere_cuisine')}")
            print(f"   📺 TV: {etat.get('tv_on')} | 🍕 Four: {etat.get('four_on')}")
            print(f"   ⏰ Heure: {etat.get('heure')}h")
            print(f"{'='*60}")

            # ENVOI UNIQUEMENT À NAILA (via MQTT)
            result = self.api.generate_and_publish_actions(self.user_id, etat)

            if result.get("success"):
                print(f"✅ Menu envoyé à Naila ({result.get('num_actions')} actions).")
                for i, action in enumerate(result.get('actions', [])[:5], 1):
                    print(f"   {i}. {action.get('description')}")
            else:
                print(f"❌ Erreur lors de l'envoi : {result.get('error')}")

    def _verification_periodique(self):
        """Vérifie périodiquement la réception des données HA"""
        wait_count = 0
        while self.running:
            if not self.premiere_donnee_recue:
                wait_count += 1
                print(f"⏳ [{wait_count * 15}s] En attente de données Home Assistant...")
                print(f"   Source actuelle: {self.api.mqtt.get_state_source()}")
                print(f"   Topics HA reçus: {self.api.mqtt._ha_topics_received or 'aucun'}")

                if wait_count >= 4:  # après 60 secondes
                    print("\n" + "!" * 60)
                    print("⚠️  AUCUNE DONNÉE DE HOME ASSISTANT REÇUE APRÈS 60s")
                    print("   Vérifiez que Nadine publie sur les topics:")
                    for topic in self.api.mqtt.TOPICS_HOMEASSISTANT[:5]:
                        print(f"     → {topic}")
                    print("!" * 60 + "\n")
                    wait_count = 0  # reset pour réafficher après 60s
            else:
                # Afficher l'état périodiquement
                state = self.api.mqtt.get_current_state()
                print(f"\n📊 État actuel (source: {'HA ✅' if self.api.mqtt.data_from_ha else '⚠️ défaut'}):")
                print(f"   💡 Lumière salon={state.get('lumiere_salon')} | cuisine={state.get('lumiere_cuisine')}")
                print(f"   📺 TV={state.get('tv_on')} | ❄️ Clim={state.get('clim_salon_power')}")

            time.sleep(15)

    def run(self):
        """Lance le système — attend les VRAIES données de HA"""
        if self.api is None:
            print("❌ API non initialisée, impossible de démarrer")
            return

        print(f"\n📡 Écoute des topics Home Assistant...")
        print(f"   Topics HA: {self.api.mqtt.HA_PREFIX}/*")
        print(f"📤 Envoi des menus sur : {self.api.mqtt.TOPIC_ACTIONS}")
        print(f"   (les actions sont envoyées UNIQUEMENT à Naila)")

        print("\n" + "=" * 60)
        print("⚠️  PAS D'ENVOI DE DONNÉES SIMULÉES AU DÉMARRAGE")
        print("   Le système attend les VRAIES données de Home Assistant")
        print("   pour que l'agent RL apprenne sur des cas RÉELS.")
        print("=" * 60)

        # Démarrer le thread de vérification
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
