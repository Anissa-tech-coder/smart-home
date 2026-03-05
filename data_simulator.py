"""
Simulateur d'état des capteurs IoT
Génère des données réalistes pour tester le système
"""
import random
from typing import Dict, Any, List
from datetime import datetime, timedelta


class IoTSimulator:
    """Simule l'état des capteurs IoT dans la maison"""
    
    def __init__(self):
        """Initialiser le simulateur avec les valeurs de base"""
        self.rooms = ["salon", "chambre_1", "chambre_2", "cuisine", "salle_bain"]
        
        # Températures de base (°C)
        self.base_temperatures = {
            "salon": 21,
            "chambre_1": 19,
            "chambre_2": 18,
            "cuisine": 22,
            "salle_bain": 22
        }
        
        # Luminosités de base (%)
        self.base_brightness = {
            "salon": 80,
            "chambre_1": 60,
            "chambre_2": 50,
            "cuisine": 90,
            "salle_bain": 85
        }
    
    # ============================================
    # 1️⃣ GÉNÉRER L'ÉTAT ACTUEL
    # ============================================
    
    def generate_current_state(self) -> Dict[str, Any]:
        """
        Génère l'état ACTUEL simulé des capteurs
        
        Ajoute du bruit réaliste pour simuler des fluctuations
        
        Retourne:
            {
                "salon": {"temperature": 22.1, "brightness": 85},
                "chambre_1": {"temperature": 20.5, "brightness": 65},
                ...
            }
        """
        state = {}
        
        for room in self.rooms:
            # Ajouter du bruit réaliste
            # Température: ±1-2°C
            temp = self.base_temperatures[room] + random.uniform(-1, 2)
            
            # Luminosité: ±10%
            brightness = max(0, min(100, 
                self.base_brightness[room] + random.randint(-10, 10)
            ))
            
            state[room] = {
                "temperature": round(temp, 1),
                "brightness": int(brightness),
                "timestamp": datetime.now().isoformat()
            }
        
        return state
    
    # ============================================
    # 2️⃣ SIMULER UN CYCLE DE 24H
    # ============================================
    
    def simulate_day_cycle(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Simule un cycle complet de 24h
        
        Variation réaliste:
        - Le jour (8h-18h): plus chaud, plus lumineux
        - La nuit (19h-7h): plus froid, moins lumineux
        
        Entrée:
            hours: Nombre d'heures à simuler (par défaut 24)
        
        Retourne:
            Liste d'états toutes les heures
            [
                {
                    "salon": {"temperature": 21.5, "brightness": 20, "hour": 0},
                    "chambre_1": {...},
                    ...
                },
                {...},
                ...
            ]
        """
        states = []
        
        for hour in range(hours):
            # Définir les variations selon l'heure
            if 8 <= hour <= 18:
                # JOUR: Plus chaud, plus lumineux
                temp_offset = 2
                brightness_multiplier = 1.3
            elif 19 <= hour <= 23:
                # SOIRÉE: Transition
                temp_offset = 0
                brightness_multiplier = 0.8
            else:
                # NUIT: Plus froid, moins lumineux
                temp_offset = -2
                brightness_multiplier = 0.3
            
            state = {}
            
            for room in self.rooms:
                # Température avec variation
                temp = (self.base_temperatures[room] + temp_offset + 
                       random.uniform(-0.5, 1))
                
                # Luminosité avec variation
                brightness = max(0, min(100, 
                    self.base_brightness[room] * brightness_multiplier + 
                    random.randint(-10, 10)
                ))
                
                state[room] = {
                    "temperature": round(temp, 1),
                    "brightness": int(brightness),
                    "hour": hour,
                    "timestamp": (datetime.now() + timedelta(hours=hour)).isoformat()
                }
            
            states.append(state)
        
        return states
    
    # ============================================
    # 3️⃣ SIMULER PLUSIEURS JOURS
    # ============================================
    
    def simulate_week_cycle(self, days: int = 7, hours_per_day: int = 24) -> List[Dict[str, Any]]:
        """
        Simule une semaine complète
        
        Entrée:
            days: Nombre de jours (par défaut 7)
            hours_per_day: Heures par jour (par défaut 24)
        
        Retourne:
            Liste d'états pour toute la semaine
        """
        all_states = []
        
        for day in range(days):
            day_states = self.simulate_day_cycle(hours=hours_per_day)
            
            # Ajouter le numéro du jour
            for state in day_states:
                for room in state:
                    state[room]["day"] = day + 1
            
            all_states.extend(day_states)
        
        return all_states
    
    # ============================================
    # 4️⃣ SCÉNARIOS SPÉCIFIQUES
    # ============================================
    
    def simulate_hot_day(self) -> Dict[str, Any]:
        """
        Simule une journée TRÈS CHAUDE
        (+3-5°C par rapport à la normale)
        """
        state = {}
        
        for room in self.rooms:
            temp = self.base_temperatures[room] + random.uniform(3, 5)
            brightness = max(0, min(100, 
                self.base_brightness[room] + random.randint(10, 20)
            ))
            
            state[room] = {
                "temperature": round(temp, 1),
                "brightness": int(brightness),
                "scenario": "hot_day"
            }
        
        return state
    
    def simulate_cold_day(self) -> Dict[str, Any]:
        """
        Simule une journée TRÈS FROIDE
        (-3-5°C par rapport à la normale)
        """
        state = {}
        
        for room in self.rooms:
            temp = self.base_temperatures[room] + random.uniform(-5, -3)
            brightness = max(0, min(100, 
                self.base_brightness[room] - random.randint(10, 20)
            ))
            
            state[room] = {
                "temperature": round(temp, 1),
                "brightness": int(brightness),
                "scenario": "cold_day"
            }
        
        return state
    
    def simulate_rainy_day(self) -> Dict[str, Any]:
        """
        Simule une journée PLUVIEUSE
        (Moins lumineux, un peu plus froid)
        """
        state = {}
        
        for room in self.rooms:
            temp = self.base_temperatures[room] + random.uniform(-1, 0)
            brightness = max(0, min(100, 
                self.base_brightness[room] * 0.6 + random.randint(-10, 10)
            ))
            
            state[room] = {
                "temperature": round(temp, 1),
                "brightness": int(brightness),
                "scenario": "rainy_day"
            }
        
        return state
    
    # ============================================
    # 5️⃣ AFFICHER LES DONNÉES
    # ============================================
    
    def print_state(self, state: Dict[str, Any]) -> None:
        """Affiche joliment l'état des capteurs"""
        print("\n🏠 État des capteurs IoT:")
        print("-" * 70)
        
        for room, data in state.items():
            temp = data["temperature"]
            brightness = data["brightness"]
            
            # Smiley selon la température
            if temp < 18:
                emoji = "❄️"
            elif temp > 24:
                emoji = "🔥"
            else:
                emoji = "😊"
            
            # Barre de luminosité
            brightness_bar = "█" * (brightness // 10) + "░" * (10 - brightness // 10)
            
            print(f"{room:15} | {emoji} {temp:5.1f}°C | 💡 {brightness_bar} {brightness}%")
    
    def print_day_cycle(self, states: List[Dict[str, Any]]) -> None:
        """Affiche un résumé du cycle de 24h"""
        print("\n📊 CYCLE DE 24H - Salon")
        print("-" * 70)
        
        for i, state in enumerate(states):
            hour = i
            temp = state["salon"]["temperature"]
            brightness = state["salon"]["brightness"]
            
            # Smiley
            if temp < 18:
                emoji = "❄️"
            elif temp > 24:
                emoji = "🔥"
            else:
                emoji = "😊"
            
            # Barre temporelle
            hour_str = f"{hour:02d}h"
            brightness_bar = "█" * (brightness // 10) + "░" * (10 - brightness // 10)
            
            print(f"{hour_str} | {emoji} {temp:5.1f}°C | {brightness_bar} {brightness}%")


# ============================================
# EXEMPLE D'UTILISATION
# ============================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("DÉMO - SIMULATEUR IoT")
    print("="*70)
    
    simulator = IoTSimulator()
    
    # 1. État actuel
    print("\n1️⃣ ÉTAT ACTUEL")
    current_state = simulator.generate_current_state()
    simulator.print_state(current_state)
    
    # 2. Cycle de 24h
    print("\n\n2️⃣ CYCLE DE 24H")
    day_cycle = simulator.simulate_day_cycle(hours=24)
    simulator.print_day_cycle(day_cycle)
    
    # 3. Scénarios spécifiques
    print("\n\n3️⃣ JOURNÉE CHAUDE")
    hot_day = simulator.simulate_hot_day()
    simulator.print_state(hot_day)
    
    print("\n\n4️⃣ JOURNÉE FROIDE")
    cold_day = simulator.simulate_cold_day()
    simulator.print_state(cold_day)
    
    print("\n\n5️⃣ JOURNÉE PLUVIEUSE")
    rainy_day = simulator.simulate_rainy_day()
    simulator.print_state(rainy_day)
    
    print("\n" + "="*70)
    print("✅ DÉMO TERMINÉE!")
    print("="*70)