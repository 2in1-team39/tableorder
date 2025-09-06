from django.contrib import admin
from .models import Order, OrderItem, Discount, PaymentMethod

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['get_total_price']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['table', 'status', 'total_amount', 'discount', 'get_final_amount', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['table__number']
    inlines = [OrderItemInline]
    readonly_fields = ['created_at', 'updated_at']
    
    def get_final_amount(self, obj):
        return obj.get_final_amount()
    get_final_amount.short_description = '최종 금액'

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'menu', 'quantity', 'unit_price', 'get_total_price']
    list_filter = ['menu', 'created_at']
    readonly_fields = ['get_total_price', 'created_at']

@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ['name', 'discount_type', 'value', 'is_active', 'created_at']
    list_filter = ['discount_type', 'is_active', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at']

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'code']
    readonly_fields = ['created_at']
