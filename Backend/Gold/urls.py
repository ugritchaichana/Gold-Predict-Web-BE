from django.urls import path
from Gold import views

urlpatterns = [
    path('',views.index),
    path('gold',views.gold),
]