from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now


class userProfile(models.Model):
    user = models.OneToOneField(User, null=True, on_delete=models.CASCADE)
    tnc_flag = models.BooleanField(default=False)
    org_name = models.CharField(max_length=50)
    org_address = models.CharField(null=True, blank=True, max_length=500)
    org_phone_number = models.CharField(max_length=15, null=True, blank=True)
    org_email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return str(self.user)
    class Meta:
        db_table = 'customer_sales_userProfile'

####################################FOR INVENTORY SYSTEM#######################

class Warehouse(models.Model):
    name = models.CharField(max_length=100, unique=True)
    location = models.CharField(max_length=255)

    def __str__(self):
        return self.name
    class Meta:
        db_table = 'warehouses'
    
class InventoryItem(models.Model):
    name = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=100, unique=True)
    product_type = models.CharField(max_length=100)
    date_added = models.DateField(auto_now_add=True)
    current_warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='inventory_items')

    def __str__(self):
        return f"{self.name} ({self.serial_number})"
    class Meta:
        db_table = 'inventory_items'
    @property
    def days_in_current_warehouse(self):
        # Get the most recent movement *into* the current warehouse
        last_movement_to_current = self.movements.filter(to_warehouse=self.current_warehouse).order_by('-date_moved').first()
        
        if last_movement_to_current:
            return (now() - last_movement_to_current.date_moved).days
        return (now() - self.date_added).days  # Fallback for items never moved
    
class InventoryMovement(models.Model):
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='movements')
    from_warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True,blank=True, related_name='moved_from')
    to_warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, related_name='moved_to')
    moved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    date_moved = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.item.serial_number} → {self.to_warehouse.name} by {self.moved_by} on {self.date_moved}"
    class Meta:
        db_table = 'inventory_movements'
        ordering = ['-date_moved']


########################POWERPAY INTERNAL MODELS###################
class InternalCustomer(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('P', 'Prefer not to say'),
        ('O', 'Other'),
    ]
    
    #HOUSEHOLD_CHOICES = [
        #('M', 'Male headed'),
        #('F', 'Female headed'),
        #('C', 'Child headed'),
        #('O', 'Other'),
        #('P', 'Prefer not to say'),
    #]
    
    #LANGUAGE_CHOICES = [
        #('EN', 'English'),
        #('SW', 'Kiswahili'),
        #('NA', 'Native'),
    #]

    name = models.CharField(max_length=255)
    external_id = models.CharField(max_length=100)
    id_number = models.CharField(max_length=20, unique=True)
    phone_number = models.CharField(max_length=15)
    #alternate_phone_number = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    #country = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    #household_type = models.CharField(max_length=1, choices=HOUSEHOLD_CHOICES)
    household_size = models.IntegerField()
    #preferred_language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES)
    date = models.DateTimeField(auto_now_add=True)
    county = models.CharField(max_length=100, null=True, blank=True)
    sub_county = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'customer_sales_customer_internal'  # Default table for regular users


class InternalSale(models.Model):
    #PRODUCT_TYPE_CHOICES = [
    #    ('EPC', 'Electric pressure cooker'),
    #    ('IC', 'Induction cooker'),
    #    ('O', 'Other'),
    #]
    
    #PURCHASE_MODE_CHOICES = [
        #('C', 'Cash'),
        #('DA', 'Deposit Account'),
        #('P', 'PAYGO'),
    #]
    #TYPE_OF_USE_CHOICES = [
        #('Domestic', 'Domestic'),
        #('Business', 'Business'),
        #('Other', 'Other')
    #]
    #PAYMENT_PLAN_CHOICES = [
        #('Wholesale', 'Wholesale 10,600'),
        #('Plan_1', 'Plan 1: Deposit 4,500 with weekly payments of 190 for 40 weeks(12,100)'),
        #('Plan_2', 'Plan 2: Deposit 2,500 with weekly payments of 250 for 48 weeks(14,500)'),
        #('Retail', 'Retail 12,100')
    #]
    
    customer = models.ForeignKey(InternalCustomer, on_delete=models.CASCADE, related_name='sales')
    #registration_date = models.DateField()
    release_date = models.DateField(blank=True, null=True)
    #product_type = models.CharField(max_length=3, choices=PRODUCT_TYPE_CHOICES)
    product_name = models.CharField(max_length=255)
    product_model = models.CharField(max_length=255)
    product_serial_number = models.CharField(max_length=255)
    #purchase_mode = models.CharField(max_length=100)
    #referred_by = models.ForeignKey(InternalCustomer, on_delete=models.SET_NULL, blank=True, null=True,
                                    #related_name='referrals')
    sales_rep = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now_add=True)
    #metered = models.BooleanField(default=False)
    #type_of_use = models.CharField(max_length=10, choices=TYPE_OF_USE_CHOICES, default='Domestic')
    #specific_economic_activity = models.CharField(max_length=255, null=True, blank=True)
    #location_of_use = models.CharField(max_length=255, null=True, blank=True)
    payment_plan = models.CharField(max_length=100) 
    dealer_name = models.CharField(max_length=255)

    #def save(self, *args, **kwargs):
        # Set default payment plan based on purchase mode
        #if not self.payment_plan:
            #if self.purchase_mode == 'C':  # Cash Purchase
                #self.payment_plan = 'Retail'
            #else:  # Other purchase modes
                #self.payment_plan = 'Plan_1'

        #super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product_name} ({self.product_model})"

    class Meta:
        db_table = 'customer_sales_sale_internal'  # Default table for regular users

