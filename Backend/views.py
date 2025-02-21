from google.cloud import storage
from django.conf import settings
from django.http import JsonResponse

# ฟังก์ชันเพื่อทดสอบการเชื่อมต่อกับ Google Cloud Storage
def test_gcp_connection():
    try:
        # สร้าง client เชื่อมต่อกับ Google Cloud Storage
        client = storage.Client(
            project=settings.GCP_PROJECT_ID,
            credentials=settings.GS_CREDENTIALS
        )

        # ดึงรายการ buckets ทั้งหมด
        buckets = client.list_buckets()

        # สร้างลิสต์ชื่อ buckets
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

# API view สำหรับทดสอบการเชื่อมต่อ GCP
def test_gcp_connection_view(request):
    """API endpoint to test connection to Google Cloud Storage."""
    result = test_gcp_connection()
    return JsonResponse(result)

# ฟังก์ชันสำหรับแสดงรายการไฟล์ใน bucket ที่ระบุ
def view_files_bucket(request):
    # รับชื่อ bucket จาก query parameters
    bucket_name = request.GET.get('bucket_name', None)
    
    if not bucket_name:
        return JsonResponse({
            'status': 'error',
            'message': 'Missing bucket_name parameter'
        }, status=400)

    try:
        # สร้าง client เชื่อมต่อกับ Google Cloud Storage
        client = storage.Client(
            project=settings.GCP_PROJECT_ID,
            credentials=settings.GS_CREDENTIALS
        )

        # ดึง bucket ที่ระบุ
        bucket = client.get_bucket(bucket_name)

        # ดึงรายการไฟล์ (blobs) จาก bucket
        blobs = bucket.list_blobs()

        # สร้างรายการชื่อไฟล์
        file_names = [blob.name for blob in blobs]

        # ส่งคืนข้อมูลในรูปแบบ JSON
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
