from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.core.paginator import Paginator
from .models import Customer, Sale, TestCustomer, TestSale, SayonaCustomer, SayonaSale, MecCustomer, MecSale, Warehouse, InventoryItem, InventoryMovement
from .forms import CustomerForm, SaleForm, TestCustomerForm, TestSaleForm, SayonaCustomerForm, SayonaSaleForm, MecCustomerForm, MecSaleForm, WarehouseForm, InventoryItemForm, MoveInventoryForm, BulkMoveForm
import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
from django.http import HttpResponse
from datetime import datetime, timedelta
from collections import Counter
from powerpay.notifications import send_notification
from django.db.models import Q, Count
from django.utils.timezone import make_aware, is_naive, datetime

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


###Inventory function###################
def warehouse_list(request):
    query = request.GET.get('q')
    
    if query:
        warehouses = Warehouse.objects.filter(name__icontains=query)
    else:
        warehouses = Warehouse.objects.all()

    # Annotate each warehouse with item count
    warehouses = warehouses.annotate(item_count=Count('inventory_items'))

    paginator = Paginator(warehouses, 10)
    page = request.GET.get('page')
    warehouses = paginator.get_page(page)

    return render(request, 'customer_sales/warehouse_list.html', {
        'warehouses': warehouses,
        'query': query,
    })

def add_warehouse(request):
    user = request.user
    if request.method == 'POST':
        form = WarehouseForm(request.POST)
        # Validate the form and save if valid
        if form.is_valid():
            warehouse = form.save()  # Save and get the new customer instance
            send_notification(user, "Warehouse Added", f"{warehouse.name} added")  # Send notification
            return redirect('warehouse_list')
    else:
        form = WarehouseForm()
        return render(request, 'customer_sales/add_warehouse.html', {'form': form})
    
def warehouse_edit(request, pk):
    user = request.user

    # Retrieve the customer instance based on the selected model
    warehouse = get_object_or_404(Warehouse, pk=pk)

    if request.method == 'POST':
        # Use the correct form for the POST request with the warehouse instance
        form = WarehouseForm(request.POST, instance=warehouse)
        if form.is_valid():
            form.save()
            send_notification(user, "Warehouse Edited", f"{warehouse.name} warehouse details changed")
            return redirect('warehouse_detail', pk=warehouse.pk)
    else:
        # Use the correct form for the GET request to prefill the customer data
        form = WarehouseForm(instance=warehouse)

    return render(request, 'customer_sales/warehouse_edit.html', {'form': form})


def warehouse_detail(request, pk):
    #user = request.user
    warehouse = get_object_or_404(Warehouse, pk=pk)
    items = InventoryItem.objects.filter(current_warehouse=warehouse)
    unique_products = items.values('product_type').distinct().count()
    item_count = items.count()
    paginator = Paginator(items, 10)
    page = request.GET.get('page')
    items = paginator.get_page(page)
    context = {
        'warehouse': warehouse,
        'items': items,
        'item_count': item_count,
        'unique_products': unique_products
    }

    return render(request, 'customer_sales/warehouse_detail.html', context)  

def warehouse_delete(request, pk):
    user = request.user
    warehouse = get_object_or_404(Warehouse, pk=pk)
    if request.method == 'POST':
        warehouse.delete()
        send_notification(user, "Warehouse Deleted", f"{warehouse.name} warehouse deleted")
        return redirect('warehouse_list')
    return render(request, 'customer_sales/warehouse_delete.html', {'warehouse': warehouse})

#############ITEMS#########################
def item_list(request):
    query = request.GET.get('q')
    if query:
        items = InventoryItem.objects.filter(
            Q(name__icontains=query) | Q(serial_number__icontains=query)
        )
    else:    
        items = InventoryItem.objects.all()

    unique_products = items.values('product_type').distinct().count()
    item_count = items.count()
    paginator = Paginator(items, 10)
    page = request.GET.get('page')
    items = paginator.get_page(page)

    context = {
        'items': items,
        'query': query,
        'item_count': item_count,
        'distinct_item_count': unique_products
    }

    return render(request, 'customer_sales/item_list.html', context)

def add_item(request):
    user = request.user
    if request.method == 'POST':
        form = InventoryItemForm(request.POST)
        if form.is_valid():
            item = form.save()  # Save the item
            # Create initial movement record
            InventoryMovement.objects.create(
                item=item,
                to_warehouse=item.current_warehouse,
                moved_by=user,
                note="Initial entry"
            )
            send_notification(user, "Item Added", f"{item.name} added")  # Send notification
            return redirect('item_list')
    else:
        form = InventoryItemForm()  # Instantiate form for GET request

    return render(request, 'customer_sales/add_item.html', {'form': form})

