RESIDENCY_CHOICES = [
    ('LOCAL', 'Local Citizen'),
    ('REGIONAL', 'Regional Resident'),
    ('INTERNATIONAL', 'International Tourist'),
]

# Age Group Choices
AGE_GROUP_CHOICES = [
    ('ADULT', 'Adult (12+ years)'),
    ('CHILD', 'Child (2-11 years)'),
    ('INFANT', 'Infant (0-1 years) - Free'),
]

# Vehicle Types
VEHICLE_TYPE_CHOICES = [
    ('STANDARD', 'Standard Vehicle'),
    ('4X4', '4x4 Vehicle'),
    ('MINIBUS', 'Minibus (10-20 seats)'),
    ('BUS', 'Bus (20+ seats)'),
    ('MOTORCYCLE', 'Motorcycle'),
]

# Currency Choices
CURRENCY_CHOICES = [
    ('USD', 'US Dollar'),
    ('EUR', 'Euro'),
    ('GBP', 'British Pound'),
    ('ZAR', 'South African Rand'),
    ('KES', 'Kenyan Shilling'),
    ('TZS', 'Tanzanian Shilling'),
    ('UGX', 'Ugandan Shilling'),
]

# Property Types (for accommodations)
PROPERTY_TYPE_CHOICES = [
    ('LODGE', 'Lodge'),
    ('HOTEL', 'Hotel'),
    ('CAMP', 'Safari Camp'),
    ('TENTED_CAMP', 'Tented Camp'),
    ('GUESTHOUSE', 'Guest House'),
    ('HOSTEL', 'Hostel/Backpackers'),
    ('CAMPSITE', 'Campsite'),
    ('RESORT', 'Resort'),
]

# Meal Plan Choices
MEAL_PLAN_CHOICES = [
    ('ROOM_ONLY', 'Room Only'),
    ('BB', 'Bed & Breakfast'),
    ('HB', 'Half Board'),
    ('FB', 'Full Board'),
    ('AI', 'All Inclusive'),
]

# Default Values
DEFAULT_CURRENCY = 'USD'
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
MAX_UPLOAD_SIZE_MB = 5  # 5MB

# API Rate Limits (requests per minute)
ANON_RATE = '20/minute'
USER_RATE = '100/minute'
STAFF_RATE = '1000/minute'