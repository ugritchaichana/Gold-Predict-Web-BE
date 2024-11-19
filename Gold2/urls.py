from django.urls import path
from .views import (
    GoldDataCreateView,
    GoldDataUploadView,
    GoldDataListView,
    GoldDataDeleteView,
    GoldDataDeleteByIdView
)

urlpatterns = [
    path('create/', GoldDataCreateView.as_view(), name='gold_currency_create'),
    path('list/', GoldDataListView.as_view(), name='currency-list'),
    path('upload/', GoldDataUploadView.as_view(), name='gold_thb_upload'),
    path('delete/', GoldDataDeleteView.as_view(), name='currency-delete'),
    path('delete-by-id/', GoldDataDeleteByIdView.as_view(), name='currency-delete-by-id'),
]
