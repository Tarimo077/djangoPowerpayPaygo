from django.shortcuts import render, redirect
import requests
from requests.auth import HTTPBasicAuth
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import plotly.io as pio
from django.core.paginator import Paginator
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import HttpResponse
from customer_sales.models import Customer, Sale, TestCustomer, TestSale, userProfile, SayonaCustomer, SayonaSale, MecCustomer, MecSale
from django.utils.timezone import now
from calendar import monthrange
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from . import notifications

# Constants
BASE_URL = "https://appliapay.com/"
AUTH = HTTPBasicAuth('admin', '123Give!@#')
# At the top of your views.py file
payment_status = {
    "status": "pending",
    "message": "",
    "amount": None,
    "receipt_number": None,
    "transaction_date": None,
    "phone_number": None
}


def fetch_data(endpoint):
    response = requests.get(BASE_URL + endpoint, auth=AUTH)
    response.raise_for_status()
    return response.json()

def fetch_data_index(endpoint, range):
    response = requests.get(BASE_URL + endpoint+"?range="+str(range), auth=AUTH)
    response.raise_for_status()
    return response.json()


def fetch_data_devs(endpoint, devs, range):
    """Fetch data from the API."""
    response = requests.get(f"{BASE_URL}{endpoint}?range={range}&devs={devs}", auth=AUTH)
    response.raise_for_status()
    return response.json()

def fetch_data_accounts(endpoint, acc):
    response = requests.get(BASE_URL + endpoint+"?account="+str(acc), auth=AUTH)
    response.raise_for_status()
    return response.json()

@login_required
def terms_of_service(request):
    return render(request, 'terms_of_service.html')

@login_required
@login_required
def profile_view(request):
    return render(request, 'profile.html')

@login_required
def edit_profile(request):
    profile, created = userProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        profile.org_name = request.POST.get("org_name", "")
        profile.org_address = request.POST.get("org_address", "")
        profile.org_phone_number = request.POST.get("org_phone_number", "")
        profile.org_email = request.POST.get("org_email", "")
        profile.save()
        return redirect("profile")  # Redirect back to profile page

    return render(request, "my_profile.html", {"profile": profile})

def login_page(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            user_profile, created = userProfile.objects.get_or_create(user=user)

            # If T&C not accepted, show popup (but don't log in yet)
            if not user_profile.tnc_flag:
                return render(request, 'partials/tnc_popup.html', {'username': username, 'p': password})

            # Log in and redirect
            login(request, user)
            if user.username in ['Kimiti', 'Tarimo', 'powerpayadmin1']:
                return redirect('summary')
            return redirect('landing_page')
        
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'login.html')


def accept_tnc(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)  # Parse JSON body
            username = data.get('username')
            password = data.get('p')

            user = authenticate(username=username, password=password)
            if user:
                user_profile, created = userProfile.objects.get_or_create(user=user)
                user_profile.tnc_flag = True
                user_profile.save()

                login(request, user)
                return JsonResponse({'success': True, 'redirect_url': '/'})  # Redirect to home_page

            return JsonResponse({'error': 'User not found'}, status=404)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def live_page(request, deviceID):
    usr = request.user.username
    if usr == 'John-Maina':
        dat = fetch_data("commandScode")
    elif usr =='Mec':
        dat = fetch_data("commandMec")
    elif usr == 'Welight':
        dat = fetch_data("commandWelight")
    elif usr in ['Sayona', 'Sayona-Guest']:
        dat = fetch_data("commandSayona")
    elif usr == 'GIZ':
        dat = fetch_data("commandGIZ")
    else:
        dat = fetch_data("command")
    for z in dat:
        if z["deviceID"] == deviceID:
            status = z["active"]
    return render(request, 'live.html', {'deviceID': deviceID, 'active': status})

def logout_page(request):
    logout(request)
    return redirect('login')

def get_user_cache_key(user, range_value):
    """Generate a cache key based on username and range."""
    return f"homepage_data_{user.username}_{range_value}"

def get_user_cache_key_landing_page(user):
    return f"landingpage_data_{user}"

def get_cache_key_chart_data(user, df_type):
    """Generate a cache key based on username and range."""
    return f"chart_{user}_{df_type}"

def fetch_chart_data(usr):
        endpoint_mapping = {
            'John-Maina': "allDeviceDataScodeDjango",
            'Welight': "allDeviceDataWelightDjango",
            'GIZ': "allDeviceDataGIZDjango",
            'Sayona': "allDeviceDataSayonaDjango",
            'Sayona-Guest': "allDeviceDataSayonaDjango",
            'Mec': "allDeviceDataMecDjango"
        }
        endpoint = endpoint_mapping.get(usr, "allDeviceDataDjango")

        try:
            data = fetch_data_index(endpoint, 9999999)
        except Exception as e:
            #messages.error(request, f"Error fetching data: {e}")
            return None

        if not data or (data.get('totalkwh') == 0 and data.get('runtime') == 0 and not data.get('rawData')):
            return None

        return pd.DataFrame(data['rawData'])

