from django.urls import path, include
from django.conf.urls import handler404

urlpatterns = [
    # Include mill URLs
    path('', include('mill.urls')),
]

handler404 = 'mill.views.custom_404_view'