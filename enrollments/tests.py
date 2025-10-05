from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from accounts.models import User
from courses.models import Course, Category
from .models import Enrollment


class EnrollmentModelTest(TestCase):
    """Test cases for Enrollment model."""
    
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
        
        # Create category
        self.category = Category.objects.create(
            name='Programming',
            description='Programming courses'
        )
        
        # Create courses
        self.course1 = Course.objects.create(
            title='Python Basics',
            description='Learn Python',
            duration=40,
            price=10000.00,
            level='BEGINNER',
            category=self.category,
            created_by=self.admin
        )
        
        self.course2 = Course.objects.create(
            title='Advanced Python',
            description='Advanced Python',
            duration=60,
            price=15000.00,
            level='ADVANCED',
            category=self.category,
            created_by=self.admin
        )
        self.course2.prerequisites.add(self.course1)
    
    def test_create_enrollment(self):
        """Test creating a valid enrollment."""
        enrollment = Enrollment.objects.create(
            student=self.student,
            course=self.course1
        )
        
        self.assertEqual(enrollment.status, 'IN_PROGRESS')
        self.assertIsNotNone(enrollment.enrollment_date)
        self.assertIsNone(enrollment.completion_date)
    
    def test_duplicate_enrollment_prevention(self):
        """Test that duplicate enrollment is prevented."""
        Enrollment.objects.create(
            student=self.student,
            course=self.course1
        )
        
        with self.assertRaises(ValidationError):
            Enrollment.objects.create(
                student=self.student,
                course=self.course1
            )
    
    def test_non_student_enrollment(self):
        """Test that non-students cannot be enrolled."""
        with self.assertRaises(ValidationError):
            Enrollment.objects.create(
                student=self.admin,
                course=self.course1
            )
    
    def test_mark_completed(self):
        """Test marking enrollment as completed."""
        enrollment = Enrollment.objects.create(
            student=self.student,
            course=self.course1
        )
        
        enrollment.mark_completed(verified_by=self.admin)
        
        self.assertEqual(enrollment.status, 'COMPLETED')
        self.assertIsNotNone(enrollment.completion_date)
        self.assertEqual(enrollment.verified_by, self.admin)
    
    def test_mark_cancelled(self):
        """Test marking enrollment as cancelled."""
        enrollment = Enrollment.objects.create(
            student=self.student,
            course=self.course1
        )
        
        enrollment.mark_cancelled()
        
        self.assertEqual(enrollment.status, 'CANCELLED')
    
    def test_prerequisite_check(self):
        """Test prerequisite checking."""
        enrollment = Enrollment.objects.create(
            student=self.student,
            course=self.course2
        )
        
        met, missing = enrollment.check_prerequisites()
        
        self.assertFalse(met)
        self.assertEqual(len(missing), 1)
        self.assertEqual(missing[0].id, self.course1.id)
        
        # Complete prerequisite
        prereq_enrollment = Enrollment.objects.create(
            student=self.student,
            course=self.course1
        )
        prereq_enrollment.mark_completed()
        
        met, missing = enrollment.check_prerequisites()
        
        self.assertTrue(met)
        self.assertEqual(len(missing), 0)
    
    def test_payment_summary(self):
        """Test payment summary calculation."""
        enrollment = Enrollment.objects.create(
            student=self.student,
            course=self.course1
        )
        
        summary = enrollment.get_payment_summary()
        
        self.assertEqual(summary['course_price'], self.course1.price)
        self.assertEqual(summary['total_paid'], 0)
        self.assertEqual(summary['outstanding_balance'], self.course1.price)
        self.assertFalse(summary['is_fully_paid'])
    
    def test_duration_days(self):
        """Test duration calculation."""
        enrollment = Enrollment.objects.create(
            student=self.student,
            course=self.course1
        )
        
        duration = enrollment.get_duration_days()
        
        self.assertGreaterEqual(duration, 0)
    
    def test_string_representation(self):
        """Test string representation."""
        enrollment = Enrollment.objects.create(
            student=self.student,
            course=self.course1
        )
        
        expected = f"{self.student.get_full_name()} - {self.course1.title} (IN_PROGRESS)"
        self.assertEqual(str(enrollment), expected)


class EnrollmentAPITest(TestCase):
    """Test cases for Enrollment API endpoints."""
    
    # Add API tests here if needed
    pass