from django.contrib import admin
from django.urls import path, include
from . import views
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.auth import views as auth_views
from django.views.generic.base import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('live/<str:deviceID>/', views.live_page, name='live_page'),
    path('customer_sales/', include('customer_sales.urls'), name="customers"),
    path('', views.landingpage, name='landing_page'),
    path('analysis/', views.homepage, name='home_page'),
    path('terms_of_service/', views.terms_of_service, name='terms_of_service'),
    path('accept_tnc/', views.accept_tnc, name='accept_tnc'),
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
    path('device/<str:deviceID>/', views.device_data_page, name='device_data_page'),
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
    path('summary/', views.summary, name='summary'),
    path('change_device_status/', views.change_device_status, name='change_device_status'),
    path('status_dev/', views.status_dev, name='status_dev'),
    path('export_bulk_device_data/', views.export_bulk_device_data, name='export_bulk_device_data'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name="edit_profile"),
    path('mec_downloads/', views.mec_downloads, name='mec_downloads'),
    path('export_mec_downloads/', views.export_mec_downloads, name='export_mec_downloads'),
    path('export_single_mec_download/', views.mec_single_download, name='export_mec_downloads_single'),
    path("robots.txt",TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