def plot_line(df, x_col, y_col, y_label, chart_title, unit=""):
    df = df.copy()                                 # keep caller untouched
    df["week_end"] = df[x_col] + timedelta(days=6)

    fig = go.Figure()
    if y_label == 'kwh':
        fig.add_trace(
            go.Scatter(
                x=df[x_col],
                y=df[y_col],
                mode="lines",
                fill="tozeroy",
                line=dict(color="#0ead00"),
                fillcolor="#d0ffcc",
                line_shape="spline",
                customdata=df[["week_end", x_col]],
                hovertemplate=(
                    "Period: From %{customdata[1]|%Y-%m-%d}"
                    " to %{customdata[0]|%Y-%m-%d}<br>"
                    f"{y_label}: %{{y:.2f}} {unit}<extra></extra>"
                ),
            )
        )
    else:
        fig.add_trace(
            go.Scatter(
                x=df[x_col],
                y=df[y_col],
                mode="lines",
                fill="tozeroy",
                line=dict(color="#0ead00"),
                fillcolor="#d0ffcc",
                line_shape="spline",
                customdata=df[["week_end", x_col]],
                hovertemplate=(
                    "Period: From %{customdata[1]|%Y-%m-%d}"
                    " to %{customdata[0]|%Y-%m-%d}<br>"
                    f"{y_label}: %{{y:.0f}} {unit}<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        title=chart_title,
        xaxis_title="Week",
        yaxis_title=y_label,
        xaxis=dict(type="date"),
        title_x=0.5,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=50, b=10),
    )

    return pio.to_html(fig, full_html=False)


def plot_bar(df, x_col, y_col, y_label, chart_title, unit=""):
    df = df.copy()
    df["week_end"] = df[x_col] + timedelta(days=6)

    fig = go.Figure()
    if y_label == 'kwh':
        fig.add_trace(
            go.Bar(
                x=df[x_col],
                y=df[y_col],
                marker_color="#0ead00",
                customdata=df[["week_end", x_col]],
                hovertemplate=(
                    "Period: From %{customdata[1]|%Y-%m-%d}"
                    " to %{customdata[0]|%Y-%m-%d}<br>"
                    f"{y_label}: %{{y:.2f}} {unit}<extra></extra>"
                ),
            )
        )
    else:
        fig.add_trace(
            go.Bar(
                x=df[x_col],
                y=df[y_col],
                marker_color="#0ead00",
                customdata=df[["week_end", x_col]],
                hovertemplate=(
                    "Period: From %{customdata[1]|%Y-%m-%d}"
                    " to %{customdata[0]|%Y-%m-%d}<br>"
                    f"{y_label}: %{{y:.0f}} {unit}<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        title=chart_title,
        xaxis_title="Week",
        yaxis_title=y_label,
        xaxis=dict(type="date"),
        title_x=0.5,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=50, b=10),
    )

    return pio.to_html(fig, full_html=False)

def pick_models(user):
    """Return (CustomerModel, SaleModel) based on the username."""
    return {
        'John-Maina':    (Customer,      Sale),
        'Mec':           (MecCustomer,   MecSale),
        'Welight':       (TestCustomer,  TestSale),
        'GIZ':           (TestCustomer,  TestSale),
        'Sayona':        (SayonaCustomer, SayonaSale),
        'Sayona-Guest':  (SayonaCustomer, SayonaSale),
    }.get(user, (Customer, Sale))


def weekly_counts(df, date_col="date"):
    """Return a DataFrame with 'week' (Monday start) and 'count'."""
    if df.empty:
        return pd.DataFrame(columns=["week", "count"])
    out = (
        df.assign(week=pd.to_datetime(df[date_col]).dt.to_period("W").apply(lambda p: p.start_time))
          .groupby("week")
          .size()
          .rename("count")
          .sort_index()
          .reset_index()
    )
    return out


def chart_toggle(request, chart_slug):
    # ── 1.  pick the right tables ───────────────────────────────────────────
    CustomerModel, SaleModel = pick_models(request.user.username)
    # pick the right series
    if chart_slug == "customer":
        cache_key = get_cache_key_chart_data(request.user.username, "customer")
        cached_page = cache.get(cache_key)
        if cached_page is not None:
            df_old = cached_page
            df = df_old.reset_index()
            df.columns = ["week", "count"]
        else:    
            customers_df = pd.DataFrame(list(CustomerModel.objects.values("date")))
            weekly_customers = weekly_counts(customers_df)
            df = weekly_customers          # columns: week, count
            cache.set(cache_key, df, timeout=60*60) 
        y_label = "Customers"
        title  = "Weekly Customer Uptake"
    elif chart_slug == "sales":
        cache_key = get_cache_key_chart_data(request.user.username, "sale")
        cached_page = cache.get(cache_key)
        if cached_page is not None:
            df_old = cached_page
            df = df_old.reset_index()
            df.columns = ["week", "count"]  
        else: 
            sales_df  = pd.DataFrame(list(SaleModel.objects.values("date")))
            weekly_sales  = weekly_counts(sales_df)
            df = weekly_sales
            cache.set(cache_key, df, timeout=60*60)             
        y_label = "Sales"
        title   = "Weekly Sales Uptake"
    elif chart_slug == "energy":
        cache_key = get_cache_key_chart_data(request.user.username, "energy")
        cached_page = cache.get(cache_key)
        if cached_page is not None:
            df = cached_page  
        else: 
            dfE = fetch_chart_data(request.user.username)
            dfE['txtime'] = pd.to_datetime(dfE['txtime'], format='%Y%m%d%H%M%S')
            dfE = dfE[dfE['kwh'] >= 0]
            # Group by week
            dfE['week'] = dfE['txtime'].dt.to_period('W').apply(lambda r: r.start_time)  # Get start of each week
            df_weekly = dfE.groupby('week')['kwh'].sum().reset_index()
            # Convert 'week' column back to datetime for plotting
            df_weekly['week'] = pd.to_datetime(df_weekly['week'])
            df_weekly['count'] = df_weekly['kwh']
            df = df_weekly
            cache.set(cache_key, df, timeout=60*60) 
        y_label = "kwh"
        title = "Weekly Energy Consumption"

    chart_type = request.GET.get("type", "line")

    if chart_type == "bar":
        chart_html = plot_bar(df, "week", "count", y_label, title, y_label)
    else:
        chart_html = plot_line(df, "week", "count", y_label, title,y_label)


    # ── 4.  return the fragment HTMX swaps in ───────────────────────────────
    return render(request, "partials/chart.html",  # keep one path
                  {"chart_html": chart_html})


@login_required
def landingpage(request):
    usr = request.user.username
    # Generate cache key based on user and range
    cache_key = get_user_cache_key_landing_page(usr)

    # Check if the entire page context is cached
    cached_page = cache.get(cache_key)
    if cached_page:
        return cached_page  # Return the cached page directly

    if usr == 'John-Maina':
        devs = fetch_data("commandScode")
        CustomerModel = Customer
        SaleModel = Sale
    elif usr == 'Mec':
        devs = fetch_data("commandMec")
        CustomerModel = MecCustomer
        SaleModel = MecSale
    elif usr == 'Welight':
        devs = fetch_data("commandWelight")
        CustomerModel = TestCustomer
        SaleModel = TestSale
    elif usr == 'GIZ':
        devs = fetch_data("commandGIZ")
        CustomerModel = TestCustomer
        SaleModel = TestSale
    elif usr in ['Sayona', 'Sayona-Guest']:
        devs = fetch_data("commandSayona")
        CustomerModel = SayonaCustomer
        SaleModel = SayonaSale
    else:
        devs = fetch_data("command")
        CustomerModel = Customer
        SaleModel = Sale


    devs = pd.DataFrame(devs)
    active_count = devs[devs['active'] == True].shape[0]
    inactive_count = devs[devs['active'] == False].shape[0]
    total_customers = CustomerModel.objects.count() if usr != 'GIZ' else 0
    total_sales = SaleModel.objects.count() if usr != 'GIZ' else 0

    # Define function to fetch and process data
    def fetch_and_process_data():
        endpoint_mapping = {
            'John-Maina': "allDeviceDataScodeDjango",
            'Welight': "allDeviceDataWelightDjango",
            'GIZ': "allDeviceDataGIZDjango",
            'Sayona': "allDeviceDataSayonaDjango",
            'Sayona-Guest': "allDeviceDataSayonaDjango",
            'Mec': "allDeviceDataMecDjango"
        }
        endpoint = endpoint_mapping.get(usr, "allDeviceDataDjango")

        try:
            data = fetch_data_index(endpoint, 9999999)
        except Exception as e:
            messages.error(request, f"Error fetching data: {e}")
            return None

        if not data or (data.get('totalkwh') == 0 and data.get('runtime') == 0 and not data.get('rawData')):
            return None

        runtime = data['runtime']
        top_devices = sorted(runtime.items(), key=lambda x: x[1], reverse=True)[:3]
        bottom_devices = sorted(runtime.items(), key=lambda x: x[1])[:3]
        sumRuntime = sum(runtime.values())
        totalKwh = data['totalkwh']
        return sumRuntime, totalKwh, data['rawData'], top_devices, bottom_devices
    
    runtime, kwh, rawData, top_devices, bottom_devices = fetch_and_process_data()
    # ---- 1.  Get your data (already queried) ----
    customers_all = pd.DataFrame(CustomerModel.objects.all().values())
    sales_all     = pd.DataFrame(SaleModel.objects.all().values())

    # ---- 2.  Ensure date columns are datetime ----
    customers_all['date'] = pd.to_datetime(customers_all['date'])
    sales_all['date'] = pd.to_datetime(sales_all['date'])

    # ---- 3.  Add a "week-start" column (Monday 00:00) ----
    customers_all['week'] = customers_all['date'].dt.to_period('W').apply(lambda r: r.start_time)
    sales_all['week'] = sales_all['date'].dt.to_period('W').apply(lambda r: r.start_time)

    # --- 4. Tally counts ---------------------------------------------------
    weekly_customers = (
        customers_all
            .groupby("week")
            .size()                # Series of counts
            .rename("count")      # optional—but nice for debugging
            .sort_index()
    )

    weekly_sales = (
        sales_all
            .groupby("week")
            .size()
            .rename("count")
            .sort_index()
    )

    fig_customers = go.Figure()
    fig_customers.add_trace(go.Scatter(
        x=weekly_customers.index,
        y=weekly_customers.values,
        fill='tozeroy',  # Fill area below line
        mode='lines', 
        line=dict(color='#0ead00'),
        fillcolor='#d0ffcc',
        line_shape='spline',
        hovertemplate='Week Start: %{x|%Y-%m-%d}<br>Customers: %{y} customers'
    ))
    fig_customers.update_layout(
        title="Weekly Customer Uptake",
        xaxis_title="Date",
        yaxis_title="Customers",
        xaxis=dict(type='date'),
        title_x=0.2,
        paper_bgcolor='rgba(0,0,0,0)',  # Transparent background
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=10, r=10, t=50, b=10),  # Reduce margins for better fit
    )

    fig_sales = go.Figure()
    fig_sales.add_trace(go.Scatter(
        x=weekly_sales.index,
        y=weekly_sales.values,
        fill='tozeroy',  # Fill area below line
        mode='lines', 
        line=dict(color='#0ead00'),
        fillcolor='#d0ffcc',
        line_shape='spline',
        hovertemplate='Week Start: %{x|%Y-%m-%d}<br>Customers: %{y} sales'
    ))
    fig_sales.update_layout(
        title="Weekly Sale Uptake",
        xaxis_title="Date",
        yaxis_title="Sales",
        xaxis=dict(type='date'),
        title_x=0.5,
        paper_bgcolor='rgba(0,0,0,0)',  # Transparent background
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=10, r=10, t=50, b=10),  # Reduce margins for better fit
    )
    


    df = pd.DataFrame(rawData)
    df['txtime'] = pd.to_datetime(df['txtime'], format='%Y%m%d%H%M%S')
    df = df[df['kwh'] >= 0]
    # Group by week
    df['week'] = df['txtime'].dt.to_period('W').apply(lambda r: r.start_time)  # Get start of each week
    df_weekly = df.groupby('week')['kwh'].sum().reset_index()

    # Convert 'week' column back to datetime for plotting
    df_weekly['week'] = pd.to_datetime(df_weekly['week'])
    df_weekly['count'] = df_weekly['kwh']

    # Create filled line plot
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_weekly['week'], 
        y=df_weekly['kwh'], 
        fill='tozeroy',  # Fill area below line
        mode='lines', 
        line=dict(color='#0ead00'),
        fillcolor='#d0ffcc',
        line_shape='spline',
        hovertemplate='Week Start: %{x|%Y-%m-%d}<br>Energy: %{y:.2f} kWh'
    ))

    fig.update_layout(
        title="Weekly Energy Consumption",
        xaxis_title="Date",
        yaxis_title="Energy (kWh)",
        xaxis=dict(type='date'),
        title_x=0.5,
        paper_bgcolor='rgba(0,0,0,0)',  # Transparent background
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=10, r=10, t=50, b=10),  # Reduce margins for better fit
    )
    context = {
        'kwh': kwh,
        'runtime': runtime,
        'active_devs': active_count,
        'inactive_devs': inactive_count,
        'total_devs' : active_count + inactive_count,
        'emissions' : kwh * 0.28 * 0.4999,
        'cost' : kwh * 23.0,
        'energy_chart': pio.to_html(fig, full_html=False),
        'customer_chart': pio.to_html(fig_customers, full_html=False),
        'sales_chart': pio.to_html(fig_sales, full_html=False),
        'top_devices': top_devices,
        'bottom_devices': bottom_devices,
        'total_sales': total_sales,
        'total_customers': total_customers
    }
    # Cache the entire page context for 1 hour
    response = render(request, 'landingPage.html', context)
    cache_key_sale = get_cache_key_chart_data(usr, "sale")
    cache_key_customer = get_cache_key_chart_data(usr, "customer")
    cache_key_energy = get_cache_key_chart_data(usr, "energy")
    cache.set(cache_key_energy, df_weekly, timeout=60*60)
    cache.set(cache_key_sale, weekly_sales, timeout=60*60)
    cache.set(cache_key_customer, weekly_customers, timeout=60*60)
    cache.set(cache_key, response, timeout=60*60)  # Cache the full response

    return response

