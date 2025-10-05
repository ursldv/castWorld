import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional

# URLs des APIs
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

def get_weekly_precipitation(latitude: float, longitude: float, start_date: str) -> Optional[pd.DataFrame]:
    """
    Récupère les données de prévisions quotidiennes de précipitations via l'API Open-Meteo
    pour une semaine à partir de la date de début.
    """
    try:
        # Calcul de la date de fin (7 jours à partir de la date de début)
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = start_dt + timedelta(days=6)
        end_date = end_dt.strftime("%Y-%m-%d")

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": ["precipitation_sum", "precipitation_probability_max"],
            "timezone": "auto",
            "start_date": start_date,
            "end_date": end_date
        }

        response = requests.get(OPEN_METEO_URL, params=params)
        response.raise_for_status()

        data = response.json()
        
        if "daily" not in data or not data["daily"]["time"]:
            return None

        daily_data = data["daily"]
        
        # Création d'un DataFrame Pandas pour l'analyse
        df = pd.DataFrame({
            "Date": daily_data["time"],
            "Precipitation_mm": daily_data["precipitation_sum"],
            "Probabilite_Max_%": daily_data["precipitation_probability_max"]
        })
        
        return df
        
    except requests.exceptions.RequestException as e:
        print(f"Erreur de connexion à l'API météo : {e}")
        return None
    except Exception as e:
        print(f"Une erreur inattendue est survenue : {e}")
        return None
    
def detect_meteo_risks(df):
    from datetime import timedelta

    alerts = []
    sequence_seche = 0
    seuil_inondation = 50  # mm de pluie en 24h

    for item in df.to_dict('records'):
        pluie = item.get('Precipitation_mm', 0)
        date = item.get('Date')

        # Séquence sèche
        if pluie == 0:
            sequence_seche += 1
        else:
            if sequence_seche >= 5:
                alerts.append({
                    "type": "Sécheresse",
                    "message": f"🌵 Séquence sèche détectée jusqu’au {date}",
                    "niveau": "moyen"
                })
            sequence_seche = 0

        # Inondation localisée
        if pluie >= seuil_inondation:
            alerts.append({
                "type": "Inondation",
                "message": f"🌊 Risque d’inondation le {date} ({pluie} mm)",
                "niveau": "élevé"
            })

    return alerts
