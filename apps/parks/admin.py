from django.contrib import admin
from .models import GamePark, EntranceGate, EntranceFee

@admin.register(GamePark)
class GameParkAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'region', 'is_active', 'created_at')
    list_filter = ('country', 'is_active', 'created_at')
    search_fields = ('name', 'description', 'country')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)


@admin.register(EntranceGate)
class EntranceGateAdmin(admin.ModelAdmin):
    list_display = ('name', 'park', 'is_main_gate', 'is_active')
    list_filter = ('park', 'is_main_gate', 'is_active')
    search_fields = ('name', 'park__name')
    ordering = ('park', 'name')


@admin.register(EntranceFee)
class EntranceFeeAdmin(admin.ModelAdmin):
    list_display = ('park', 'residency_status', 'age_group', 'vehicle_type', 'amount', 'currency', 'is_active')
    list_filter = ('park', 'residency_status', 'age_group', 'vehicle_type', 'is_active')
    search_fields = ('park__name', 'description')
    ordering = ('park', 'residency_status', 'age_group')
