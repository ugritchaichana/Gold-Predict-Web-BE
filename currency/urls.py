from django.urls import path
from .views import (
    CurrencyDataUploadView,
    # CurrencyDataListView,
    CurrencyDataDeleteView,
    CurrencyDataDeleteByIdView,
    CurrencyDataCreateView
)
from . import views
from .views import get_currency_data

urlpatterns = [
    path('create/', CurrencyDataCreateView.as_view(), name='currency-create'),
    path('upload/', CurrencyDataUploadView.as_view(), name='currency-upload'),
    # path('list/', CurrencyDataListView.as_view(), name='currency-list'),
    path('get/', get_currency_data, name='currency-get'),
    path('delete/', CurrencyDataDeleteView.as_view(), name='currency-delete'),
    path('delete-by-id/', CurrencyDataDeleteByIdView.as_view(), name='currency-delete-by-id'),
    path('add-crrencyth/', views.add_usdthb_data, name='add-goldth'),
]