def item_edit(request, pk):
    user = request.user
    item = get_object_or_404(InventoryItem, pk=pk)
    old_warehouse = item.current_warehouse
    if request.method == 'POST':
        form = InventoryItemForm(request.POST, instance=item)
        if form.is_valid():
            updated_item = form.save(commit=False)  # Don't save to DB yet
            if updated_item.current_warehouse != old_warehouse:
                # Warehouse changed – log the movement
                InventoryMovement.objects.create(
                    item=item,
                    from_warehouse=old_warehouse,
                    to_warehouse=updated_item.current_warehouse,
                    moved_by=user,
                )
                send_notification(user, "Item Moved", f"{item.name} moved from {old_warehouse} to {updated_item.current_warehouse}")

            updated_item.save()  # Save updated item after checking movement
            send_notification(user, "Item Edited", f"{item.name} item details changed")

            return redirect('item_detail', pk=item.pk)
    else:
        form = InventoryItemForm(instance=item)

    return render(request, 'customer_sales/item_edit.html', {'form': form})


def item_detail(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    item_movements = InventoryMovement.objects.filter(item=item).order_by('date_moved')  # oldest first

    movement_list = []

    # Convert date_added (a date object) to a timezone-aware datetime
    previous_date = datetime.combine(item.date_added, datetime.min.time())
    if is_naive(previous_date):
        previous_date = make_aware(previous_date)

    for move in item_movements:
        duration = move.date_moved - previous_date
        move.duration_at_previous_warehouse = duration
        previous_date = move.date_moved
        movement_list.append(move)

    context = {
        'item': item,
        'item_movements': movement_list[::-1],  # newest first
    }
    return render(request, 'customer_sales/item_detail.html', context)  

def item_delete(request, pk):
    user = request.user
    item = get_object_or_404(InventoryItem, pk=pk)
    if request.method == 'POST':
        item.delete()
        send_notification(user, "Item Deleted", f"{item.name} item deleted")
        return redirect('item_list')
    return render(request, 'customer_sales/item_delete.html', {'item': item})


def move_inventory_item(request, item_id):
    item = get_object_or_404(InventoryItem, id=item_id)
    user = request.user
    if request.method == 'POST':
        form = MoveInventoryForm(request.POST, current_warehouse=item.current_warehouse)
        if form.is_valid():
            new_warehouse = form.cleaned_data['new_warehouse']
            note = form.cleaned_data['note']
            from_wh = item.current_warehouse
            InventoryMovement.objects.create(
                item=item,
                from_warehouse=item.current_warehouse,
                to_warehouse=new_warehouse,
                moved_by=request.user,
                note=note,
            )

            item.current_warehouse = new_warehouse
            item.save()
            send_notification(user, "Item Moved", f"{item.name}({item.serial_number}) has been moved from {from_wh} warehouse to {new_warehouse} warehouse")
            return redirect('item_detail', pk=item.id)
    else:
        form = MoveInventoryForm(current_warehouse=item.current_warehouse)

    return render(request, 'customer_sales/move_item.html', {
        'form': form,
        'item': item,
    })

def bulk_move_items(request):
    user = request.user

    if request.method == 'POST':
        form = BulkMoveForm(request.POST)
        if form.is_valid():
            items = form.cleaned_data['items']
            new_warehouse = form.cleaned_data['new_warehouse']
            note = form.cleaned_data['note']
            for item in items:
                from_wh = item.current_warehouse
                if item.current_warehouse != new_warehouse:
                    InventoryMovement.objects.create(
                        item=item,
                        from_warehouse=item.current_warehouse,
                        to_warehouse=new_warehouse,
                        moved_by=user,
                        note=note,
                    )
                    item.current_warehouse = new_warehouse
                    item.save()
                    send_notification(user, "Item Moved", f"{item.name}({item.serial_number}) has been moved from {from_wh} warehouse to {new_warehouse} warehouse")
            return redirect('item_list')  # or wherever you want
    else:
        form = BulkMoveForm()

    return render(request, 'customer_sales/bulk_move.html', {'form': form})
 

# Existing customer views...
def customers_list(request):
    query = request.GET.get('q')
    user = request.user
    # Choose the model based on user
    if user.first_name == 'Welight':
        CustomerModel = TestCustomer
    elif user.first_name == 'Mec':
        CustomerModel = MecCustomer
    elif user.first_name in ['Sayona', 'Sayona-Guest']:
        CustomerModel = SayonaCustomer
    else:
        CustomerModel = Customer
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
    if user.first_name == 'Welight':
        CustomerModel = TestCustomer
    elif user.first_name == 'Mec':
        CustomerModel = MecCustomer
    elif user.first_name in ['Sayona', 'Sayona-Guest']:
        CustomerModel = SayonaCustomer
    else:
        CustomerModel = Customer
    
    # Get the customer
    customer = get_object_or_404(CustomerModel, pk=pk)
    
    # Calculate the registration time
    registration_time = customer.date + timedelta(hours=3)
    
    # Choose the correct sales model based on the user
    # Choose the model based on user
    if user.first_name == 'Welight':
        SaleModel = TestSale
    elif user.first_name == 'Mec':
        SaleModel = MecSale
    elif user.first_name in ['Sayona', 'Sayona-Guest']:
        SaleModel = SayonaSale
    else:
        SaleModel = Sale
    
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
    elif user.first_name == 'Mec':
        CustomerModel = MecCustomer
        CustomerFormClass = MecSaleForm
    elif user.first_name in ['Sayona', 'Sayona-Guest']:
        CustomerModel = SayonaCustomer
        CustomerFormClass = SayonaCustomerForm
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
            send_notification(user, "Customer Edited", f"{customer.name} details changed")
            return redirect('customer_detail', pk=customer.pk)
    else:
        # Use the correct form for the GET request to prefill the customer data
        form = CustomerFormClass(instance=customer)

    return render(request, 'customer_sales/customer_edit.html', {'form': form})


def customer_delete(request, pk):
    user = request.user
    # Choose the model based on user
    if user.first_name == 'Welight':
        CustomerModel = TestCustomer
    elif user.first_name == 'Mec':
        CustomerModel = MecCustomer
    elif user.first_name in ['Sayona', 'Sayona-Guest']:
        CustomerModel = SayonaCustomer
    else:
        CustomerModel = Customer
    customer = get_object_or_404(CustomerModel, pk=pk)
    if request.method == 'POST':
        customer.delete()
        send_notification(user, "Customer Deleted", f"{customer.name} deleted")
        return redirect('customers_list')
    return render(request, 'customer_sales/customer_delete.html', {'customer': customer})

def add_customer(request):
    user = request.user

    # Check if it's a POST request
    if request.method == 'POST':
        # Use TestCustomerForm if the user is from Welight, otherwise use CustomerForm
        if user.first_name == 'Welight':
            form = TestCustomerForm(request.POST)
        elif user.first_name == 'Mec':
            form = MecCustomerForm(request.POST)
        elif user.first_name in ['Sayona', 'Sayona-Guest']:
            form = SayonaCustomerForm(request.POST)  # Fixed the typo
        else:
            form = CustomerForm(request.POST)

        # Validate the form and save if valid
        if form.is_valid():
            customer = form.save()  # Save and get the new customer instance
            send_notification(user, "Customer Added", f"{customer.name} added")  # Send notification
            return redirect('customers_list')
    
    # If it's not a POST request (i.e., it's a GET request), initialize the form
    else:
        # Ensure you use the correct form based on the user's first name
        if user.first_name == 'Welight':
            form = TestCustomerForm()
        elif user.first_name == 'Mec':
            form = MecCustomerForm()
        elif user.first_name in ['Sayona', 'Sayona-Guest']:
            form = SayonaCustomerForm()
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
    elif user.first_name == 'Mec':
        CustomerModel = MecCustomer
        SaleFormClass = MecSaleForm
    elif user.first_name in ['Sayona', 'Sayona-Guest']:
        CustomerModel = SayonaCustomer
        SaleFormClass = SayonaSaleForm
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
            send_notification(user, "Sale Added", f"{sale.product_serial_number} has been sold")
            return redirect('customer_detail', pk=sale.customer.pk if sale.customer else 'sales_list')
    else:
        form = SaleFormClass(current_customer_id=customer_id if customer_id else None)

    return render(request, 'customer_sales/sale_add.html', {'form': form, 'customer': customer})

# New sales views...

def sales_list(request):
    query = request.GET.get('q')
    user = request.user
    # Choose the model based on user
    if user.first_name == 'Welight':
        SaleModel = TestSale
    elif user.first_name == 'Mec':
        SaleModel = MecSale
    elif user.first_name in ['Sayona', 'Sayona-Guest']:
        SaleModel = SayonaSale
    else:
        SaleModel = Sale
    if query:
        sales = SaleModel.objects.filter(product_serial_number__icontains=query)
    else:
        sales = SaleModel.objects.all()
    
    paginator = Paginator(sales, 10)  # Show 10 sales per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'customer_sales/sales_list.html', {'sales': page_obj, 'query': query})

def sale_detail(request, pk):
    user = request.user
    # Choose the model based on user
    # Choose the model based on user
    if user.first_name == 'Welight':
        SaleModel = TestSale
    elif user.first_name == 'Mec':
        SaleModel = MecSale
    elif user.first_name in ['Sayona', 'Sayona-Guest']:
        SaleModel = SayonaSale
    else:
        SaleModel = Sale
    sale = get_object_or_404(SaleModel, pk=pk)
    return render(request, 'customer_sales/sale_detail.html', {'sale': sale})

def sale_edit(request, pk):
    user = request.user
    # Choose the model based on user
    if user.first_name == 'Welight':
        SaleModel = TestSale
    elif user.first_name == 'Mec':
        SaleModel = MecSale
    elif user.first_name in ['Sayona', 'Sayona-Guest']:
        SaleModel = SayonaSale
    else:
        SaleModel = Sale
    sale = get_object_or_404(SaleModel, pk=pk)

    # Choose the correct form based on user
    if user.first_name == 'Welight':
        SaleFormClass = TestSaleForm
    elif user.first_name == 'Mec':
        SaleFormClass = MecSaleForm
    elif user.first_name in ['Sayona', 'Sayona-Guest']:
        SaleFormClass = SayonaSaleForm
    else:
        SaleFormClass = SaleForm

    if request.method == 'POST':
        form = SaleFormClass(request.POST, instance=sale)
        if form.is_valid():
            form.save()
            send_notification(user, "Sale Edited", f"{sale.product_serial_number} sale has been edited")
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
    if user.first_name == 'Welight':
        SaleModel = TestSale
    elif user.first_name == 'Mec':
        SaleModel = MecSale
    elif user.first_name in ['Sayona', 'Sayona-Guest']:
        SaleModel = SayonaSale
    else:
        SaleModel = Sale
    sale = get_object_or_404(SaleModel, pk=pk)
    if request.method == 'POST':
        sale.delete()
        send_notification(user, "Sale Deleted", f"{sale.product_serial_number} sale has been deleted")
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
    total_sales = len(sales_data)
    # Count the number of sales by payment status
    status_counts = Counter(sale['paymentData'].get('payment_status', 'unknown') for sale in sales_data)

    if query:
        sales_data = [
            sale for sale in sales_data
            if query in sale['product_serial_number'].lower()
        ]

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
        'fully_paid_count': status_counts.get('fully-paid', 0),
        'on_time_count': status_counts.get('on-time', 0),
        'overdue_count': status_counts.get('overdue', 0),
        'total_count': total_sales
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
    total_sales = len(sales_data)
    # Count the number of sales by payment status
    status_counts = Counter(sale['paymentData'].get('payment_status', 'unknown') for sale in sales_data)
    if query:
        sales_data = [
            sale for sale in sales_data
            if query in sale['product_serial_number'].lower()
        ]

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
        'fully_paid_count': status_counts.get('fully-paid', 0),
        'on_time_count': status_counts.get('on-time', 0),
        'overdue_count': status_counts.get('overdue', 0),
        'total_count': total_sales
    }
    return render(request, 'customer_sales/paygo_sales_non_metered.html', context)