################################################END OF INTERNAL MODELS################################


###############################################SCODE MODELS###########################################
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
    PAYMENT_PLAN_CHOICES = [
        ('Wholesale', 'Wholesale 10,600'),
        ('Plan_1', 'Plan 1: Deposit 4,500 with weekly payments of 190 for 40 weeks(12,100)'),
        ('Plan_2', 'Plan 2: Deposit 2,500 with weekly payments of 250 for 48 weeks(14,500)'),
        ('Retail', 'Retail 12,100')
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
    payment_plan = models.CharField(max_length=10, choices=PAYMENT_PLAN_CHOICES, blank=True, null=True)  # Allow blank initially

    def save(self, *args, **kwargs):
        # Set default payment plan based on purchase mode
        if not self.payment_plan:
            if self.purchase_mode == 'C':  # Cash Purchase
                self.payment_plan = 'Retail'
            else:  # Other purchase modes
                self.payment_plan = 'Plan_1'

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product_name} ({self.product_model})"

    class Meta:
        db_table = 'customer_sales_sale'  # Default table for regular users

######################################################END OF SCODE MODELS####################################################


########################################################### FOR WELIGHT INSTANCE #############################################
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




########################################################### FOR SAYONA INSTANCE #############################################
class SayonaCustomer(models.Model):
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
        db_table = 'customer_sales_customer_sayona'  # Default table for regular users

class SayonaSale(models.Model):
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
    
    customer = models.ForeignKey(SayonaCustomer, on_delete=models.CASCADE, related_name='sayonasales')
    registration_date = models.DateField()
    release_date = models.DateField(blank=True, null=True)
    product_type = models.CharField(max_length=3, choices=PRODUCT_TYPE_CHOICES)
    product_name = models.CharField(max_length=255)
    product_model = models.CharField(max_length=255)
    product_serial_number = models.CharField(max_length=255)
    purchase_mode = models.CharField(max_length=2, choices=PURCHASE_MODE_CHOICES)
    referred_by = models.ForeignKey(SayonaCustomer, on_delete=models.SET_NULL, blank=True, null=True,
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
        db_table = 'customer_sales_sale_sayona'  # Default table for regular users

########################################################### FOR MEC INSTANCE #############################################
class MecCustomer(models.Model):
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
        db_table = 'customer_sales_customer_mec'  # Default table for regular users

class MecSale(models.Model):
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
    
    customer = models.ForeignKey(MecCustomer, on_delete=models.CASCADE, related_name='testsales')
    registration_date = models.DateField()
    release_date = models.DateField(blank=True, null=True)
    product_type = models.CharField(max_length=3, choices=PRODUCT_TYPE_CHOICES)
    product_name = models.CharField(max_length=255)
    product_model = models.CharField(max_length=255)
    product_serial_number = models.CharField(max_length=255)
    purchase_mode = models.CharField(max_length=2, choices=PURCHASE_MODE_CHOICES)
    referred_by = models.ForeignKey(MecCustomer, on_delete=models.SET_NULL, blank=True, null=True,
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
        db_table = 'customer_sales_sale_mec'  # Default table for regular users

