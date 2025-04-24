from google.cloud import storage
from django.conf import settings
from django.http import JsonResponse
from django.core.cache import cache

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

def test_gcp_connection_view(request):
    result = test_gcp_connection()
    return JsonResponse(result)

def view_files_bucket(request):
    bucket_name = request.GET.get('bucket_name', None)
    
    if not bucket_name:
        return JsonResponse({
            'status': 'error',
            'message': 'Missing bucket_name parameter'
        }, status=400)

    try:
        client = storage.Client(
            project=settings.GCP_PROJECT_ID,
            credentials=settings.GS_CREDENTIALS
        )

        bucket = client.get_bucket(bucket_name)

        blobs = bucket.list_blobs()

        file_names = [blob.name for blob in blobs]

        return JsonResponse({
            'status': 'success',
            'bucket': bucket_name,
            'files': file_names
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

def clear_redis_cache(request):
    try:
        cache.clear()
        return JsonResponse({'status': 'success', 'message': 'Redis cache cleared successfully.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
