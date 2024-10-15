from django.urls import path
from .views import (CurrencyDataUploadView,CurrencyDataListView,CurrencyDataDeleteView,CurrencyDataDeleteByIdView)

urlpatterns = [
    path('upload/', CurrencyDataUploadView.as_view(), name='currency-upload'),
    path('list/', CurrencyDataListView.as_view(), name='currency-list'),
    path('delete/', CurrencyDataDeleteView.as_view(), name='currency-delete'),
    path('delete-by-id/', CurrencyDataDeleteByIdView.as_view(), name='currency-delete-by-id'),
]
