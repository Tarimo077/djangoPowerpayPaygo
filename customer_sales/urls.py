from django.urls import path
from . import views

urlpatterns = [
    path('', views.customers_list, name='customers_list'),
    path('customer/<int:pk>/', views.customer_detail, name='customer_detail'),
    path('customer/<int:pk>/edit/', views.customer_edit, name='customer_edit'),
    path('customer/<int:pk>/delete/', views.customer_delete, name='customer_delete'),
    path('customer/<int:customer_id>/sale/add/', views.sale_add, name='sale_add'),
    path('add_customer/', views.add_customer, name='add_customer'),
    path('sales/', views.sales_list, name='sales_list'),
    path('sales/add/', views.sale_add, name='sales_add'),
    path('sales/<int:pk>/', views.sale_detail, name='sale_detail'),
    path('sales/<int:pk>/edit/', views.sale_edit, name='sale_edit'),
    path('sales/<int:pk>/delete/', views.sale_delete, name='sale_delete'),
    path('paygo_sales/', views.paygo_sales, name='paygo_sales'),
    path('paygo_sales/detail/<str:id>/', views.sale_detail_paygo, name='paygo_sale_detail'),
    path('paygo_sales_non_metered/', views.paygo_sales_non_metered, name='paygo_sales_non_metered'),
    path('export/customers/', views.export_customer_data, name='export_customers'),
    path('export/sales/', views.export_sales_data, name='export_sales'),
    path('export/paygoScode/', views.export_paygo_data, name='export_paygoscode'),
    path('export/paygoScodeNonmetered/', views.export_paygoNonmetered_data, name='export_paygoscodenonmetered'),
]

