import requests
import logging
from django.conf import settings
from apps.core.utils import calculate_distance, estimate_fuel_cost

logger = logging.getLogger(__name__)


class MapboxService:
    
    BASE_URL = 'https://api.mapbox.com/directions/v5/mapbox'
    
    def __init__(self):
        self.access_token = getattr(settings, 'MAPBOX_ACCESS_TOKEN', None)
    
    def get_route(self, start_coords, end_coords, profile='driving'):
        
        if not self.access_token:
            logger.warning("Mapbox access token not configured")
            return self._get_mock_route(start_coords, end_coords)
        
        # Mapbox expects coordinates as "longitude,latitude;longitude,latitude"
        coordinates = f"{start_coords[0]},{start_coords[1]};{end_coords[0]},{end_coords[1]}"
        
        url = f"{self.BASE_URL}/{profile}/{coordinates}"
        params = {
            'access_token': self.access_token,
            'geometries': 'geojson',
            'overview': 'full',
            'steps': 'true',
            'annotations': 'distance,duration'
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('code') != 'Ok':
                logger.error(f"Mapbox API error: {data.get('message')}")
                return None
            
            route = data['routes'][0]
            
            return {
                'distance_km': round(route['distance'] / 1000, 2),  # Convert meters to km
                'duration_minutes': round(route['duration'] / 60, 1),  # Convert seconds to minutes
                'geometry': route['geometry'],  # GeoJSON for map display
                'steps': self._format_steps(route.get('legs', [{}])[0].get('steps', [])),
                'summary': route.get('summary', '')
            }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Mapbox API request failed: {e}")
            return self._get_mock_route(start_coords, end_coords)
    
    def _format_steps(self, steps):

        formatted_steps = []
        for step in steps[:10]:  # Limit to first 10 steps
            formatted_steps.append({
                'instruction': step.get('maneuver', {}).get('instruction', ''),
                'distance_m': step.get('distance', 0),
                'duration_s': step.get('duration', 0),
                'maneuver': step.get('maneuver', {}).get('type', '')
            })
        return formatted_steps
    
    def _get_mock_route(self, start_coords, end_coords):
       
        straight_distance = calculate_distance(
            start_coords[1], start_coords[0],  # lat, lon
            end_coords[1], end_coords[0]
        )
        road_distance = straight_distance * 1.3  # Estimate road distance
        
        # Estimate duration (average 60 km/h)
        duration_minutes = (road_distance / 60) * 60
        
        return {
            'distance_km': round(road_distance, 2),
            'duration_minutes': round(duration_minutes, 1),
            'geometry': None,  # No map geometry available
            'steps': [],
            'summary': 'Route calculated (offline mode)'
        }


class TripBudgetCalculator:
    
    def __init__(self):
        self.mapbox_service = MapboxService()
    
    def calculate_trip_budget(self, trip_data):
        
        from apps.parks.models import EntranceFee
        from apps.accomodations.models import RoomType
        
        budget = {
            'park_fees': self._calculate_park_fees(trip_data),
            'accommodation': self._calculate_accommodation_cost(trip_data),
            'fuel': self._calculate_fuel_cost(trip_data),
            'currency': 'USD'
        }
        
        # Calculate totals
        budget['total'] = round(
            budget['park_fees']['total'] +
            budget['accommodation']['total'] +
            budget['fuel']['total_cost'],
            2
        )
        
        return budget
    
    def _calculate_park_fees(self, trip_data):

        from apps.parks.models import EntranceFee
        
        park_id = trip_data.get('park_id')
        residency = trip_data.get('residency_status', 'INTERNATIONAL')
        num_adults = trip_data.get('num_adults', 1)
        num_children = trip_data.get('num_children', 0)
        vehicle_type = trip_data.get('vehicle_type', 'STANDARD')
        num_days = trip_data.get('num_days', 1)
        
        # Get adult fee
        adult_fee = EntranceFee.objects.filter(
            park_id=park_id,
            residency_status=residency,
            age_group='ADULT',
            vehicle_type='STANDARD',
            is_active=True
        ).first()
        
        # Get child fee
        child_fee = EntranceFee.objects.filter(
            park_id=park_id,
            residency_status=residency,
            age_group='CHILD',
            vehicle_type='STANDARD',
            is_active=True
        ).first()
        
        # Get vehicle fee
        vehicle_fee = EntranceFee.objects.filter(
            park_id=park_id,
            residency_status=residency,
            age_group='ADULT',
            vehicle_type=vehicle_type,
            is_active=True
        ).first()
        
        adult_total = float(adult_fee.amount) * num_adults * num_days if adult_fee else 0
        child_total = float(child_fee.amount) * num_children * num_days if child_fee else 0
        vehicle_total = float(vehicle_fee.amount) * num_days if vehicle_fee else 0
        
        return {
            'adults': {
                'count': num_adults,
                'fee_per_person': float(adult_fee.amount) if adult_fee else 0,
                'subtotal': adult_total
            },
            'children': {
                'count': num_children,
                'fee_per_child': float(child_fee.amount) if child_fee else 0,
                'subtotal': child_total
            },
            'vehicle': {
                'type': vehicle_type,
                'fee_per_day': float(vehicle_fee.amount) if vehicle_fee else 0,
                'subtotal': vehicle_total
            },
            'total': adult_total + child_total + vehicle_total,
            'currency': adult_fee.currency if adult_fee else 'USD'
        }
    
    def _calculate_accommodation_cost(self, trip_data):
        
        from apps.accomodations.models import RoomType, Accommodation
        
        accommodation_id = trip_data.get('accommodation_id')
        check_in = trip_data.get('check_in_date')
        check_out = trip_data.get('check_out_date')
        
        if not accommodation_id or not check_in or not check_out:
            return {'total': 0, 'nights': 0}
        
        nights = (check_out - check_in).days
        
        # Get cheapest available room
        accommodation = Accommodation.objects.filter(id=accommodation_id).first()
        if not accommodation:
            return {'total': 0, 'nights': nights}
        
        cheapest_room = accommodation.room_types.filter(is_available=True).order_by('price_per_night').first()
        
        if not cheapest_room:
            return {'total': 0, 'nights': nights}
        
        subtotal = float(cheapest_room.price_per_night) * nights
        taxes = subtotal * 0.16  # 16% VAT
        total = subtotal + taxes
        
        return {
            'accommodation_name': accommodation.name,
            'room_type': cheapest_room.name,
            'price_per_night': float(cheapest_room.price_per_night),
            'nights': nights,
            'subtotal': subtotal,
            'taxes': round(taxes, 2),
            'total': round(total, 2),
            'currency': cheapest_room.currency
        }
    
    def _calculate_fuel_cost(self, trip_data):
        
        start_lat = trip_data.get('start_latitude')
        start_lon = trip_data.get('start_longitude')
        end_lat = trip_data.get('end_latitude')
        end_lon = trip_data.get('end_longitude')
        vehicle_type = trip_data.get('vehicle_type', 'STANDARD')
        
        if not all([start_lat, start_lon, end_lat, end_lon]):
            return {'total_cost': 0, 'distance_km': 0}
        
        # Get route from Mapbox
        route = self.mapbox_service.get_route(
            (start_lon, start_lat),
            (end_lon, end_lat)
        )
        
        if not route:
            return {'total_cost': 0, 'distance_km': 0}
        
        distance_km = route['distance_km']
        
        # Estimate fuel cost (round trip)
        round_trip_distance = distance_km * 2
        fuel_estimate = estimate_fuel_cost(
            round_trip_distance,
            vehicle_type,
            fuel_price_per_liter=1.50  # Default price
        )
        
        return {
            'one_way_distance_km': distance_km,
            'round_trip_distance_km': round_trip_distance,
            'duration_minutes': route['duration_minutes'],
            **fuel_estimate
        }