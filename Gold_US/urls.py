# Gold_US\urls.py

from django.urls import path
from Gold_US.API.CSVUploadView import CSVUploadView

urlpatterns = [
    path('upload-csv/', CSVUploadView.as_view(), name='upload_csv'),
]
