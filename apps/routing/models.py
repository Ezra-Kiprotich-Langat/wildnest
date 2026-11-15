from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from apps.core.models import TimeStampedModel
from apps.parks.models import GamePark, EntranceGate
from apps.accomodations.models import Accommodation


class SavedTrip(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saved_trips'
    )
    name = models.CharField(max_length=200, help_text="e.g., 'Family Safari to Kruger'")
    
    # Linked entities
    park = models.ForeignKey(
        GamePark,
        on_delete=models.CASCADE,
        related_name='trips'
    )
    entrance_gate = models.ForeignKey(
        EntranceGate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='trips'
    )
    accommodation = models.ForeignKey(
        Accommodation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='trips'
    )
    
    # Trip details
    start_location_name = models.CharField(max_length=300, blank=True)
    start_latitude = models.DecimalField(max_digits=9, decimal_places=6)
    start_longitude = models.DecimalField(max_digits=9, decimal_places=6)
    
    # Travel group
    num_adults = models.PositiveIntegerField(default=1)
    num_children = models.PositiveIntegerField(default=0)
    vehicle_type = models.CharField(
        max_length=20,
        choices=[
            ('STANDARD', 'Standard Vehicle'),
            ('4X4', '4x4 Vehicle'),
            ('MINIBUS', 'Minibus'),
            ('BUS', 'Bus'),
            ('MOTORCYCLE', 'Motorcycle'),
        ],
        default='STANDARD'
    )
    
    # Dates
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    num_days = models.PositiveIntegerField(default=1)
    
    # Calculated budget (stored for quick access)
    total_park_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_accommodation_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_fuel_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_budget = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='USD')
    
    # Status
    is_planned = models.BooleanField(default=True)
    is_completed = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Saved Trip'
        verbose_name_plural = 'Saved Trips'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.name} ({self.park.name})"


class RouteWaypoint(TimeStampedModel):
    trip = models.ForeignKey(
        SavedTrip,
        on_delete=models.CASCADE,
        related_name='waypoints'
    )
    order = models.PositiveIntegerField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    name = models.CharField(max_length=200, blank=True)
    waypoint_type = models.CharField(
        max_length=20,
        choices=[
            ('START', 'Start Point'),
            ('WAYPOINT', 'Intermediate Waypoint'),
            ('END', 'End Point (Park Gate)'),
            ('POI', 'Point of Interest'),
        ],
        default='WAYPOINT'
    )
    
    class Meta:
        ordering = ['order']
        unique_together = ['trip', 'order']
    
    def __str__(self):
        return f"{self.trip.name} - Waypoint {self.order}"


class PointOfInterest(TimeStampedModel):

    POI_TYPE_CHOICES = [
        ('FUEL_STATION', 'Fuel Station'),
        ('ATM', 'ATM/Bank'),
        ('RESTAURANT', 'Restaurant'),
        ('REST_STOP', 'Rest Stop'),
        ('HOSPITAL', 'Hospital/Clinic'),
        ('POLICE', 'Police Station'),
        ('VETERINARY', 'Veterinary Checkpoint'),
        ('VIEWPOINT', 'Scenic Viewpoint'),
        ('OTHER', 'Other'),
    ]
    
    name = models.CharField(max_length=200)
    poi_type = models.CharField(max_length=20, choices=POI_TYPE_CHOICES)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    address = models.CharField(max_length=300, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    description = models.TextField(blank=True)
    
    # Link to nearest park (optional)
    nearest_park = models.ForeignKey(
        GamePark,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='nearby_pois'
    )
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Point of Interest'
        verbose_name_plural = 'Points of Interest'
        ordering = ['poi_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_poi_type_display()})"