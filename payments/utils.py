"""
Utility functions for payment management.
"""

from decimal import Decimal
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from django.conf import settings
from datetime import timedelta


def calculate_enrollment_payment_status(enrollment):
    """
    Calculate comprehensive payment status for an enrollment.
    
    Args:
        enrollment: Enrollment instance
    
    Returns:
        dict: Payment status details
    """
    from .models import Payment
    
    course_price = enrollment.course.price
    total_paid = Payment.get_total_paid_for_enrollment(enrollment)
    outstanding = course_price - total_paid
    
    payments = Payment.objects.filter(enrollment=enrollment).order_by('payment_date')
    payment_count = payments.count()
    
    last_payment = payments.last()
    first_payment = payments.first()
    
    return {
        'course_price': course_price,
        'total_paid': total_paid,
        'outstanding_balance': max(outstanding, Decimal('0.00')),
        'is_fully_paid': outstanding <= 0,
        'payment_count': payment_count,
        'first_payment_date': first_payment.payment_date if first_payment else None,
        'last_payment_date': last_payment.payment_date if last_payment else None,
        'percentage_paid': round((total_paid / course_price * 100), 2) if course_price > 0 else 0
    }


def get_student_payment_summary(student):
    """
    Get comprehensive payment summary for a student across all enrollments.
    
    Args:
        student: User instance (student)
    
    Returns:
        dict: Student's payment summary
    """
    from enrollments.models import Enrollment
    from .models import Payment
    
    enrollments = Enrollment.objects.filter(student=student)
    
    total_course_fees = Decimal('0.00')
    total_paid = Decimal('0.00')
    fully_paid_count = 0
    partially_paid_count = 0
    unpaid_count = 0
    
    for enrollment in enrollments:
        course_price = enrollment.course.price
        total_course_fees += course_price
        
        paid = Payment.get_total_paid_for_enrollment(enrollment)
        total_paid += paid
        
        if paid >= course_price:
            fully_paid_count += 1
        elif paid > 0:
            partially_paid_count += 1
        else:
            unpaid_count += 1
    
    return {
        'total_enrollments': enrollments.count(),
        'total_course_fees': total_course_fees,
        'total_paid': total_paid,
        'total_outstanding': total_course_fees - total_paid,
        'fully_paid_enrollments': fully_paid_count,
        'partially_paid_enrollments': partially_paid_count,
        'unpaid_enrollments': unpaid_count
    }


def generate_payment_receipt_data(payment):
    """
    Generate data for payment receipt.
    
    Args:
        payment: Payment instance
    
    Returns:
        dict: Receipt data
    """
    enrollment = payment.enrollment
    remaining_balance = payment.get_remaining_balance()
    
    from .models import Payment
    total_paid = Payment.get_total_paid_for_enrollment(enrollment)
    
    return {
        'receipt_number': payment.receipt_number,
        'payment_date': payment.payment_date,
        'payment_method': payment.get_payment_method_display(),
        'amount': payment.amount,
        'student_name': enrollment.student.get_full_name(),
        'student_email': enrollment.student.email,
        'student_phone': enrollment.student.phone_number,
        'course_title': enrollment.course.title,
        'course_price': enrollment.course.price,
        'total_paid': total_paid,
        'remaining_balance': remaining_balance,
        'received_by': payment.received_by.get_full_name() if payment.received_by else 'N/A',
        'notes': payment.notes
    }


