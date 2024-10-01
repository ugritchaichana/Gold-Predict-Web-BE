from django.urls import path
from .views import fetch_gold_th

urlpatterns = [
    path('fetch-gold-th/', fetch_gold_th, name='fetch_gold_th'),
]
