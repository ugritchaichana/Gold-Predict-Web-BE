from django.urls import path,include
from .views import test_gcp_connection_view, view_files_bucket

urlpatterns = [
    path('currency/', include('currency.urls')),
    path('gold/', include('gold.urls')),
    path('api/test-gcp/', test_gcp_connection_view, name='test_gcp_connection'),
    path('api/view-files-bucket/', view_files_bucket, name='view_files_bucket'),
    path('api/', include('logging_app.urls')),
    path('finnomenaGold/', include('finnomenaGold.urls')),
    path('predicts/', include('predicts.urls')),
]