###############################DOWNLOAD INVENTORY DATA#####################################################
def export_warehouse_items(request, pk):
    warehouse = get_object_or_404(Warehouse, pk=pk)
    items = InventoryItem.objects.filter(current_warehouse=warehouse)

    # Serialize data into a list of dictionaries
    data = []
    for item in items:
        data.append({
            'Name': item.name,
            'Serial Number': item.serial_number,
            'Product Type': item.product_type,
            'Date Added': item.date_added,
            'Current Warehouse': item.current_warehouse.name,
            'Days in Current Warehouse': item.days_in_current_warehouse,
        })

    # Create a DataFrame from the data
    df = pd.DataFrame(data)

    fileName = f"{warehouse.name}_warehouse_data.xlsx"
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = f'attachment; filename="{fileName}"'
    df.to_excel(response, index=False, engine='openpyxl')

    return response

def export_items(request):
    items = InventoryItem.objects.all()

    # Serialize data into a list of dictionaries
    data = []
    for item in items:
        data.append({
            'Name': item.name,
            'Serial Number': item.serial_number,
            'Product Type': item.product_type,
            'Date Added': item.date_added,
            'Current Warehouse': item.current_warehouse.name,
            'Days in Current Warehouse': item.days_in_current_warehouse,
        })

    # Create a DataFrame from the data
    df = pd.DataFrame(data)

    fileName = f"inventory_list.xlsx"
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = f'attachment; filename="{fileName}"'
    df.to_excel(response, index=False, engine='openpyxl')

    return response


###############################DOWNLOAD CUSTOMER DATA#######################################################
def export_customer_data(request):
    user = request.user
    # Choose the model based on user
    if user.first_name == 'Welight':
        CustomerModel = TestCustomer
    elif user.first_name == 'Mec':
        CustomerModel = MecCustomer
    elif user.first_name in ['Sayona', 'Sayona-Guest']:
        CustomerModel = SayonaCustomer
    else:
        CustomerModel = Customer
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
    if user.first_name == 'Welight':
        SaleModel = TestSale
    elif user.first_name == 'Mec':
        SaleModel = MecSale
    elif user.first_name in ['Sayona', 'Sayona-Guest']:
        SaleModel = SayonaSale
    else:
        SaleModel = Sale
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