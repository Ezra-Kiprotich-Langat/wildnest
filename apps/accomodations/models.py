from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.models import TimeStampedModel
from apps.parks.models import GamePark, EntranceGate


class Amenity(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Icon name for frontend")
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Amenity'
        verbose_name_plural = 'Amenities'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Accommodation(TimeStampedModel):
    
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
    
    STAR_RATING_CHOICES = [(i, f'{i} Star') for i in range(1, 6)]
    
    # Basic info
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField()
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPE_CHOICES, default='LODGE')
    star_rating = models.IntegerField(choices=STAR_RATING_CHOICES, default=3)
    
    # Location - linked to park and nearest gate
    park = models.ForeignKey(
        GamePark, 
        on_delete=models.CASCADE, 
        related_name='accommodations'
    )
    nearest_gate = models.ForeignKey(
        EntranceGate, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='nearby_accommodations'
    )
    distance_to_gate_km = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Distance in km to the nearest gate"
    )
    
    # GPS coordinates
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Address
    address = models.CharField(max_length=300, blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100)
    
    # Contact info
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    website = models.URLField(blank=True)
    
    # Amenities (many-to-many)
    amenities = models.ManyToManyField(Amenity, related_name='accommodations', blank=True)
    
    # Main image
    main_image = models.ImageField(upload_to='accommodations/', blank=True, null=True)
    
    # Ratings & reviews
    average_rating = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    total_reviews = models.PositiveIntegerField(default=0)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Accommodation'
        verbose_name_plural = 'Accommodations'
        ordering = ['-is_featured', '-average_rating', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_property_type_display()}) - {self.park.name}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Accommodation.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class AccommodationImage(TimeStampedModel):
    accommodation = models.ForeignKey(
        Accommodation, 
        on_delete=models.CASCADE, 
        related_name='images'
    )
    image = models.ImageField(upload_to='accommodations/gallery/')
    caption = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order', '-is_primary']
    
    def __str__(self):
        return f"{self.accommodation.name} - Image {self.id}"


class RoomType(TimeStampedModel):
    
    ROOM_CATEGORY_CHOICES = [
        ('STANDARD', 'Standard Room'),
        ('DELUXE', 'Deluxe Room'),
        ('SUITE', 'Suite'),
        ('FAMILY', 'Family Room'),
        ('TENT', 'Safari Tent'),
        ('COTTAGE', 'Cottage/Chalet'),
        ('DORMITORY', 'Dormitory'),
    ]
    
    VIEW_CHOICES = [
        ('GARDEN', 'Garden View'),
        ('POOL', 'Pool View'),
        ('SAFARI', 'Safari/Bush View'),
        ('OCEAN', 'Ocean/Lake View'),
        ('MOUNTAIN', 'Mountain View'),
        ('CITY', 'City View'),
    ]
    
    accommodation = models.ForeignKey(
        Accommodation, 
        on_delete=models.CASCADE, 
        related_name='room_types'
    )
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=ROOM_CATEGORY_CHOICES, default='STANDARD')
    description = models.TextField(blank=True)
    
    # Capacity
    max_adults = models.PositiveIntegerField(default=2)
    max_children = models.PositiveIntegerField(default=2)
    
    # View type
    view_type = models.CharField(max_length=20, choices=VIEW_CHOICES, blank=True)
    
    # Pricing
    price_per_night = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    currency = models.CharField(max_length=3, default='USD')
    
    # Meal plan
    MEAL_PLAN_CHOICES = [
        ('ROOM_ONLY', 'Room Only'),
        ('BB', 'Bed & Breakfast'),
        ('HB', 'Half Board'),
        ('FB', 'Full Board'),
        ('AI', 'All Inclusive'),
    ]
    meal_plan = models.CharField(max_length=20, choices=MEAL_PLAN_CHOICES, default='BB')
    
    # Availability
    total_rooms = models.PositiveIntegerField(default=1)
    is_available = models.BooleanField(default=True)
    
    # Image for this room type
    image = models.ImageField(upload_to='accommodations/rooms/', blank=True, null=True)
    
    class Meta:
        ordering = ['price_per_night']
        unique_together = ['accommodation', 'name']
    
    def __str__(self):
        return f"{self.accommodation.name} - {self.name} ({self.price_per_night} {self.currency}/night)"
