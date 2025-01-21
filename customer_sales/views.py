from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.core.paginator import Paginator
from .models import Customer, Sale, TestCustomer, TestSale
from .forms import CustomerForm, SaleForm, TestCustomerForm, TestSaleForm
from datetime import timedelta
import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
from django.http import HttpResponse
from datetime import datetime

# Constants
BASE_URL = "https://appliapay.com/"
AUTH = HTTPBasicAuth('admin', '123Give!@#')

PRODUCT_TYPE_MAP = {
    'EPC': 'Electric pressure cooker',
    'IC': 'Induction cooker',
    'O': 'Other',
}

PURCHASE_MODE_MAP = {
    'C': 'Cash',
    'DA': 'Deposit Account',
    'P': 'PAYGO',
}

TYPE_OF_USE_MAP = {
    'Domestic': 'Domestic',
    'Business': 'Business',
    'Other': 'Other',
}



# Existing customer views...
def customers_list(request):
    query = request.GET.get('q')
    user = request.user
    # Choose the model based on user
    CustomerModel = TestCustomer if user.first_name == 'Welight' else Customer
    # Query the appropriate model
    if query:
        customers = CustomerModel.objects.filter(name__icontains=query)
    else:
        customers = CustomerModel.objects.all()

    # Pagination
    paginator = Paginator(customers, 10)
    page = request.GET.get('page')
    customers = paginator.get_page(page)
    
    return render(request, 'customer_sales/customers_list.html', {'customers': customers, 'query': query})


def customer_detail(request, pk): 
    user = request.user
    
    # Choose the correct customer model based on the user
    CustomerModel = TestCustomer if user.first_name == 'Welight' else Customer
    
    # Get the customer
    customer = get_object_or_404(CustomerModel, pk=pk)
    
    # Calculate the registration time
    registration_time = customer.date + timedelta(hours=3)
    
    # Choose the correct sales model based on the user
    SaleModel = TestSale if user.first_name == 'Welight' else Sale
    
    # Pull the sales associated with this customer
    sales = SaleModel.objects.filter(customer=customer)
    
    # Render the customer details and sales
    return render(request, 'customer_sales/customer_detail.html', {
        'customer': customer,
        'sales': sales,
        'registration_time': registration_time
    })


