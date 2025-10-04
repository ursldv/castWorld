import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Tuple

# URLs des APIs
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

def traiter_requete(request):
    ville = request.GET.get('ville', 'Cotonou')
    # Utilise la ville pour faire une requête API ou autre
    return geocode_city(ville)


def geocode_city(city_name: str) -> Optional[Tuple[float, float, str]]:
    """
    Convertit un nom de ville en coordonnées (latitude, longitude, nom affiché).
    """
    try:
        params = {"q": city_name, "format": "json", "limit": 1}
        headers = {"User-Agent": "MeteoWeekForecastApp/1.0"}
        
        response = requests.get(NOMINATIM_URL, params=params, headers=headers)
        response.raise_for_status()
        
        results = response.json()
        
        if results:
            lat = float(results[0]["lat"])
            lon = float(results[0]["lon"])
            name = results[0]["display_name"]
            return lat, lon, name
        else:
            print(f"Erreur : Lieu '{city_name}' non trouvé par le géocodage.")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Erreur de connexion lors du géocodage : {e}")
        return None
    except Exception as e:
        print(f"Erreur inattendue pendant le géocodage : {e}")
        return None


def get_weekly_precipitation(latitude: float, longitude: float, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
    """
    Récupère les données de prévisions quotidiennes de précipitations via l'API Open-Meteo.
    """
    try:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": ["precipitation_sum", "precipitation_probability_max"],
            "timezone": "auto",
            "start_date": start_date,
            "end_date": end_date
        }

        print(f"\n-> Requête API pour {start_date} à {end_date}...")
        
        response = requests.get(OPEN_METEO_URL, params=params)
        response.raise_for_status()

        data = response.json()
        
        if "daily" not in data or not data["daily"]["time"]:
            print("Erreur: L'API n'a pas retourné de données quotidiennes (vérifiez que la période n'excède pas 16 jours à partir d'aujourd'hui).")
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


def main():
    """
    Fonction principale pour l'interaction utilisateur simplifiée.
    """
    print("="*60)
    print(" PRÉVISION DE PLUIE HEBDOMADAIRE (7 JOURS) ")
    print("="*60)
    
    # 1. Demande de la ville
    city_name = requests
    geocode_result = geocode_city(city_name)
    
    if geocode_result is None:
        return # Sortie si le géocodage a échoué

    latitude, longitude, location_display = geocode_result
    
    # 2. Demande de la date de début
    print("\nFormat de date requis : AAAA-MM-JJ (ex: 2025-10-06)")
    start_date_str = input("Entrez la date de DÉBUT de la semaine de prévision : ")
    
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        # Calculer la date de fin (7 jours au total, donc + 6 jours)
        end_date = start_date + timedelta(days=6)
        end_date_str = end_date.strftime('%Y-%m-%d')
    except ValueError:
        print("Erreur : Format de date incorrect. Utilisez AAAA-MM-JJ.")
        return

    # 3. Récupération des données
    forecast_data = get_weekly_precipitation(latitude, longitude, start_date_str, end_date_str)

    if forecast_data is not None:
        
        print("\n" + "="*60)
        print(f"PRÉVISIONS DE PLUIE POUR LA SEMAINE À {location_display.upper()}")
        print(f"Période : Du {start_date_str} au {end_date_str}")
        print("="*60)
        
        # Créer une colonne pour la prédiction simple
        def predict_rain(row):
            # Considérons qu'il y aura "Pluie" si le cumul est > 0 ET la proba > 20%
            if row["Precipitation_mm"] > 0.0 and row["Probabilite_Max_%"] >= 20:
                return "🌧️ OUI"
            elif row["Precipitation_mm"] > 0.0:
                return "💧 Faible Risque"
            else:
                return "☀️ NON"
        
        forecast_data["Pluie_Prévue"] = forecast_data.apply(predict_rain, axis=1)

        # Calcul des statistiques agrégées
        total_precipitation = forecast_data["Precipitation_mm"].sum()
        rainy_days_count = (forecast_data["Pluie_Prévue"].isin(["🌧️ OUI", "💧 Faible Risque"])).sum()

        # Affichage du résumé
        print(f"Total des précipitations prévues pour la semaine : {total_precipitation:.2f} mm")
        print(f"Nombre de jours avec risque de pluie : {rainy_days_count} / 7")
        print("-" * 60)
        
        # Affichage des données détaillées
        print(forecast_data.to_string(index=False))
        print("="*60)

    else:
        print("Impossible d'obtenir les prévisions météo. Veuillez vérifier les entrées et l'accès à l'API.")

if __name__ == "__main__":
    # Assurez-vous d'avoir installé : pip install requests pandas
    main()
    