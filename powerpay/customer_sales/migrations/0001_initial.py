# Generated by Django 5.0.6 on 2024-06-21 09:21

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('id_number', models.CharField(max_length=20, unique=True)),
                ('phone_number', models.CharField(max_length=15)),
                ('alternate_phone_number', models.CharField(blank=True, max_length=15, null=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('country', models.CharField(max_length=100)),
                ('location', models.CharField(max_length=100)),
                ('gender', models.CharField(choices=[('M', 'Male'), ('F', 'Female'), ('P', 'Prefer not to say'), ('O', 'Other')], max_length=1)),
                ('household_type', models.CharField(choices=[('M', 'Male headed'), ('F', 'Female headed'), ('C', 'Child headed'), ('O', 'Other'), ('P', 'Prefer not to say')], max_length=1)),
                ('household_size', models.IntegerField()),
                ('preferred_language', models.CharField(choices=[('EN', 'English'), ('SW', 'Kiswahili'), ('NA', 'Native')], max_length=2)),
                ('date', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Sale',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('registration_date', models.DateField()),
                ('release_date', models.DateField(blank=True, null=True)),
                ('product_type', models.CharField(choices=[('EPC', 'Electric pressure cooker'), ('IC', 'Induction cooker'), ('O', 'Other')], max_length=3)),
                ('product_name', models.CharField(max_length=255)),
                ('product_model', models.CharField(max_length=255)),
                ('product_serial_number', models.CharField(max_length=255)),
                ('purchase_mode', models.CharField(choices=[('C', 'Cash'), ('DA', 'Deposit Account'), ('P', 'PAYGO')], max_length=2)),
                ('referred_by', models.CharField(blank=True, max_length=255, null=True)),
                ('sales_rep', models.CharField(max_length=255)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sales', to='customer_sales.customer')),
            ],
        ),
    ]