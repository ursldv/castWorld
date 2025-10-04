from django.shortcuts import render

from requests import request
# Create your views here.

from datetime import date
from meteo_app import geocode_city, get_weekly_precipitation

def home(request):
    jour = request.GET.get('date')
    if not jour:
        jour = date.today().isoformat()  # format "2025-10-04"
    return render(request, 'pages/index.html', {'date': jour})


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