from django.contrib import admin
from .models import Amenity, Accommodation, AccommodationImage, RoomType

@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'created_at')
    search_fields = ('name',)


class AccommodationImageInline(admin.TabularInline):
    model = AccommodationImage
    extra = 1


class RoomTypeInline(admin.TabularInline):
    model = RoomType
    extra = 1


@admin.register(Accommodation)
class AccommodationAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'property_type', 'park', 'star_rating',
        'average_rating', 'distance_to_gate_km', 'is_active', 'is_featured'
    )
    list_filter = ('property_type', 'star_rating', 'park', 'country', 'is_active', 'is_featured')
    search_fields = ('name', 'description', 'city', 'address')
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ('amenities',)
    inlines = [AccommodationImageInline, RoomTypeInline]
    ordering = ('-is_featured', 'name')


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'accommodation', 'category', 'price_per_night', 'currency', 'is_available')
    list_filter = ('category', 'meal_plan', 'is_available')
    search_fields = ('name', 'accommodation__name')
