from rest_framework import serializers
from .models import GamePark, EntranceGate, EntranceFee

class EntranceGateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntranceGate
        fields = [
            'id', 'name', 'latitude', 'longitude', 
            'is_main_gate', 'description', 'is_active'
        ]
        read_only_fields = ['id']


class EntranceFeeSerializer(serializers.ModelSerializer):
    residency_display = serializers.CharField(source='get_residency_status_display', read_only=True)
    age_group_display = serializers.CharField(source='get_age_group_display', read_only=True)
    vehicle_type_display = serializers.CharField(source='get_vehicle_type_display', read_only=True)
    
    class Meta:
        model = EntranceFee
        fields = [
            'id', 'residency_status', 'residency_display',
            'age_group', 'age_group_display',
            'vehicle_type', 'vehicle_type_display',
            'amount', 'currency', 'description',
            'valid_from', 'valid_to', 'is_active'
        ]
        read_only_fields = ['id']


class GameParkListSerializer(serializers.ModelSerializer):
    gate_count = serializers.IntegerField(source='gates.count', read_only=True)
    country_flag = serializers.SerializerMethodField()
    
    class Meta:
        model = GamePark
        fields = [
            'id', 'name', 'slug', 'country', 'region',
            'country_flag', 'main_image', 'gate_count',
            'is_active'
        ]
    
    def get_country_flag(self, obj):
        # Simple emoji flag mapping
        flags = {
            'South Africa': '🇿🇦',
            'Kenya': '🇰🇪',
            'Tanzania': '🇹🇿',
            'Uganda': '🇺🇬',
            'Botswana': '🇧🇼',
            'Namibia': '🇳🇦',
        }
        return flags.get(obj.country, '🌍')


class GameParkDetailSerializer(serializers.ModelSerializer):
    gates = EntranceGateSerializer(many=True, read_only=True)
    fees = EntranceFeeSerializer(many=True, read_only=True)
    
    class Meta:
        model = GamePark
        fields = [
            'id', 'name', 'slug', 'description', 'country', 'region',
            'opening_time', 'closing_time', 'latitude', 'longitude',
            'main_image', 'is_active', 'gates', 'fees',
            'created_at', 'updated_at'
        ]

class FeeCalculationSerializer(serializers.Serializer):
    park_id = serializers.IntegerField()
    residency_status = serializers.ChoiceField(choices=['LOCAL', 'REGIONAL', 'INTERNATIONAL'])
    num_adults = serializers.IntegerField(min_value=0, default=1)
    num_children = serializers.IntegerField(min_value=0, default=0)
    vehicle_type = serializers.ChoiceField(
        choices=['STANDARD', '4X4', 'MINIBUS', 'BUS', 'MOTORCYCLE'],
        default='STANDARD'
    )
    num_days = serializers.IntegerField(min_value=1, default=1)