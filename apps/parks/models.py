from django.db import models
from apps.core.models import TimeStampedModel
from django.core.validators import MinValueValidator


class GamePark(TimeStampedModel):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(blank=True)
    country = models.CharField(max_length=100)
    region = models.CharField(max_length=100, blank=True)
    
    # Operating hours
    opening_time = models.TimeField(default='06:00:00')
    closing_time = models.TimeField(default='18:30:00')
    
    # Location (for map display)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Images
    main_image = models.ImageField(upload_to='parks/', blank=True, null=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Game Park'
        verbose_name_plural = 'Game Parks'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.country})"
    
    def save(self, *args, **kwargs):
        # Auto-generate slug from name if not provided
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class EntranceGate(TimeStampedModel):
    park = models.ForeignKey(GamePark, on_delete=models.CASCADE, related_name='gates')
    name = models.CharField(max_length=200)
    
    # GPS coordinates for routing
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    
    # Gate-specific info
    is_main_gate = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Entrance Gate'
        verbose_name_plural = 'Entrance Gates'
        ordering = ['park', 'name']
        unique_together = ['park', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.park.name}"


class EntranceFee(TimeStampedModel):
    RESIDENCY_CHOICES = [
        ('LOCAL', 'Local Citizen'),
        ('REGIONAL', 'Regional Resident'),
        ('INTERNATIONAL', 'International Tourist'),
    ]
    
    AGE_GROUP_CHOICES = [
        ('ADULT', 'Adult (12+ years)'),
        ('CHILD', 'Child (2-11 years)'),
        ('INFANT', 'Infant (0-1 years) - Free'),
    ]
    
    VEHICLE_TYPE_CHOICES = [
        ('STANDARD', 'Standard Vehicle'),
        ('4X4', '4x4 Vehicle'),
        ('MINIBUS', 'Minibus (10-20 seats)'),
        ('BUS', 'Bus (20+ seats)'),
        ('MOTORCYCLE', 'Motorcycle'),
    ]
    
    park = models.ForeignKey(GamePark, on_delete=models.CASCADE, related_name='fees')
    
    # Fee category
    residency_status = models.CharField(max_length=20, choices=RESIDENCY_CHOICES)
    age_group = models.CharField(max_length=20, choices=AGE_GROUP_CHOICES, default='ADULT')
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPE_CHOICES, default='STANDARD')
    
    # Fee amount
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, default='USD')

    # Validity period (optional - for seasonal pricing)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)
    
    # Description
    description = models.TextField(blank=True, help_text="e.g., 'Per person per day'")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Entrance Fee'
        verbose_name_plural = 'Entrance Fees'
        ordering = ['park', 'residency_status', 'age_group']
    
    def __str__(self):
        return f"{self.park.name} - {self.get_residency_status_display()} {self.get_age_group_display()} - {self.amount} {self.currency}"


