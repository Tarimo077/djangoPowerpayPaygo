# Generated by Django 5.0.6 on 2025-02-07 12:58

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer_sales', '0006_testcustomer_alter_customer_table_alter_sale_table_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelTable(
            name='testcustomer',
            table='customer_sales_customer_welight',
        ),
        migrations.AlterModelTable(
            name='testsale',
            table='customer_sales_sale_welight',
        ),
        migrations.CreateModel(
            name='userProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tnc_flag', models.BooleanField(default=False)),
                ('org_name', models.CharField(max_length=50)),
                ('user', models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
