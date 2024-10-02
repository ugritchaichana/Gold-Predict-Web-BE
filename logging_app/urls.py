from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LogViewSet

router = DefaultRouter()
router.register(r'logs', LogViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
