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
    
    bounds = [[6.2, 0.8], [12.5, 3.9]]  # Limites du Bénin
    geolocator = Nominatim(user_agent="meteo_app")

    if lieu:
        location = geolocator.geocode(lieu)
        if location:
            lat, lon = location.latitude, location.longitude
            message = f"✅ Résultat pour : {lieu}"
            zoom_level = 14  # Zoom rapproché pour un lieu spécifique
            ville = lieu
        else:
            lat, lon = 6.3703, 2.3912  # Coordonnées par défaut (Cotonou, Bénin)
            message = f"❌ Lieu introuvable : {lieu}"
            zoom_level = 6  # Zoom large pour lieu introuvable
            ville = "Cotonou, BJ"
    else:
        g = geocoder.ip('me')
        lat, lon = g.latlng if g.latlng else (6.3703, 2.3912)
        message = "📍 Position détectée automatiquement"
        zoom_level = 10  # Zoom intermédiaire pour géolocalisation IP
        try:
            location_reverse = geolocator.reverse(f"{lat}, {lon}")
            ville = location_reverse.address.split(',')[0] if location_reverse else "Cotonou, BJ"
        except:
            ville = "Cotonou, BJ"

    # Création de la carte
    carte = folium.Map(location=[lat, lon], zoom_start=zoom_level, control_scale=True, max_bounds=True)
    carte.fit_bounds(bounds)  # Assure que la carte reste dans les limites du Bénin

    # Ajouter un marqueur pour le lieu
    folium.Marker(
        [lat, lon],
        tooltip=message,
        popup=f"<b>{message}</b><br>Lat: {lat:.4f}, Lon: {lon:.4f}",
        icon=folium.Icon(color="blue", icon="info-sign")
    ).add_to(carte)

    carte.add_child(folium.LatLngPopup())
    carte_html = carte._repr_html_()

    # Initialiser weather_data et température actuelle
    weather_data = []
    temperature_actuelle = 28
    condition_actuelle = "Partly Cloudy"
    
    df = get_weekly_precipitation(lat, lon, jour)
    if df is None or df.empty:
        message += " | ❌ Données météo indisponibles"
    else:
        message += f" | ✅ Données météo du {jour} au {df['Date'].iloc[-1]}"
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

    risque_inondation = "Données insuffisantes"
    recommandation = "Impossible de formuler une recommandation sans données fiables."
    message = ""

    if df is not None and not df.empty:
        avg_precip = df.get("Precipitation_mm", pd.Series([0])).mean()
        avg_temp = df.get("Temperature_Max", pd.Series([28])).mean()  # Valeur par défaut si pas de colonne

        if avg_precip >= 100:
            risque_inondation = " Risque d’inondation critique"
            recommandation = (
                "Quittez les zones inondables si possible. "
                "Protégez vos documents importants et coupez l’électricité en cas de montée d’eau."
            )
        elif avg_precip >= 70:
            risque_inondation = "⚠️ Risque d’inondation élevé"
            recommandation = (
                "Restez vigilants. Surélevez vos biens, évitez les déplacements en soirée, "
                "et tenez-vous informés des alertes locales."
            )
        elif avg_precip >= 40:
            risque_inondation = " Risque modéré d’inondation"
            recommandation = (
                "Nettoyez les caniveaux, évitez d’obstruer les voies d’écoulement, "
                "et préparez un kit d’urgence si vous vivez en zone basse."
            )
        else:
            risque_inondation = " Faible risque d’inondation"
            recommandation = (
                "Aucune alerte majeure, mais restez prudents. "
                "Les sols peuvent encore être humides si des pluies récentes ont eu lieu."
            )

        if avg_temp > 35 and avg_precip > 40:
            recommandation += " La chaleur pourrait intensifier le ruissellement, soyez attentif."

        dernier_jour = df['Date'].iloc[-1] if 'Date' in df.columns else jour
        message = f"Données analysées pour {lieu or 'Cotonou'} du {jour} au {dernier_jour}."
    else:
        message = " Données météo indisponibles pour ce lieu ou cette période."

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

    elements.append(Paragraph(f"🌍 Rapport Météo WorldCast - {lieu}", style_title))
    elements.append(Paragraph(f"Résumé hebdomadaire des précipitations et températures du {jour}", style_body))
    elements.append(Spacer(1, 12))

    df = get_weekly_precipitation(lat, lon, jour)
    if df is None or df.empty:
        elements.append(Paragraph("❌ Données météo indisponibles pour cette période ou ce lieu.", style_body))
        elements.append(Spacer(1, 20))
        doc.build(elements)
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename="WorldCast_Dashboard_Report.pdf")

    df = df.rename(columns={'Probabilite_Max_%': 'Probabilite_Max'})
    avg_temperature = round(df['Temperature_Max'].mean(), 1) if 'Temperature_Max' in df.columns else 28
    avg_precipitation = round(df['Precipitation_mm'].mean(), 1) if 'Precipitation_mm' in df.columns else 5
    avg_humidity = 65
    avg_wind_speed = 12

    data = [
        ["Variable", "Valeur", "Unité"],
        ["Température", f"{avg_temperature}", "°C"],
        ["Humidité", f"{avg_humidity}", "%"],
        ["Vitesse du vent", f"{avg_wind_speed}", "km/h"],
        ["Précipitations", f"{avg_precipitation}", "mm"]
    ]
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

    days = [d.strftime('%a') for d in df['Date']]
    
    plt.figure(figsize=(4, 2))
    plt.plot(days, df['Precipitation_mm'], marker='o', color='skyblue', label='Précipitations (mm)')
    plt.title("Précipitations Hebdomadaires")
    plt.xlabel("Jours")
    plt.ylabel("Précipitations (mm)")
    plt.grid(True)
    temp_img_precip = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(temp_img_precip.name, bbox_inches='tight')
    plt.close()

    elements.append(Paragraph("Précipitations Hebdomadaires", style_subtitle))
    elements.append(Image(temp_img_precip.name, width=5*inch, height=2*inch))
    elements.append(Paragraph("Ce graphique montre la variation hebdomadaire des précipitations.", style_body))
    elements.append(Spacer(1, 20))

    plt.figure(figsize=(4, 2))
    plt.plot(days, df['Temperature_Max'], marker='o', color='orange', label='Température (°C)')
    plt.title("Températures Hebdomadaires")
    plt.xlabel("Jours")
    plt.ylabel("Température (°C)")
    plt.grid(True)
    temp_img_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(temp_img_temp.name, bbox_inches='tight')
    plt.close()

    elements.append(Paragraph("Températures Hebdomadaires", style_subtitle))
    elements.append(Image(temp_img_temp.name, width=5*inch, height=2*inch))
    elements.append(Paragraph("Ce graphique montre la variation hebdomadaire des températures maximales.", style_body))
    elements.append(Spacer(1, 20))

    fig, ax1 = plt.subplots(figsize=(4, 2))
    ax1.plot(days, df['Precipitation_mm'], marker='o', color='skyblue', label='Précipitations (mm)')
    ax1.set_xlabel("Jours")
    ax1.set_ylabel("Précipitations (mm)", color='skyblue')
    ax1.tick_params(axis='y', labelcolor='skyblue')
    ax1.grid(True)

    ax2 = ax1.twinx()
    ax2.plot(days, df['Temperature_Max'], marker='o', color='orange', label='Température (°C)')
    ax2.set_ylabel("Température (°C)", color='orange')
    ax2.tick_params(axis='y', labelcolor='orange')

    plt.title("Évolution Hebdomadaire (Précipitations et Température)")
    fig.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=2)
    temp_img_combined = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(temp_img_combined.name, bbox_inches='tight')
    plt.close()

    elements.append(Paragraph("Évolution Hebdomadaire", style_subtitle))
    elements.append(Image(temp_img_combined.name, width=5*inch, height=2*inch))
    elements.append(Paragraph("Ce graphique combine les précipitations et les températures pour montrer leur évolution hebdomadaire.", style_body))
    elements.append(Spacer(1, 20))

    elements.append(Spacer(1, 30))
    elements.append(Paragraph(f"<i>Généré automatiquement par WorldCast Dashboard © {date.today().year}</i>", style_body))

    doc.build(elements)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename="WorldCast_Dashboard_Report.pdf")