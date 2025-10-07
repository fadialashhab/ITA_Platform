"""
Management command to generate payment reports.
Usage: python manage.py generate_payment_report --start-date 2025-01-01 --end-date 2025-12-31
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from payments.models import Payment
from payments.utils import export_payment_report_csv
from decimal import Decimal


class Command(BaseCommand):
    help = 'Generate payment reports for a specified date range'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--start-date',
            type=str,
            help='Start date in YYYY-MM-DD format'
        )
        
        parser.add_argument(
            '--end-date',
            type=str,
            help='End date in YYYY-MM-DD format'
        )
        
        parser.add_argument(
            '--output',
            type=str,
            default='payment_report.csv',
            help='Output filename for CSV report'
        )
        
        parser.add_argument(
            '--payment-method',
            type=str,
            help='Filter by payment method'
        )
    
    def handle(self, *args, **options):
        start_date_str = options['start_date']
        end_date_str = options['end_date']
        output_file = options['output']
        payment_method = options['payment_method']
        
        # Default to current month if dates not provided
        if not start_date_str:
            start_date = timezone.now().date().replace(day=1)
        else:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        
        if not end_date_str:
            end_date = timezone.now().date()
        else:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        self.stdout.write(f"Generating payment report from {start_date} to {end_date}")
        
        # Query payments
        payments = Payment.objects.filter(
            payment_date__gte=start_date,
            payment_date__lte=end_date
        ).select_related(
            'enrollment__student',
            'enrollment__course',
            'received_by'
        ).order_by('payment_date')
        
        if payment_method:
            payments = payments.filter(payment_method=payment_method)
        
        # Calculate statistics
        total_revenue = payments.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
        
        payment_count = payments.count()
        
        # Display summary
        self.stdout.write(self.style.SUCCESS(f"\nPayment Summary:"))
        self.stdout.write(f"  Total Payments: {payment_count}")
        self.stdout.write(f"  Total Revenue: ${total_revenue:,.2f}")
        
        if payment_count > 0:
            avg_payment = total_revenue / payment_count
            self.stdout.write(f"  Average Payment: ${avg_payment:,.2f}")
        
        # Export to CSV
        csv_content = export_payment_report_csv(payments, output_file)
        
        with open(output_file, 'w') as f:
            f.write(csv_content)
        
        self.stdout.write(self.style.SUCCESS(f"\nReport exported to: {output_file}"))