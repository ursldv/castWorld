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
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
import matplotlib.pyplot as plt
import tempfile
import io


from requests import request
# Create your views here.

from datetime import date
from meteo_app import get_weekly_precipitation


def home(request):

    jour = request.GET.get('date')
    if not jour:
        jour = date.today().isoformat()  # format "2025-10-04"
    
    bounds = [[6.2, 0.8], [12.5, 3.9]]  # Limites du Bénin
    lieu = request.GET.get('lieu')
    geolocator = Nominatim(user_agent="meteo_app")

    if lieu:
        location = geolocator.geocode(lieu)
        if location:
            lat, lon = location.latitude, location.longitude
            message = f"✅ Résultat pour : {lieu}"
            zoom_level = 12 
            ville = lieu  # ✅ Stocker le nom de la ville pour l'affichage
        else:
            lat, lon = 6.3703, 2.3912  # Coordonnées par défaut (Cotonou, Bénin)
            message = f"❌ Lieu introuvable : {lieu}"
            zoom_level = 6 
            ville = "Cotonou, BJ"  # Ville par défaut
    else:
        g = geocoder.ip('me')
        lat, lon = g.latlng if g.latlng else (6.3703, 2.3912)
        message = "📍 Position détectée automatiquement"
        zoom_level = 10  # Vue intermédiaire
        # Essayer de récupérer le nom de la ville depuis la position
        try:
            location_reverse = geolocator.reverse(f"{lat}, {lon}")
            ville = location_reverse.address.split(',')[0] if location_reverse else "Cotonou, BJ"
        except:
            ville = "Cotonou, BJ"

    # Création de la carte APRÈS avoir défini lat/lon
    carte = folium.Map(location=[lat, lon], zoom_start=zoom_level, control_scale=True, max_bounds=True)
    carte.fit_bounds(bounds)

    folium.Marker(
        [lat, lon],
        tooltip=message,
        popup=f"<b>{message}</b>",
        icon=folium.Icon(color="blue", icon="info-sign")
    ).add_to(carte)

    carte.add_child(folium.LatLngPopup())

    carte_html = carte._repr_html_()

    # Initialiser weather_data et température actuelle
    weather_data = []
    temperature_actuelle = 28  # Valeur par défaut
    condition_actuelle = "Partly Cloudy"  # Valeur par défaut
    
    df = get_weekly_precipitation(lat, lon, jour)
    if df is None or df.empty:
        message += " | ❌ Données météo indisponibles"
    else:
        message += f" | ✅ Données météo du {jour} au {df['Date'].iloc[-1]}"
        # Renommer la colonne problématique avant conversion
        df = df.rename(columns={'Probabilite_Max_%': 'Probabilite_Max'})
        
        # Récupérer la température actuelle (premier jour)
        if 'Temperature_Max' in df.columns and not df.empty:
            temperature_actuelle = round(df['Temperature_Max'].iloc[0], 1)
        
        # Déterminer la condition actuelle basée sur les précipitations du jour
        if 'Precipitation_mm' in df.columns and not df.empty:
            precip_aujourd_hui = df['Precipitation_mm'].iloc[0]
            if precip_aujourd_hui > 10:
                condition_actuelle = "Rainy"
            elif precip_aujourd_hui > 0:
                condition_actuelle = "Cloudy"
            else:
                condition_actuelle = "Sunny"
        
        # Convertir le DataFrame en liste de dictionnaires
        weather_data = df.to_dict('records')
        
        # S'assurer que les dates sont bien formatées
        for item in weather_data:
            if 'Date' in item and not isinstance(item['Date'], date):
                # Convertir la date si c'est une chaîne
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
        'lieu': lieu or '',
        'date': jour,
        'weather_data': weather_data,  # ✅ Ajout des données météo avec dates
        'ville': ville,  # ✅ Ajout de la ville
        'temperature_actuelle': temperature_actuelle,  # ✅ Température actuelle
        'condition_actuelle': condition_actuelle,  # ✅ Condition météo actuelle
    })

def dashboard(request):
    jour = request.GET.get('date')
    if not jour:
        jour = date.today().isoformat()
    return render(request, 
                  'pages/dashboard.html', 
                  {})
def map_view(request):
    return render(request, 
                  'pages/map.html', 
                  {})
def suggestions(request):
    jour = request.GET.get('date')
    if not jour:
        jour = date.today().isoformat()
    return render(request, 
                  'pages/suggestions.html', 
                  {})
def contact(request):
    jour = request.GET.get('date')
    if not jour:
        jour = date.today().isoformat()
    return render(request, 
                  'pages/contact.html', 
                  {'date': jour})



def download_dashboard_pdf(request):
    # Création du buffer mémoire
    buffer = io.BytesIO()

    # Création du document PDF
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    style_title = styles["Heading1"]
    style_subtitle = styles["Heading2"]
    style_body = styles["BodyText"]

    # --- TITRE PRINCIPAL ---
    elements.append(Paragraph("🌍 WorldCast Weather Dashboard Report", style_title))
    elements.append(Paragraph("Weekly summary of temperature, humidity, wind speed, and precipitation.", style_body))
    elements.append(Spacer(1, 12))

    # --- TABLEAU DES VALEURS MOYENNES ---
    data = [
        ["Variable", "Value", "Unit"],
        ["Temperature", "28", "°C"],
        ["Humidity", "65", "%"],
        ["Wind Speed", "12", "km/h"],
        ["Precipitation", "5", "mm"]
    ]
    table = Table(data, hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightblue),
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 12),
        ('BOTTOMPADDING', (0,0), (-1,0), 10),
        ('BACKGROUND',(0,1),(-1,-1),colors.beige),
        ('GRID',(0,0),(-1,-1),1,colors.gray)
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))

    # --- CRÉATION DES GRAPHIQUES AVEC MATPLOTLIB ---
    variables = {
        "Temperature (°C)": [28, 29, 27, 30, 31, 32, 29],
        "Humidity (%)": [60, 62, 65, 63, 66, 64, 61],
        "Wind Speed (km/h)": [10, 12, 14, 9, 11, 13, 12],
        "Precipitation (mm)": [2, 5, 3, 4, 6, 5, 4],
    }
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    for variable, values in variables.items():
        plt.figure(figsize=(4,2))
        plt.plot(days, values, marker='o', color='skyblue')
        plt.title(variable)
        plt.xlabel("Days")
        plt.ylabel(variable.split()[0])
        plt.grid(True)
        temp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        plt.savefig(temp_img.name, bbox_inches='tight')
        plt.close()

        # Ajouter le graphique au PDF
        elements.append(Paragraph(variable, style_subtitle))
        elements.append(Image(temp_img.name, width=5*inch, height=2*inch))
        elements.append(Paragraph(f"This chart shows the weekly variation of {variable.lower()}.", style_body))
        elements.append(Spacer(1, 20))

    # --- PIED DE PAGE ---
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("<i>Generated automatically by WorldCast Dashboard © 2025</i>", style_body))

    # Construction du PDF
    doc.build(elements)
    buffer.seek(0)

    return FileResponse(buffer, as_attachment=True, filename="WorldCast_Dashboard_Report.pdf")
