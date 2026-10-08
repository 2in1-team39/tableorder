from django.contrib import admin
from .models import Menu, MenuOption

class MenuOptionInline(admin.TabularInline):
    model = MenuOption
    extra = 1

@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ['name', 'sort_order', 'price', 'min_order', 'is_active', 'is_sold_out', 'created_at']
    list_display_links = ['name']
    list_editable = ['sort_order']
    list_filter = ['is_active', 'is_sold_out', 'min_order']
    ordering = ['sort_order', 'name']
    search_fields = ['name']
    inlines = [MenuOptionInline]
    readonly_fields = ['created_at', 'updated_at']
