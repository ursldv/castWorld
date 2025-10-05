from django.shortcuts import render
from geopy.geocoders import Nominatim
import folium
import geocoder
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from requests import request
# Create your views here.

from datetime import date
import io
from django.http import FileResponse
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
import matplotlib.pyplot as plt
import tempfile
from meteo_app import get_weekly_precipitation

def get_date_from_request(request):
    return request.GET.get('date_choice') or date.today().isoformat()

def get_lieu_from_request(request):
    return request.GET.get('lieu', '')

def home(request):
    jour = get_date_from_request(request)
    lieu = get_lieu_from_request(request)
    
    bounds = [[6.2, 0.8], [12.5, 3.9]]  
    geolocator = Nominatim(user_agent="meteo_app")

    if lieu:
        location = geolocator.geocode(lieu)
        if location:
            lat, lon = location.latitude, location.longitude
            message = f" Answers for : {lieu}"
            zoom_level = 14  
            ville = lieu
        else:
            lat, lon = 6.3703, 2.3912  
            message = f" Place not found : {lieu}"
            zoom_level = 6  
            ville = "Cotonou, BJ"
    else:
        g = geocoder.ip('me')
        lat, lon = g.latlng if g.latlng else (6.3703, 2.3912)
        message = "Location detected automatically"
        zoom_level = 10  
        try:
            location_reverse = geolocator.reverse(f"{lat}, {lon}")
            ville = location_reverse.address.split(',')[0] if location_reverse else "Cotonou, BJ"
        except:
            ville = "Cotonou, BJ"

    # MAP creation
    carte = folium.Map(location=[lat, lon], zoom_start=zoom_level, control_scale=True, max_bounds=True)
    carte.fit_bounds(bounds)  

    # Add a marker for the location
    folium.Marker(
        [lat, lon],
        tooltip=message,
        popup=f"<b>{message}</b><br>Lat: {lat:.4f}, Lon: {lon:.4f}",
        icon=folium.Icon(color="red", icon="info-sign")
    ).add_to(carte)

    carte.add_child(folium.LatLngPopup())
    carte_html = carte._repr_html_()

    # Initialize weather_data and current temperature
    weather_data = []
    temperature_actuelle = 28
    condition_actuelle = "Partly Cloudy"
    
    df = get_weekly_precipitation(lat, lon, jour)
    if df is None or df.empty:
        message += " | Data not available for this location or period."
    else:
        message += f" |  Weather data from {jour} to {df['Date'].iloc[-1]}"
        df = df.rename(columns={'Probabilite_Max_%': 'Probabilite_Max'})
        
        if 'Temperature_Max' in df.columns and not df.empty:
            temperature_actuelle = round(df['Temperature_Max'].iloc[0], 1)
        
        if 'Precipitation_mm' in df.columns and not df.empty:
            precip_aujourd_hui = df['Precipitation_mm'].iloc[0]
            if precip_aujourd_hui > 10:
                condition_actuelle = "Rainy"
            elif precip_aujourd_hui > 0:
                condition_actuelle = "Cloudy"
            else:
                condition_actuelle = "Sunny"
        
        weather_data = df.to_dict('records')
        
        for item in weather_data:
            if 'Date' in item and not isinstance(item['Date'], date):
                try:
                    from datetime import datetime
                    if isinstance(item['Date'], str):
                        item['Date'] = datetime.strptime(item['Date'], '%Y-%m-%d').date()
                except:
                    pass

    return render(request, 'pages/index.html', {
        'message': message,
        'carte': carte_html,
        'latitude': lat,
        'longitude': lon,
        'lieu': lieu,
        'jour': jour,
        'weather_data': weather_data,
        'ville': ville,
        'temperature_actuelle': temperature_actuelle,
        'condition_actuelle': condition_actuelle,
    })

from datetime import date
from meteo_app import get_weekly_precipitation

def dashboard(request):
    jour = get_date_from_request(request)
    lieu = get_lieu_from_request(request)
    return render(request, 'pages/dashboard.html', {
        'date': jour,
        'lieu': lieu,
        'jour': jour,
    })
