# admin.py
from django.contrib import admin
from .models import InternalCustomer, InternalSale, Customer, Sale, TestCustomer, TestSale, userProfile, SayonaCustomer, SayonaSale

@admin.register(userProfile)
class userProfileAdmin(admin.ModelAdmin):
    list_display = ('tnc_flag', 'org_name')

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

