import math
from decimal import Decimal
from django.utils.text import slugify as django_slugify
import re

def generate_unique_slug(model_instance, slug_field, slug_source):
    slug = django_slugify(getattr(model_instance, slug_source))
    unique_slug = slug
    num = 1
    
    ModelClass = model_instance.__class__
    while ModelClass.objects.filter(**{slug_field: unique_slug}).exists():
        unique_slug = f'{slug}-{num}'
        num += 1
    
    return unique_slug


def calculate_distance(lat1, lon1, lat2, lon2):
    # Earth's radius in kilometers
    R = 6371.0
    
    # Convert to radians
    lat1_rad = math.radians(float(lat1))
    lon1_rad = math.radians(float(lon1))
    lat2_rad = math.radians(float(lat2))
    lon2_rad = math.radians(float(lon2))
    
    # Differences
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    
    # Haversine formula
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return round(distance, 2)

def format_currency(amount, currency='USD'):
    currency_symbols = {
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
        'ZAR': 'R',
        'KES': 'KSh',
        'TZS': 'TSh',
        'UGX': 'USh',
    }
    
    symbol = currency_symbols.get(currency, currency + ' ')
    
    if isinstance(amount, Decimal):
        amount = float(amount)
    
    formatted_amount = f"{amount:,.2f}"
    return f"{symbol}{formatted_amount}"


def estimate_fuel_cost(distance_km, vehicle_type='STANDARD', fuel_price_per_liter=1.50):
    # Average fuel consumption in liters per 100km
    consumption_rates = {
        'STANDARD': 8.0,      # 8L/100km
        '4X4': 12.0,          # 12L/100km
        'MINIBUS': 15.0,      # 15L/100km
        'BUS': 25.0,          # 25L/100km
        'MOTORCYCLE': 4.0,    # 4L/100km
    }
    
    consumption = consumption_rates.get(vehicle_type, 10.0)
    liters_needed = (distance_km / 100) * consumption
    total_cost = liters_needed * fuel_price_per_liter
    
    return {
        'distance_km': distance_km,
        'liters_needed': round(liters_needed, 2),
        'fuel_price_per_liter': fuel_price_per_liter,
        'total_cost': round(total_cost, 2),
        'vehicle_type': vehicle_type
    }

def sanitize_phone_number(phone_number, country_code='+254'):
    if not phone_number:
        return None
    
    # Remove all non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', phone_number)
    
    # If starts with 0, replace with country code
    if cleaned.startswith('0'):
        cleaned = country_code + cleaned[1:]
    
    # If starts with country code without +, add it
    if cleaned.startswith('254') and not cleaned.startswith('+'):
        cleaned = '+' + cleaned
    
    return cleaned


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip