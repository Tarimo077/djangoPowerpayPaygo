# admin.py
from django.contrib import admin
from .models import Customer, Sale, TestCustomer, TestSale, userProfile

@admin.register(userProfile)
class userProfileAdmin(admin.ModelAdmin):
    list_display = ('tnc_flag', 'org_name')

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'id_number', 'phone_number')

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'product_model', 'customer', 'registration_date')


##############FOR TEST PURPOSES ONLY##################
@admin.register(TestCustomer)
class TestCustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'id_number', 'phone_number')

@admin.register(TestSale)
class TestSaleAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'product_model', 'customer', 'registration_date')

