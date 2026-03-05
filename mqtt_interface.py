"""
Interface MQTT pour la communication avec Naila (SAC)
Topics:
- tasnim/actions/{user_id} : Publications des actions recommandées
- tasnim/state/{user_id} : État du système
- naila/feedback/{user_id} : Réception des feedbacks (accepté/refusé)
"""

import json
import paho.mqtt.client as mqtt
from typing import Dict, Any, Callable, Optional
from datetime import datetime
import threading
import time

class MQTTInterface:
    """
    Interface MQTT pour communiquer avec Naila
    ⭐ Pas besoin d'interface séparée, MQTT suffit!
    """
    
    def __init__(self, client_id: str = "tasnim_broker"):
        self.client_id = client_id
        self.client = mqtt.Client(client_id=client_id)
        self.connected = False
        self.feedback_callbacks = {}
        
        # Configuration broker
        self.broker = "broker.hivemq.com"  # Broker public gratuit
        self.port = 1883
        
        # Callbacks MQTT
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback de connexion"""
        if rc == 0:
            self.connected = True
            print(f"✅ MQTT Connecté à {self.broker}")
            
            # S'abonner aux topics de feedback
            self.client.subscribe("naila/feedback/+")  # + = wildcard pour user_id
            print("📡 Abonné aux feedbacks Naila")
        else:
            print(f"❌ Erreur connexion MQTT: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback de déconnexion"""
        self.connected = False
        print("⚠️ MQTT Déconnecté")
    
    def _on_message(self, client, userdata, msg):
        """Callback de réception de message"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            print(f"📥 Message reçu: {topic}")
            
            # Topic: naila/feedback/{user_id}
            if topic.startswith("naila/feedback/"):
                user_id = topic.split("/")[-1]
                self._handle_feedback(user_id, payload)
                
        except Exception as e:
            print(f"❌ Erreur traitement message: {e}")
    
    def _handle_feedback(self, user_id: str, payload: Dict):
        """Gère les feedbacks de Naila"""
        action_id = payload.get("action_id")
        accepted = payload.get("accepted", False)
        reward = payload.get("reward", 0)
        
        print(f"💬 Feedback de Naila pour {user_id}:")
        print(f"   Action: {action_id}")
        print(f"   Accepté: {'✅' if accepted else '❌'}")
        print(f"   Reward: {reward}")
        
        # Appeler le callback si enregistré
        if user_id in self.feedback_callbacks:
            self.feedback_callbacks[user_id](user_id, action_id, accepted, reward)
    
    def connect(self):
        """Connexion au broker MQTT"""
        try:
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            time.sleep(1)  # Laisser le temps de se connecter
            return True
        except Exception as e:
            print(f"❌ Erreur connexion MQTT: {e}")
            return False
    
    def disconnect(self):
        """Déconnexion"""
        self.client.loop_stop()
        self.client.disconnect()
    
    def publish_actions(self, user_id: str, actions: List[Dict], 
                       current_state: Dict) -> bool:
        """
        Publie les actions recommandées pour Naila
        Topic: tasnim/actions/{user_id}
        """
        try:
            topic = f"tasnim/actions/{user_id}"
            
            message = {
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "state": current_state,  # L'état actuel pour contexte
                "actions": actions,       # Les actions recommandées
                "num_actions": len(actions)
            }
            
            payload = json.dumps(message, ensure_ascii=False, default=str)
            
            result = self.client.publish(
                topic,
                payload,
                qos=1  # QoS 1 = au moins une fois
            )
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"📤 {len(actions)} actions publiées pour {user_id}")
                return True
            else:
                print(f"❌ Échec publication: {result.rc}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur publication: {e}")
            return False
    
    def publish_state(self, user_id: str, state: Dict) -> bool:
        """
        Publie l'état complet du système
        Topic: tasnim/state/{user_id}
        """
        try:
            topic = f"tasnim/state/{user_id}"
            
            message = {
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "state": state
            }
            
            payload = json.dumps(message, ensure_ascii=False, default=str)
            
            result = self.client.publish(topic, payload, qos=0)  # QoS 0 = fire and forget
            return result.rc == mqtt.MQTT_ERR_SUCCESS
            
        except Exception as e:
            print(f"❌ Erreur publication état: {e}")
            return False
    
    def register_feedback_callback(self, user_id: str, 
                                  callback: Callable[[str, str, bool, float], None]):
        """Enregistre un callback pour les feedbacks"""
        self.feedback_callbacks[user_id] = callback
        print(f"📝 Callback enregistré pour {user_id}")
    
    def wait_for_feedback(self, user_id: str, timeout: float = 30) -> Optional[Dict]:
        """
        Attend un feedback de Naila (bloquant)
        Utile pour la synchronisation
        """
        event = threading.Event()
        result = {"feedback": None}
        
        def callback(uid, action_id, accepted, reward):
            if uid == user_id:
                result["feedback"] = {
                    "action_id": action_id,
                    "accepted": accepted,
                    "reward": reward
                }
                event.set()
        
        self.register_feedback_callback(user_id, callback)
        
        if event.wait(timeout):
            return result["feedback"]
        return None