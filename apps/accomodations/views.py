# backend/apps/accomodations/views.py
from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q, Min
from django_filters.rest_framework import DjangoFilterBackend
from .models import Amenity, Accommodation, RoomType
from .serializers import (AmenitySerializer, AccommodationListSerializer, AccommodationDetailSerializer,AccommodationCostCalculatorSerializer)

class AmenityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Amenity.objects.all()
    serializer_class = AmenitySerializer
    permission_classes = [permissions.AllowAny]


class AccommodationViewSet(viewsets.ReadOnlyModelViewSet):
   
    queryset = Accommodation.objects.filter(is_active=True).prefetch_related(
        'amenities', 'room_types', 'images'
    )
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['park', 'property_type', 'star_rating', 'country', 'is_featured']
    search_fields = ['name', 'description', 'city', 'address']
    ordering_fields = ['name', 'average_rating', 'distance_to_gate_km', 'created_at']
    ordering = ['-is_featured', '-average_rating']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return AccommodationListSerializer
        return AccommodationDetailSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        
        # Filter by nearest gate
        gate_id = params.get('gate_id')
        if gate_id:
            queryset = queryset.filter(nearest_gate_id=gate_id)
        
        # Filter by price range
        min_price = params.get('min_price')
        max_price = params.get('max_price')
        if min_price:
            queryset = queryset.filter(
                room_types__price_per_night__gte=min_price,
                room_types__is_available=True
            ).distinct()
        if max_price:
            queryset = queryset.filter(
                room_types__price_per_night__lte=max_price,
                room_types__is_available=True
            ).distinct()
        
        # Filter by amenities (can pass multiple: ?amenity=1&amenity=2)
        amenity_ids = params.getlist('amenity')
        if amenity_ids:
            for amenity_id in amenity_ids:
                queryset = queryset.filter(amenities__id=amenity_id)
        
        # Filter by distance
        max_distance = params.get('max_distance_km')
        if max_distance:
            queryset = queryset.filter(distance_to_gate_km__lte=max_distance)
        
        # Only available accommodations
        available_only = params.get('available_only', 'true').lower() == 'true'
        if available_only:
            queryset = queryset.filter(room_types__is_available=True).distinct()
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def rooms(self, request, pk=None):
        accommodation = self.get_object()
        rooms = accommodation.room_types.filter(is_available=True)
        from .serializers import RoomTypeSerializer
        serializer = RoomTypeSerializer(rooms, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def calculate_cost(self, request):
        
        serializer = AccommodationCostCalculatorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        accommodation = get_object_or_404(
            Accommodation, 
            id=data['accommodation_id'], 
            is_active=True
        )
        
        # Get room type
        if data.get('room_type_id'):
            room = get_object_or_404(
                RoomType,
                id=data['room_type_id'],
                accommodation=accommodation,
                is_available=True
            )
        else:
            # Get cheapest available room that fits the group
            room = accommodation.room_types.filter(
                is_available=True,
                max_adults__gte=data['num_adults'],
                max_children__gte=data['num_children']
            ).order_by('price_per_night').first()
            
            if not room:
                return Response(
                    {'error': 'No available room fits your group size.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Calculate nights and total
        nights = (data['check_out'] - data['check_in']).days
        subtotal = float(room.price_per_night) * nights
        
        # Estimate taxes/fees 
        tax_rate = 0.16
        taxes = round(subtotal * tax_rate, 2)
        total = round(subtotal + taxes, 2)
        
        return Response({
            'accommodation': accommodation.name,
            'room_type': room.name,
            'check_in': data['check_in'],
            'check_out': data['check_out'],
            'nights': nights,
            'guests': {
                'adults': data['num_adults'],
                'children': data['num_children']
            },
            'price_breakdown': {
                'price_per_night': float(room.price_per_night),
                'subtotal': subtotal,
                'tax_rate': f"{tax_rate * 100}%",
                'taxes': taxes,
                'total': total,
                'currency': room.currency
            },
            'meal_plan': room.get_meal_plan_display()
        })
    
    @action(detail=False, methods=['get'])
    def near_gate(self, request):
    
        gate_id = request.query_params.get('gate_id')
        radius_km = request.query_params.get('radius_km', 20)
        
        if not gate_id:
            return Response(
                {'error': 'gate_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        accommodations = Accommodation.objects.filter(
            nearest_gate_id=gate_id,
            is_active=True,
            distance_to_gate_km__lte=radius_km
        ).order_by('distance_to_gate_km')
        
        serializer = AccommodationListSerializer(accommodations, many=True)
        return Response(serializer.data)
