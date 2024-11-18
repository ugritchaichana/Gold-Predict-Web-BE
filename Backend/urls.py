from django.urls import path,include
from .views import test_gcp_connection_view

urlpatterns = [
    # path('th', include('Gold_TH.urls')),
    # path('us/', include('Gold_US.urls')),
    path('currency/', include('currency.urls')),
    path('gold/', include('gold.urls')),
    path('api/test-gcp/', test_gcp_connection_view, name='test_gcp_connection'),
    path('api/', include('logging_app.urls')),
]
