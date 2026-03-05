"""
Calcul des métriques de performance du système
Mesure l'efficacité et la satisfaction utilisateur
"""
from typing import List, Dict, Any
from datetime import datetime


class PerformanceMetrics:
    """Évalue la performance du système de recommandation"""
    
    def __init__(self):
        """Initialiser les compteurs"""
        self.recommendations_count = 0
        self.accepted_count = 0
        self.rejected_count = 0
    
    # ============================================
    # 1️⃣ TAUX D'ACCEPTATION
    # ============================================
    
    def calculate_acceptance_rate(self, user_action_history: List[Dict[str, Any]]) -> float:
        """
        Calcule le TAUX D'ACCEPTATION des recommandations
        
        Formule: (Recommandations acceptées / Total recommandations) * 100
        
        Entrée:
            user_action_history: Historique des actions de l'utilisateur
            [
                {"accepted": True, ...},
                {"accepted": False, ...},
                ...
            ]
        
        Retourne:
            Pourcentage d'acceptation (0-100)
        """
        if not user_action_history:
            return 0.0
        
        accepted = sum(1 for action in user_action_history if action.get("accepted"))
        total = len(user_action_history)
        
        rate = (accepted / total) * 100 if total > 0 else 0
        return round(rate, 2)
    
    # ============================================
    # 2️⃣ EFFICACITÉ ÉNERGÉTIQUE
    # ============================================
    
    def calculate_energy_efficiency(self, 
                                   recommended_actions: List[Dict[str, Any]],
                                   accepted_actions: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calcule l'EFFICACITÉ ÉNERGÉTIQUE
        
        Compare l'énergie recommandée vs l'énergie réellement économisée
        
        Entrée:
            recommended_actions: Actions recommandées
            accepted_actions: Actions acceptées par l'utilisateur
        
        Retourne:
            {
                "recommended_kwh": 2.5,
                "accepted_kwh": 1.8,
                "implementation_rate": 72.0  (en %)
            }
        """
        # Calculer l'énergie recommandée
        recommended_energy = sum(
            action.get("energy_saved_kwh", 0) for action in recommended_actions
        )
        
        # Calculer l'énergie réelle (acceptée)
        accepted_energy = sum(
            action.get("energy_saved_kwh", 0) for action in accepted_actions
        )
        
        # Taux d'implémentation
        implementation_rate = (accepted_energy / recommended_energy * 100) \
                            if recommended_energy > 0 else 0
        
        return {
            "recommended_kwh": round(recommended_energy, 3),
            "accepted_kwh": round(accepted_energy, 3),
            "implementation_rate": round(implementation_rate, 2)
        }
    
    # ============================================
    # 3️⃣ SATISFACTION UTILISATEUR
    # ============================================
    
    def calculate_user_satisfaction(self, user_action_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calcule la SATISFACTION UTILISATEUR
        
        Basée sur:
        - Taux d'acceptation
        - Raison des refus (si fournie)
        
        Entrée:
            user_action_history: Historique avec raisons
            [
                {"accepted": True, "reason": "Bonne idée"},
                {"accepted": False, "reason": "Trop froid"},
                ...
            ]
        
        Retourne:
            {
                "satisfaction_score": 8.5 (sur 10),
                "positive_feedback": 3,
                "negative_feedback": 1,
                "reasons_for_rejection": ["Trop froid", "Pas d'éclairage"]
            }
        """
        if not user_action_history:
            return {
                "satisfaction_score": 0,
                "positive_feedback": 0,
                "negative_feedback": 0,
                "reasons_for_rejection": []
            }
        
        acceptance_rate = self.calculate_acceptance_rate(user_action_history)
        
        # Score de satisfaction (0-10)
        satisfaction_score = acceptance_rate / 10  # Convertir en 0-10
        
        # Compter les raisons de refus
        positive_feedback = sum(1 for a in user_action_history if a.get("accepted"))
        negative_feedback = sum(1 for a in user_action_history if not a.get("accepted"))
        
        # Extraire les raisons de refus
        rejection_reasons = [
            a.get("reason", "Pas de raison") 
            for a in user_action_history 
            if not a.get("accepted") and a.get("reason")
        ]
        
        return {
            "satisfaction_score": round(satisfaction_score, 1),
            "positive_feedback": positive_feedback,
            "negative_feedback": negative_feedback,
            "reasons_for_rejection": rejection_reasons
        }
    
    # ============================================
    # 4️⃣ STATISTIQUES DÉTAILLÉES
    # ============================================
    
    def calculate_detailed_statistics(self, user_action_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calcule les STATISTIQUES DÉTAILLÉES
        
        Retourne:
            {
                "total_actions": 10,
                "accepted": 7,
                "rejected": 3,
                "acceptance_rate": 70.0,
                "average_daily": 2.3,
                "peak_acceptance_time": "matin"
            }
        """
        if not user_action_history:
            return {
                "total_actions": 0,
                "accepted": 0,
                "rejected": 0,
                "acceptance_rate": 0,
                "average_daily": 0,
                "status": "Aucune donnée"
            }
        
        total = len(user_action_history)
        accepted = sum(1 for a in user_action_history if a.get("accepted"))
        rejected = total - accepted
        acceptance_rate = (accepted / total * 100) if total > 0 else 0
        
        # Estimé: moyenne par jour (nombre de jours = ?)
        # Pour simplifier, on divise par 5 (environ 1 semaine de test)
        average_daily = total / 5
        
        return {
            "total_actions": total,
            "accepted": accepted,
            "rejected": rejected,
            "acceptance_rate": round(acceptance_rate, 2),
            "average_daily": round(average_daily, 2),
            "status": "Données disponibles"
        }
    
    # ============================================
    # 5️⃣ RAPPORT DE PERFORMANCE
    # ============================================
    
    def generate_performance_report(self, 
                                   user_name: str,
                                   user_action_history: List[Dict[str, Any]],
                                   recommended_actions: List[Dict[str, Any]] = None) -> str:
        """
        Génère un RAPPORT COMPLET de performance
        
        Entrée:
            user_name: Nom de l'utilisateur
            user_action_history: Historique des actions
            recommended_actions: Actions recommandées (optionnel)
        
        Retourne:
            Rapport formaté en texte
        """
        acceptance_rate = self.calculate_acceptance_rate(user_action_history)
        satisfaction = self.calculate_user_satisfaction(user_action_history)
        stats = self.calculate_detailed_statistics(user_action_history)
        
        report = f"""
╔════════════════════════════════════════════════════════════════╗
║              RAPPORT DE PERFORMANCE                            ║
╚════════════════════════════════════════════════════════════════╝

👤 UTILISATEUR: {user_name}
📅 DATE: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 STATISTIQUES GLOBALES:

   Total recommandations: {stats['total_actions']}
   ├─ Acceptées: {stats['accepted']} ✅
   ├─ Refusées: {stats['rejected']} ❌
   └─ Taux d'acceptation: {acceptance_rate}%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

😊 SATISFACTION UTILISATEUR:

   Score de satisfaction: {satisfaction['satisfaction_score']}/10
   ├─ Feedback positif: {satisfaction['positive_feedback']}
   ��─ Feedback négatif: {satisfaction['negative_feedback']}
"""
        
        if satisfaction['reasons_for_rejection']:
            report += f"\n   Raisons des refus:\n"
            for i, reason in enumerate(satisfaction['reasons_for_rejection'], 1):
                report += f"      {i}. {reason}\n"
        
        report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 MOYENNES:

   Moyenne par jour: {stats['average_daily']} actions/jour
   Nombre jours testés: ~5 jours

════════════════════════════════════════════════════════════════════

📋 INTERPRÉTATION:

"""
        
        if acceptance_rate >= 80:
            report += "   ✅ EXCELLENT! L'utilisateur accepte presque toutes les recommandations.\n"
            report += "      Le système comprend bien ses préférences!"
        elif acceptance_rate >= 60:
            report += "   ✅ BON! La majorité des recommandations sont acceptées.\n"
            report += "      Quelques ajustements pourraient aider."
        elif acceptance_rate >= 40:
            report += "   ⚠️  MOYEN. L'utilisateur refuse environ la moitié des recommandations.\n"
            report += "      À revoir les préférences utilisateur."
        else:
            report += "   ❌ FAIBLE. L'utilisateur refuse la plupart des recommandations.\n"
            report += "      Amélioration urgente nécessaire!"
        
        report += "\n════════════════════════════════════════════════════════════════════\n"
        
        return report
    
    # ============================================
    # 6️⃣ COMPARAISON ENTRE UTILISATEURS
    # ============================================
    
    def compare_users(self, 
                     users_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Compare les performances entre PLUSIEURS utilisateurs
        
        Entrée:
            users_data: 
            {
                "Tasnim": [historique],
                "Naila": [historique],
                ...
            }
        
        Retourne:
            Comparaison détaillée
        """
        comparison = {}
        
        for user_name, history in users_data.items():
            acceptance_rate = self.calculate_acceptance_rate(history)
            satisfaction = self.calculate_user_satisfaction(history)
            stats = self.calculate_detailed_statistics(history)
            
            comparison[user_name] = {
                "acceptance_rate": acceptance_rate,
                "satisfaction_score": satisfaction['satisfaction_score'],
                "total_actions": stats['total_actions'],
                "accepted": stats['accepted']
            }
        
        return comparison
    
    # ============================================
    # 7️⃣ AFFICHAGE DES RÉSULTATS
    # ============================================
    
    def print_metrics_summary(self, user_action_history: List[Dict[str, Any]]) -> None:
        """Affiche un résumé des métriques"""
        if not user_action_history:
            print("❌ Aucune donnée disponible")
            return
        
        acceptance_rate = self.calculate_acceptance_rate(user_action_history)
        satisfaction = self.calculate_user_satisfaction(user_action_history)
        stats = self.calculate_detailed_statistics(user_action_history)
        
        print("\n📊 RÉSUMÉ DES MÉTRIQUES")
        print("=" * 70)
        print(f"Total actions: {stats['total_actions']:3} | Acceptées: {stats['accepted']:2} | Refusées: {stats['rejected']:2}")
        print(f"Taux d'acceptation: {acceptance_rate:6.2f}% | Satisfaction: {satisfaction['satisfaction_score']}/10")
        print("=" * 70)


# ============================================
# EXEMPLE D'UTILISATION
# ============================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("DÉMO - MÉTRIQUES DE PERFORMANCE")
    print("="*70)
    
    # Simuler un historique utilisateur
    user_history = [
        {"timestamp": "2026-02-21T10:00", "accepted": True, "reason": "Bonne idée"},
        {"timestamp": "2026-02-21T11:00", "accepted": True, "reason": "Économies"},
        {"timestamp": "2026-02-21T12:00", "accepted": False, "reason": "Trop froid"},
        {"timestamp": "2026-02-21T13:00", "accepted": True, "reason": "D'accord"},
        {"timestamp": "2026-02-21T14:00", "accepted": True, "reason": "OK"},
        {"timestamp": "2026-02-21T15:00", "accepted": False, "reason": "Pas d'éclairage"},
        {"timestamp": "2026-02-21T16:00", "accepted": True, "reason": "Oui"},
    ]
    
    metrics = PerformanceMetrics()
    
    # 1. Taux d'acceptation
    print("\n1️⃣ TAUX D'ACCEPTATION")
    acceptance_rate = metrics.calculate_acceptance_rate(user_history)
    print(f"Taux: {acceptance_rate}%")
    
    # 2. Satisfaction
    print("\n2️⃣ SATISFACTION UTILISATEUR")
    satisfaction = metrics.calculate_user_satisfaction(user_history)
    print(f"Score: {satisfaction['satisfaction_score']}/10")
    print(f"Feedback positif: {satisfaction['positive_feedback']}")
    print(f"Feedback négatif: {satisfaction['negative_feedback']}")
    print(f"Raisons refus: {satisfaction['reasons_for_rejection']}")
    
    # 3. Statistiques
    print("\n3️⃣ STATISTIQUES DÉTAILLÉES")
    stats = metrics.calculate_detailed_statistics(user_history)
    print(f"Total: {stats['total_actions']}")
    print(f"Acceptées: {stats['accepted']}")
    print(f"Refusées: {stats['rejected']}")
    
    # 4. Rapport complet
    print("\n4️⃣ RAPPORT COMPLET")
    report = metrics.generate_performance_report("Tasnim", user_history)
    print(report)
    
    # 5. Résumé des métriques
    print("\n5️⃣ RÉSUMÉ")
    metrics.print_metrics_summary(user_history)
    
    print("\n" + "="*70)
    print("✅ DÉMO TERMINÉE!")
    print("="*70)