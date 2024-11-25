# forms.py
from django import forms
from .models import Customer, Sale, TestCustomer, TestSale

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'id_number', 'phone_number', 'alternate_phone_number', 'email', 'country','county', 'sub_county', 'location', 'gender', 'household_type', 'household_size', 'preferred_language']

class TestCustomerForm(forms.ModelForm):
    class Meta:
        model = TestCustomer
        fields = ['name', 'id_number', 'phone_number', 'alternate_phone_number', 'email', 'country','county', 'sub_county', 'location', 'gender', 'household_type', 'household_size', 'preferred_language']


class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = '__all__'  # You can specify fields explicitly if needed
        widgets = {
            'registration_date': forms.DateInput(format='%d %b %Y', attrs={'class': 'datepicker'}),
            'release_date': forms.DateInput(format='%d %b %Y', attrs={'class': 'datepicker'}),
            # Add widgets for other date fields as needed
        }
    
    def __init__(self, *args, **kwargs):
        current_customer_id = kwargs.pop('current_customer_id', None)
        super().__init__(*args, **kwargs)
        
        if current_customer_id:
            # Exclude the current customer from referral choices
            self.fields['referred_by'].queryset = Customer.objects.exclude(id=current_customer_id)
            
class TestSaleForm(forms.ModelForm):
    class Meta:
        model = TestSale
        fields = '__all__'  # You can specify fields explicitly if needed
        widgets = {
            'registration_date': forms.DateInput(format='%d %b %Y', attrs={'class': 'datepicker'}),
            'release_date': forms.DateInput(format='%d %b %Y', attrs={'class': 'datepicker'}),
            # Add widgets for other date fields as needed
        }
    
    def __init__(self, *args, **kwargs):
        current_customer_id = kwargs.pop('current_customer_id', None)
        super().__init__(*args, **kwargs)
        
        if current_customer_id:
            # Exclude the current customer from referral choices
            self.fields['referred_by'].queryset = TestCustomer.objects.exclude(id=current_customer_id)