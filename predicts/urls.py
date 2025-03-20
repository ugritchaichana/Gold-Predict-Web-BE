from django.urls import path
from .views import create_week_view, read_week_view, update_week_view, delete_week_view, create_month_view, read_month_view, update_month_view, delete_month_view, read_all_months_view
from .test.read import read

urlpatterns = [
    # Week CRUD URLs
    path('week/create/', create_week_view, name='create_week'),
    path('week/read/', read_week_view, name='read_week'),
    path('week/update/', update_week_view, name='update_week'),
    path('week/delete/', delete_week_view, name='delete_week'),

    # path('week/test/read/', read, name='read'),

    # Month CRUD URLs
    path('month/create/', create_month_view, name='create_month'),
    path('month/read/<int:month_id>/', read_month_view, name='read_month'),
    path('month/update/<int:month_id>/', update_month_view, name='update_month'),
    path('month/delete/<int:month_id>/', delete_month_view, name='delete_month'),
    path('month/read_all/', read_all_months_view, name='read_all_months'),
]
