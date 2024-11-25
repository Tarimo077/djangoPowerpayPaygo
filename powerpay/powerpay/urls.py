"""
URL configuration for powerpay project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from . import views
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('live/', views.live_page, name='live_page'),
    path('customer_sales/', include('customer_sales.urls'), name="customers"),
    path('', views.homepage, name='home_page'),
    path('add-device/', views.add_device, name='add_device'),
    path('transactions/', views.transactions_page, name='transactions_page'),
    path('export/excel/<str:range>', views.export_transactions_excel, name='export_transactions'),
    path('export/csv/', views.export_meter_data, name='export_meter_data'),
    path('payment_prompt', views.payment_prompt, name='payment_prompt'),
    path('payment_waiting/<str:ref>', views.payment_waiting, name='payment_waiting'),
    path('payment_confirmation', views.payment_confirmation, name='payment_confirmation'),
    path('payment_confirmation_status', views.payment_confirmation_status, name='payment_confirmation_status'),
    path('payment_confirmation_page/', views.payment_confirmation_page, name='payment_confirmation_page'),
    path('devices/', views.devices_page, name='devices_page'),
    path('device/<str:device_id>/', views.device_data_page, name='device_data_page'),
    path('export/device_data/<str:device_id>/<str:range>', views.export_device_data, name='export_device_data'),
    path('export/ml-data/', views.export_ml_dataset, name='export_ml_data'),
    path('export/<str:set>/', views.export_ml, name='export_ml'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('login/', views.login_page, name='login'),
    path('logout/', views.logout_page, name='logout'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='password_reset.html'), name='password_reset'),
    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
    path('password_reset_confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), name='password_reset_confirm'),
    path('password_reset_complete/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
