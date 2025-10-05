from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('map/', views.map_view, name='map'),
    path('sugestion/', views.suggestions, name='suggestions'),
    path('contact/', views.contact, name='contact'),
    path('download-pdf/', views.download_dashboard_pdf, name='download_pdf'),
]