def customer_edit(request, pk):
    user = request.user

    # Choose the model and form based on the user
    if user.first_name == 'Welight':
        CustomerModel = TestCustomer
        CustomerFormClass = TestCustomerForm
    else:
        CustomerModel = Customer
        CustomerFormClass = CustomerForm

    # Retrieve the customer instance based on the selected model
    customer = get_object_or_404(CustomerModel, pk=pk)

    if request.method == 'POST':
        # Use the correct form for the POST request with the customer instance
        form = CustomerFormClass(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            return redirect('customer_detail', pk=customer.pk)
    else:
        # Use the correct form for the GET request to prefill the customer data
        form = CustomerFormClass(instance=customer)

    return render(request, 'customer_sales/customer_edit.html', {'form': form})


def customer_delete(request, pk):
    user = request.user
    # Choose the model based on user
    CustomerModel = TestCustomer if user.first_name == 'Welight' else Customer
    customer = get_object_or_404(CustomerModel, pk=pk)
    if request.method == 'POST':
        customer.delete()
        return redirect('customers_list')
    return render(request, 'customer_sales/customer_delete.html', {'customer': customer})

def add_customer(request):
    user = request.user

    # Check if it's a POST request
    if request.method == 'POST':
        # Use TestCustomerForm if the user is from Welight, otherwise use CustomerForm
        if user.first_name == 'Welight':
            form = TestCustomerForm(request.POST)
        else:
            form = CustomerForm(request.POST)

        # Validate the form and save if valid
        if form.is_valid():
            form.save()
            return redirect('customers_list')
    
    # If it's not a POST request (i.e., it's a GET request), initialize the form
    else:
        # Ensure you use the correct form based on the user's first name
        if user.first_name == 'Welight':
            form = TestCustomerForm()
        else:
            form = CustomerForm()

    # Render the form in the template
    return render(request, 'customer_sales/add_customer.html', {'form': form})


def sale_add(request, customer_id=None):
    user = request.user

    # Choose the correct model and form based on the user
    if user.first_name == 'Welight':
        CustomerModel = TestCustomer
        SaleFormClass = TestSaleForm  # Use TestSaleForm for Welight users
    else:
        CustomerModel = Customer
        SaleFormClass = SaleForm  # Use SaleForm for regular users

    # Get the customer based on the user type
    customer = get_object_or_404(CustomerModel, pk=customer_id) if customer_id else None

    if request.method == 'POST':
        form = SaleFormClass(request.POST)
        if form.is_valid():
            sale = form.save(commit=False)
            if customer:
                sale.customer = customer
            sale.save()
            return redirect('customer_detail', pk=sale.customer.pk if sale.customer else 'sales_list')
    else:
        form = SaleFormClass(current_customer_id=customer_id if customer_id else None)

    return render(request, 'customer_sales/sale_add.html', {'form': form, 'customer': customer})

# New sales views...

def sales_list(request):
    query = request.GET.get('q')
    user = request.user
    # Choose the model based on user
    SaleModel = TestSale if user.first_name == 'Welight' else Sale
    if query:
        sales = SaleModel.objects.filter(product_name__icontains=query)
    else:
        sales = SaleModel.objects.all()
    
    paginator = Paginator(sales, 10)  # Show 10 sales per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'customer_sales/sales_list.html', {'sales': page_obj, 'query': query})

def sale_detail(request, pk):
    user = request.user
    # Choose the model based on user
    SaleModel = TestSale if user.first_name == 'Welight' else Sale
    sale = get_object_or_404(SaleModel, pk=pk)
    return render(request, 'customer_sales/sale_detail.html', {'sale': sale})

def sale_edit(request, pk):
    user = request.user
    # Choose the model based on user
    SaleModel = TestSale if user.first_name == 'Welight' else Sale
    sale = get_object_or_404(SaleModel, pk=pk)

    # Choose the correct form based on user
    SaleFormClass = TestSaleForm if user.first_name == 'Welight' else SaleForm

    if request.method == 'POST':
        form = SaleFormClass(request.POST, instance=sale)
        if form.is_valid():
            form.save()
            if sale.customer:
                return redirect('customer_detail', pk=sale.customer.pk)
            else:
                return redirect('sales_list')
    else:
        form = SaleFormClass(instance=sale)

    return render(request, 'customer_sales/sale_form.html', {'form': form})

def sale_delete(request, pk):
    user = request.user
    # Choose the model based on user
    SaleModel = TestSale if user.first_name == 'Welight' else Sale
    sale = get_object_or_404(SaleModel, pk=pk)
    if request.method == 'POST':
        sale.delete()
        return redirect('sales_list')
    return render(request, 'customer_sales/sale_confirm_delete.html', {'sale': sale})


def fetch_data(endpoint):
    response = requests.get(BASE_URL + endpoint, auth=AUTH)
    response.raise_for_status()
    return response.json()

def fetch_data_index(endpoint, id):
    response = requests.get(BASE_URL + endpoint+"?id="+str(id), auth=AUTH)
    response.raise_for_status()
    return response.json()
#######PAYGO
def paygo_sales(request):
    sort_field = request.GET.get('sort', 'product_serial_number')
    sort_direction = request.GET.get('direction', 'asc')
    query = request.GET.get('q', '')

    # Fetch sales data (assuming it's coming from an external source or model)
    sales_data = fetch_data('paygoScode')

    # Custom sorting function
    def sort_sales(data, sort_field, direction='asc'):
        def sort_key(sale):
            if sort_field == 'product_serial_number':
                # Sort by the last 4 digits of the serial number
                return int(sale['product_serial_number'][-4:])
            elif sort_field == 'payment_status':
                # Define a custom order for payment statuses
                status_order = {
                    'overdue': 0,
                    'on-time': 1,
                    'fully-paid': 2
                }
                return status_order.get(sale['paymentData']['payment_status'], 3)
            elif sort_field in ['totalPaid', 'paygoBalance', 'days', 'balance']:
                # Convert to float or int as necessary
                value = sale['paymentData'].get(sort_field, 0)
                try:
                    return float(value)  # Convert to float for consistency
                except ValueError:
                    return 0
            else:
                return sale.get(sort_field, '')

        reverse = direction == 'desc'
        return sorted(data, key=sort_key, reverse=reverse)


    # Apply custom sorting
    sorted_sales = sort_sales(sales_data, sort_field, sort_direction)

    # Add pagination or any other processing as needed
    paginator = Paginator(sorted_sales, 10)  # Show 10 sales per page
    page_number = request.GET.get('page')
    page_sales = paginator.get_page(page_number)

    context = {
        'sales': page_sales,
        'sort_field': sort_field,
        'sort_direction': sort_direction,
        'query': query,
    }
    return render(request, 'customer_sales/paygo_sales.html', context)

def sale_detail_paygo(request, id):
    sale_data = fetch_data_index('paygoSaleDetail', id)
    sale_data['sale']['release_date'] = datetime.strptime(sale_data['sale']['release_date'], "%Y-%m-%dT%H:%M:%S.%fZ")
    sale_data['sale']['registration_date'] = datetime.strptime(sale_data['sale']['registration_date'], "%Y-%m-%dT%H:%M:%S.%fZ")
    # Convert transtime and apply mappings
    for transaction in sale_data['sale']['transactions']:
        transaction['transtime'] = datetime.strptime(str(transaction['transtime']), "%Y%m%d%H%M%S")
        
    sale_data['sale']['transactions'].sort(key=lambda x: x['transtime'], reverse=True)
    # Map product type, purchase mode, and type of use to readable values
    sale_data['sale']['product_type'] = PRODUCT_TYPE_MAP.get(sale_data['sale']['product_type'], 'Unknown')
    sale_data['sale']['purchase_mode'] = PURCHASE_MODE_MAP.get(sale_data['sale']['purchase_mode'], 'Unknown')
    sale_data['sale']['type_of_use'] = TYPE_OF_USE_MAP.get(sale_data['sale']['type_of_use'], 'Unknown')

    return render(request, 'customer_sales/sale_detail_paygo.html', {
        'sale': sale_data['sale'],
        'paymentStatus': sale_data['paymentStatus'],
    })


def paygo_sales_non_metered(request):
    sort_field = request.GET.get('sort', 'product_serial_number')
    sort_direction = request.GET.get('direction', 'asc')
    query = request.GET.get('q', '')

    # Fetch sales data (assuming it's coming from an external source or model)
    sales_data = fetch_data('paygoScodeNonMetered')

    # Custom sorting function
    def sort_sales(data, sort_field, direction='asc'):
        def sort_key(sale):
            if sort_field == 'product_serial_number':
                # Sort by the last 4 digits of the serial number
                return int(sale['product_serial_number'][-4:])
            elif sort_field == 'payment_status':
                # Define a custom order for payment statuses
                status_order = {
                    'overdue': 0,
                    'on-time': 1,
                    'fully-paid': 2
                }
                return status_order.get(sale['paymentData']['payment_status'], 3)
            elif sort_field in ['totalPaid', 'paygoBalance', 'days', 'balance']:
                # Convert to float or int as necessary
                value = sale['paymentData'].get(sort_field, 0)
                try:
                    return float(value)  # Convert to float for consistency
                except ValueError:
                    return 0
            else:
                return sale.get(sort_field, '')

        reverse = direction == 'desc'
        return sorted(data, key=sort_key, reverse=reverse)


    # Apply custom sorting
    sorted_sales = sort_sales(sales_data, sort_field, sort_direction)

    # Add pagination or any other processing as needed
    paginator = Paginator(sorted_sales, 10)  # Show 10 sales per page
    page_number = request.GET.get('page')
    page_sales = paginator.get_page(page_number)

    context = {
        'sales': page_sales,
        'sort_field': sort_field,
        'sort_direction': sort_direction,
        'query': query,
    }
    return render(request, 'customer_sales/paygo_sales_non_metered.html', context)

###############################DOWNLOAD CUSTOMER DATA#######################################################
def export_customer_data(request):
    user = request.user
    # Choose the model based on user
    CustomerModel = TestCustomer if user.first_name == 'Welight' else Customer
    customers = CustomerModel.objects.all().values()
    df = pd.DataFrame(customers)
    # Convert any datetime columns to timezone-unaware
    for column in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[column]):
            df[column] = df[column].dt.tz_convert(None)  # Remove timezone information
    # Create the filename
    fileName = "customer_data.xlsx"
    
    # Create a HttpResponse with content_type as ms-excel
    response = HttpResponse(content_type='application/vnd.ms-excel')
    
    # Specify the file name using f-string
    response['Content-Disposition'] = f'attachment; filename="{fileName}"'
    
    # Use pandas to save the dataframe as an excel file in the response
    df.to_excel(response, index=False, engine='openpyxl')

    return response

