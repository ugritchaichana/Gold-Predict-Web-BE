from django.urls import path,include
from .views import test_gcp_connection_view

urlpatterns = [
    # path('', include("Gold.urls")),
    path('th', include('Gold_TH.urls')),
    path('', include('Gold_US.urls')),
    path('api/test-gcp/', test_gcp_connection_view, name='test_gcp_connection'),
]
