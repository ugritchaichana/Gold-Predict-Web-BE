# Gold_US\urls.py

from django.urls import path
from .views import CSVUploadView, TestAPIView

urlpatterns = [
    path('upload-csv/', CSVUploadView.as_view(), name='upload_csv'),
    path('', TestAPIView.as_view(), name='test_api'),  # เส้นทางสำหรับฟังก์ชันทดสอบ
    # path('upload-csv/', CSVUploadView.as_view(), name='upload_csv'),
]