###############################DOWNLOAD SALES DATA#######################################################
def export_sales_data(request):
    user = request.user
    # Choose the model based on user
    SaleModel = TestSale if user.first_name == 'Welight' else Sale
    sales = SaleModel.objects.all().values()
    df = pd.DataFrame(sales)
    # Convert any datetime columns to timezone-unaware
    for column in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[column]):
            df[column] = df[column].dt.tz_convert(None)  # Remove timezone information
    # Create the filename
    fileName = "sales_data.xlsx"
    
    # Create a HttpResponse with content_type as ms-excel
    response = HttpResponse(content_type='application/vnd.ms-excel')
    
    # Specify the file name using f-string
    response['Content-Disposition'] = f'attachment; filename="{fileName}"'
    
    # Use pandas to save the dataframe as an excel file in the response
    df.to_excel(response, index=False, engine='openpyxl')

    return response

###############################DOWNLOAD PAYGO DATA(METERED)###############################################################
def export_paygo_data(request):
    data = fetch_data('paygoScode')
    for obj in data:
        # Extract relevant fields from paymentData
        payment_data = obj.pop("paymentData", {})
        obj["balance"] = payment_data.get("balance", 0)
        obj["paygo_balance"] = payment_data.get("paygoBalance", 0)
        obj["payment_status"] = payment_data.get("payment_status", "unknown")
        obj["days_past/to_payment_date"] = payment_data.get("days", 0)  # Days past/to payment day
        obj["amount_paid"] = payment_data.get("totalPaid", 0)  # Rename amount to amount paid
        obj.pop("date", None)
        obj.pop("amount", None)
    df = pd.DataFrame(data)
    # Create the filename
    fileName = "paygo_data.xlsx"
    
    # Create a HttpResponse with content_type as ms-excel
    response = HttpResponse(content_type='application/vnd.ms-excel')
    
    # Specify the file name using f-string
    response['Content-Disposition'] = f'attachment; filename="{fileName}"'
    
    # Use pandas to save the dataframe as an excel file in the response
    df.to_excel(response, index=False, engine='openpyxl')

    return response

####################################DOWNLOAD PAYGO DATA(NON=METERED)##########################################################
def export_paygoNonmetered_data(request):
    data = fetch_data('paygoScodeNonMetered')
    for obj in data:
        # Extract relevant fields from paymentData
        payment_data = obj.pop("paymentData", {})
        obj["balance"] = payment_data.get("balance", 0)
        obj["paygo_balance"] = payment_data.get("paygoBalance", 0)
        obj["payment_status"] = payment_data.get("payment_status", "unknown")
        obj["days_past/to_payment_date"] = payment_data.get("days", 0)  # Days past/to payment day
        obj["amount_paid"] = payment_data.get("totalPaid", 0)  # Rename amount to amount paid
        obj.pop("date", None)
        obj.pop("amount", None)
    df = pd.DataFrame(data)
    # Create the filename
    fileName = "paygoNonmetered_data.xlsx"
    
    # Create a HttpResponse with content_type as ms-excel
    response = HttpResponse(content_type='application/vnd.ms-excel')
    
    # Specify the file name using f-string
    response['Content-Disposition'] = f'attachment; filename="{fileName}"'
    
    # Use pandas to save the dataframe as an excel file in the response
    df.to_excel(response, index=False, engine='openpyxl')

    return response