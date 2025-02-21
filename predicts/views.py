from django.http import JsonResponse
from .crud_week import create_week, read_week, update_week, delete_week
from .crud_month import create_month, read_month, update_month, delete_month

# Week Views
def create_week_view(request):
    return create_week(request)

def read_week_view(request):
    # รับค่า 'week_id' จาก query parameter
    week_id = request.GET.get('week_id')
    return read_week(request, week_id)

def update_week_view(request):
    return update_week(request)

def delete_week_view(request):
    week_id = request.GET.get('week_id')
    if week_id:
        return delete_week(request)
    return JsonResponse({'status': 'error', 'message': 'week_id is required'}, status=400)

# Month Views
def create_month_view(request):
    return create_month(request)

def read_month_view(request, month_id=None):
    return read_month(request, month_id)

def update_month_view(request, month_id):
    return update_month(request, month_id)

def delete_month_view(request, month_id):
    return delete_month(request, month_id)
