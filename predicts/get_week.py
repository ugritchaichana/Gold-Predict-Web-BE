from django.http import JsonResponse
from .models import Week
import json
from datetime import datetime, timedelta

def get_week(request):
    if request.method == 'GET':
        weeks = Week.objects.all().values()
        return JsonResponse(list(weeks), safe=False)
    return JsonResponse({'error': 'GET method required'}, status=405)