from django.contrib import admin
from .models import Table, TableGroup

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ['number', 'seats', 'status', 'created_at']
    list_filter = ['status', 'seats']
    search_fields = ['number']
    ordering = ['number']
    readonly_fields = ['qr_code', 'created_at', 'updated_at']

@admin.register(TableGroup)
class TableGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    filter_horizontal = ['tables']