def get_revenue_by_period(start_date, end_date, group_by='day'):
    """
    Get revenue grouped by time period.
    
    Args:
        start_date: Start date
        end_date: End date
        group_by: 'day', 'week', 'month', or 'year'
    
    Returns:
        list: Revenue data grouped by period
    """
    from .models import Payment
    from django.db.models.functions import TruncMonth, TruncDay
    
    payments = Payment.objects.filter(
        payment_date__gte=start_date,
        payment_date__lte=end_date
    )
    
    if group_by == 'day':
        revenue_data = []
        current_date = start_date
        while current_date <= end_date:
            daily_revenue = payments.filter(
                payment_date=current_date
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            revenue_data.append({
                'date': current_date,
                'revenue': daily_revenue,
                'payment_count': payments.filter(payment_date=current_date).count()
            })
            current_date += timedelta(days=1)
        
        return revenue_data
    
    elif group_by == 'month':
        revenue_data = payments.annotate(
            month=TruncMonth('payment_date')
        ).values('month').annotate(
            revenue=Sum('amount'),
            payment_count=Count('id')
        ).order_by('month')
        
        return list(revenue_data)
    
    else:
        return []


def get_overdue_payments(days_threshold=30):
    """
    Get enrollments with outstanding payments that are overdue.
    
    Args:
        days_threshold: Number of days since enrollment to consider overdue
    
    Returns:
        list: Overdue payment information
    """
    from enrollments.models import Enrollment
    from .models import Payment
    
    threshold_date = timezone.now().date() - timedelta(days=days_threshold)
    
    # Get enrollments older than threshold with outstanding balance
    enrollments = Enrollment.objects.filter(
        enrollment_date__lte=threshold_date,
        status__in=['IN_PROGRESS', 'COMPLETED']
    ).select_related('student', 'course')
    
    overdue_list = []
    
    for enrollment in enrollments:
        outstanding = Payment.get_outstanding_balance(enrollment)
        
        if outstanding > 0:
            days_overdue = (timezone.now().date() - enrollment.enrollment_date).days
            
            overdue_list.append({
                'enrollment': enrollment,
                'student': enrollment.student,
                'course': enrollment.course,
                'outstanding_balance': outstanding,
                'days_overdue': days_overdue,
                'enrollment_date': enrollment.enrollment_date
            })
    
    return overdue_list


def calculate_payment_plan(course_price, num_installments):
    """
    Calculate equal payment installments for a course.
    
    Args:
        course_price: Total course price
        num_installments: Number of installments
    
    Returns:
        list: Installment amounts
    """
    if num_installments <= 0:
        return []
    
    installment_amount = course_price / num_installments
    installments = [installment_amount] * num_installments
    
    # Adjust last installment for rounding differences
    total_calculated = sum(installments)
    difference = course_price - total_calculated
    if difference != 0:
        installments[-1] += difference
    
    return installments


def validate_payment_amount(enrollment, amount):
    """
    Validate if a payment amount is acceptable for an enrollment.
    
    Args:
        enrollment: Enrollment instance
        amount: Payment amount to validate
    
    Returns:
        tuple: (is_valid, error_message)
    """
    from .models import Payment
    
    if amount <= 0:
        return False, "Payment amount must be greater than zero"
    
    outstanding = Payment.get_outstanding_balance(enrollment)
    
    if amount > outstanding:
        return False, f"Payment amount (${amount}) exceeds outstanding balance (${outstanding})"
    
    return True, None


def get_payment_statistics(start_date=None, end_date=None):
    """
    Get comprehensive payment statistics for a date range.
    
    Args:
        start_date: Start date (optional)
        end_date: End date (optional)
    
    Returns:
        dict: Payment statistics
    """
    from .models import Payment
    
    queryset = Payment.objects.all()
    
    if start_date:
        queryset = queryset.filter(payment_date__gte=start_date)
    if end_date:
        queryset = queryset.filter(payment_date__lte=end_date)
    
    stats = queryset.aggregate(
        total_revenue=Sum('amount'),
        payment_count=Count('id'),
        average_payment=Avg('amount')
    )
    
    # Revenue by payment method
    by_method = {}
    for method, _ in Payment.PAYMENT_METHOD_CHOICES:
        method_total = queryset.filter(
            payment_method=method
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        if method_total > 0:
            by_method[method] = method_total
    
    return {
        'total_revenue': stats['total_revenue'] or Decimal('0.00'),
        'payment_count': stats['payment_count'],
        'average_payment': stats['average_payment'] or Decimal('0.00'),
        'by_method': by_method
    }


def send_payment_confirmation_email(payment):
    """
    Send payment confirmation email to student (placeholder).
    
    Args:
        payment: Payment instance
    
    Returns:
        bool: Success status
    """
    # TODO: Implement email sending logic
    # This is a placeholder for future implementation
    
    student = payment.enrollment.student
    subject = f"Payment Confirmation - Receipt #{payment.receipt_number}"
    
    message = f"""
    Dear {student.get_full_name()},
    
    This confirms your payment of ${payment.amount} for {payment.enrollment.course.title}.
    
    Receipt Number: {payment.receipt_number}
    Payment Date: {payment.payment_date}
    Payment Method: {payment.get_payment_method_display()}
    
    Remaining Balance: ${payment.get_remaining_balance()}
    
    Thank you for your payment.
    """
    
    # In production, use Django's send_mail or email backend
    # from django.core.mail import send_mail
    # send_mail(subject, message, 'from@example.com', [student.email])
    
    return True


def send_payment_reminder_email(enrollment):
    """
    Send payment reminder email to student with outstanding balance (placeholder).
    
    Args:
        enrollment: Enrollment instance
    
    Returns:
        bool: Success status
    """
    from .models import Payment
    
    outstanding = Payment.get_outstanding_balance(enrollment)
    
    if outstanding <= 0:
        return False
    
    student = enrollment.student
    subject = f"Payment Reminder - {enrollment.course.title}"
    
    message = f"""
    Dear {student.get_full_name()},
    
    This is a reminder about your outstanding balance for {enrollment.course.title}.
    
    Course Price: ${enrollment.course.price}
    Amount Paid: ${Payment.get_total_paid_for_enrollment(enrollment)}
    Outstanding Balance: ${outstanding}
    
    Please make a payment at your earliest convenience.
    
    Thank you.
    """
    
    # In production, use Django's send_mail or email backend
    # from django.core.mail import send_mail
    # send_mail(subject, message, 'from@example.com', [student.email])
    
    return True


def export_payment_report_csv(payments, filename='payment_report.csv'):
    """
    Export payment data to CSV format.
    
    Args:
        payments: QuerySet of Payment objects
        filename: Output filename
    
    Returns:
        str: CSV content
    """
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Write headers
    writer.writerow([
        'Receipt Number',
        'Student Name',
        'Student Email',
        'Course Title',
        'Amount',
        'Payment Date',
        'Payment Method',
        'Received By',
        'Notes'
    ])
    
    # Write data
    for payment in payments:
        writer.writerow([
            payment.receipt_number,
            payment.get_student_name(),
            payment.enrollment.student.email,
            payment.get_course_title(),
            payment.amount,
            payment.payment_date,
            payment.get_payment_method_display(),
            payment.received_by.get_full_name() if payment.received_by else 'N/A',
            payment.notes
        ])
    
    return output.getvalue()


def bulk_payment_validation(payment_data_list):
    """
    Validate multiple payments before bulk creation.
    
    Args:
        payment_data_list: List of payment data dictionaries
    
    Returns:
        tuple: (is_valid, errors_list)
    """
    from enrollments.models import Enrollment
    from .models import Payment
    
    errors = []
    
    for i, payment_data in enumerate(payment_data_list):
        # Validate required fields
        required_fields = ['enrollment_id', 'amount', 'payment_method']
        for field in required_fields:
            if field not in payment_data:
                errors.append({
                    'index': i,
                    'error': f"Missing required field: {field}"
                })
                continue
        
        # Validate enrollment exists
        try:
            enrollment = Enrollment.objects.get(id=payment_data['enrollment_id'])
        except Enrollment.DoesNotExist:
            errors.append({
                'index': i,
                'error': f"Enrollment {payment_data['enrollment_id']} does not exist"
            })
            continue
        
        # Validate amount
        try:
            amount = Decimal(str(payment_data['amount']))
            if amount <= 0:
                errors.append({
                    'index': i,
                    'error': "Payment amount must be greater than zero"
                })
                continue
        except (ValueError, TypeError):
            errors.append({
                'index': i,
                'error': "Invalid amount format"
            })
            continue
        
        # Validate doesn't exceed outstanding balance
        outstanding = Payment.get_outstanding_balance(enrollment)
        if amount > outstanding:
            errors.append({
                'index': i,
                'error': f"Amount ${amount} exceeds outstanding balance ${outstanding}"
            })
    
    return len(errors) == 0, errors


def generate_receipt_pdf(payment):
    """
    Generate a PDF receipt for a payment using ReportLab.
    
    Args:
        payment: Payment instance
    
    Returns:
        ContentFile: PDF file content
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import inch
        from reportlab.pdfgen import canvas
        from reportlab.platypus import Table, TableStyle
        from reportlab.lib import colors
        from io import BytesIO
        from django.core.files.base import ContentFile
    except ImportError:
        # ReportLab not installed
        return None
    
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Get receipt data
    receipt_data = generate_payment_receipt_data(payment)
    
    # Header
    p.setFont("Helvetica-Bold", 20)
    p.drawCentredString(width/2, height - 1*inch, "PAYMENT RECEIPT")
    
    # Institution info
    p.setFont("Helvetica", 10)
    institution_name = getattr(settings, 'INSTITUTION_NAME', 'Institute Name')
    p.drawCentredString(width/2, height - 1.3*inch, institution_name)
    
    # Receipt number and date
    p.setFont("Helvetica-Bold", 12)
    p.drawString(1*inch, height - 2*inch, f"Receipt No: {receipt_data['receipt_number']}")
    p.drawRightString(width - 1*inch, height - 2*inch, f"Date: {receipt_data['payment_date'].strftime('%B %d, %Y')}")
    
    # Line separator
    p.setStrokeColorRGB(0.5, 0.5, 0.5)
    p.line(1*inch, height - 2.2*inch, width - 1*inch, height - 2.2*inch)
    
    # Student information
    y_position = height - 2.8*inch
    p.setFont("Helvetica-Bold", 11)
    p.drawString(1*inch, y_position, "Student Information:")
    
    p.setFont("Helvetica", 10)
    y_position -= 0.3*inch
    p.drawString(1.2*inch, y_position, f"Name: {receipt_data['student_name']}")
    y_position -= 0.25*inch
    p.drawString(1.2*inch, y_position, f"Email: {receipt_data['student_email']}")
    if receipt_data['student_phone']:
        y_position -= 0.25*inch
        p.drawString(1.2*inch, y_position, f"Phone: {receipt_data['student_phone']}")
    
    # Course information
    y_position -= 0.5*inch
    p.setFont("Helvetica-Bold", 11)
    p.drawString(1*inch, y_position, "Course Information:")
    
    p.setFont("Helvetica", 10)
    y_position -= 0.3*inch
    p.drawString(1.2*inch, y_position, f"Course: {receipt_data['course_title']}")
    y_position -= 0.25*inch
    p.drawString(1.2*inch, y_position, f"Course Fee: ${receipt_data['course_price']:,.2f}")
    
    # Payment details table
    y_position -= 0.7*inch
    p.setFont("Helvetica-Bold", 11)
    p.drawString(1*inch, y_position, "Payment Details:")
    
    y_position -= 0.4*inch
    
    # Create payment details table
    data = [
        ['Description', 'Amount'],
        ['Payment Method', receipt_data['payment_method']],
        ['Amount Paid', f"${receipt_data['amount']:,.2f}"],
        ['Total Paid to Date', f"${receipt_data['total_paid']:,.2f}"],
        ['Remaining Balance', f"${receipt_data['remaining_balance']:,.2f}"]
    ]
    
    table = Table(data, colWidths=[3*inch, 2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    # Draw table
    table.wrapOn(p, width, height)
    table.drawOn(p, 1*inch, y_position - 1.5*inch)
    
    # Notes
    if receipt_data['notes']:
        y_position -= 2.2*inch
        p.setFont("Helvetica-Bold", 10)
        p.drawString(1*inch, y_position, "Notes:")
        p.setFont("Helvetica", 9)
        y_position -= 0.2*inch
        notes = receipt_data['notes'][:200]
        p.drawString(1.2*inch, y_position, notes)
    
    # Footer
    p.setFont("Helvetica-Italic", 9)
    p.drawString(1*inch, 1.5*inch, f"Received by: {receipt_data['received_by']}")
    
    p.setFont("Helvetica", 8)
    p.drawCentredString(width/2, 1*inch, "Thank you for your payment!")
    p.drawCentredString(width/2, 0.7*inch, "This is a computer-generated receipt.")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    filename = f"receipt_{receipt_data['receipt_number']}.pdf"
    return ContentFile(buffer.read(), name=filename)


def get_payment_trends(days=30):
    """
    Get payment trends for the specified number of days.
    
    Args:
        days: Number of days to analyze
    
    Returns:
        dict: Trend analysis data
    """
    from .models import Payment
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    payments = Payment.objects.filter(
        payment_date__gte=start_date,
        payment_date__lte=end_date
    )
    
    # Daily payment count
    daily_counts = {}
    current_date = start_date
    while current_date <= end_date:
        count = payments.filter(payment_date=current_date).count()
        daily_counts[current_date.strftime('%Y-%m-%d')] = count
        current_date += timedelta(days=1)
    
    # Calculate trend
    total_payments = payments.count()
    avg_per_day = total_payments / days if days > 0 else 0
    
    # Compare first half vs second half
    mid_date = start_date + timedelta(days=days//2)
    first_half = payments.filter(payment_date__lt=mid_date).count()
    second_half = payments.filter(payment_date__gte=mid_date).count()
    
    trend = 'increasing' if second_half > first_half else 'decreasing' if second_half < first_half else 'stable'
    
    return {
        'period_days': days,
        'total_payments': total_payments,
        'average_per_day': round(avg_per_day, 2),
        'first_half_count': first_half,
        'second_half_count': second_half,
        'trend': trend,
        'daily_counts': daily_counts
    }


def get_payment_completion_rate():
    """
    Calculate the payment completion rate across all enrollments.
    
    Returns:
        dict: Completion rate statistics
    """
    from enrollments.models import Enrollment
    from .models import Payment
    
    all_enrollments = Enrollment.objects.filter(
        status__in=['IN_PROGRESS', 'COMPLETED']
    )
    
    total_enrollments = all_enrollments.count()
    if total_enrollments == 0:
        return {
            'total_enrollments': 0,
            'fully_paid': 0,
            'partially_paid': 0,
            'unpaid': 0,
            'completion_rate': 0.0
        }
    
    fully_paid = 0
    partially_paid = 0
    unpaid = 0
    
    for enrollment in all_enrollments:
        total_paid = Payment.get_total_paid_for_enrollment(enrollment)
        course_price = enrollment.course.price
        
        if total_paid >= course_price:
            fully_paid += 1
        elif total_paid > 0:
            partially_paid += 1
        else:
            unpaid += 1
    
    completion_rate = (fully_paid / total_enrollments) * 100
    
    return {
        'total_enrollments': total_enrollments,
        'fully_paid': fully_paid,
        'partially_paid': partially_paid,
        'unpaid': unpaid,
        'completion_rate': round(completion_rate, 2)
    }


def reconcile_enrollment_payments(enrollment):
    """
    Reconcile and verify all payments for an enrollment.
    
    Args:
        enrollment: Enrollment instance
    
    Returns:
        dict: Reconciliation report
    """
    from .models import Payment
    
    payments = Payment.objects.filter(enrollment=enrollment).order_by('payment_date')
    
    course_price = enrollment.course.price
    total_paid = sum(p.amount for p in payments)
    outstanding = course_price - total_paid
    
    payment_details = []
    running_balance = course_price
    
    for payment in payments:
        running_balance -= payment.amount
        payment_details.append({
            'receipt_number': payment.receipt_number,
            'date': payment.payment_date,
            'amount': payment.amount,
            'method': payment.get_payment_method_display(),
            'balance_after': running_balance
        })
    
    is_reconciled = abs(outstanding - running_balance) < Decimal('0.01')
    
    return {
        'enrollment_id': enrollment.id,
        'student': enrollment.student.get_full_name(),
        'course': enrollment.course.title,
        'course_price': course_price,
        'total_paid': total_paid,
        'outstanding': outstanding,
        'payment_count': payments.count(),
        'payments': payment_details,
        'is_reconciled': is_reconciled,
        'discrepancy': Decimal('0.00') if is_reconciled else outstanding - running_balance
    }


def get_payment_method_statistics():
    """
    Get detailed statistics for each payment method.
    
    Returns:
        list: Statistics per payment method
    """
    from .models import Payment
    
    method_stats = []
    
    for method_code, method_name in Payment.PAYMENT_METHOD_CHOICES:
        payments = Payment.objects.filter(payment_method=method_code)
        
        if payments.exists():
            stats = payments.aggregate(
                total_revenue=Sum('amount'),
                payment_count=Count('id'),
                average_payment=Avg('amount')
            )
            
            method_stats.append({
                'method_code': method_code,
                'method_name': method_name,
                'total_revenue': stats['total_revenue'],
                'payment_count': stats['payment_count'],
                'average_payment': stats['average_payment'],
                'percentage_of_total': 0
            })
    
    # Calculate percentages
    total_revenue = sum(m['total_revenue'] for m in method_stats)
    if total_revenue > 0:
        for method in method_stats:
            method['percentage_of_total'] = round(
                (method['total_revenue'] / total_revenue) * 100, 2
            )
    
    # Sort by total revenue
    method_stats.sort(key=lambda x: x['total_revenue'], reverse=True)
    
    return method_stats


def generate_payment_aging_report():
    """
    Generate an aging report for outstanding payments.
    
    Returns:
        dict: Aging report with categorized outstanding balances
    """
    from enrollments.models import Enrollment
    from .models import Payment
    
    today = timezone.now().date()
    
    aging_categories = {
        'current': [],
        '31_60': [],
        '61_90': [],
        'over_90': []
    }
    
    enrollments = Enrollment.objects.filter(
        status__in=['IN_PROGRESS', 'COMPLETED']
    ).select_related('student', 'course')
    
    for enrollment in enrollments:
        outstanding = Payment.get_outstanding_balance(enrollment)
        
        if outstanding > 0:
            days_outstanding = (today - enrollment.enrollment_date).days
            
            item = {
                'enrollment_id': enrollment.id,
                'student_name': enrollment.student.get_full_name(),
                'course_title': enrollment.course.title,
                'outstanding_balance': float(outstanding),
                'days_outstanding': days_outstanding,
                'enrollment_date': enrollment.enrollment_date
            }
            
            if days_outstanding <= 30:
                aging_categories['current'].append(item)
            elif days_outstanding <= 60:
                aging_categories['31_60'].append(item)
            elif days_outstanding <= 90:
                aging_categories['61_90'].append(item)
            else:
                aging_categories['over_90'].append(item)
    
    # Calculate totals
    totals = {}
    for category, items in aging_categories.items():
        totals[category] = sum(item['outstanding_balance'] for item in items)
    
    return {
        'report_date': today,
        'aging_categories': aging_categories,
        'totals_by_category': totals,
        'grand_total': sum(totals.values()),
        'total_outstanding_accounts': sum(len(items) for items in aging_categories.values())
    }