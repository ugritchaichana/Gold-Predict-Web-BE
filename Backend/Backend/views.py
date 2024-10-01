# views.py
from django.http import JsonResponse
from .utils import test_gcp_connection

def test_gcp_connection_view(request):
    """API endpoint to test connection to Google Cloud Storage."""
    result = test_gcp_connection()
    return JsonResponse(result)
