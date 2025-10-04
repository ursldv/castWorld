
from django.shortcuts import render
from geopy.geocoders import Nominatim
import folium
import geocoder

from requests import request
# Create your views here.

from datetime import date
from meteo_app import geocode_city, get_weekly_precipitation


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
            message = f"📍 Résultat pour : {lieu}"
        else:
            lat, lon = 6.3703, 2.3912
            message = f"❌ Lieu introuvable : {lieu}"
    else:
        g = geocoder.ip('me')
        lat, lon = g.latlng if g.latlng else (6.3703, 2.3912)
        message = "📍 Position détectée automatiquement"

    # Création de la carte APRÈS avoir défini lat/lon
    carte = folium.Map(location=[lat, lon], zoom_start=6, control_scale=True, max_bounds=True)
    carte.fit_bounds(bounds)

    folium.Marker(
        [lat, lon],
        tooltip=message,
        popup=f"<b>{message}</b>",
        icon=folium.Icon(color="blue", icon="info-sign")
    ).add_to(carte)

    carte.add_child(folium.LatLngPopup())

    carte_html = carte._repr_html_()
    return render(request, 'pages/index.html', {
        'message': message,
        'carte': carte_html,
        'latitude': lat,
        'longitude': lon,
        'lieu': lieu or '',
        'date': jour,
        })
  

def dashboard(request):
    return render(request, 
                  'pages/dashboard.html', 
                  {})
def map_view(request):
    return render(request, 
                  'pages/map.html', 
                  {})
def suggestions(request):
    return render(request, 
                  'pages/suggestions.html', 
                  {})
def contact(request):
    return render(request, 
                  'pages/contact.html', 
                  {})