import requests
from datetime import datetime
from django.shortcuts import render

import requests
from datetime import datetime, timedelta
from django.shortcuts import render
from geopy.geocoders import Nominatim

import requests
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim

def dashboard(request):
    jour = get_date_from_request(request)
    lieu = get_lieu_from_request(request)

    # Géolocalisation du lieu
    geolocator = Nominatim(user_agent="meteo_app")
    location = geolocator.geocode(lieu)
    if not location:
        return render(request, 'pages/dashboard.html', {
            'error': f"Location '{lieu}' not found.",
            'jour': jour,
            'lieu': lieu,
        })

    latitude, longitude = location.latitude, location.longitude

    # Déterminer la période (7 jours à partir du jour choisi)
    start_date = jour
    end_date = (datetime.strptime(jour, "%Y-%m-%d") + timedelta(days=6)).strftime("%Y-%m-%d")

    # Requête vers Open-Meteo
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={latitude}&longitude={longitude}"
        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max,relative_humidity_2m_max"
        f"&timezone=auto&start_date={start_date}&end_date={end_date}"
    )

    response = requests.get(url)
    data = response.json()

    if "daily" not in data:
        return render(request, 'pages/dashboard.html', {
            'error': "No weather data available.",
            'jour': jour,
            'lieu': lieu,
        })

    daily = data["daily"]

    # Récupération des données
    dates = daily.get("time", [])
    temp_max = daily.get("temperature_2m_max", [])
    temp_min = daily.get("temperature_2m_min", [])
    humidite = daily.get("relative_humidity_2m_max", [])
    vent = daily.get("wind_speed_10m_max", [])
    precip = daily.get("precipitation_sum", [])

    # Moyennes (pour les cartes du haut)
    def moyenne(values):
        return round(sum(values) / len(values), 1) if values else 0

    temp_moy = moyenne([(x + y) / 2 for x, y in zip(temp_max, temp_min)])
    humid_moy = moyenne(humidite)
    vent_moy = moyenne(vent)
    precip_moy = moyenne(precip)

    return render(request, 'pages/dashboard.html', {
        'jour': jour,
        'lieu': lieu,
        'dates': dates,
        'temp_max': temp_max,
        'temp_min': temp_min,
        'humid': humidite,
        'vent': vent,
        'precip': precip,
        'temp_moy': temp_moy,
        'humid_moy': humid_moy,
        'vent_moy': vent_moy,
        'precip_moy': precip_moy,
    })

def map_view(request):
    jour = get_date_from_request(request)
    lieu = get_lieu_from_request(request)
    return render(request, 'pages/map.html', {
        'lieu': lieu,
        'jour': jour,
    })
import pandas as pd
def suggestions(request):
    jour = get_date_from_request(request)
    lieu = get_lieu_from_request(request)

    geolocator = Nominatim(user_agent="meteo_app")
    if lieu:
        location = geolocator.geocode(lieu)
        if location:
            lat, lon = location.latitude, location.longitude
        else:
            lat, lon = 6.3703, 2.3912  # Cotonou par défaut
    else:
        lat, lon = 6.3703, 2.3912

    df = get_weekly_precipitation(lat, lon, jour)

    risque_inondation = "Insufficient data to assess flood risk"
    recommandation = "Impossible recommandation due to lack of data."
    message = ""

    if df is not None and not df.empty:
        avg_precip = df.get("Precipitation_mm", pd.Series([0])).mean()
        avg_temp = df.get("Temperature_Max", pd.Series([28])).mean()  # default value

        if avg_precip >= 100:
            risque_inondation = " Hard flood risk"
            recommandation = (
                "Leave flood-prone areas if possible."
                "Protect your important documents and turn off the electricity in case of rising water."
            )
        elif avg_precip >= 70:
            risque_inondation = "⚠️ High flood risk"
            recommandation = (
                "Stay vigilant. Elevate your belongings, avoid travel in the evening, "
                "and stay informed about local alerts."
            )
        elif avg_precip >= 40:
            risque_inondation = " Moderate flood risk"
            recommandation = (
                "Clean the gutters, avoid obstructing drainage paths, "
                "and prepare an emergency kit if you live in a low-lying area."
            )
        else:
            risque_inondation = " Low flood risk"
            recommandation = (
                "No major alerts, but stay cautious. The ground may still be wet if there has been recent rainfall"
            )
            

        if avg_temp > 35 and avg_precip > 40:
            recommandation += " The heat could intensify runoff, be vigilant."

        dernier_jour = df['Date'].iloc[-1] if 'Date' in df.columns else jour
        message = f"Data analyzed for {lieu or 'Cotonou'} from {jour} to {dernier_jour}."
    else:
        message = " Weather data not available for this location or period."

    return render(request, 'pages/suggestions.html', {
        'jour': jour,
        'lieu': lieu,
        'message': message,
        'risque_inondation': risque_inondation,
        'recommandation': recommandation,
    })


