from django.urls import path
from Gold import views

urlpatterns = [
    path('',views.index),
    path('api/scrape_gold_price/', views.scrape_gold_price),
]