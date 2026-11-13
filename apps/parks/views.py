# backend/apps/parks/views.py
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import GamePark, EntranceGate, EntranceFee
from .serializers import (GameParkListSerializer, GameParkDetailSerializer, EntranceGateSerializer, EntranceFeeSerializer, FeeCalculationSerializer)

class GameParkViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GamePark.objects.filter(is_active=True)
    permission_classes = [permissions.AllowAny]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return GameParkListSerializer
        return GameParkDetailSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by country
        country = self.request.query_params.get('country')
        if country:
            queryset = queryset.filter(country__iexact=country)
        
        # Search by name
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(description__icontains=search)
            )
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def gates(self, request, pk=None):
        """Get all gates for a specific park"""
        park = self.get_object()
        gates = park.gates.filter(is_active=True)
        serializer = EntranceGateSerializer(gates, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def fees(self, request, pk=None):
        """Get all fees for a specific park"""
        park = self.get_object()
        fees = park.fees.filter(is_active=True)
        serializer = EntranceFeeSerializer(fees, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def calculate_fees(self, request):
        
        serializer = FeeCalculationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        park_id = serializer.validated_data['park_id']
        residency = serializer.validated_data['residency_status']
        num_adults = serializer.validated_data['num_adults']
        num_children = serializer.validated_data['num_children']
        vehicle_type = serializer.validated_data['vehicle_type']
        num_days = serializer.validated_data['num_days']
        
        park = get_object_or_404(GamePark, id=park_id, is_active=True)
        
        # Calculate adult fees
        adult_fee_obj = EntranceFee.objects.filter(
            park=park,
            residency_status=residency,
            age_group='ADULT',
            vehicle_type='STANDARD',  # Per-person fee
            is_active=True
        ).first()
        
        # Calculate child fees
        child_fee_obj = EntranceFee.objects.filter(
            park=park,
            residency_status=residency,
            age_group='CHILD',
            vehicle_type='STANDARD',
            is_active=True
        ).first()
        
        # Calculate vehicle fee
        vehicle_fee_obj = EntranceFee.objects.filter(
            park=park,
            residency_status=residency,
            age_group='ADULT',  # Vehicle fees are usually under adult category
            vehicle_type=vehicle_type,
            is_active=True
        ).first()
        
        # Calculate totals
        adult_total = 0
        if adult_fee_obj:
            adult_total = float(adult_fee_obj.amount) * num_adults * num_days
        
        child_total = 0
        if child_fee_obj:
            child_total = float(child_fee_obj.amount) * num_children * num_days
        
        vehicle_total = 0
        if vehicle_fee_obj:
            vehicle_total = float(vehicle_fee_obj.amount) * num_days
        
        total = adult_total + child_total + vehicle_total
        
        return Response({
            'park': park.name,
            'breakdown': {
                'adults': {
                    'count': num_adults,
                    'fee_per_person': float(adult_fee_obj.amount) if adult_fee_obj else 0,
                    'subtotal': adult_total
                },
                'children': {
                    'count': num_children,
                    'fee_per_child': float(child_fee_obj.amount) if child_fee_obj else 0,
                    'subtotal': child_total
                },
                'vehicle': {
                    'type': vehicle_type,
                    'fee_per_day': float(vehicle_fee_obj.amount) if vehicle_fee_obj else 0,
                    'subtotal': vehicle_total
                }
            },
            'num_days': num_days,
            'total': total,
            'currency': adult_fee_obj.currency if adult_fee_obj else 'USD'
        })


class EntranceGateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EntranceGate.objects.filter(is_active=True)
    serializer_class = EntranceGateSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by park
        park_id = self.request.query_params.get('park_id')
        if park_id:
            queryset = queryset.filter(park_id=park_id)
        
        return queryset