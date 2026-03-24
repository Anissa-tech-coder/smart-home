"""
Interface MQTT pour la communication avec Naila (SAC)
Version avec intégration complète des états Home Assistant
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
        
        # Stockage du dernier état reçu - INITIALISÉ À None
        self.current_house_state = {
            'temp_salon': None,
            'temp_cuisine': None,
            'temp_ext': None,
            'user_target': None,
            'presence_salon': None,
            'presence_cuisine': None,
            'heure': None,
            'jour_nuit': None,
            'clim_salon_power': 0.0,
            'chauffage_salon_power': 0.0,
            'lumiere_salon': 0.0,
            'tv_on': 0.0,
            'four_on': 0.0,
            'hotte_on': 0.0,
            'chauffage_cuisine_power': 0.0,
            'lumiere_cuisine': 0.0,
            'temp_cuisine_precedente': None,
            'consommation': 0.0
        }
        
        # Configuration broker
        self.broker = "broker.hivemq.com"
        self.port = 1883
        
        # Topics Tasnim <-> Naila
        self.TOPIC_ACTIONS = "pfe_smart_home/tasnim/reco/menu"
        self.TOPIC_FEEDBACK = "pfe_smart_home/naila/feedback"
        self.TOPIC_DEMANDE = "pfe_smart_home/naila/demande"
        self.TOPIC_NAILA_STATE = "pfe_smart_home/naila/state"
        
        # Topics Home Assistant
        self.TOPICS_HOMEASSISTANT = [
            "home/sensors/temperatures",
            "home/sensors/presence",
            "home/sensors/time",
            "home/livingroom/light/state",
            "home/livingroom/light/intensity",
            "home/livingroom/tv/state",
            "home/livingroom/ac/state",
            "home/livingroom/ac/power",
            "home/kitchen/light/state",
            "home/kitchen/hood/state",
            "home/kitchen/oven/state",
            "home/kitchen/heating/state",
            "home/kitchen/heating/power",
            "home/global/state",
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
            self.client.publish("home/request/states", "get")
            print("   📡 Demande d'états frais envoyée à Home Assistant")
            
            print("\n📡 EN ATTENTE DES DONNÉES HOME ASSISTANT...")
        else:
            print(f"❌ Erreur connexion MQTT: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        self.connected = False
        print("⚠️ MQTT Déconnecté")
    
    def _on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload_str = msg.payload.decode().strip()
            
            # Filtrer les messages des inconnus
            ALLOWED = ['livingroom', 'kitchen', 'sensors', 'global', 'pfe_smart_home']
            if not any(kw in topic for kw in ALLOWED):
                return
            
            print(f"📥 Message reçu: {topic}")
            
            # ============================================================
            # 1. SYNCHRONISATION DES CAPTEURS (SENSORS)
            # ============================================================
            
            if topic == "home/sensors/temperatures":
                try:
                    payload = json.loads(payload_str)
                    self.current_house_state['temp_salon'] = float(payload.get('salon', self.current_house_state.get('temp_salon', 22.0)))
                    self.current_house_state['temp_cuisine'] = float(payload.get('cuisine', self.current_house_state.get('temp_cuisine', 22.0)))
                    self.current_house_state['temp_ext'] = float(payload.get('exterieure', self.current_house_state.get('temp_ext', 20.0)))
                    self.current_house_state['temp_cuisine_precedente'] = self.current_house_state['temp_cuisine']
                    print(f"   🌡️ Salon: {self.current_house_state['temp_salon']}°C | Cuisine: {self.current_house_state['temp_cuisine']}°C | Ext: {self.current_house_state['temp_ext']}°C")
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"   ⚠️ Erreur parsing températures: {e}")
                self._check_all_data_received()
            
            elif topic == "home/sensors/presence":
                try:
                    payload = json.loads(payload_str)
                    self.current_house_state['presence_salon'] = 1.0 if payload.get('salon') == 'on' else 0.0
                    self.current_house_state['presence_cuisine'] = 1.0 if payload.get('cuisine') == 'on' else 0.0
                    print(f"   👤 Présence salon: {'✅' if self.current_house_state['presence_salon'] else '❌'} | cuisine: {'✅' if self.current_house_state['presence_cuisine'] else '❌'}")
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"   ⚠️ Erreur parsing présence: {e}")
                self._check_all_data_received()
            
            elif topic == "home/sensors/time":
                try:
                    payload = json.loads(payload_str)
                    self.current_house_state['heure'] = float(payload.get('heure', self.current_house_state.get('heure', 12)))
                    self.current_house_state['jour_nuit'] = 1.0 if 6 <= self.current_house_state['heure'] <= 18 else 0.0
                    print(f"   ⏰ Heure: {self.current_house_state['heure']}h ({'Jour' if self.current_house_state['jour_nuit'] else 'Nuit'})")
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"   ⚠️ Erreur parsing time: {e}")
                self._check_all_data_received()
            
            # ============================================================
            # 2. ÉTATS DES APPAREILS (DEVICE STATES)
            # ============================================================
            
            elif topic == "home/livingroom/ac/power":
                try:
                    self.current_house_state['clim_salon_power'] = float(payload_str)
                    print(f"   ❄️ Puissance clim salon: {self.current_house_state['clim_salon_power']*100:.0f}%")
                except ValueError:
                    pass
            
            elif topic == "home/livingroom/light/intensity":
                try:
                    self.current_house_state['lumiere_salon'] = float(payload_str)
                    print(f"   💡 Intensité salon: {self.current_house_state['lumiere_salon']*100:.0f}%")
                except ValueError:
                    pass
            
            elif topic == "home/livingroom/light/state":
                is_on = payload_str.lower() == 'on'
                self.current_house_state['lumiere_salon'] = 1.0 if is_on else 0.0
                print(f"   💡 Lumière salon: {'✅ ON' if is_on else '❌ OFF'}")
            
            elif topic == "home/livingroom/tv/state":
                is_on = payload_str.lower() == 'on'
                self.current_house_state['tv_on'] = 1.0 if is_on else 0.0
                print(f"   📺 TV: {'📺 allumée' if is_on else '⬛ éteinte'}")
            
            elif topic == "home/livingroom/ac/state":
                is_on = payload_str.lower() == 'on'
                self.current_house_state['clim_salon_power'] = 1.0 if is_on else 0.0
                print(f"   ❄️ Clim: {'ON' if is_on else 'OFF'}")
            
            elif topic == "home/kitchen/light/state":
                is_on = payload_str.lower() == 'on'
                self.current_house_state['lumiere_cuisine'] = 1.0 if is_on else 0.0
                print(f"   💡 Lumière cuisine: {'✅ ON' if is_on else '❌ OFF'}")
            
            elif topic == "home/kitchen/hood/state":
                is_on = payload_str.lower() == 'on'
                self.current_house_state['hotte_on'] = 1.0 if is_on else 0.0
                print(f"   🍳 Hotte: {'allumée' if is_on else 'éteinte'}")
            
            elif topic == "home/kitchen/oven/state":
                is_on = payload_str.lower() == 'on'
                self.current_house_state['four_on'] = 1.0 if is_on else 0.0
                print(f"   🍕 Four: {'allumé' if is_on else 'éteint'}")
            
            elif topic == "home/kitchen/heating/state":
                is_on = payload_str.lower() == 'on'
                self.current_house_state['chauffage_cuisine_power'] = 1.0 if is_on else 0.0
                print(f"   🔥 Chauffage cuisine: {'ON' if is_on else 'OFF'}")
            
            elif topic == "home/kitchen/heating/power":
                try:
                    self.current_house_state['chauffage_cuisine_power'] = float(payload_str)
                    print(f"   🔥 Puissance chauffage cuisine: {self.current_house_state['chauffage_cuisine_power']*100:.0f}%")
                except ValueError:
                    pass
            
            # ============================================================
            # 3. ÉTAT GLOBAL (HOME ASSISTANT)
            # ============================================================
            
            elif topic == "home/global/state":
                try:
                    payload = json.loads(payload_str)
                    self.current_house_state['temp_salon'] = float(payload.get('input_number.temp_salon', self.current_house_state.get('temp_salon', 22.0)))
                    self.current_house_state['user_target'] = float(payload.get('input_number.temp_preference_salon', self.current_house_state.get('user_target', 22.0)))
                    print(f"   🌡️ Global - Salon: {self.current_house_state['temp_salon']}°C | Cible: {self.current_house_state['user_target']}°C")
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"   ⚠️ Erreur parsing global state: {e}")
                self._check_all_data_received()
            
            # ============================================================
            # 4. NAILA / FEEDBACK TOPICS
            # ============================================================
            
            elif topic == self.TOPIC_NAILA_STATE:
                try:
                    data = json.loads(payload_str) if isinstance(payload_str, str) else payload_str
                    naila_state = data.get('state', {})
                    for key, value in naila_state.items():
                        if key in self.current_house_state:
                            self.current_house_state[key] = value
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
                    for key, value in etat.items():
                        if key in self.current_house_state:
                            self.current_house_state[key] = value
                    if "demande" in self.state_callbacks:
                        self.state_callbacks["demande"](user_id, self.current_house_state)
                except Exception:
                    pass
                
        except Exception as e:
            print(f"❌ Erreur traitement message: {e}")
    
    def _check_all_data_received(self):
        """Vérifie si toutes les données critiques sont reçues et valides"""
        # Vérifier que les températures ne sont pas 0 ou None (données fausses)
        temp_salon_ok = self.current_house_state['temp_salon'] is not None and self.current_house_state['temp_salon'] != 0
        temp_cuisine_ok = self.current_house_state['temp_cuisine'] is not None and self.current_house_state['temp_cuisine'] != 0
        presence_ok = self.current_house_state['presence_salon'] is not None
        heure_ok = self.current_house_state['heure'] is not None
        
        all_received = (temp_salon_ok and temp_cuisine_ok and presence_ok and heure_ok)
        
        if all_received and "state_update" in self.state_callbacks:
            print("\n✅ TOUTES LES DONNÉES HOME ASSISTANT REÇUES!")
            print("   → Génération des actions...")
            self.state_callbacks["state_update"](self.current_house_state)
    
    def _has_all_data(self):
        """Vérifie si toutes les données sont présentes"""
        return (self.current_house_state['temp_salon'] is not None and
                self.current_house_state['temp_cuisine'] is not None and
                self.current_house_state['presence_salon'] is not None and
                self.current_house_state['presence_cuisine'] is not None and
                self.current_house_state['heure'] is not None)
    
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
    
    def publish_actions(self, user_id, actions, current_state):
        """Publie les actions pour Naila"""
        try:
            naila_state = self._convert_to_naila_state(current_state)
            message = {
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "state": naila_state,
                "actions": actions,
                "num_actions": len(actions)
            }
            payload = json.dumps(message, ensure_ascii=False, default=str)
            result = self.client.publish(self.TOPIC_ACTIONS, payload, qos=1)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"📤 {len(actions)} actions publiées pour {user_id}")
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
            print("   ↪ Données déjà disponibles, déclenchement immédiat!")
            callback(self.current_house_state)
    
    def register_naila_callback(self, callback_type, callback):
        """Enregistre un callback pour les demandes de Naila"""
        self.register_state_callback(callback_type, callback)
        print(f"📝 Callback Naila '{callback_type}' enregistré")
