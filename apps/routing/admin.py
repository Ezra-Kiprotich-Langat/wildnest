from django.contrib import admin
from .models import SavedTrip, RouteWaypoint, PointOfInterest

class RouteWaypointInline(admin.TabularInline):
    model = RouteWaypoint
    extra = 0

@admin.register(SavedTrip)
class SavedTripAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'user', 'park', 'check_in_date', 'check_out_date',
        'total_budget', 'currency', 'is_planned', 'is_completed'
    )
    list_filter = ('park', 'is_planned', 'is_completed', 'vehicle_type')
    search_fields = ('name', 'user__username', 'park__name')
    date_hierarchy = 'check_in_date'
    inlines = [RouteWaypointInline]
    readonly_fields = (
        'total_park_fees', 'total_accommodation_cost',
        'total_fuel_cost', 'total_budget', 'created_at', 'updated_at'
    )

@admin.register(PointOfInterest)
class PointOfInterestAdmin(admin.ModelAdmin):
    list_display = ('name', 'poi_type', 'nearest_park', 'is_active')
    list_filter = ('poi_type', 'nearest_park', 'is_active')
    search_fields = ('name', 'address', 'description')