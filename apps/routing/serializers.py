from rest_framework import serializers
from django.utils import timezone
from .models import SavedTrip, RouteWaypoint, PointOfInterest

class PointOfInterestSerializer(serializers.ModelSerializer):
    poi_type_display = serializers.CharField(source='get_poi_type_display', read_only=True)
    
    class Meta:
        model = PointOfInterest
        fields = [
            'id', 'name', 'poi_type', 'poi_type_display',
            'latitude', 'longitude', 'address', 'phone',
            'description', 'nearest_park'
        ]


class RouteWaypointSerializer(serializers.ModelSerializer):
    class Meta:
        model = RouteWaypoint
        fields = ['id', 'order', 'latitude', 'longitude', 'name', 'waypoint_type']
        read_only_fields = ['id']


class SavedTripSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    park_name = serializers.CharField(source='park.name', read_only=True)
    gate_name = serializers.CharField(source='entrance_gate.name', read_only=True, allow_null=True)
    accommodation_name = serializers.CharField(source='accommodation.name', read_only=True, allow_null=True)
    waypoints = RouteWaypointSerializer(many=True, read_only=True)
    
    class Meta:
        model = SavedTrip
        fields = [
            'id', 'username', 'name',
            'park', 'park_name', 'entrance_gate', 'gate_name',
            'accommodation', 'accommodation_name',
            'start_location_name', 'start_latitude', 'start_longitude',
            'num_adults', 'num_children', 'vehicle_type',
            'check_in_date', 'check_out_date', 'num_days',
            'total_park_fees', 'total_accommodation_cost',
            'total_fuel_cost', 'total_budget', 'currency',
            'is_planned', 'is_completed', 'notes',
            'waypoints', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'username', 'total_park_fees', 'total_accommodation_cost',
            'total_fuel_cost', 'total_budget', 'created_at', 'updated_at'
        ]
    
    def validate(self, attrs):
        check_in = attrs.get('check_in_date')
        check_out = attrs.get('check_out_date')
        
        if check_in and check_out:
            if check_out <= check_in:
                raise serializers.ValidationError(
                    "Check-out date must be after check-in date."
                )
            
            # Calculate num_days
            attrs['num_days'] = (check_out - check_in).days
        
        return attrs


class SavedTripListSerializer(serializers.ModelSerializer):
    park_name = serializers.CharField(source='park.name', read_only=True)
    accommodation_name = serializers.CharField(source='accommodation.name', read_only=True, allow_null=True)
    
    class Meta:
        model = SavedTrip
        fields = [
            'id', 'name', 'park_name', 'accommodation_name',
            'check_in_date', 'check_out_date', 'num_days',
            'total_budget', 'currency', 'is_planned', 'is_completed'
        ]


class RouteCalculationSerializer(serializers.Serializer):
    start_latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    start_longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    end_latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    end_longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    vehicle_type = serializers.ChoiceField(
        choices=['STANDARD', '4X4', 'MINIBUS', 'BUS', 'MOTORCYCLE'],
        default='STANDARD'
    )
    profile = serializers.ChoiceField(
        choices=['driving', 'walking', 'cycling'],
        default='driving'
    )


class TripBudgetSerializer(serializers.Serializer):
    park_id = serializers.IntegerField()
    accommodation_id = serializers.IntegerField(required=False, allow_null=True)
    residency_status = serializers.ChoiceField(
        choices=['LOCAL', 'REGIONAL', 'INTERNATIONAL']
    )
    start_latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    start_longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    end_latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    end_longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    num_adults = serializers.IntegerField(min_value=1, default=1)
    num_children = serializers.IntegerField(min_value=0, default=0)
    vehicle_type = serializers.ChoiceField(
        choices=['STANDARD', '4X4', 'MINIBUS', 'BUS', 'MOTORCYCLE'],
        default='STANDARD'
    )
    check_in_date = serializers.DateField()
    check_out_date = serializers.DateField()