from django.urls import path
from .views import  index, gold_start, gold_list, delete_all_tasks, delete_task_by_id

urlpatterns = [
    path('', index, name='index'),
    path('gold_start/', gold_start, name='gold_start'),
    # gold_start -> ex : Http [GET] : http://127.0.0.1:8000/gold_start?delay=180 (ทำงานทุกๆ 180 วิ)
    path('gold_list/', gold_list, name='gold_list'),
    path('delete_task/', delete_task_by_id, name='delete_task_by_id'),
    path('delete_all_tasks/', delete_all_tasks, name='delete_all_tasks'),
]