@login_required
def homepage(request):
    usr = request.user.username
    range_value = request.GET.get('range', 9999999)  # Default range value

    # Generate cache key based on user and range
    cache_key = get_user_cache_key(request.user, range_value)

    # Check if the entire page context is cached
    cached_page = cache.get(cache_key)
    if cached_page:
        return cached_page  # Return the cached page directly

    # Define function to fetch and process data
    def fetch_and_process_data(range_value):
        endpoint_mapping = {
            'John-Maina': "allDeviceDataScodeDjango",
            'Welight': "allDeviceDataWelightDjango",
            'GIZ': "allDeviceDataGIZDjango",
            'Sayona': "allDeviceDataSayonaDjango",
            'Sayona-Guest': "allDeviceDataSayonaDjango",
            'Mec' : "allDeviceDataMecDjango"
        }
        endpoint = endpoint_mapping.get(usr, "allDeviceDataDjango")

        try:
            data = fetch_data_index(endpoint, range_value)
        except Exception as e:
            messages.error(request, f"Error fetching data: {e}")
            return None

        if not data or (data.get('totalkwh') == 0 and data.get('runtime') == 0 and not data.get('rawData')):
            return None

        runtime = data['runtime']
        raw_data = data['rawData']
        
        if not raw_data:
            return None  # Prevent unnecessary DataFrame creation

        df = pd.DataFrame(raw_data)
        data_list = df.to_dict(orient='records')
        meals, mls = classify_and_count_meals(data_list)
        morning, afternoon, night = categorize_kwh(data_list)

        processed_data = (runtime, data_list, meals, morning, afternoon, night)
        return processed_data

    # Fetch and process data if not cached
    processed_data = fetch_and_process_data(range_value)

    if not processed_data:
        messages.warning(request, 'No data for the selected range. Showing default data.')
        range_value = 9999999
        processed_data = fetch_and_process_data(range_value)

    runtime, data_list, meals, morning, afternoon, night = processed_data

    # Summing up data for charts and other outputs
    meal_counts = [info['count'] for info in meals.values()]
    sumKwh = sum(x['kwh'] for x in data_list)
    sumRuntime = sum(runtime.values())
    sumMeals = sum(meal_counts)

    charts = generate_charts(data_list, runtime, meals, morning, afternoon, night)
    linked_data = linkAllDataAndKwh(request, meals, data_list)
    linked_data = pd.DataFrame(linked_data)

    # Generate meal and kWh classifications
    locations, countries, genders, household_size, household_type, sales_reps, locations_kwh, countries_kwh, genders_kwh, household_size_kwh, household_type_kwh, sales_reps_kwh = plot_classifications(linked_data)

    # Create context dictionary
    context = {
        'line_chart': charts['line_chart'],
        'pie_chart': charts['pie_chart'],
        'meals_pie_html': charts['meals_pie_html'],
        'meals_kwh_html': charts['meals_kwh_html'],
        'cooking_time_pie_html': charts['cooking_time_pie_html'],
        'meals_emissions_html': charts['meals_emissions_html'],
        'pie_chart_emissions': charts['pie_chart_emissions'],
        'sumKwh': sumKwh,
        'sumRuntime': sumRuntime,
        'sumEmissions': sumKwh * 0.28 * 0.4999,
        'sumEnergyCost': sumKwh * 23.0,
        'sumMeals': sumMeals,
        'selected_range': str(range_value),
        'meals': meals,
        'linked_data': linked_data,
        'location_graph': locations,
        'countries_graph': countries,
        'genders_graph': genders,
        'household_size_graph': household_size,
        'household_type_graph': household_type,
        'sales_reps_graph': sales_reps,
        'location_graph_kwh': locations_kwh,
        'countries_graph_kwh': countries_kwh,
        'genders_graph_kwh': genders_kwh,
        'household_size_graph_kwh': household_size_kwh,
        'household_type_graph_kwh': household_type_kwh,
        'sales_reps_graph_kwh': sales_reps_kwh
    }

    # Cache the entire page context for 1 hour
    response = render(request, 'index.html', context)
    cache.set(cache_key, response, timeout=60*60)  # Cache the full response

    return response

@login_required
def linkAllDataAndKwh(request, devData, kwhData):
    user = request.user
    # Choose the model based on user
    if user.first_name == 'Welight':
        CustomerModel = TestCustomer
        SaleModel = TestSale
    elif user.first_name == 'Mec':
        CustomerModel = MecCustomer
        SaleModel = MecSale
    elif user.first_name in ['Sayona', 'Sayona-Guest']:
        CustomerModel = SayonaCustomer
        SaleModel = SayonaSale
    else:
        CustomerModel = Customer
        SaleModel = Sale
    customer_data = CustomerModel.objects.all().values()    
    sales_data = SaleModel.objects.all().values()
    linked_data = []

    # Step 1: Link meals data with sales data
    for sale in sales_data:
        serial_number = sale['product_serial_number']
        meals_cooked = 0
        last_txtime = None
        matched_kwh = 0

        # Find the matching deviceID in the meals and kWh data
        for device in devData:
            if device == serial_number:
                meals_cooked = devData[device]['count']
                last_txtime = devData[device]['last_txtime']
                break
        
        for device in kwhData:
            if device['deviceID'] == serial_number:
                matched_kwh += device['kwh']
                

        sale['meals_cooked'] = meals_cooked
        sale['last_txtime'] = last_txtime
        sale['kwh'] = matched_kwh

        # Step 2: Link sales data with customer data
        for customer in customer_data:
            if customer['id'] == sale['customer_id']:
                linked_entry = {**sale, **customer}  # Merge the dictionaries
                linked_data.append(linked_entry)

    return linked_data

