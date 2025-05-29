# forms.py
from django import forms
from .models import InternalCustomer, InternalSale, Customer, Sale, TestCustomer, TestSale, SayonaCustomer, SayonaSale, userProfile, MecCustomer, MecSale, Warehouse, InventoryItem


class userProfileForm(forms.ModelForm):
    class Meta:
        model = userProfile
        fields = ['org_name', 'org_address', 'org_phone_number', 'org_email']

class WarehouseForm(forms.ModelForm):
    class Meta:
        model = Warehouse
        fields = '__all__'

class InventoryItemForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = '__all__'

class MoveInventoryForm(forms.Form):
    new_warehouse = forms.ModelChoiceField(queryset=Warehouse.objects.all(), label="Move to Warehouse")
    note = forms.CharField(required=False, widget=forms.Textarea, label="Note")

    def __init__(self, *args, **kwargs):
        self.current_warehouse = kwargs.pop('current_warehouse', None)
        super(MoveInventoryForm, self).__init__(*args, **kwargs)

    def clean_new_warehouse(self):
        new_warehouse = self.cleaned_data['new_warehouse']
        if new_warehouse == self.current_warehouse:
            raise forms.ValidationError("New warehouse must be different from the current warehouse.")
        return new_warehouse

class InternalCustomerForm(forms.ModelForm):
    class Meta:
        model = InternalCustomer
        fields = ['name', 'id_number', 'phone_number', 'email', 'county', 'sub_county', 'location', 'gender', 'household_size']

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'id_number', 'phone_number', 'alternate_phone_number', 'email', 'country','county', 'sub_county', 'location', 'gender', 'household_type', 'household_size', 'preferred_language']

class TestCustomerForm(forms.ModelForm):
    class Meta:
        model = TestCustomer
        fields = ['name', 'id_number', 'phone_number', 'alternate_phone_number', 'email', 'country','county', 'sub_county', 'location', 'gender', 'household_type', 'household_size', 'preferred_language']

class SayonaCustomerForm(forms.ModelForm):
    class Meta:
        model = SayonaCustomer
        fields = ['name', 'id_number', 'phone_number', 'alternate_phone_number', 'email', 'country','county', 'sub_county', 'location', 'gender', 'household_type', 'household_size', 'preferred_language']

class MecCustomerForm(forms.ModelForm):
    class Meta:
        model = MecCustomer
        fields = ['name', 'id_number', 'phone_number', 'alternate_phone_number', 'email', 'country','county', 'sub_county', 'location', 'gender', 'household_type', 'household_size', 'preferred_language']


class InternalSaleForm(forms.ModelForm):
    class Meta:
        model = InternalSale
        fields = '__all__'  # You can specify fields explicitly if needed
        widgets = {
            #'registration_date': forms.DateInput(format='%d %b %Y', attrs={'class': 'datepicker'}),
            'release_date': forms.DateInput(format='%d %b %Y', attrs={'class': 'datepicker'}),
            # Add widgets for other date fields as needed
        }
    
    #def __init__(self, *args, **kwargs):
        #current_customer_id = kwargs.pop('current_customer_id', None)
        #super().__init__(*args, **kwargs)
        
        #if current_customer_id:
            # Exclude the current customer from referral choices
            #self.fields['referred_by'].queryset = Customer.objects.exclude(id=current_customer_id)
 

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

class SayonaSaleForm(forms.ModelForm):
    class Meta:
        model = SayonaSale
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
            self.fields['referred_by'].queryset = SayonaCustomer.objects.exclude(id=current_customer_id)

class MecSaleForm(forms.ModelForm):
    class Meta:
        model = MecSale
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
            self.fields['referred_by'].queryset = MecCustomer.objects.exclude(id=current_customer_id)