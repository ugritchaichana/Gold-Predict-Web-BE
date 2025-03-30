from django.urls import path
from .views import create_data_set, get_data, delete_data


urlpatterns = [
    path('create_data_set/', create_data_set),
    path('get_data/', get_data),
    path('delete_data/', delete_data),
]