def plot_classifications(data):
    # Create a dictionary to store the HTML of each graph
    graphs_html = {}

    # Shared function for creating pie charts for both meals and kWh
    def create_pie_chart_for_classification(classification_column, value_column, label):
        fig = go.Figure()
        classification_data = data.groupby(classification_column)[value_column].sum().reset_index()
        fig = create_pie_chart(classification_data[classification_column], classification_data[value_column], label)
        fig.update_traces(hole=.5, hovertemplate=f'<b>{classification_column.capitalize()}: %{{label}}<br>{value_column.capitalize()}: %{{value}} {value_column}')
        return pio.to_html(fig, full_html=False)

    # Meals classification
    graphs_html['meals_by_household_type'] = create_pie_chart_for_classification('household_type', 'meals_cooked', 'Meals Cooked by Household Type')
    graphs_html['meals_by_household_size'] = create_pie_chart_for_classification('household_size', 'meals_cooked', 'Meals Cooked by Household Size')
    graphs_html['meals_by_country'] = create_pie_chart_for_classification('country', 'meals_cooked', 'Meals Cooked by Country')
    graphs_html['meals_by_location'] = create_pie_chart_for_classification('location', 'meals_cooked', 'Meals Cooked by Location')
    graphs_html['meals_by_sales_rep'] = create_pie_chart_for_classification('sales_rep', 'meals_cooked', 'Meals Cooked by Sales Rep')
    graphs_html['meals_by_gender'] = create_pie_chart_for_classification('gender', 'meals_cooked', 'Meals Cooked by Gender')

    # kWh classification
    graphs_html['kwh_by_household_type'] = create_pie_chart_for_classification('household_type', 'kwh', 'Energy Use by Household Type')
    graphs_html['kwh_by_household_size'] = create_pie_chart_for_classification('household_size', 'kwh', 'Energy Use by Household Size')
    graphs_html['kwh_by_country'] = create_pie_chart_for_classification('country', 'kwh', 'Energy Use by Country')
    graphs_html['kwh_by_location'] = create_pie_chart_for_classification('location', 'kwh', 'Energy Use by Location')
    graphs_html['kwh_by_sales_rep'] = create_pie_chart_for_classification('sales_rep', 'kwh', 'Energy Use by Sales Rep')
    graphs_html['kwh_by_gender'] = create_pie_chart_for_classification('gender', 'kwh', 'Energy Use by Gender')

    return graphs_html['meals_by_location'], graphs_html['meals_by_country'], graphs_html['meals_by_gender'], graphs_html['meals_by_household_size'], graphs_html['meals_by_household_type'], graphs_html['meals_by_sales_rep'], \
           graphs_html['kwh_by_location'], graphs_html['kwh_by_country'], graphs_html['kwh_by_gender'], graphs_html['kwh_by_household_size'], graphs_html['kwh_by_household_type'], graphs_html['kwh_by_sales_rep']


def plotAllDevData(data):
    # Convert txtime to datetime format
    data['txtime'] = pd.to_datetime(data['txtime'], format='%Y%m%d%H%M%S')

    fig = go.Figure()

    # Create scatter plots for each unique deviceID
    for device_id in data['deviceID'].unique():
        device_data = data[data['deviceID'] == device_id]
        
        fig.add_trace(go.Scatter(
            x=device_data['txtime'],
            y=(device_data['kwh']*1000),
            mode='lines+markers',
            name=device_id,
            line_shape='spline'
        ))

    fig.update_traces(hovertemplate='Date: %{x}<br>Energy: %{y} Wh')

    fig.update_layout(
        title='Scatter plot for all devices',
        xaxis_title='Date',
        yaxis_title='KWH',
        showlegend=True,
        autosize=True,
        title_x=0.5,
        height=500,
        margin=dict(l=20, r=20, t=40, b=20)
    )

    # Convert the figure to HTML
    fig_html = pio.to_html(fig, full_html=False)
    
    return fig_html

@login_required
def mec_downloads(request):
    usr = request.user.username
    if usr == 'John-Maina':
        data = fetch_data("commandScode")
    elif usr == 'Mec':
        data = fetch_data("commandMec")
    elif usr == 'Welight':
        data = fetch_data("commandWelight")
    elif usr == 'GIZ':
        data = fetch_data("commandGIZ")
    elif usr in ['Sayona', 'Sayona-Guest']:
        data = fetch_data("commandSayona")
    else:
        data = fetch_data("command")

    data = pd.DataFrame(data)
    if not data.empty:
        # Sorting and handling different naming conventions
        def sort_key(x):
            if x == 'OfficeFridge1':
                return (4, float('inf'))  # Always last
            elif x.startswith('JD-29ED'):
                return (0, int(x.split('JD-29ED')[-1]))  # Sorted first
            elif x.isdigit():  # Pure numeric device IDs
                return (1, int(x))  # Sorted second
            elif x.startswith('device'):
                return (2, int(x.split('device')[-1]))  # Sorted third
            else:
                return (3, float('inf') - 1)  # Other strings sorted fourth

        data['sort_key'] = data['deviceID'].apply(sort_key)
        data = data.sort_values(by='sort_key')
    # Convert the DataFrame to a list of dictionaries
    devices_list = data.to_dict(orient='records')
    device_list = [device['deviceID'] for device in devices_list]
    context = {
        "dev_List": device_list
    }
    return render(request, "customerDeviceDownloads.html", context)

@login_required
def export_mec_downloads(request):
    if request.method == "POST":
        selected_range = request.GET.get('timerange1', '9999999')
        selected_devices = request.POST.getlist('devices')
        data = fetch_data_devs("mecdownloads", selected_devices, selected_range)
        df = pd.DataFrame(data)
        # Create a HttpResponse with content_type as ms-excel
        response = HttpResponse(content_type='application/vnd.ms-excel')
    
    # Specify the file name
        response['Content-Disposition'] = 'attachment; filename="transactions.xlsx"'
    # Use pandas to save the dataframe as an excel file in the response
    df.to_excel(response, index=False, engine='openpyxl')

    return response

@login_required
def mec_single_download(request):
    if request.method == "POST":
        selected_range = request.POST.get('timerange', '9999999')
        device = request.POST.get('device')
        selected_devices = []
        selected_devices.append(device)
        data = fetch_data_devs("mecdownloads", selected_devices, selected_range)
        df = pd.DataFrame(data)
        # Create a HttpResponse with content_type as ms-excel
        response = HttpResponse(content_type='application/vnd.ms-excel')
        # Specify the file name
        response['Content-Disposition'] = 'attachment; filename="merged_customer_device_data.xlsx"'
        # Use pandas to save the dataframe as an excel file in the response
        df.to_excel(response, index=False, engine='openpyxl')
        return response

