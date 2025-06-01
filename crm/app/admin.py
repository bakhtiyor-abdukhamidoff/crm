from django.contrib import admin
from .models import Customer, Product, Order, OrderItem

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'email', 'customer_type', 'created_at']
    list_filter = ['customer_type', 'created_at']
    search_fields = ['first_name', 'last_name', 'email']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock_quantity', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['name', 'description']

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'status', 'total_amount', 'order_date']
    list_filter = ['status', 'order_date']
    search_fields = ['customer__first_name', 'customer__last_name']
    inlines = [OrderItemInline]