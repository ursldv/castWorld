from django.shortcuts import render
# Create your views here.
def home(request):
   
    return render(request, 
                  'pages/index.html', 
                  {})
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