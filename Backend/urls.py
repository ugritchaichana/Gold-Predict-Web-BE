from django.urls import path,include
from .views import test_gcp_connection_view

urlpatterns = [
    path('currency/', include('currency.urls')),
    path('gold/', include('gold.urls')),
    path('api/test-gcp/', test_gcp_connection_view, name='test_gcp_connection'),
    path('api/', include('logging_app.urls')),
    path('finnomenaGold/', include('finnomenaGold.urls')),
]
