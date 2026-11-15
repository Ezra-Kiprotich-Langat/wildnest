from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import SavedTrip, PointOfInterest
from .serializers import (SavedTripSerializer, SavedTripListSerializer, PointOfInterestSerializer, RouteCalculationSerializer,TripBudgetSerializer    )
from .services import MapboxService, TripBudgetCalculator


class SavedTripViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return SavedTripListSerializer
        return SavedTripSerializer
    
    def get_queryset(self):
        return SavedTrip.objects.filter(user=self.request.user).select_related(
            'park', 'entrance_gate', 'accommodation'
        ).prefetch_related('waypoints')
    
    def perform_create(self, serializer):
        # Calculate budget before saving
        trip_data = serializer.validated_data
        
        # Add IDs for budget calculation
        trip_data['park_id'] = trip_data['park'].id
        if trip_data.get('accommodation'):
            trip_data['accommodation_id'] = trip_data['accommodation'].id
        trip_data['end_latitude'] = trip_data['entrance_gate'].latitude if trip_data.get('entrance_gate') else trip_data['park'].latitude
        trip_data['end_longitude'] = trip_data['entrance_gate'].longitude if trip_data.get('entrance_gate') else trip_data['park'].longitude
        
        calculator = TripBudgetCalculator()
        budget = calculator.calculate_trip_budget(trip_data)
        
        # Save the trip with calculated budget
        serializer.save(
            user=self.request.user,
            total_park_fees=budget['park_fees']['total'],
            total_accommodation_cost=budget['accommodation']['total'],
            total_fuel_cost=budget['fuel']['total_cost'],
            total_budget=budget['total'],
            currency=budget['currency']
        )
    
    @action(detail=True, methods=['post'])
    def recalculate_budget(self, request, pk=None):
        trip = self.get_object()
        
        trip_data = {
            'park_id': trip.park.id,
            'accommodation_id': trip.accommodation.id if trip.accommodation else None,
            'residency_status': request.user.residency_status,
            'start_latitude': trip.start_latitude,
            'start_longitude': trip.start_longitude,
            'end_latitude': trip.entrance_gate.latitude if trip.entrance_gate else trip.park.latitude,
            'end_longitude': trip.entrance_gate.longitude if trip.entrance_gate else trip.park.longitude,
            'num_adults': trip.num_adults,
            'num_children': trip.num_children,
            'vehicle_type': trip.vehicle_type,
            'check_in_date': trip.check_in_date,
            'check_out_date': trip.check_out_date
        }
        
        calculator = TripBudgetCalculator()
        budget = calculator.calculate_trip_budget(trip_data)
        
        # Update trip with new budget
        trip.total_park_fees = budget['park_fees']['total']
        trip.total_accommodation_cost = budget['accommodation']['total']
        trip.total_fuel_cost = budget['fuel']['total_cost']
        trip.total_budget = budget['total']
        trip.currency = budget['currency']
        trip.save()
        
        return Response({
            'message': 'Budget recalculated successfully',
            'budget': budget
        })
    
    @action(detail=True, methods=['post'])
    def mark_completed(self, request, pk=None):
        """Mark a trip as completed"""
        trip = self.get_object()
        trip.is_completed = True
        trip.is_planned = False
        trip.save()
        return Response({'message': 'Trip marked as completed'})


class PointOfInterestViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PointOfInterest.objects.filter(is_active=True)
    serializer_class = PointOfInterestSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by type
        poi_type = self.request.query_params.get('type')
        if poi_type:
            queryset = queryset.filter(poi_type=poi_type)
        
        # Filter by park
        park_id = self.request.query_params.get('park_id')
        if park_id:
            queryset = queryset.filter(nearest_park_id=park_id)
        
        # Search by name
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(address__icontains=search)
            )
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def near_location(self, request):
        from apps.core.utils import calculate_distance
        
        latitude = request.query_params.get('latitude')
        longitude = request.query_params.get('longitude')
        radius_km = float(request.query_params.get('radius_km', 10))
        poi_type = request.query_params.get('type')
        
        if not latitude or not longitude:
            return Response(
                {'error': 'latitude and longitude are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get all active POIs
        pois = PointOfInterest.objects.filter(is_active=True)
        if poi_type:
            pois = pois.filter(poi_type=poi_type)
        
        # Calculate distance and filter
        nearby_pois = []
        for poi in pois:
            distance = calculate_distance(
                float(latitude), float(longitude),
                float(poi.latitude), float(poi.longitude)
            )
            if distance <= radius_km:
                poi_data = PointOfInterestSerializer(poi).data
                poi_data['distance_km'] = distance
                nearby_pois.append(poi_data)
        
        # Sort by distance
        nearby_pois.sort(key=lambda x: x['distance_km'])
        
        return Response(nearby_pois)


class RouteCalculationView(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False, methods=['post'])
    def calculate_route(self, request):
        serializer = RouteCalculationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        mapbox_service = MapboxService()
        route = mapbox_service.get_route(
            (float(data['start_longitude']), float(data['start_latitude'])),
            (float(data['end_longitude']), float(data['end_latitude'])),
            profile=data.get('profile', 'driving')
        )
        
        if not route:
            return Response(
                {'error': 'Unable to calculate route'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Calculate fuel cost
        from apps.core.utils import estimate_fuel_cost
        fuel_cost = estimate_fuel_cost(
            route['distance_km'] * 2,  # Round trip
            data.get('vehicle_type', 'STANDARD')
        )
        
        return Response({
            'route': route,
            'fuel_estimate': fuel_cost
        })
    
    @action(detail=False, methods=['post'])
    def calculate_trip_budget(self, request):
        serializer = TripBudgetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        calculator = TripBudgetCalculator()
        budget = calculator.calculate_trip_budget(serializer.validated_data)
        
        return Response(budget)