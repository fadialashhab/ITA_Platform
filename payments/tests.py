from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from django.core.exceptions import ValidationError

from accounts.models import User
from courses.models import Course, Category
from enrollments.models import Enrollment
from .models import Payment


class PaymentModelTest(TestCase):
    """Test cases for Payment model."""
    
    def setUp(self):
        """Set up test data."""
        # Create users
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            first_name='Admin',
            last_name='User',
            role='ADMIN'
        )
        
        self.finance_staff = User.objects.create_user(
            username='finance',
            email='finance@test.com',
            password='testpass123',
            first_name='Finance',
            last_name='Staff',
            role='FINANCE'
        )
        
        self.student = User.objects.create_user(
            username='student',
            email='student@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Student',
            role='STUDENT'
        )
        
        # Create category and course
        self.category = Category.objects.create(
            name='Programming',
            description='Programming courses'
        )
        
        self.course = Course.objects.create(
            title='Python Basics',
            description='Learn Python programming',
            duration=40,
            price=Decimal('1000.00'),
            level='BEGINNER',
            category=self.category,
            created_by=self.admin
        )
        
        # Create enrollment
        self.enrollment = Enrollment.objects.create(
            student=self.student,
            course=self.course,
            enrollment_date=timezone.now().date()
        )
    
    def test_payment_creation(self):
        """Test creating a valid payment."""
        payment = Payment.objects.create(
            enrollment=self.enrollment,
            amount=Decimal('500.00'),
            payment_method='CASH',
            received_by=self.finance_staff
        )
        
        self.assertIsNotNone(payment.receipt_number)
        self.assertEqual(payment.amount, Decimal('500.00'))
        self.assertEqual(payment.enrollment, self.enrollment)
    
    def test_receipt_number_generation(self):
        """Test automatic receipt number generation."""
        payment = Payment.objects.create(
            enrollment=self.enrollment,
            amount=Decimal('500.00'),
            payment_method='CASH',
            received_by=self.finance_staff
        )
        
        self.assertTrue(payment.receipt_number.startswith('RCP-'))
    
    def test_payment_exceeds_course_price(self):
        """Test that payment cannot exceed course price."""
        # First payment
        Payment.objects.create(
            enrollment=self.enrollment,
            amount=Decimal('800.00'),
            payment_method='CASH',
            received_by=self.finance_staff
        )
        
        # Second payment that would exceed
        with self.assertRaises(ValidationError):
            payment = Payment(
                enrollment=self.enrollment,
                amount=Decimal('300.00'),
                payment_method='CASH',
                received_by=self.finance_staff
            )
            payment.save()
    
    def test_negative_payment_amount(self):
        """Test that negative payment amount is not allowed."""
        with self.assertRaises(ValidationError):
            payment = Payment(
                enrollment=self.enrollment,
                amount=Decimal('-100.00'),
                payment_method='CASH',
                received_by=self.finance_staff
            )
            payment.save()
    
    def test_get_total_paid_for_enrollment(self):
        """Test calculating total paid for enrollment."""
        Payment.objects.create(
            enrollment=self.enrollment,
            amount=Decimal('300.00'),
            payment_method='CASH',
            received_by=self.finance_staff
        )
        
        Payment.objects.create(
            enrollment=self.enrollment,
            amount=Decimal('400.00'),
            payment_method='BANK_TRANSFER',
            received_by=self.finance_staff
        )
        
        total = Payment.get_total_paid_for_enrollment(self.enrollment)
        self.assertEqual(total, Decimal('700.00'))
    
    def test_get_outstanding_balance(self):
        """Test calculating outstanding balance."""
        Payment.objects.create(
            enrollment=self.enrollment,
            amount=Decimal('600.00'),
            payment_method='CASH',
            received_by=self.finance_staff
        )
        
        outstanding = Payment.get_outstanding_balance(self.enrollment)
        self.assertEqual(outstanding, Decimal('400.00'))
    
    def test_is_enrollment_fully_paid(self):
        """Test checking if enrollment is fully paid."""
        # Not fully paid
        Payment.objects.create(
            enrollment=self.enrollment,
            amount=Decimal('600.00'),
            payment_method='CASH',
            received_by=self.finance_staff
        )
        self.assertFalse(Payment.is_enrollment_fully_paid(self.enrollment))
        
        # Add remaining payment
        Payment.objects.create(
            enrollment=self.enrollment,
            amount=Decimal('400.00'),
            payment_method='CASH',
            received_by=self.finance_staff
        )
        self.assertTrue(Payment.is_enrollment_fully_paid(self.enrollment))