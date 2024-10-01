from google.cloud import storage
from django.conf import settings  # Import settings

def test_gcp_connection():
    """Test connection to Google Cloud Storage and return list of buckets."""
    try:
        # สร้าง client ของ Google Cloud Storage พร้อม credentials และ project
        client = storage.Client(
            project=settings.GCP_PROJECT_ID,  # ใช้ Project ID จาก settings
            credentials=settings.GS_CREDENTIALS  # ใช้ credentials จาก settings
        )

        # ลิสต์ bucket ที่มีอยู่
        buckets = client.list_buckets()

        # เก็บชื่อ bucket ในลิสต์
        bucket_names = [bucket.name for bucket in buckets]

        return {
            'status': 'success',
            'buckets': bucket_names
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }
