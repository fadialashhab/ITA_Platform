from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal


class Payment(models.Model):
    """Model for tracking payments made by students for course enrollments."""
    
    PAYMENT_METHOD_CHOICES = [
        ('CASH', 'Cash'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('CARD', 'Credit/Debit Card'),
        ('MOBILE_MONEY', 'Mobile Money'),
        ('CHEQUE', 'Cheque'),
        ('OTHER', 'Other'),
    ]
    
    # Relations
    enrollment = models.ForeignKey(
        'enrollments.Enrollment',
        on_delete=models.CASCADE,
        related_name='payments'
    )
    
    # Payment details
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    payment_date = models.DateField(default=timezone.now)
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='CASH'
    )
    
    # Receipt information
    receipt_number = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True
    )
    
    # Audit fields
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='received_payments'
    )
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payments_payment'
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-payment_date', '-created_at']
        indexes = [
            models.Index(fields=['enrollment', 'payment_date']),
            models.Index(fields=['payment_date']),
            models.Index(fields=['receipt_number']),
            models.Index(fields=['payment_method']),
        ]
    
    def __str__(self):
        return f"Payment {self.receipt_number or self.id} - {self.enrollment.student.get_full_name()} - ${self.amount}"
    
    def save(self, *args, **kwargs):
        """Generate receipt number and validate on save."""
        if not self.pk:  # New payment
            if not self.receipt_number:
                self.receipt_number = self.generate_receipt_number()
        
        # Run validations
        self.clean()
        super().save(*args, **kwargs)
    
    def clean(self):
        """Validate payment business rules."""
        # Check if enrollment exists
        if not self.enrollment:
            raise ValidationError({
                'enrollment': 'Payment must be linked to an enrollment.'
            })
        
        # Check if payment amount is positive
        if self.amount <= 0:
            raise ValidationError({
                'amount': 'Payment amount must be greater than zero.'
            })
        
        # Check if total payments don't exceed course price
        existing_payments = Payment.objects.filter(
            enrollment=self.enrollment
        ).exclude(pk=self.pk)
        
        total_paid = sum(p.amount for p in existing_payments) + self.amount
        course_price = self.enrollment.course.price
        
        if total_paid > course_price:
            raise ValidationError({
                'amount': f'Total payments (${total_paid}) cannot exceed course price (${course_price}).'
            })
        
        # Check if payment date is not before enrollment date
        if self.payment_date < self.enrollment.enrollment_date:
            raise ValidationError({
                'payment_date': 'Payment date cannot be before enrollment date.'
            })
        
        # Check if payment date is not in the future
        if self.payment_date > timezone.now().date():
            raise ValidationError({
                'payment_date': 'Payment date cannot be in the future.'
            })
    
    def generate_receipt_number(self):
        """Generate a unique receipt number."""
        year = timezone.now().year
        month = timezone.now().month
        
        # Count payments this month
        count = Payment.objects.filter(
            payment_date__year=year,
            payment_date__month=month
        ).count() + 1
        
        return f"RCP-{year}{month:02d}-{count:05d}"
    
    def get_student_name(self):
        """Return the student's full name."""
        return self.enrollment.student.get_full_name()
    
    def get_course_title(self):
        """Return the course title."""
        return self.enrollment.course.title
    
    def get_remaining_balance(self):
        """Calculate remaining balance after this payment."""
        total_paid = Payment.objects.filter(
            enrollment=self.enrollment,
            payment_date__lte=self.payment_date
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
        
        return self.enrollment.course.price - total_paid
    
    @classmethod
    def get_total_paid_for_enrollment(cls, enrollment):
        """Get total amount paid for an enrollment."""
        total = cls.objects.filter(
            enrollment=enrollment
        ).aggregate(
            total=models.Sum('amount')
        )['total']
        
        return total or Decimal('0.00')
    
    @classmethod
    def get_outstanding_balance(cls, enrollment):
        """Get outstanding balance for an enrollment."""
        total_paid = cls.get_total_paid_for_enrollment(enrollment)
        return enrollment.course.price - total_paid
    
    @classmethod
    def is_enrollment_fully_paid(cls, enrollment):
        """Check if enrollment is fully paid."""
        return cls.get_outstanding_balance(enrollment) <= 0
    
    @classmethod
    def get_revenue_summary(cls, start_date=None, end_date=None):
        """Get revenue summary for a date range."""
        queryset = cls.objects.all()
        
        if start_date:
            queryset = queryset.filter(payment_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(payment_date__lte=end_date)
        
        total_revenue = queryset.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
        
        payment_count = queryset.count()
        
        by_method = {}
        for method, _ in cls.PAYMENT_METHOD_CHOICES:
            method_total = queryset.filter(
                payment_method=method
            ).aggregate(
                total=models.Sum('amount')
            )['total'] or Decimal('0.00')
            
            if method_total > 0:
                by_method[method] = method_total
        
        return {
            'total_revenue': total_revenue,
            'payment_count': payment_count,
            'by_method': by_method
        }