from django.db import models


class Customer(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('P', 'Prefer not to say'),
        ('O', 'Other'),
    ]
    
    HOUSEHOLD_CHOICES = [
        ('M', 'Male headed'),
        ('F', 'Female headed'),
        ('C', 'Child headed'),
        ('O', 'Other'),
        ('P', 'Prefer not to say'),
    ]
    
    LANGUAGE_CHOICES = [
        ('EN', 'English'),
        ('SW', 'Kiswahili'),
        ('NA', 'Native'),
    ]

    name = models.CharField(max_length=255)
    id_number = models.CharField(max_length=20, unique=True)
    phone_number = models.CharField(max_length=15)
    alternate_phone_number = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    country = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    household_type = models.CharField(max_length=1, choices=HOUSEHOLD_CHOICES)
    household_size = models.IntegerField()
    preferred_language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES)
    date = models.DateTimeField(auto_now_add=True)
    county = models.CharField(max_length=100, null=True, blank=True)
    sub_county = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'customer_sales_customer'  # Default table for regular users


class Sale(models.Model):
    PRODUCT_TYPE_CHOICES = [
        ('EPC', 'Electric pressure cooker'),
        ('IC', 'Induction cooker'),
        ('O', 'Other'),
    ]
    
    PURCHASE_MODE_CHOICES = [
        ('C', 'Cash'),
        ('DA', 'Deposit Account'),
        ('P', 'PAYGO'),
    ]
    TYPE_OF_USE_CHOICES = [
        ('Domestic', 'Domestic'),
        ('Business', 'Business'),
        ('Other', 'Other')
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='sales')
    registration_date = models.DateField()
    release_date = models.DateField(blank=True, null=True)
    product_type = models.CharField(max_length=3, choices=PRODUCT_TYPE_CHOICES)
    product_name = models.CharField(max_length=255)
    product_model = models.CharField(max_length=255)
    product_serial_number = models.CharField(max_length=255)
    purchase_mode = models.CharField(max_length=2, choices=PURCHASE_MODE_CHOICES)
    referred_by = models.ForeignKey(Customer, on_delete=models.SET_NULL, blank=True, null=True,
                                    related_name='referrals')
    sales_rep = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now_add=True)
    metered = models.BooleanField(default=False)
    type_of_use = models.CharField(max_length=10, choices=TYPE_OF_USE_CHOICES, default='Domestic')
    specific_economic_activity = models.CharField(max_length=255, null=True, blank=True)
    location_of_use = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.product_name} ({self.product_model})"

    class Meta:
        db_table = 'customer_sales_sale'  # Default table for regular users


########################################################### FOR TESTING PURPOSES ONLY #############################################
class TestCustomer(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('P', 'Prefer not to say'),
        ('O', 'Other'),
    ]
    
    HOUSEHOLD_CHOICES = [
        ('M', 'Male headed'),
        ('F', 'Female headed'),
        ('C', 'Child headed'),
        ('O', 'Other'),
        ('P', 'Prefer not to say'),
    ]
    
    LANGUAGE_CHOICES = [
        ('EN', 'English'),
        ('SW', 'Kiswahili'),
        ('NA', 'Native'),
    ]

    name = models.CharField(max_length=255)
    id_number = models.CharField(max_length=20, unique=True)
    phone_number = models.CharField(max_length=15)
    alternate_phone_number = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    country = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    household_type = models.CharField(max_length=1, choices=HOUSEHOLD_CHOICES)
    household_size = models.IntegerField()
    preferred_language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES)
    date = models.DateTimeField(auto_now_add=True)
    county = models.CharField(max_length=100, null=True, blank=True)
    sub_county = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'customer_sales_customer_welight'  # Default table for regular users

class TestSale(models.Model):
    PRODUCT_TYPE_CHOICES = [
        ('EPC', 'Electric pressure cooker'),
        ('IC', 'Induction cooker'),
        ('O', 'Other'),
    ]
    
    PURCHASE_MODE_CHOICES = [
        ('C', 'Cash'),
        ('DA', 'Deposit Account'),
        ('P', 'PAYGO'),
    ]
    TYPE_OF_USE_CHOICES = [
        ('Domestic', 'Domestic'),
        ('Business', 'Business'),
        ('Other', 'Other')
    ]
    
    customer = models.ForeignKey(TestCustomer, on_delete=models.CASCADE, related_name='testsales')
    registration_date = models.DateField()
    release_date = models.DateField(blank=True, null=True)
    product_type = models.CharField(max_length=3, choices=PRODUCT_TYPE_CHOICES)
    product_name = models.CharField(max_length=255)
    product_model = models.CharField(max_length=255)
    product_serial_number = models.CharField(max_length=255)
    purchase_mode = models.CharField(max_length=2, choices=PURCHASE_MODE_CHOICES)
    referred_by = models.ForeignKey(TestCustomer, on_delete=models.SET_NULL, blank=True, null=True,
                                    related_name='referrals')
    sales_rep = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now_add=True)
    metered = models.BooleanField(default=False)
    type_of_use = models.CharField(max_length=10, choices=TYPE_OF_USE_CHOICES, default='Domestic')
    specific_economic_activity = models.CharField(max_length=255, null=True, blank=True)
    location_of_use = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.product_name} ({self.product_model})"

    class Meta:
        db_table = 'customer_sales_sale_welight'  # Default table for regular users