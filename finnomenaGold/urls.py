from django.urls import path
from .views import fetch_gold_data, delete_all_gold_data, get_gold_data, create_gold_data

urlpatterns = [
    path('fetch-gold-data/', fetch_gold_data, name='fetch_gold_data'),
    path('delete-all-gold-data/', delete_all_gold_data, name='delete_all_gold_data'),
    path('get-gold-data/', get_gold_data, name='get_gold_data'),
    path('create-gold-data/', create_gold_data, name='create_gold_data'),
]
