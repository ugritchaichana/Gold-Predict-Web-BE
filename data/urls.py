from django.urls import path
from .views import create_data_set, get_data, delete_data, daily_data, set_database
from .check.check_data import check_data


urlpatterns = [
    path('daily_data/', daily_data),
    path('create_data_set/', create_data_set),
    path('get_data/', get_data),
    path('delete_data/', delete_data),
    path('set_database/', set_database),


    # check - include both with and without trailing slash
    path('check', check_data),  # Without trailing slash
    path('check/', check_data),  # With trailing slash
]

