from django.urls import path
from .views import gold_start, gold_stop, gold_list, index

urlpatterns = [
    path('gold_start/', gold_start, name='gold_start'),
    # path('gold_start/', gold_start, name='gold_start'),   -> ex : Http [GET] : http://127.0.0.1:8000/gold_start?delay=180
    #                                                                                           (กำหนดความถี่ทำงานทุกๆ 180 วิ)
    # ยังไม่เสร็จ ใช้ใน cmd ไปก่อน
    # path('gold_stop/', gold_stop, name='gold_stop'),      -> cmd : py manage.py delete_all_tasks
    # path('gold_list/', gold_status, name='gold_list'),    -> cmd : py manage.py show_tasks
    path('', index, name='index'),
]
