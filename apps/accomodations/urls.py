from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AccommodationViewSet, AmenityViewSet

router = DefaultRouter()
router.register(r'accommodations', AccommodationViewSet, basename='accommodation')
router.register(r'amenities', AmenityViewSet, basename='amenity')

urlpatterns = [
    path('', include(router.urls)),
]