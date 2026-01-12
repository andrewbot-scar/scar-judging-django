"""
URL configuration for SCAR Judge Portal
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('tournaments.urls')),
]
