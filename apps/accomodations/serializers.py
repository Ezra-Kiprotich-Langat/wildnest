from rest_framework import serializers
from .models import Amenity, Accommodation, AccommodationImage, RoomType


class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = ['id', 'name', 'icon', 'description']


class AccommodationImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccommodationImage
        fields = ['id', 'image', 'caption', 'is_primary', 'order']


class RoomTypeSerializer(serializers.ModelSerializer):
    meal_plan_display = serializers.CharField(source='get_meal_plan_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = RoomType
        fields = [
            'id', 'name', 'category', 'category_display',
            'description', 'max_adults', 'max_children',
            'view_type', 'price_per_night', 'currency',
            'meal_plan', 'meal_plan_display',
            'total_rooms', 'is_available', 'image'
        ]
        read_only_fields = ['id']


class AccommodationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing accommodations"""
    property_type_display = serializers.CharField(source='get_property_type_display', read_only=True)
    park_name = serializers.CharField(source='park.name', read_only=True)
    nearest_gate_name = serializers.CharField(source='nearest_gate.name', read_only=True, allow_null=True)
    amenity_names = serializers.SerializerMethodField()
    starting_price = serializers.SerializerMethodField()
    
    class Meta:
        model = Accommodation
        fields = [
            'id', 'name', 'slug', 'property_type', 'property_type_display',
            'star_rating', 'park_name', 'nearest_gate_name',
            'distance_to_gate_km', 'main_image', 'average_rating',
            'total_reviews', 'amenity_names', 'starting_price',
            'is_featured', 'country'
        ]
    
    def get_amenity_names(self, obj):
        return list(obj.amenities.values_list('name', flat=True)[:5])
    
    def get_starting_price(self, obj):
        cheapest_room = obj.room_types.filter(is_available=True).order_by('price_per_night').first()
        if cheapest_room:
            return {
                'amount': float(cheapest_room.price_per_night),
                'currency': cheapest_room.currency
            }
        return None


class AccommodationDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for a single accommodation"""
    property_type_display = serializers.CharField(source='get_property_type_display', read_only=True)
    park_name = serializers.CharField(source='park.name', read_only=True)
    nearest_gate_name = serializers.CharField(source='nearest_gate.name', read_only=True, allow_null=True)
    
    amenities = AmenitySerializer(many=True, read_only=True)
    images = AccommodationImageSerializer(many=True, read_only=True)
    room_types = RoomTypeSerializer(many=True, read_only=True)
    
    class Meta:
        model = Accommodation
        fields = [
            'id', 'name', 'slug', 'description', 'property_type',
            'property_type_display', 'star_rating',
            'park_name', 'nearest_gate_name', 'distance_to_gate_km',
            'latitude', 'longitude', 'address', 'city', 'country',
            'email', 'phone', 'website',
            'amenities', 'main_image', 'images', 'room_types',
            'average_rating', 'total_reviews',
            'is_active', 'is_featured',
            'created_at', 'updated_at'
        ]


class AccommodationCostCalculatorSerializer(serializers.Serializer):
    """Serializer for calculating accommodation costs"""
    accommodation_id = serializers.IntegerField()
    room_type_id = serializers.IntegerField(required=False, allow_null=True)
    check_in = serializers.DateField()
    check_out = serializers.DateField()
    num_adults = serializers.IntegerField(min_value=1, default=2)
    num_children = serializers.IntegerField(min_value=0, default=0)
    
    def validate(self, attrs):
        if attrs['check_out'] <= attrs['check_in']:
            raise serializers.ValidationError("Check-out date must be after check-in date.")
        
        # Limit max stay to 30 days
        stay_duration = (attrs['check_out'] - attrs['check_in']).days
        if stay_duration > 30:
            raise serializers.ValidationError("Maximum stay duration is 30 days.")
        
        return attrs