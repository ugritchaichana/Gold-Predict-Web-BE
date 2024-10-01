from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from background_task import background
from background_task.models import Task
from datetime import datetime
from django.utils import timezone
from .serializers import DailyGoldPriceSerializer
import requests
from bs4 import BeautifulSoup
import json

@background(schedule=0)
def scrape_task():
    start_time = datetime.now()
    print('🔥 Task START')

    url = 'https://www.goldtraders.or.th/'
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        span_element = soup.find('span', id='DetailPlace_uc_goldprices1_lblBLSell')

        if span_element:
            try:
                price = float(span_element.get_text(strip=True).replace(',', ''))

                data = {
                    'date': timezone.now(),
                    'gold_price': price
                }

                serializer = DailyGoldPriceSerializer(data=data)
                if serializer.is_valid():
                    serializer.save()
                    current_time = datetime.now().strftime('%H:%M:%S %d/%m/%y')
                    print(f'✅ Success at {current_time}')
                else:
                    print(f'Error: {serializer.errors}')
            except ValueError:
                print('Invalid price format')
        else:
            print('Price element not found')
    else:
        print(f'Failed to retrieve data: {response.status_code}')

    end_time = datetime.now()
    duration = end_time - start_time
    print(f'⌛ Task completed in: {duration} \n')

def gold_start(request):
    try:
        delay = int(request.GET.get('delay', 86400))
    except ValueError:
        return JsonResponse({"status": "error", "message": "Invalid delay value. Please provide a valid integer."})

    scrape_task(repeat=delay)

    return JsonResponse({
        "status": "success",
        "message": f"Task scheduled to start immediately and repeat every {delay} seconds."
    })

def gold_list(request):
    tasks = Task.objects.all()
    tasks_data = list(tasks.values('id', 'task_name', 'task_params', 'task_hash', 'verbose_name', 'priority', 'run_at'))

    if tasks_data:
        return JsonResponse({"status": "success", "tasks": tasks_data})
    else:
        return JsonResponse({"status": "success", "message": "No tasks found."})

@csrf_exempt
@require_http_methods(["POST"])
def delete_task_by_id(request):
    try:
        body = json.loads(request.body)
        task_id = body.get('id')
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON format."}, status=400)

    if not task_id:
        return JsonResponse({"status": "error", "message": "Task ID is required."}, status=400)
    
    try:
        task = Task.objects.get(id=task_id)
        task.delete()
        return JsonResponse({"status": "success", "message": f"Task with ID {task_id} has been deleted."})
    except Task.DoesNotExist:
        return JsonResponse({"status": "error", "message": f"Task with ID {task_id} does not exist."}, status=404)

@csrf_exempt
@require_http_methods(["POST"])
def delete_all_tasks(request):
    Task.objects.all().delete()
    return JsonResponse({"status": "success", "message": "Successfully deleted all background tasks."})

def index(request):
    return JsonResponse({
        'Create task(1 day)' : 'get - http://127.0.0.1:8000/gold_start',
        'Create task custom(180 sec)' : 'get - http://127.0.0.1:8000/gold_start?delay=180',
        'AutoScrapeGoldTH' : 'py manage.py process_tasks',
        'Show all background tasks' : 'py manage.py show_tasks',
        'Delete all background tasks' : 'py manage.py delete_all_tasks'
    })