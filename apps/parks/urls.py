from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GameParkViewSet, EntranceGateViewSet

router = DefaultRouter()
router.register(r'parks', GameParkViewSet, basename='gamepark')
router.register(r'gates', EntranceGateViewSet, basename='entrancegate')

urlpatterns = [
    path('', include(router.urls)),
]