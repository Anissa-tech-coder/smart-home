# Clic droit → New File → Tapez: config.py
# Puis copiez-collez ce code:

ENERGY_CONFIG = {
    "heating": {
        "watts_per_degree": 50,
        "default_temp": 20,
        "min_temp": 16,
        "max_temp": 26,
    },
    "lighting": {
        "watts_per_light": 15,
        "default_brightness": 80,
    },
    "appliances": {
        "dishwasher": {"watts": 1800, "duration_minutes": 120},
        "washing_machine": {"watts": 2000, "duration_minutes": 60},
        "fridge": {"watts": 150, "duration_minutes": None},
    }
}

ROOMS = ["salon", "chambre_1", "chambre_2", "cuisine", "salle_bain"]
PREFERENCE_TYPES = ["comfort_level", "temperature", "lighting", "appliance_usage"]
COMFORT_LEVELS = ["eco", "normal", "confort"]