@login_required
def devices_page(request):
    usr = request.user.username
    if usr == 'John-Maina':
        data = fetch_data("commandScode")
    elif usr == 'Mec':
        data = fetch_data("commandMec")
    elif usr == 'Welight':
        data = fetch_data("commandWelight")
    elif usr == 'GIZ':
        data = fetch_data("commandGIZ")
    elif usr in ['Sayona', 'Sayona-Guest']:
        data = fetch_data("commandSayona")
    else:
        data = fetch_data("command")

    data = pd.DataFrame(data)
    
    if not data.empty:
        # Sorting and handling different naming conventions
        def sort_key(x):
            if x == 'OfficeFridge1':
                return (4, float('inf'))  # Always last
            elif x.startswith('JD-29ED'):
                return (0, int(x.split('JD-29ED')[-1]))  # Sorted first
            elif x.isdigit():  # Pure numeric device IDs
                return (1, int(x))  # Sorted second
            elif x.startswith('device'):
                return (2, int(x.split('device')[-1]))  # Sorted third
            else:
                return (3, float('inf') - 1)  # Other strings sorted fourth

        data['sort_key'] = data['deviceID'].apply(sort_key)
        data = data.sort_values(by='sort_key')

        # Convert 'time' to datetime format
        data['time'] = pd.to_datetime(data['time'], format="%Y-%m-%dT%H:%M:%S.%fZ")
        data['time'] = data['time'] + timedelta(hours=3)

        # Handle search query
        query = request.GET.get('q')
        if query:
            data = data[data['deviceID'].str.lower().str.contains(query.lower())]

        # Get counts of active and inactive devices
        active_count = data[data['active'] == True].shape[0]
        inactive_count = data[data['active'] == False].shape[0]

        # Convert the DataFrame to a list of dictionaries
        devices_list = data.to_dict(orient='records')

        # Implement pagination with 10 items per page
        paginator = Paginator(devices_list, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
    else:
        page_obj = []
        active_count = 0
        inactive_count = 0

    device_list = [device['deviceID'] for device in devices_list]
    context = {
        'devices_table': page_obj,
        'query': query,
        'device_list': device_list,  # Add the device list to the context
        'active_count': active_count,  # Add active devices count
        'inactive_count': inactive_count,  # Add inactive devices count
        'total_count': active_count + inactive_count
    }

    return render(request, 'devices.html', context)


@login_required
def change_device_status(request):
    if request.method == "POST":
        try:
            # ✅ Parse form data instead of JSON
            selected_dev = request.POST.get("selectedDev")
            status = request.POST.get("status") == "true"  # Convert string "true"/"false" to boolean

            # ✅ Send request to external API
            response = requests.post("https://appliapay.com/changeStatus", json={
                "selectedDev": selected_dev,
                "status": not status
            })

            response_data = response.json()  # Parse response

            if response.status_code == 200:
                # ✅ Extract updated values from API response
                new_device_id = response_data.get("selectedDev", selected_dev)
                new_status = response_data.get("status")
                updated_time = pd.to_datetime(response_data.get("time"), format="%Y-%m-%dT%H:%M:%S.%fZ")

                #send notification
                user = request.user
                action = "activated" if new_status == True else "deactivated"
                notifications.send_notification(user, "Status Change", f"{new_device_id} has been {action}")

                # ✅ Render updated row
                return render(
                    request,
                    "partials/device_row.html",
                    {
                        "row": {
                            "deviceID": new_device_id,
                            "active": new_status,
                            "time": updated_time
                        }
                    },
                )
            
            else:
                return JsonResponse({"error": "Failed to update device status"}, status=500)

        except requests.exceptions.RequestException as e:
            return JsonResponse({"error": f"External API error: {str(e)}"}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)

@login_required
def status_dev(request):
    if request.method == "POST":
        try:
            # ✅ Parse form data instead of JSON
            selected_dev = request.POST.get("selectedDev")
            status = request.POST.get("status") == "true"  # Convert string "true"/"false" to boolean

            # ✅ Send request to external API
            response = requests.post("https://appliapay.com/changeStatus", json={
                "selectedDev": selected_dev,
                "status": not status
            })

            response_data = response.json()  # Parse response

            if response.status_code == 200:
                # ✅ Extract updated values from API response
                new_device_id = response_data.get("selectedDev", selected_dev)
                new_status = response_data.get("status")
                updated_time = pd.to_datetime(response_data.get("time"), format="%Y-%m-%dT%H:%M:%S.%fZ")

                #send notification 
                user = request.user
                action = "activated" if new_status == True else "deactivated"
                notifications.send_notification(user, "Status Change", f"{new_device_id} has been {action}")
                # ✅ Render updated row
                return render(
                    request,
                    "partials/switchWLabel.html",
                    {
                            "deviceID": new_device_id,
                            "active": new_status,
                            "time": updated_time
                    },
                )
            else:
                return JsonResponse({"error": "Failed to update device status"}, status=500)

        except requests.exceptions.RequestException as e:
            return JsonResponse({"error": f"External API error: {str(e)}"}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)


def classify_and_count_meals(data):
    sorted_data = sorted(data, key=lambda x: (x['deviceID'], x['txtime']))
    device_meal_counts = {}
    day_meal_counts = {}

    for entry in sorted_data:
        if entry['deviceID'] != 'OfficeFridge1':
            device_id = entry['deviceID']
            txtime = datetime.strptime(str(entry['txtime']), "%Y%m%d%H%M%S")

            if device_id not in device_meal_counts:
                device_meal_counts[device_id] = {'count': 0, 'last_txtime': None}
            if device_meal_counts[device_id]['last_txtime'] is not None:
                time_diff = txtime - device_meal_counts[device_id]['last_txtime']
                if time_diff > timedelta(minutes=20):
                    device_meal_counts[device_id]['count'] += 1
            else:
                device_meal_counts[device_id]['count'] += 1

            date = txtime.strftime('%Y-%m-%d')
            if date not in day_meal_counts:
                day_meal_counts[date] = {}
            if device_id not in day_meal_counts[date]:
                day_meal_counts[date][device_id] = 0
            if 'last_txtime' in day_meal_counts[date]:
                time_diff = txtime - day_meal_counts[date]['last_txtime']
                if time_diff > timedelta(minutes=20):
                    day_meal_counts[date][device_id] += 1
            else:
                day_meal_counts[date][device_id] += 1
            
            device_meal_counts[device_id]['last_txtime'] = txtime
            day_meal_counts[date]['last_txtime'] = txtime

    total_meals_per_day = {date: sum(count for device, count in counts.items() if device != 'last_txtime') for date, counts in day_meal_counts.items()}
    return device_meal_counts, total_meals_per_day

def categorize_kwh(data):
    morning_kwh = 0
    afternoon_kwh = 0
    night_kwh = 0
    for record in data:
        hour = int(str(record['txtime'])[8:10])
        if 4 <= hour < 11:
            morning_kwh += record['kwh']
        elif 11 <= hour < 17:
            afternoon_kwh += record['kwh']
        else:
            night_kwh += record['kwh']
    return morning_kwh, afternoon_kwh, night_kwh

def generate_charts(data, runtime, meals, morning, afternoon, night):
    # Convert data to DataFrame
    df = pd.DataFrame(data)
    df['txtime'] = pd.to_datetime(df['txtime'], format='%Y%m%d%H%M%S')
    df = df[df['kwh'] >= 0]

    device_ids = [device_id for device_id, info in meals.items()]
    meal_counts = [info['count'] for device_id, info in meals.items()]
    runtime_device_ids = list(runtime.keys())
    runtime_hours = list(runtime.values())

    # Create Pie Charts
    cooking_time_pie = create_pie_chart(runtime_device_ids, runtime_hours, 'Cooking Time by Device')
    meals_pie = create_pie_chart(device_ids, meal_counts, 'Meals Distribution by Device')
    kwh_pie = create_pie_chart(["Breakfast", "Lunch", "Supper"], [morning, afternoon, night], 'KWH Per Meal')
    emissions_pie = create_pie_chart(["Breakfast", "Lunch", "Supper"], [morning * 0.4999 * 0.28, afternoon * 0.4999 * 0.28, night * 0.4999 * 0.28], 'Emissions Per Meal')

    # Line Chart
    energy_line_chart = create_line_chart(df, 'txtime', 'kwh', 'Energy Consumption')

    # Device kWh Pie Chart
    df_pie = df.groupby('deviceID')['kwh'].sum().reset_index()
    kwh_pie_chart = create_pie_chart(df_pie['deviceID'], df_pie['kwh'], 'kWh Distribution by Device')

    # Emissions per Device Pie Chart
    df_pie_emissions = df.copy()
    df_pie_emissions['emissions'] = df_pie_emissions['kwh'] * 0.4999 * 0.28
    emissions_device_pie_chart = create_pie_chart(df_pie_emissions['deviceID'], df_pie_emissions['emissions'], 'Carbon Emissions Per Device')
    cooking_time_pie.update_traces(hovertemplate='<b>%{label}: %{value} hours', hole=.5)
    meals_pie.update_traces(hovertemplate='<b>%{label}: %{value} meals', hole=.5)
    kwh_pie.update_traces(hovertemplate='<b>%{label}: %{value} kWh', hole=.5)
    kwh_pie_chart.update_traces(hovertemplate='<b>%{label}: %{value} kWh', hole=.5)
    emissions_pie.update_traces(hovertemplate='<b>%{label}: %{value} kg CO₂', hole=.5)
    emissions_device_pie_chart.update_traces(hovertemplate='<b>%{label}: %{value} kg CO₂', hole=.5)

    return {
        'line_chart': pio.to_html(energy_line_chart, full_html=False),
        'pie_chart': pio.to_html(kwh_pie_chart, full_html=False),
        'meals_pie_html': pio.to_html(meals_pie, full_html=False),
        'meals_kwh_html': pio.to_html(kwh_pie, full_html=False),
        'cooking_time_pie_html': pio.to_html(cooking_time_pie, full_html=False),
        'meals_emissions_html': pio.to_html(emissions_pie, full_html=False),
        'pie_chart_emissions': pio.to_html(emissions_device_pie_chart, full_html=False)
    }

def create_pie_chart(names, values, title):
    pie_chart = px.pie(names=names, values=values, title=title)
    pie_chart.update_traces(textposition='inside', hoverinfo='label+value+percent',
                            hovertemplate='<b>%{label}: %{value}</b>')
    pie_chart.update_layout(
        showlegend=True,
        autosize=True,
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
        title_x=0.5
    )
    #pie_chart.update_layout(legend=dict(
    #orientation="v",
    #yanchor="bottom",
    #y=0.01,
    #xanchor="left",
    #x=0.01
    #))
    return pie_chart

def create_line_chart(df, x_column, y_column, title):
    # Create the bar chart
    bar_chart = px.bar(df, x=x_column, y=y_column, title=title, labels={x_column: 'Time', y_column: 'kWh'})

    # Update the trace for better visibility
    bar_chart.update_traces(
        marker=dict(color="#0ead00"),
        hovertemplate='%{x}<br>%{y} kWh<br>Device ID: %{text}',
        text=df['deviceID'],
        width=0.8  # Adjust width if needed
    )

    # Update layout for better visualization
    bar_chart.update_layout(
        xaxis_title='Time',
        yaxis_title='kWh',
        showlegend=False,
        autosize=True,
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
        title_x=0.5
    )

    return bar_chart

@login_required
def transactions_page(request):
    usr = request.user.username
    range_value = request.GET.get('range', 9999999)

    # Fetch data based on user
    if usr == 'John-Maina':
        data = fetch_data_index("mpesarecordsscode", range_value)
    else:
        data = fetch_data_index("mpesarecords", range_value)

    # Convert data to a DataFrame
    if data:  # Check if data is not empty
        data = pd.DataFrame(data)
        data['transtime'] = pd.to_datetime(data['transtime'], format='%Y%m%d%H%M%S')

        # Sort the data by 'transtime' in descending order
        data = data.sort_values(by='transtime', ascending=False)
    else:
        data = pd.DataFrame(columns=['name', 'ref', 'id', 'transtime', 'amount'])  # Empty DataFrame

    # Handle search query
    query = request.GET.get('q')
    if query and not data.empty:
        data = data[data.apply(lambda row: query.lower() in row['name'].lower() or
                                             query.lower() in row['ref'].lower() or
                                             query.lower() in row['id'].lower(), axis=1)]
    
    # Group by week and sum 'amount'
    if not data.empty:
        data['week'] = data['transtime'].dt.to_period('W').apply(lambda r: r.start_time)  # Get start of each week
        df_weekly = data.groupby('week')['amount'].sum().reset_index()

        # Convert 'week' column back to datetime for plotting
        df_weekly['week'] = pd.to_datetime(df_weekly['week'])

    # Convert the DataFrame to a list of dictionaries
    transactions_list = data.to_dict(orient='records')

    # Implement pagination with 10 items per page
    paginator = Paginator(transactions_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Line chart data (only if there's data to plot)
    weekly_chart = ''
    if not data.empty:
        # Plotting weekly aggregated data
        fig_weekly = px.line(df_weekly, x='week', y='amount', title='Weekly Transaction Amounts',
                             labels={'week': 'Week', 'amount': 'Total Amount'},
                             line_shape='spline')

        fig_weekly.update_traces(line=dict(color="#0ead00"), hovertemplate='Week Start: %{x|%Y-%m-%d}<br>Amount: KSHS. %{y:,.0f}', mode='lines', fillcolor='#d0ffcc', fill='tozeroy')
        fig_weekly.update_layout(
            xaxis_title='Week',
            yaxis_title='Total Amount',
            showlegend=False,
            autosize=True,
            title_x=0.5,
            height=400,
            margin=dict(l=20, r=20, t=40, b=20),
            paper_bgcolor='rgba(0,0,0,0)',  # Transparent background
            plot_bgcolor='rgba(0,0,0,0)',
        )

        weekly_chart = pio.to_html(fig_weekly, full_html=False)

    # Prepare the context with the relevant data
    context = {
        'transactions_table': page_obj,  # Pass the page object to the template
        'query': query,  # Pass the query to the template to preserve it in the search box
        'line_chart': weekly_chart,  # Pass the weekly aggregated line chart HTML
        'selected_range': str(range_value),
        'is_data_empty': data.empty  # Pass whether data is empty to the template
    }

    return render(request, 'transactions.html', context)



def fetch_data_with_params(endpoint, dev, range_value):
    response = requests.get(BASE_URL + endpoint +"?device="+dev+"&range=" + str(range_value), auth=AUTH)
    response.raise_for_status()
    return response.json()

#######################################################STK PAYMENT CODE############################################################################


def post_payment_prompt(endpoint, contact, amount, ref):
    data = {"contact": contact, "ref": ref, "amount":amount}
    response = requests.post(BASE_URL + endpoint, json=data, auth=AUTH)
    response.raise_for_status()
    return response.json()

def payment_prompt_action(usr, contact, amount, ref):
    global payment_status
    payment_status = {
    "status": "pending",
    "message": "",
    "amount": None,
    "receipt_number": None,
    "transaction_date": None,
    "phone_number": None
    }
    if usr == 'John-Maina':
        res = post_payment_prompt(endpoint="stkpushscode", contact=contact, amount=amount, ref=ref)
    else:
        res = post_payment_prompt(endpoint="stkpush", contact=contact, amount=amount, ref=ref)
    return res

@login_required
def payment_prompt(request):
    usr = request.user.username
    global ref

    if request.method == 'POST':
        contact = request.POST.get('contact')
        amount = request.POST.get('amount')
        ref = request.POST.get('ref')
        try:
            res = payment_prompt_action(contact=contact, amount=amount, ref=ref, usr=usr)
            if res.get('ResponseCode') == 0:
                messages.info(request, res.get('ResponseDescription'))
                return redirect('payment_waiting', ref=ref)
            else:
                messages.error(request, "Failed. Kindly try again.")
        except requests.RequestException as e:
            messages.error(request, f"Error: {e}")
        return render(request, "payment_prompt.html")
    
    elif request.method == 'GET':
        ref = request.GET.get('ref')
        amount = request.GET.get('amount')
        contact = ""  # You may fetch this from the database using the ref or other logic
        return render(request, "payment_prompt.html", {'ref': ref, 'amount': amount, 'contact': contact})

    return render(request, "payment_prompt.html")



@csrf_exempt
def payment_confirmation(request):
    global payment_status  # Use the global variable
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            stk_callback = data.get('Body', {}).get('stkCallback', {})
            result_code = stk_callback.get('ResultCode')
            result_desc = stk_callback.get('ResultDesc')

            if result_code == 0:
                status = 'success'
                message = result_desc
                callback_metadata = stk_callback.get('CallbackMetadata', {}).get('Item', [])
                amount = next((item.get('Value') for item in callback_metadata if item.get('Name') == 'Amount'), None)
                receipt_number = next((item.get('Value') for item in callback_metadata if item.get('Name') == 'MpesaReceiptNumber'), None)
                transaction_date = next((item.get('Value') for item in callback_metadata if item.get('Name') == 'TransactionDate'), None)
                phone_number = next((item.get('Value') for item in callback_metadata if item.get('Name') == 'PhoneNumber'), None)
            else:
                status = 'failed'
                message = 'The user cancelled the request'
                amount = None
                receipt_number = None
                transaction_date = None
                phone_number = None

            # Update the global variable
            payment_status.update({
                "status": status,
                "message": message,
                "amount": amount,
                "receipt_number": receipt_number,
                "transaction_date": transaction_date,
                "phone_number": phone_number
            })

            return JsonResponse({"status": status, "message": message})
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)

# Handle the payment confirmation status check
@login_required
def payment_confirmation_page(request):
    global payment_status  # Use the global variable
    
    context = {
        'status': payment_status.get('status'),
        'message': payment_status.get('message'),
        'amount': payment_status.get('amount'),
        'receipt_number': payment_status.get('receipt_number'),
        'transaction_date': payment_status.get('transaction_date'),
        'phone_number': payment_status.get('phone_number')
    }

    return render(request, 'payment_confirmation.html', context)


@csrf_exempt
def payment_confirmation_status(request):
    global payment_status  # Use the global variable
    if request.method == 'GET':
        ref = request.GET.get('ref')
        status = payment_status.get('status')
        if status != 'pending':
            message = payment_status.get('message')
            return JsonResponse({'status': status, 'message': message})
        else:
            return JsonResponse({'status': 'pending', 'message': 'Payment is still pending.'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)


# Render the payment waiting page
@login_required
def payment_waiting(request, ref):
    return render(request, "payment_waiting.html", {"ref": ref})


##########################################################END OF STK PAYMENT CODE#################################################################  


@login_required
def device_data_page(request, deviceID):
    range_value = request.GET.get('range', 9999999)
    # Fetch data based on device_id and range_value
    data = fetch_data_with_params("deviceDataDjangoo", deviceID, range_value)
    runtime = data['runtime']
    sum_kwh = data['sumKwh']
    emissions = sum_kwh * 0.4999 * 0.28
    energy_cost = sum_kwh * 23.0
    meals_with_durations = data['mealsWithDurations'][::-1]
    total_meals_per_day = data['totalMealsPerDay']

    # Convert the 'Date' keys to datetime
    total_meals_per_day = {pd.to_datetime(k): v for k, v in total_meals_per_day.items()}

    # Create DataFrame for total meals per day
    df_meals = pd.DataFrame(list(total_meals_per_day.items()), columns=["Date", "Meals"])
    fig_meals_bar = px.bar(df_meals, x="Date", y="Meals", title="Total Meals Per Day", labels={"Meals": "Number of Meals"})
    fig_meals_bar.update_traces(marker=dict(color="#0ead00"), hovertemplate='Date: %{x}<br>Number of Meals: %{y}')
    fig_meals_bar.update_layout(
        xaxis_title='Date',
        yaxis_title='Meals',
        showlegend=False,
        autosize=True,
        title_x=0.5,
        height=400,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    meals_per_day_chart = pio.to_html(fig_meals_bar, full_html=False)

    # Process meals_with_durations
    for x in meals_with_durations:
        x['mealDuration'] = x['mealDuration'] / 60
        x['startTime'] = datetime.strptime(x['startTime'], '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%d %b %Y %I:%M:%S %p')
        x['endTime'] = datetime.strptime(x['endTime'], '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%d %b %Y %I:%M:%S %p')
        x['emissions'] = x['totalKwh'] * 0.4999 * 0.28
        x['energy_cost'] = x['totalKwh'] * 23.0

    fig_metrics_bar = go.Figure(data=[
        go.Scatter(name='Carbon Emissions', x=[date['startTime'] for date in meals_with_durations[::-1]], y=[(e['emissions']*1000) for e in meals_with_durations[::-1]], hovertemplate='Date: %{x}<br>Carbon Emissions: %{y} grams of CO₂', line_shape='spline'),
        go.Scatter(name='Energy Cost', x=[date['startTime'] for date in meals_with_durations[::-1]], y=[e['energy_cost'] for e in meals_with_durations[::-1]], hovertemplate='Date: %{x}<br>Energy Cost: %{y} Kenya Shillings', line_shape='spline'),
        go.Scatter(name='Energy Consumption', x=[date['startTime'] for date in meals_with_durations[::-1]], y=[(e['totalKwh']*1000) for e in meals_with_durations[::-1]], hovertemplate='Date: %{x}<br>Energy: %{y} watt-hours', line_shape='spline')
    ])
    #fig_metrics_bar.update_traces(title='Combined Device Metrics')
    fig_metrics_bar.update_layout(
        xaxis_title='Date',
        yaxis_title='Value',
        showlegend=True,
        autosize=True,
        title_x=0.5,
        height=500,
        margin=dict(l=20, r=20, t=40, b=20),
        #xaxis_visible=False,
        xaxis_showticklabels=False,
        #barmode='group',
        #barcornerradius=10
    )
    metrics_chart = pio.to_html(fig_metrics_bar, full_html=False)

    usr = request.user.username
    if usr == 'John-Maina':
        dat = fetch_data("commandScode")
    elif usr == 'Mec':
        dat = fetch_data("commandMec")
    elif usr == 'Welight':
        dat = fetch_data("commandWelight")
    elif usr in ['Sayona', 'Sayona-Guest']:
        dat = fetch_data("commandSayona")
    elif usr == 'GIZ':
        dat = fetch_data("commandGIZ")
    else:
        dat = fetch_data("command")
    for z in dat:
        if z["deviceID"] == deviceID:
            status = z["active"]
    dat = pd.DataFrame(dat)
    if not dat.empty:
        # Sorting and handling different naming conventions
        def sort_key(x):
            if x == 'OfficeFridge1':
                return float('inf')
            elif x.startswith('device'):
                return int(x.split('device')[-1])
            elif x.startswith('JD-29ED'):
                return int(x.split('JD-29ED')[-1])
            else:
                return float('inf') - 1
        
        dat['sort_key'] = dat['deviceID'].apply(sort_key)
        dat = dat.sort_values(by='sort_key')

    # Pagination logic
    paginator = Paginator(meals_with_durations, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    dev_List = dat['deviceID'].tolist()

    context = {
        "deviceID": str(deviceID),  # Ensure device_id is a string
        "runtime": runtime,
        "sum_kwh": sum_kwh,
        "emissions": emissions,
        "meals_with_durations": page_obj,  # Pass paginated meals_with_durations
        "total_meals_per_day": total_meals_per_day,
        "meals_per_day_chart": meals_per_day_chart,
        "metrics_chart": metrics_chart,  # Pass the metrics chart HTML to the template
        "energy_cost": energy_cost,
        "dev_List": dev_List,  # Ensure dev_List is a list of strings
        "active": status,
        "selected_range": str(range_value)
    }

    return render(request, "device_data.html", context)

@login_required
def add_device(request):
    if request.method == 'POST':
        device_name = request.POST.get('device_name')
        if device_name:
            devs = fetch_data("command")
            for devEntry in devs:
                if devEntry['deviceID'] == device_name:
                    return JsonResponse({
                        "exists": True,
                        "device": device_name
                    })
            # Replace with your actual endpoint URL
            endpoint = 'https://appliapay.com/addDevice'
            # Replace with your actual credentials
            username = 'admin'
            password = '123Give!@#'
            credentials = (username, password)
            headers = {'Content-Type': 'application/json'}

            data = {'device': device_name}

            response = requests.post(endpoint, json=data, auth=credentials, headers=headers)

            if response.status_code == 200:
                return JsonResponse({
                    "added": True,
                    "device": device_name
                })  # ✅ Return JSON success response
            else:
                return JsonResponse({
                    "error": "Failed to add device"
                })

    return render(request, 'add_device.html')

#################################DOWNLOAD TRANSACTIONS EXCEL##############################################
@login_required
def export_transactions_excel(request, range):
    # Fetch data based on the user
    usr = request.user.username
    if usr == 'John-Maina':
        data = fetch_data_index("mpesarecordsscode", range)
    else:
        data = fetch_data_index("mpesarecords", range)

    # Convert the data to a DataFrame
    df = pd.DataFrame(data)
    
    if usr == 'SAF':
        df['name'] = '**REDACTED**'
        df['ref'] = '**REDACTED**'
        df['transtime'] = pd.to_datetime(df['transtime'], format='%Y%m%d%H%M%S').dt.strftime('%Y-%m-%dT%H:%M:%S')
    else:
        # Convert 'transtime' to datetime format
        df['transtime'] = pd.to_datetime(df['transtime'], format='%Y%m%d%H%M%S')
    # Sort the data by 'transtime' in descending order
    df = df.sort_values(by='transtime', ascending=False)

    # Drop the 'time' column to remove it from the export
    df = df.drop(columns=['time'])

    # Create a HttpResponse with content_type as ms-excel
    response = HttpResponse(content_type='application/vnd.ms-excel')
    
    # Specify the file name
    response['Content-Disposition'] = 'attachment; filename="transactions.xlsx"'

    # Use pandas to save the dataframe as an excel file in the response
    df.to_excel(response, index=False, engine='openpyxl')

    return response

###############################DOWNLOAD DEVICE DATA#######################################################
@login_required
def export_device_data(request, device_id, range):
    # Fetch data based on device_id and range_value
    data = fetch_data_with_params("deviceDataDjangoo", device_id, range)
    meals_with_durations = data['mealsWithDurations'][::-1]
    for x in meals_with_durations:
        x['mealDuration'] = round(x['mealDuration']/60)
        x['mealDuration'] = str(x['mealDuration']) + " minutes"
        x['emissions'] = round(x['totalKwh'] * 0.4999 * 0.28, 3)
        x['emissions'] = str(x['emissions']) + " kg CO₂"
        x['energyCost'] = round(x['totalKwh'] * 23.0, 1) 
        x['energyCost'] = "KSHS. " + str(x['energyCost'])
        x['totalKwh'] = round(x['totalKwh'],3)
        x['totalKwh'] = str(x['totalKwh']) + " kWh"
    # Convert the data to a DataFrame
    df = pd.DataFrame(meals_with_durations)
    
    # Create the filename
    fileName = f"{device_id}_cooking_data.xlsx"
    
    # Create a HttpResponse with content_type as ms-excel
    response = HttpResponse(content_type='application/vnd.ms-excel')
    
    # Specify the file name using f-string
    response['Content-Disposition'] = f'attachment; filename="{fileName}"'
    
    # Use pandas to save the dataframe as an excel file in the response
    df.to_excel(response, index=False, engine='openpyxl')

    return response

#######################BULK METER DATA FOR SAF###################################################
@login_required
def export_bulk_device_data(request):
     # Fetch data based on device_id and range_value
    data = fetch_data("bulkDeviceData")
    # Convert the data to a DataFrame
    df = pd.DataFrame(data)
    
    # Create the filename
    fileName = f"bulk_meter_data.xlsx"
    
    # Create a HttpResponse with content_type as ms-excel
    response = HttpResponse(content_type='application/vnd.ms-excel')
    
    # Specify the file name using f-string
    response['Content-Disposition'] = f'attachment; filename="{fileName}"'
    
    # Use pandas to save the dataframe as an excel file in the response
    df.to_excel(response, index=False, engine='openpyxl')

    return response

#######################AI MIGAA METER DOWNLOAD####################################################
@login_required
def export_meter_data(request):
    data = fetch_data("migaaMeterDownload")

    # Convert the data to a DataFrame
    df = pd.DataFrame(data)
    # Create a HttpResponse with content_type as ms-excel
    response = HttpResponse(content_type='application/vnd.ms-excel')
    
    # Specify the file name
    response['Content-Disposition'] = 'attachment; filename="migaaMeter.csv"'

    # Use pandas to save the dataframe as an excel file in the response
    df.to_csv(response, index=False)

    return response

@login_required
def export_ml_dataset(request):
    dataset = fetch_data('getMeasurements')
    context = {
        'dataset': dataset
    }
    return render(request, 'ai_data_download.html', context)

@login_required
def export_ml(request, set):
    data = fetch_measurement_data('getMeasurementData', set)

    # Convert the data to a DataFrame
    df = pd.DataFrame(data)
    # Create a HttpResponse with content_type as ms-excel
    response = HttpResponse(content_type='application/vnd.ms-excel')
    fileName = f"{set}.csv"
    
    # Specify the file name using f-string
    response['Content-Disposition'] = f'attachment; filename="{fileName}"'

    # Use pandas to save the dataframe as an excel file in the response
    df.to_csv(response, index=False)

    return response

@login_required
def fetch_measurement_data(endpoint, q):
    response = requests.get(BASE_URL + endpoint+"?q="+q, auth=AUTH)
    response.raise_for_status()
    return response.json()


########################################################GENERAL STATS######################

def get_customer_statistics(x):
    customer_models = [Customer, TestCustomer, SayonaCustomer, MecCustomer]  # List all models
    total_customers = 0
    customers_x_days = 0

    # Calculate the date range for x days ago
    x_days_ago = now() - timedelta(days=x)

    for CustomerModel in customer_models:
        total_customers += CustomerModel.objects.count()
        customers_x_days += CustomerModel.objects.filter(date__gte=x_days_ago).count()

    return {
        "total_customers": total_customers,
        "customer_last_x_days": customers_x_days,
    }

def calculate_rar(sales_data):
    # Initialize totals
    total_overdue_risk = 0
    total_amount_due = 0
    today = now().date()
    
    for sale in sales_data:
        payment_data = sale.get("paymentData", {})
        balance = payment_data.get("balance", 0)
        days_overdue = payment_data.get("days", 0)

        # Add to total amount due
        total_amount_due += balance

        # Check if overdue by 90 days or more
        if payment_data.get("payment_status") == "overdue" and days_overdue >= 90:
            total_overdue_risk += balance

    # Avoid division by zero
    if total_amount_due == 0:
        return 0

    # Calculate RAR
    rar = (total_overdue_risk / total_amount_due) * 100
    return rar

@cache_page(60 * 60)
@login_required
def summary(request):
    customerSummary = get_customer_statistics(30)
    orgs = ['Scode', 'Welight', 'GIZ', 'Sayona', 'Mec']
    revenue_orgs = ['Powerpay Africa', 'Scode']
    revenue_accounts = ['319403', '4121691_scode']
    total_collected = 0
    total_cash_in = 0
    last_month_in = 0
    this_month_in = 0
    org_data = {}
    org_transactions = {}
    
    today = datetime.now()
    first_day_last_month = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
    last_day_last_month = first_day_last_month.replace(
        day=monthrange(first_day_last_month.year, first_day_last_month.month)[1]
    )

    for org, account in zip(revenue_orgs, revenue_accounts):
        try:
            data = fetch_data_accounts('accounts', account)
            df = pd.DataFrame(data)

            if df.empty:
                total_amount = last_30_days_amount = last_7_days_amount = last_24_hours_amount = last_month_amount = 0
            else:
                df['transtime'] = pd.to_datetime(df['transtime'], format='%Y%m%d%H%M%S')

                total_amount = df['amount'].sum()
                last_30_days_amount = df.loc[df['transtime'] >= today - timedelta(days=30), 'amount'].sum()
                last_7_days_amount = df.loc[df['transtime'] >= today - timedelta(days=7), 'amount'].sum()
                last_24_hours_amount = df.loc[df['transtime'] >= today - timedelta(hours=24), 'amount'].sum()
                last_month_amount = df.loc[
                    (df['transtime'] >= first_day_last_month) & (df['transtime'] <= last_day_last_month),
                    'amount'
                ].sum()
                total_collected += last_30_days_amount
                total_cash_in += total_amount
                last_month_in += last_month_amount

            org_transactions[org] = {
                'total_amount': total_amount,
                'last_30_days_amount': last_30_days_amount,
                'last_7_days_amount': last_7_days_amount,
                'last_24_hours_amount': last_24_hours_amount,
            }

        except Exception as e:
            org_transactions[org] = {
                'total_amount': 0,
                'last_30_days_amount': 0,
                'last_7_days_amount': 0,
                'last_24_hours_amount': 0,
            }

    for org in orgs:
        try:
            data = fetch_data_index(f"allDeviceData{org}Django", 999999999)
            df = pd.DataFrame(data['rawData'])
            runtime_sum = sum(data['runtime'].values())
            devs = len(data['allDevs'])
            meals, _ = classify_and_count_meals(df.to_dict(orient='records'))
            kwh_sum = df['kwh'].sum()
            meal_count = sum(info['count'] for device_id, info in meals.items())
            org_data[org] = {
                'runtime': runtime_sum,
                'meals': meal_count,
                'kwh': kwh_sum,
                'emissions': kwh_sum * 0.4999 * 0.28,
                'cost': kwh_sum * 23.0,
                'devs': devs,
            }
        except Exception as e:
            org_data[org] = {"runtime": 0, "meals": 0, "kwh": 0}

    total_customers = customerSummary['total_customers']
    customer_diff = customerSummary['customer_last_x_days'] - total_customers

    churn_rate = (customer_diff / total_customers) * 100 if total_customers != 0 else 0
    portfolio_growth = (
        (customerSummary['total_customers'] / customerSummary['customer_last_x_days']) * 100
        if customerSummary['customer_last_x_days'] != 0
        else 0
    )
    
    paygo_data = fetch_data('paygoScode')
    rar = calculate_rar(paygo_data)

    month_growth = ((total_collected - last_month_in) / last_month_in) * 100 if last_month_in != 0 else 0

    context = {
        'customers_today': total_customers,
        'customers_then': customerSummary['customer_last_x_days'],
        'churn_rate': churn_rate,
        'organizations': orgs,
        'org_data': org_data,
        'portfolio_growth': portfolio_growth,
        'org_transactions': org_transactions,
        'total_collected': total_cash_in,
        'accounts': revenue_accounts,
        'arpa': total_collected / len(revenue_accounts) if revenue_accounts else 0,
        'rar': rar,
        'mrr': total_collected,
        'month_growth': month_growth,
    }

    return render(request, 'summary.html', context)
