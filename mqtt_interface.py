"""
Interface MQTT pour la communication avec Naila (SAC)
Version corrigée — séparation state/power, protection des états HA,
cooldown sur les callbacks, topics avec préfixe unique
"""

from typing import List, Dict, Any, Callable, Optional
import json
import paho.mqtt.client as mqtt
from datetime import datetime
import threading
import time


class MQTTInterface:
    def __init__(self, client_id: str = "tasnim_broker"):
        self.client_id = client_id
        self.client = mqtt.Client(client_id=client_id)
        self.connected = False
        self.feedback_callbacks = {}
        self.state_callbacks = {}

        # ====================================================================
        # ÉTAT DE LA MAISON — variables séparées pour state (on/off) et power
        # ====================================================================
        self.current_house_state = {
            # Capteurs
            'temp_salon': None,
            'temp_cuisine': None,
            'temp_ext': None,
            'user_target': None,
            'presence_salon': None,
            'presence_cuisine': None,
            'heure': None,
            'jour_nuit': None,
            'temp_cuisine_precedente': None,
            'consommation': 0.0,

            # Salon — appareils
            'lumiere_salon': 0.0,       # valeur finale utilisée par le système
            'tv_on': 0.0,
            'clim_salon_power': 0.0,    # valeur finale utilisée par le système
            'chauffage_salon_power': 0.0,

            # Cuisine — appareils
            'lumiere_cuisine': 0.0,     # valeur finale utilisée par le système
            'four_on': 0.0,
            'hotte_on': 0.0,
            'chauffage_cuisine_power': 0.0,  # valeur finale utilisée par le système
        }

        # Variables internes séparées pour éviter les conflits state vs power
        self._light_salon_on = False
        self._light_salon_intensity = 0.0
        self._light_cuisine_on = False
        self._clim_salon_on = False
        self._clim_salon_power_level = 0.0
        self._chauffage_cuisine_on = False
        self._chauffage_cuisine_power_level = 0.0

        # Tracking de la source des données
        self.data_from_ha = False
        self._ha_topics_received = set()

        # Cooldown pour éviter les callbacks trop fréquents
        self._last_state_update_time = 0
        self._state_update_cooldown = 3  # secondes minimum entre 2 callbacks

        # Configuration broker
        self.broker = "broker.hivemq.com"
        self.port = 1883

        # Topics Tasnim <-> Naila
        self.TOPIC_ACTIONS = "pfe_smart_home/tasnim/reco/menu"
        self.TOPIC_FEEDBACK = "pfe_smart_home/naila/feedback"
        self.TOPIC_DEMANDE = "pfe_smart_home/naila/demande"
        self.TOPIC_NAILA_STATE = "pfe_smart_home/naila/state"

        # Topics Home Assistant — avec préfixe unique pour éviter la pollution
        self.HA_PREFIX = "pfe_smart_home/home"
        self.TOPICS_HOMEASSISTANT = [
            f"{self.HA_PREFIX}/sensors/temperatures",
            f"{self.HA_PREFIX}/sensors/presence",
            f"{self.HA_PREFIX}/sensors/time",
            f"{self.HA_PREFIX}/livingroom/light/state",
            f"{self.HA_PREFIX}/livingroom/light/intensity",
            f"{self.HA_PREFIX}/livingroom/tv/state",
            f"{self.HA_PREFIX}/livingroom/ac/state",
            f"{self.HA_PREFIX}/livingroom/ac/power",
            f"{self.HA_PREFIX}/kitchen/light/state",
            f"{self.HA_PREFIX}/kitchen/hood/state",
            f"{self.HA_PREFIX}/kitchen/oven/state",
            f"{self.HA_PREFIX}/kitchen/heating/state",
            f"{self.HA_PREFIX}/kitchen/heating/power",
        ]

        # Callbacks MQTT
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            print(f"✅ MQTT Connecté à {self.broker}")

            # Subscribe to Naila topics
            self.client.subscribe(f"{self.TOPIC_FEEDBACK}/+")
            self.client.subscribe(self.TOPIC_DEMANDE)
            self.client.subscribe(self.TOPIC_NAILA_STATE)

            # Subscribe to HA topics
            for topic in self.TOPICS_HOMEASSISTANT:
                self.client.subscribe(topic)
                print(f"   📡 Abonné à: {topic}")

            # Request fresh states from HA
            self.client.publish(f"{self.HA_PREFIX}/request/states", "get")
            print("   📡 Demande d'états frais envoyée à Home Assistant")

            print("\n📡 EN ATTENTE DES DONNÉES HOME ASSISTANT...")
            print("   ⚠️  Les données simulées NE SERONT PAS utilisées.")
        else:
            print(f"❌ Erreur connexion MQTT: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        self.connected = False
        print("⚠️ MQTT Déconnecté")

    # ====================================================================
    # RECALCUL DES VALEURS FINALES (state + power combinés)
    # ====================================================================

    def _recalculate_lumiere_salon(self):
        """Calcule lumiere_salon à partir du on/off et de l'intensité"""
        if not self._light_salon_on:
            self.current_house_state['lumiere_salon'] = 0.0
        elif self._light_salon_intensity > 0:
            self.current_house_state['lumiere_salon'] = self._light_salon_intensity
        else:
            self.current_house_state['lumiere_salon'] = 1.0  # on sans intensité = 100%

    def _recalculate_lumiere_cuisine(self):
        """Calcule lumiere_cuisine à partir du on/off"""
        self.current_house_state['lumiere_cuisine'] = 1.0 if self._light_cuisine_on else 0.0

    def _recalculate_clim_salon(self):
        """Calcule clim_salon_power à partir du on/off et de la puissance"""
        if not self._clim_salon_on:
            self.current_house_state['clim_salon_power'] = 0.0
        elif self._clim_salon_power_level > 0:
            self.current_house_state['clim_salon_power'] = self._clim_salon_power_level
        else:
            self.current_house_state['clim_salon_power'] = 1.0

    def _recalculate_chauffage_cuisine(self):
        """Calcule chauffage_cuisine_power à partir du on/off et de la puissance"""
        if not self._chauffage_cuisine_on:
            self.current_house_state['chauffage_cuisine_power'] = 0.0
        elif self._chauffage_cuisine_power_level > 0:
            self.current_house_state['chauffage_cuisine_power'] = self._chauffage_cuisine_power_level
        else:
            self.current_house_state['chauffage_cuisine_power'] = 1.0

    # ====================================================================
    # HANDLER PRINCIPAL DES MESSAGES MQTT
    # ====================================================================

    def _on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload_str = msg.payload.decode().strip()

            # Filtrer les messages parasites
            ALLOWED = ['pfe_smart_home']
            if not any(kw in topic for kw in ALLOWED):
                return

            # ============================================================
            # 1. CAPTEURS (SENSORS) — données de Home Assistant
            # ============================================================

            if topic == f"{self.HA_PREFIX}/sensors/temperatures":
                try:
                    payload = json.loads(payload_str)
                    self.current_house_state['temp_salon'] = float(payload.get('salon', self.current_house_state.get('temp_salon', 22.0)))
                    self.current_house_state['temp_cuisine'] = float(payload.get('cuisine', self.current_house_state.get('temp_cuisine', 22.0)))
                    self.current_house_state['temp_ext'] = float(payload.get('exterieure', self.current_house_state.get('temp_ext', 20.0)))
                    self.current_house_state['user_target'] = float(payload.get('target', self.current_house_state.get('user_target', 22.0)))
                    self.current_house_state['temp_cuisine_precedente'] = self.current_house_state['temp_cuisine']
                    self._mark_ha_received("temperatures")
                    print(f"   🌡️ [HA] Salon: {self.current_house_state['temp_salon']}°C | Cuisine: {self.current_house_state['temp_cuisine']}°C | Ext: {self.current_house_state['temp_ext']}°C")
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"   ⚠️ Erreur parsing températures: {e}")
                self._check_all_data_received()

            elif topic == f"{self.HA_PREFIX}/sensors/presence":
                try:
                    payload = json.loads(payload_str)
                    self.current_house_state['presence_salon'] = 1.0 if payload.get('salon') == 'on' else 0.0
                    self.current_house_state['presence_cuisine'] = 1.0 if payload.get('cuisine') == 'on' else 0.0
                    self._mark_ha_received("presence")
                    print(f"   👤 [HA] Présence salon: {'✅' if self.current_house_state['presence_salon'] else '❌'} | cuisine: {'✅' if self.current_house_state['presence_cuisine'] else '❌'}")
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"   ⚠️ Erreur parsing présence: {e}")
                self._check_all_data_received()

            elif topic == f"{self.HA_PREFIX}/sensors/time":
                try:
                    payload = json.loads(payload_str)
                    self.current_house_state['heure'] = float(payload.get('heure', self.current_house_state.get('heure', 12)))
                    self.current_house_state['jour_nuit'] = 1.0 if 6 <= self.current_house_state['heure'] <= 18 else 0.0
                    self._mark_ha_received("time")
                    print(f"   ⏰ [HA] Heure: {self.current_house_state['heure']}h ({'Jour' if self.current_house_state['jour_nuit'] else 'Nuit'})")
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"   ⚠️ Erreur parsing time: {e}")
                self._check_all_data_received()

            # ============================================================
            # 2. ÉTATS DES APPAREILS — state (on/off) et power séparés
            # ============================================================

            # --- LUMIÈRE SALON ---
            elif topic == f"{self.HA_PREFIX}/livingroom/light/state":
                self._light_salon_on = payload_str.lower() == 'on'
                self._recalculate_lumiere_salon()
                self._mark_ha_received("light_salon")
                print(f"   💡 [HA] Lumière salon: {'✅ ON' if self._light_salon_on else '❌ OFF'} → final={self.current_house_state['lumiere_salon']}")

            elif topic == f"{self.HA_PREFIX}/livingroom/light/intensity":
                try:
                    self._light_salon_intensity = float(payload_str)
                    self._recalculate_lumiere_salon()
                    self._mark_ha_received("light_salon_intensity")
                    print(f"   💡 [HA] Intensité salon: {self._light_salon_intensity*100:.0f}% → final={self.current_house_state['lumiere_salon']}")
                except ValueError:
                    pass

            # --- TV SALON ---
            elif topic == f"{self.HA_PREFIX}/livingroom/tv/state":
                is_on = payload_str.lower() == 'on'
                self.current_house_state['tv_on'] = 1.0 if is_on else 0.0
                self._mark_ha_received("tv")
                print(f"   📺 [HA] TV: {'📺 allumée' if is_on else '⬛ éteinte'}")

            # --- CLIM SALON ---
            elif topic == f"{self.HA_PREFIX}/livingroom/ac/state":
                self._clim_salon_on = payload_str.lower() == 'on'
                self._recalculate_clim_salon()
                self._mark_ha_received("ac_salon")
                print(f"   ❄️ [HA] Clim: {'ON' if self._clim_salon_on else 'OFF'} → final={self.current_house_state['clim_salon_power']}")

            elif topic == f"{self.HA_PREFIX}/livingroom/ac/power":
                try:
                    self._clim_salon_power_level = float(payload_str)
                    self._recalculate_clim_salon()
                    self._mark_ha_received("ac_salon_power")
                    print(f"   ❄️ [HA] Puissance clim: {self._clim_salon_power_level*100:.0f}% → final={self.current_house_state['clim_salon_power']}")
                except ValueError:
                    pass

            # --- LUMIÈRE CUISINE ---
            elif topic == f"{self.HA_PREFIX}/kitchen/light/state":
                self._light_cuisine_on = payload_str.lower() == 'on'
                self._recalculate_lumiere_cuisine()
                self._mark_ha_received("light_cuisine")
                print(f"   💡 [HA] Lumière cuisine: {'✅ ON' if self._light_cuisine_on else '❌ OFF'} → final={self.current_house_state['lumiere_cuisine']}")

            # --- HOTTE ---
            elif topic == f"{self.HA_PREFIX}/kitchen/hood/state":
                is_on = payload_str.lower() == 'on'
                self.current_house_state['hotte_on'] = 1.0 if is_on else 0.0
                self._mark_ha_received("hood")
                print(f"   🍳 [HA] Hotte: {'allumée' if is_on else 'éteinte'}")

            # --- FOUR ---
            elif topic == f"{self.HA_PREFIX}/kitchen/oven/state":
                is_on = payload_str.lower() == 'on'
                self.current_house_state['four_on'] = 1.0 if is_on else 0.0
                self._mark_ha_received("oven")
                print(f"   🍕 [HA] Four: {'allumé' if is_on else 'éteint'}")

            # --- CHAUFFAGE CUISINE ---
            elif topic == f"{self.HA_PREFIX}/kitchen/heating/state":
                self._chauffage_cuisine_on = payload_str.lower() == 'on'
                self._recalculate_chauffage_cuisine()
                self._mark_ha_received("heating_cuisine")
                print(f"   🔥 [HA] Chauffage cuisine: {'ON' if self._chauffage_cuisine_on else 'OFF'} → final={self.current_house_state['chauffage_cuisine_power']}")

            elif topic == f"{self.HA_PREFIX}/kitchen/heating/power":
                try:
                    self._chauffage_cuisine_power_level = float(payload_str)
                    self._recalculate_chauffage_cuisine()
                    self._mark_ha_received("heating_cuisine_power")
                    print(f"   🔥 [HA] Puissance chauffage cuisine: {self._chauffage_cuisine_power_level*100:.0f}% → final={self.current_house_state['chauffage_cuisine_power']}")
                except ValueError:
                    pass

            # ============================================================
            # 3. NAILA / FEEDBACK TOPICS
            # ============================================================

            elif topic == self.TOPIC_NAILA_STATE:
                try:
                    data = json.loads(payload_str) if isinstance(payload_str, str) else payload_str
                    naila_state = data.get('state', {})

                    # PROTECTION: Naila ne peut PAS écraser les états d'appareils HA
                    HA_PROTECTED_KEYS = {
                        'lumiere_salon', 'lumiere_cuisine', 'tv_on', 'four_on',
                        'hotte_on', 'clim_salon_power', 'chauffage_cuisine_power',
                        'chauffage_salon_power', 'temp_salon', 'temp_cuisine',
                        'temp_ext', 'presence_salon', 'presence_cuisine'
                    }
                    for key, value in naila_state.items():
                        if key in self.current_house_state and key not in HA_PROTECTED_KEYS:
                            self.current_house_state[key] = value
                        elif key in HA_PROTECTED_KEYS:
                            print(f"   ⛔ [NAILA] Tentative d'écraser '{key}' ignorée (protégé HA)")

                    self._check_all_data_received()
                except Exception:
                    pass

            elif topic.startswith(self.TOPIC_FEEDBACK):
                try:
                    data = json.loads(payload_str)
                    user_id = topic.split("/")[-1]
                    action_id = data.get("action_id")
                    accepted = data.get("accepted", False)
                    reward = data.get("reward", 0)
                    print(f"💬 Feedback de Naila pour {user_id}: {action_id} {'✅' if accepted else '❌'} (reward: {reward})")

                    if user_id in self.feedback_callbacks:
                        self.feedback_callbacks[user_id](user_id, action_id, accepted, reward)
                    elif "default" in self.feedback_callbacks:
                        self.feedback_callbacks["default"](user_id, action_id, accepted, reward)
                except Exception:
                    pass

            elif topic == self.TOPIC_DEMANDE:
                try:
                    data = json.loads(payload_str)
                    user_id = data.get("user_id")
                    etat = data.get("etat", {})
                    print(f"📢 Demande d'actions de Naila pour {user_id}")

                    # PROTECTION: Naila demande ne peut PAS écraser les états HA
                    HA_PROTECTED_KEYS = {
                        'lumiere_salon', 'lumiere_cuisine', 'tv_on', 'four_on',
                        'hotte_on', 'clim_salon_power', 'chauffage_cuisine_power',
                        'chauffage_salon_power', 'temp_salon', 'temp_cuisine',
                        'temp_ext', 'presence_salon', 'presence_cuisine'
                    }
                    for key, value in etat.items():
                        if key in self.current_house_state and key not in HA_PROTECTED_KEYS:
                            self.current_house_state[key] = value

                    if "demande" in self.state_callbacks:
                        self.state_callbacks["demande"](user_id, self.current_house_state)
                except Exception:
                    pass

        except Exception as e:
            print(f"❌ Erreur traitement message: {e}")

    # ====================================================================
    # VÉRIFICATION DES DONNÉES
    # ====================================================================

    def _mark_ha_received(self, source: str):
        """Marque qu'une donnée HA a été reçue"""
        self._ha_topics_received.add(source)
        if not self.data_from_ha:
            self.data_from_ha = True
            print("   ✅ PREMIÈRE DONNÉE RÉELLE DE HOME ASSISTANT REÇUE!")

    def _check_all_data_received(self):
        """Vérifie si toutes les données critiques sont reçues et valides"""
        # Vérifier que les températures ne sont pas 0 ou None (données fausses)
        temp_salon_ok = self.current_house_state['temp_salon'] is not None and self.current_house_state['temp_salon'] != 0
        temp_cuisine_ok = self.current_house_state['temp_cuisine'] is not None and self.current_house_state['temp_cuisine'] != 0
        presence_ok = self.current_house_state['presence_salon'] is not None
        heure_ok = self.current_house_state['heure'] is not None

        all_received = (temp_salon_ok and temp_cuisine_ok and presence_ok and heure_ok)

        if all_received and "state_update" in self.state_callbacks:
            # COOLDOWN: ne pas déclencher trop souvent
            now = time.time()
            if now - self._last_state_update_time < self._state_update_cooldown:
                return
            self._last_state_update_time = now

            source = "HOME ASSISTANT" if self.data_from_ha else "⚠️ DONNÉES PAR DÉFAUT"
            print(f"\n✅ TOUTES LES DONNÉES REÇUES! (source: {source})")
            print(f"   📊 État actuel complet:")
            print(f"      🌡️ Salon={self.current_house_state['temp_salon']}°C | Cuisine={self.current_house_state['temp_cuisine']}°C")
            print(f"      💡 Lumière salon={self.current_house_state['lumiere_salon']} | cuisine={self.current_house_state['lumiere_cuisine']}")
            print(f"      📺 TV={self.current_house_state['tv_on']} | 🍕 Four={self.current_house_state['four_on']}")
            print(f"      👤 Présence salon={self.current_house_state['presence_salon']} | cuisine={self.current_house_state['presence_cuisine']}")
            print(f"   → Génération des actions...")
            self.state_callbacks["state_update"](self.current_house_state)

    def _has_all_data(self):
        """Vérifie si toutes les données sont présentes"""
        return (self.current_house_state['temp_salon'] is not None and
                self.current_house_state['temp_cuisine'] is not None and
                self.current_house_state['presence_salon'] is not None and
                self.current_house_state['presence_cuisine'] is not None and
                self.current_house_state['heure'] is not None)

    def get_state_source(self) -> str:
        """Retourne la source des données actuelles"""
        if self.data_from_ha:
            topics = ", ".join(sorted(self._ha_topics_received))
            return f"HOME ASSISTANT (topics reçus: {topics})"
        else:
            return "⚠️ AUCUNE DONNÉE DE HOME ASSISTANT — valeurs par défaut"

    def _convert_to_naila_state(self, state):
        """Convertit l'état au format de l'environnement Naila"""
        heure = int(state.get('heure', 12))
        jour_nuit = 1.0 if 6 <= heure <= 18 else 0.0
        return {
            'temp_salon': float(state.get('temp_salon', 22.0)),
            'temp_cuisine': float(state.get('temp_cuisine', 22.0)),
            'temp_ext': float(state.get('temp_ext', 20.0)),
            'user_target': float(state.get('user_target', 22.0)),
            'presence_salon': bool(state.get('presence_salon', False)),
            'presence_cuisine': bool(state.get('presence_cuisine', False)),
            'heure': heure,
            'jour_nuit': jour_nuit,
            'clim_salon_power': float(state.get('clim_salon_power', 0.0)),
            'chauffage_salon_power': float(state.get('chauffage_salon_power', 0.0)),
            'lumiere_salon': float(state.get('lumiere_salon', 0.0)),
            'tv_on': float(state.get('tv_on', 0.0)),
            'four_on': float(state.get('four_on', 0.0)),
            'hotte_on': float(state.get('hotte_on', 0.0)),
            'chauffage_cuisine_power': float(state.get('chauffage_cuisine_power', 0.0)),
            'lumiere_cuisine': float(state.get('lumiere_cuisine', 0.0)),
            'temp_cuisine_precedente': float(state.get('temp_cuisine_precedente', state.get('temp_cuisine', 22.0))),
            'consommation': float(state.get('consommation', 0.0))
        }

    def get_current_state(self):
        """Retourne le dernier état reçu"""
        return self.current_house_state.copy()

    def connect(self):
        """Connexion au broker"""
        try:
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            time.sleep(1)
            return True
        except Exception as e:
            print(f"❌ Erreur connexion: {e}")
            return False

    def disconnect(self):
        """Déconnexion"""
        self.client.loop_stop()
        self.client.disconnect()

    def publish_actions(self, user_id, actions, current_state, user_prefs=None):
        """Publie les actions pour Naila"""
        try:
            naila_state = self._convert_to_naila_state(current_state)

            # Combine state and user preferences into the format Naila expects
            combined_prefs = {}
            if user_prefs:
                combined_prefs.update(user_prefs)
            combined_prefs.update(naila_state)

            message = {
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "user_preferences": combined_prefs,
                "actions": actions,
                "num_actions": len(actions),
                "data_source": "home_assistant" if self.data_from_ha else "default_values"
            }
            payload = json.dumps(message, ensure_ascii=False, default=str)
            result = self.client.publish(self.TOPIC_ACTIONS, payload, qos=1)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                source_tag = "✅ HA" if self.data_from_ha else "⚠️ DEFAULT"
                print(f"📤 {len(actions)} actions publiées pour {user_id} [{source_tag}]")
                return True
            return False
        except Exception as e:
            print(f"❌ Erreur publication: {e}")
            return False

    def register_feedback_callback(self, user_id, callback):
        """Enregistre un callback pour les feedbacks"""
        self.feedback_callbacks[user_id] = callback
        print(f"📝 Callback feedback enregistré pour {user_id}")

    def register_state_callback(self, callback_type, callback):
        """Enregistre un callback pour les mises à jour d'état"""
        self.state_callbacks[callback_type] = callback
        print(f"📝 Callback état '{callback_type}' enregistré")

        # Si les données sont déjà disponibles, déclencher immédiatement
        if callback_type == "state_update" and self._has_all_data():
            if self.data_from_ha:
                print("   ↪ Données HA déjà disponibles, déclenchement immédiat!")
                callback(self.current_house_state)
            else:
                print("   ↪ Données par défaut seulement — attente de HA...")

    def register_naila_callback(self, callback_type, callback):
        """Enregistre un callback pour les demandes de Naila"""
        self.register_state_callback(callback_type, callback)
        print(f"📝 Callback Naila '{callback_type}' enregistré")
