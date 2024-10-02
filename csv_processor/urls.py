from django.urls import path
from .views import UploadCSV_XAUUSD

urlpatterns = [
    path('upload-xauusd/', UploadCSV_XAUUSD.as_view(), name='upload_xauusd'),
]
