from django.urls import path
from Gold import views
from .views import DailyGoldPriceView


urlpatterns = [
    path('',views.index),
    path('gold',views.gold),
    path('api/create-gold-prices/', DailyGoldPriceView.as_view(), name='gold-prices'),
]