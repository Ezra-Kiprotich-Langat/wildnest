from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SavedTripViewSet, PointOfInterestViewSet, RouteCalculationView

router = DefaultRouter()
router.register(r'trips', SavedTripViewSet, basename='trip')
router.register(r'pois', PointOfInterestViewSet, basename='poi')
router.register(r'routes', RouteCalculationView, basename='route')

urlpatterns = [
    path('', include(router.urls)),
]