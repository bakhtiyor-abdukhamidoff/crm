from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from crm.models import Customer, Product, Order, OrderItem
from decimal import Decimal
import random
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Create sample data for the CRM system'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')

        # Create sample customers
        customers_data = [
            {
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john.doe@example.com',
                'phone': '+1-555-0101',
                'address': '123 Main St, New York, NY 10001',
                'customer_type': 'individual'
            },
            {
                'first_name': 'Jane',
                'last_name': 'Smith',
                'email': 'jane.smith@example.com',
                'phone': '+1-555-0102',
                'address': '456 Oak Ave, Los Angeles, CA 90210',
                'customer_type': 'individual'
            },
            {
                'first_name': 'Acme',
                'last_name': 'Corporation',
                'email': 'contact@acme.com',
                'phone': '+1-555-0103',
                'address': '789 Business Blvd, Chicago, IL 60601',
                'customer_type': 'business'
            },
            {
                'first_name': 'Tech',
                'last_name': 'Solutions Inc',
                'email': 'info@techsolutions.com',
                'phone': '+1-555-0104',
                'address': '321 Innovation Dr, San Francisco, CA 94105',
                'customer_type': 'business'
            },
            {
                'first_name': 'Sarah',
                'last_name': 'Johnson',
                'email': 'sarah.johnson@example.com',
                'phone': '+1-555-0105',
                'address': '654 Pine St, Seattle, WA 98101',
                'customer_type': 'individual'
            }
        ]

        for customer_data in customers_data:
            customer, created = Customer.objects.get_or_create(
                email=customer_data['email'],
                defaults=customer_data
            )
            if created:
                self.stdout.write(f'Created customer: {customer.full_name}')

        # Create sample products
        products_data = [
            {
                'name': 'Wireless Headphones',
                'description': 'High-quality wireless headphones with noise cancellation',
                'price': Decimal('199.99'),
                'category': 'electronics',
                'stock_quantity': 50
            },
            {
                'name': 'Cotton T-Shirt',
                'description': 'Comfortable 100% cotton t-shirt in various colors',
                'price': Decimal('29.99'),
                'category': 'clothing',
                'stock_quantity': 100
            },
            {
                'name': 'Programming Book',
                'description': 'Learn Python programming from scratch',
                'price': Decimal('49.99'),
                'category': 'books',
                'stock_quantity': 25
            },
            {
                'name': 'Garden Tools Set',
                'description': 'Complete set of essential garden tools',
                'price': Decimal('89.99'),
                'category': 'home',
                'stock_quantity': 30
            },
            {
                'name': 'Running Shoes',
                'description': 'Professional running shoes for athletes',
                'price': Decimal('129.99'),
                'category': 'sports',
                'stock_quantity': 75
            },
            {
                'name': 'Smartphone Case',
                'description': 'Protective case for smartphones',
                'price': Decimal('24.99'),
                'category': 'electronics',
                'stock_quantity': 8  # Low stock for testing
            },
            {
                'name': 'Coffee Mug',
                'description': 'Ceramic coffee mug with custom design',
                'price': Decimal('14.99'),
                'category': 'other',
                'stock_quantity': 60
            }
        ]

        for product_data in products_data:
            product, created = Product.objects.get_or_create(
                name=product_data['name'],
                defaults=product_data
            )
            if created:
                self.stdout.write(f'Created product: {product.name}')

        # Create sample orders
        customers = Customer.objects.all()
        products = Product.objects.all()
        statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']

        for i in range(20):
            customer = random.choice(customers)
            status = random.choice(statuses)
            
            # Create order with random date in the last 6 months
            order_date = datetime.now() - timedelta(days=random.randint(1, 180))
            
            order = Order.objects.create(
                customer=customer,
                status=status,
                order_date=order_date,
                total_amount=Decimal('0.00')
            )

            # Add random products to the order
            num_items = random.randint(1, 4)
            total_amount = Decimal('0.00')
            
            for _ in range(num_items):
                product = random.choice(products)
                quantity = random.randint(1, 3)
                price = product.price
                
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=price
                )
                
                total_amount += price * quantity

            order.total_amount = total_amount
            order.save()
            
            self.stdout.write(f'Created order #{order.id} for {customer.full_name}')

        # Create superuser if it doesn't exist
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123'
            )
            self.stdout.write('Created superuser: admin/admin123')

        self.stdout.write(
            self.style.SUCCESS('Successfully created sample data!')
        )
        self.stdout.write('You can now login with username: admin, password: admin123')