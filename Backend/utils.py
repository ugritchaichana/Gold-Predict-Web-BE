from google.cloud import storage
from django.conf import settings

def test_gcp_connection():
    try:
        client = storage.Client(
            project=settings.GCP_PROJECT_ID,
            credentials=settings.GS_CREDENTIALS
        )

        buckets = client.list_buckets()

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