def contact(request):
    jour = get_date_from_request(request)
    lieu = get_lieu_from_request(request)
    return render(request, 'pages/contact.html', {
        'date': jour,
        'lieu': lieu,
        'jour': jour,
    })

def download_dashboard_pdf(request):
    import io, tempfile
    import matplotlib.pyplot as plt
    import pandas as pd
    from datetime import date
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from django.http import FileResponse

    lieu = request.GET.get('lieu', 'Cotonou, BJ')
    jour = request.GET.get('date_choice') or date.today().isoformat()
    lat = float(request.GET.get('latitude', 6.3703))
    lon = float(request.GET.get('longitude', 2.3912))

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    style_title = styles["Heading1"]
    style_subtitle = styles["Heading2"]
    style_body = styles["BodyText"]

    elements.append(Paragraph(f"WorldCast Weather Report - {lieu}", style_title))
    elements.append(Paragraph(f"Weekly summary from {jour}", style_body))
    elements.append(Spacer(1, 12))

    df = get_weekly_precipitation(lat, lon, jour)
    if df is None or df.empty:
        elements.append(Paragraph("❌ Weather data not available for this period or location.", style_body))
        elements.append(Spacer(1, 20))
        doc.build(elements)
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename="WorldCast_Dashboard_Report.pdf")

    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    days = [d.strftime('%a') for d in df['Date'] if pd.notnull(d)]

    # Tableau résumé avec toutes les colonnes numériques connues
    numeric_cols = ['Temperature_Max', 'Temperature_Min', 'Precipitation_mm', 'Humidity_%', 'Wind_km_h']
    data = [["Variable", "Valeur moyenne", "Unité"]]
    for col in numeric_cols:
        if col in df.columns:
            mean_val = round(df[col].mean(), 1)
            unit = "°C" if "Temperature" in col else "%" if "Humidity" in col else "mm" if "Precipitation" in col else "km/h"
            data.append([col.replace("_", " "), f"{mean_val}", unit])
        else:
            data.append([col.replace("_", " "), "N/A", "-"])

    table = Table(data, hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightblue),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 12),
        ('BOTTOMPADDING', (0,0), (-1,0), 10),
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.gray)
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))

    # Créer un graphique pour chaque colonne numérique disponible
    for col in numeric_cols:
        if col in df.columns:
            plt.figure(figsize=(4,2))
            plt.plot(days, df[col], marker='o', label=col)
            plt.title(col.replace("_", " "))
            plt.xlabel("Days")
            plt.ylabel(col.replace("_", " "))
            plt.grid(True)
            temp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            plt.savefig(temp_img.name, bbox_inches='tight')
            plt.close()
            elements.append(Paragraph(col.replace("_", " "), style_subtitle))
            elements.append(Image(temp_img.name, width=5*inch, height=2*inch))
            elements.append(Spacer(1, 20))

    # Footer
    elements.append(Spacer(1, 30))
    elements.append(Paragraph(f"<i>Generated by WorldCast Dashboard © {date.today().year}</i>", style_body))

    doc.build(elements)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename="WorldCast_Dashboard_Report.pdf")
