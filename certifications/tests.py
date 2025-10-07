# certifications app
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from accounts.models import User
from courses.models import Course, Category
from enrollments.models import Enrollment
from .models import Certificate


class CertificateModelTest(TestCase):
    """Test cases for Certificate model."""
    
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
        
        self.student = User.objects.create_user(
            username='student',
            email='student@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Student',
            role='STUDENT'
        )
        
        # Create course
        self.category = Category.objects.create(name='Programming')
        self.course = Course.objects.create(
            title='Python Basics',
            description='Learn Python',
            duration=40,
            price=10000.00,
            level='BEGINNER',
            category=self.category,
            created_by=self.admin
        )
        
        # Create completed enrollment
        self.enrollment = Enrollment.objects.create(
            student=self.student,
            course=self.course,
            status='COMPLETED',
            completion_date=timezone.now().date()
        )
    
    def test_certificate_creation(self):
        """Test creating a certificate."""
        certificate = Certificate.objects.create(
            enrollment=self.enrollment,
            issued_by=self.admin
        )
        
        self.assertIsNotNone(certificate.certificate_number)
        self.assertIsNotNone(certificate.verification_code)
        self.assertTrue(certificate.certificate_number.startswith('CERT-'))
        self.assertEqual(certificate.enrollment, self.enrollment)
    
    def test_certificate_number_format(self):
        """Test certificate number format."""
        certificate = Certificate.objects.create(
            enrollment=self.enrollment,
            issued_by=self.admin
        )
        
        year = timezone.now().year
        self.assertTrue(certificate.certificate_number.startswith(f'CERT-{year}-'))
    
    def test_certificate_for_incomplete_enrollment_fails(self):
        """Test that certificate cannot be created for incomplete enrollment."""
        # Create in-progress enrollment
        enrollment = Enrollment.objects.create(
            student=self.student,
            course=self.course,
            status='IN_PROGRESS'
        )
        
        with self.assertRaises(ValidationError):
            certificate = Certificate(
                enrollment=enrollment,
                issued_by=self.admin
            )
            certificate.save()
    
    def test_duplicate_certificate_fails(self):
        """Test that duplicate certificates cannot be created."""
        Certificate.objects.create(
            enrollment=self.enrollment,
            issued_by=self.admin
        )
        
        with self.assertRaises(Exception):
            Certificate.objects.create(
                enrollment=self.enrollment,
                issued_by=self.admin
            )
    
    def test_certificate_verification(self):
        """Test certificate verification."""
        certificate = Certificate.objects.create(
            enrollment=self.enrollment,
            issued_by=self.admin,
            is_public=True
        )
        
        # Verify with correct code
        verified = Certificate.verify_certificate(certificate.verification_code)
        self.assertIsNotNone(verified)
        self.assertEqual(verified.id, certificate.id)
        
        # Verify with wrong code
        verified = Certificate.verify_certificate('wrong-code')
        self.assertIsNone(verified)
    
    def test_private_certificate_not_verifiable(self):
        """Test that private certificates are not publicly verifiable."""
        certificate = Certificate.objects.create(
            enrollment=self.enrollment,
            issued_by=self.admin,
            is_public=False
        )
        
        verified = Certificate.verify_certificate(certificate.verification_code)
        self.assertIsNone(verified)
    
    def test_get_pending_certificates(self):
        """Test getting pending certificates."""
        # Create another completed enrollment without certificate
        student2 = User.objects.create_user(
            username='student2',
            email='student2@test.com',
            password='testpass123',
            first_name='Student',
            last_name='Two',
            role='STUDENT'
        )
        
        enrollment2 = Enrollment.objects.create(
            student=student2,
            course=self.course,
            status='COMPLETED',
            completion_date=timezone.now().date()
        )
        
        pending = Certificate.get_pending_certificates()
        self.assertEqual(pending.count(), 2)  # Both enrollments don't have certificates yet
        
        # Issue certificate for one
        Certificate.objects.create(
            enrollment=self.enrollment,
            issued_by=self.admin
        )
        
        pending = Certificate.get_pending_certificates()
        self.assertEqual(pending.count(), 1)  # Only enrollment2 is pending


class CertificateAPITest(TestCase):
    """Test cases for Certificate API endpoints."""
    
    def setUp(self):
        """Set up test data and authenticate."""
        # This is a placeholder for API tests
        # You would need to set up DRF test client and authentication
        pass
    
    # Add API test cases here when implementing