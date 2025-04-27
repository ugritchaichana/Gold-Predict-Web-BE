from django.urls import path
from .Util import set_cache
urlpatterns=[
    path('set-cache',set_cache)
]