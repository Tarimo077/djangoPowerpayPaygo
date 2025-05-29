# admin.py
from django.contrib import admin
from .models import InternalCustomer, InternalSale, Customer, Sale, TestCustomer, TestSale, userProfile, SayonaCustomer, SayonaSale, Warehouse, InventoryItem, InventoryMovement

@admin.register(userProfile)
class userProfileAdmin(admin.ModelAdmin):
    list_display = ('tnc_flag', 'org_name')

@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('name', 'location')

@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'serial_number', 'product_type', 'date_added', 'current_warehouse')

@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    list_display = ('item', 'from_warehouse', 'to_warehouse', 'date_moved', 'moved_by', 'note')

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'id_number', 'phone_number')

@admin.register(InternalCustomer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'id_number', 'phone_number')

@admin.register(InternalSale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'product_model', 'customer', 'release_date')

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'product_model', 'customer', 'registration_date')

############## FOR WELIGHT ##################
@admin.register(TestCustomer)
class TestCustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'id_number', 'phone_number')

@admin.register(TestSale)
class TestSaleAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'product_model', 'customer', 'registration_date')

############## FOR SAYONA ##################
@admin.register(SayonaCustomer)
class SayonaCustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'id_number', 'phone_number')

@admin.register(SayonaSale)
class SayonaSaleAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'product_model', 'customer', 'registration_date')

