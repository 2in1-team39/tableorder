from django.contrib import admin
from .models import Menu, MenuOption

class MenuOptionInline(admin.TabularInline):
    model = MenuOption
    extra = 1

@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'min_order', 'is_active', 'created_at']
    list_filter = ['is_active', 'min_order']
    search_fields = ['name']
    inlines = [MenuOptionInline]
    readonly_fields = ['created_at', 'updated_at']
