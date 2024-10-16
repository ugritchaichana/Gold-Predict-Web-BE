from django.urls import path
from .views import (    GoldDataUploadView,
                        GoldDataListView,
                        GoldDataDeleteView,
                        GoldDataDeleteByIdView
                    )

urlpatterns = [
    path('upload/', GoldDataUploadView.as_view(), name='gold_thb_upload'),
    path('list/', GoldDataListView.as_view(), name='currency-list'),
    path('delete/', GoldDataDeleteView.as_view(), name='currency-delete'),
    path('delete-by-id/', GoldDataDeleteByIdView.as_view(), name='currency-delete-by-id'),
]
