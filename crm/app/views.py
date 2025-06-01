from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from .models import Customer, Product, Order, OrderItem
from .forms import CustomerForm, ProductForm, OrderForm
import json
from datetime import datetime, timedelta
from decimal import Decimal

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    # Get statistics
    total_customers = Customer.objects.count()
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    total_revenue = Order.objects.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    # Recent orders
    recent_orders = Order.objects.select_related('customer').order_by('-created_at')[:5]
    
    # Monthly sales data for chart
    monthly_sales = []
    for i in range(12):
        month_start = datetime.now().replace(day=1) - timedelta(days=30*i)
        month_end = month_start + timedelta(days=30)
        sales = Order.objects.filter(
            order_date__gte=month_start,
            order_date__lt=month_end
        ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        monthly_sales.append({
            'month': month_start.strftime('%b'),
            'sales': float(sales)
        })
    
    monthly_sales.reverse()
    
    # Low stock products
    low_stock_products = Product.objects.filter(stock_quantity__lt=10).count()
    
    # Pending orders
    pending_orders = Order.objects.filter(status='pending').count()
    
    context = {
        'total_customers': total_customers,
        'total_products': total_products,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
        'monthly_sales': json.dumps(monthly_sales),
        'low_stock_products': low_stock_products,
        'pending_orders': pending_orders,
    }
    return render(request, 'crm/dashboard.html', context)

# Customer Views
@login_required
def customer_list(request):
    search_query = request.GET.get('search', '')
    customer_type = request.GET.get('type', '')
    
    customers = Customer.objects.all()
    
    if search_query:
        customers = customers.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    if customer_type:
        customers = customers.filter(customer_type=customer_type)
    
    customers = customers.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(customers, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'customers': page_obj,
        'search_query': search_query,
        'customer_type': customer_type,
        'customer_types': Customer.CUSTOMER_TYPES,
    }
    return render(request, 'crm/customer_list.html', context)

@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    orders = Order.objects.filter(customer=customer).order_by('-created_at')[:5]
    total_orders = Order.objects.filter(customer=customer).count()
    total_spent = Order.objects.filter(customer=customer).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    context = {
        'customer': customer,
        'orders': orders,
        'total_orders': total_orders,
        'total_spent': total_spent,
    }
    return render(request, 'crm/customer_detail.html', context)

@login_required
def customer_create(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Customer created successfully!')
            return redirect('customer_list')
    else:
        form = CustomerForm()
    return render(request, 'crm/customer_form.html', {'form': form, 'title': 'Add Customer'})

@login_required
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Customer updated successfully!')
            return redirect('customer_list')
    else:
        form = CustomerForm(instance=customer)
    return render(request, 'crm/customer_form.html', {'form': form, 'title': 'Edit Customer'})

@login_required
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        customer.delete()
        messages.success(request, 'Customer deleted successfully!')
        return redirect('customer_list')
    return render(request, 'crm/customer_confirm_delete.html', {'customer': customer})

# Product Views
@login_required
def product_list(request):
    search_query = request.GET.get('search', '')
    category = request.GET.get('category', '')
    
    products = Product.objects.all()
    
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    if category:
        products = products.filter(category=category)
    
    products = products.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(products, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'products': page_obj,
        'search_query': search_query,
        'category': category,
        'categories': Product.CATEGORY_CHOICES,
    }
    return render(request, 'crm/product_list.html', context)

@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    recent_orders = OrderItem.objects.filter(product=product).select_related('order', 'order__customer').order_by('-order__created_at')[:5]
    total_sold = OrderItem.objects.filter(product=product).aggregate(Sum('quantity'))['quantity__sum'] or 0
    
    context = {
        'product': product,
        'recent_orders': recent_orders,
        'total_sold': total_sold,
    }
    return render(request, 'crm/product_detail.html', context)

@login_required
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product created successfully!')
            return redirect('product_list')
    else:
        form = ProductForm()
    return render(request, 'crm/product_form.html', {'form': form, 'title': 'Add Product'})

@login_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'crm/product_form.html', {'form': form, 'title': 'Edit Product'})

@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully!')
        return redirect('product_list')
    return render(request, 'crm/product_confirm_delete.html', {'product': product})

# Order Views
@login_required
def order_list(request):
    search_query = request.GET.get('search', '')
    status = request.GET.get('status', '')
    
    orders = Order.objects.select_related('customer')
    
    if search_query:
        orders = orders.filter(
            Q(customer__first_name__icontains=search_query) |
            Q(customer__last_name__icontains=search_query) |
            Q(customer__email__icontains=search_query) |
            Q(id__icontains=search_query)
        )
    
    if status:
        orders = orders.filter(status=status)
    
    orders = orders.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'orders': page_obj,
        'search_query': search_query,
        'status': status,
        'statuses': Order.STATUS_CHOICES,
    }
    return render(request, 'crm/order_list.html', context)

@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    return render(request, 'crm/order_detail.html', {'order': order})

# Add this to your existing views.py file

@login_required
def order_create(request):
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.total_amount = Decimal('0.00')
            order.save()
            
            # Process order items
            items_data = {}
            for key, value in request.POST.items():
                if key.startswith('items['):
                    # Parse items[0][product_id] format
                    parts = key.replace('items[', '').replace(']', '').split('[')
                    if len(parts) == 2:
                        index = parts[0]
                        field = parts[1]
                        
                        if index not in items_data:
                            items_data[index] = {}
                        items_data[index][field] = value
            
            total_amount = Decimal('0.00')
            
            # Create order items
            for item_data in items_data.values():
                if all(key in item_data for key in ['product_id', 'quantity', 'price']):
                    product = Product.objects.get(id=item_data['product_id'])
                    quantity = int(item_data['quantity'])
                    price = Decimal(item_data['price'])
                    
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=quantity,
                        price=price
                    )
                    
                    total_amount += price * quantity
            
            # Update order total
            order.total_amount = total_amount
            order.save()
            
            messages.success(request, 'Order created successfully!')
            return redirect('order_detail', pk=order.pk)
    else:
        form = OrderForm()
    
    products = Product.objects.filter(stock_quantity__gt=0).order_by('name')
    
    context = {
        'form': form,
        'title': 'Create Order',
        'products': products
    }
    return render(request, 'crm/order_form.html', context)

@login_required
def order_edit(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            order = form.save(commit=False)
            
            # Delete existing order items
            order.orderitem_set.all().delete()
            
            # Process new order items (same logic as create)
            items_data = {}
            for key, value in request.POST.items():
                if key.startswith('items['):
                    parts = key.replace('items[', '').replace(']', '').split('[')
                    if len(parts) == 2:
                        index = parts[0]
                        field = parts[1]
                        
                        if index not in items_data:
                            items_data[index] = {}
                        items_data[index][field] = value
            
            total_amount = Decimal('0.00')
            
            for item_data in items_data.values():
                if all(key in item_data for key in ['product_id', 'quantity', 'price']):
                    product = Product.objects.get(id=item_data['product_id'])
                    quantity = int(item_data['quantity'])
                    price = Decimal(item_data['price'])
                    
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=quantity,
                        price=price
                    )
                    
                    total_amount += price * quantity
            
            order.total_amount = total_amount
            order.save()
            
            messages.success(request, 'Order updated successfully!')
            return redirect('order_detail', pk=order.pk)
    else:
        form = OrderForm(instance=order)
    
    products = Product.objects.filter(stock_quantity__gt=0).order_by('name')
    
    context = {
        'form': form,
        'title': 'Edit Order',
        'products': products,
        'order': order
    }
    return render(request, 'crm/order_form.html', context)

@login_required
def order_delete(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        order.delete()
        messages.success(request, 'Order deleted successfully!')
        return redirect('order_list')
    return render(request, 'crm/order_confirm_delete.html', {'order': order})

@login_required
def analytics(request):
    # Sales by month
    monthly_data = []
    for i in range(12):
        month_start = datetime.now().replace(day=1) - timedelta(days=30*i)
        month_end = month_start + timedelta(days=30)
        sales = Order.objects.filter(
            order_date__gte=month_start,
            order_date__lt=month_end
        ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        monthly_data.append({
            'month': month_start.strftime('%b %Y'),
            'sales': float(sales)
        })
    
    monthly_data.reverse()
    
    # Product categories
    category_data = []
    for category, label in Product.CATEGORY_CHOICES:
        count = Product.objects.filter(category=category).count()
        if count > 0:
            category_data.append({
                'category': label,
                'count': count
            })
    
    # Order status distribution
    status_data = []
    for status, label in Order.STATUS_CHOICES:
        count = Order.objects.filter(status=status).count()
        if count > 0:
            status_data.append({
                'status': label,
                'count': count
            })
    
    # Top customers
    top_customers = Customer.objects.annotate(
        total_spent=Sum('order__total_amount'),
        order_count=Count('order')
    ).filter(total_spent__isnull=False).order_by('-total_spent')[:5]
    
    # Top products
    top_products = Product.objects.annotate(
        total_sold=Sum('orderitem__quantity')
    ).filter(total_sold__isnull=False).order_by('-total_sold')[:5]
    
    context = {
        'monthly_sales': json.dumps(monthly_data),
        'category_data': json.dumps(category_data),
        'status_data': json.dumps(status_data),
        'top_customers': top_customers,
        'top_products': top_products,
    }
    return render(request, 'crm/analytics.html', context)

@login_required
def reports(request):
    # Date range filter
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    orders = Order.objects.all()
    
    if start_date:
        orders = orders.filter(order_date__gte=start_date)
    if end_date:
        orders = orders.filter(order_date__lte=end_date)
    
    # Summary statistics
    total_revenue = orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_orders = orders.count()
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    # Orders by status
    orders_by_status = orders.values('status').annotate(count=Count('id'))
    
    context = {
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'avg_order_value': avg_order_value,
        'orders_by_status': orders_by_status,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'crm/reports.html', context)

# API Views for AJAX requests
@login_required
def api_dashboard_stats(request):
    stats = {
        'customers': Customer.objects.count(),
        'products': Product.objects.count(),
        'orders': Order.objects.count(),
        'revenue': float(Order.objects.aggregate(Sum('total_amount'))['total_amount__sum'] or 0),
    }
    return JsonResponse(stats)

@login_required
def api_low_stock_products(request):
    products = Product.objects.filter(stock_quantity__lt=10).values(
        'id', 'name', 'stock_quantity'
    )
    return JsonResponse(list(products), safe=False)

@login_required
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Product "{product.name}" created successfully!')
            return redirect('product_list')
    else:
        form = ProductForm()
    
    context = {
        'form': form,
        'title': 'Add Product'
    }
    return render(request, 'crm/product_form.html', context)