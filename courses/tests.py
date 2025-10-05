from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from .models import Category, Course

User = get_user_model()


class CategoryModelTest(TestCase):
    """Test cases for Category model."""
    
    def setUp(self):
        """Set up test data."""
        self.category = Category.objects.create(
            name='Programming',
            description='Programming courses',
            is_active=True
        )
    
    def test_category_creation(self):
        """Test category is created correctly."""
        self.assertEqual(self.category.name, 'Programming')
        self.assertTrue(self.category.is_active)
        self.assertIsNotNone(self.category.created_at)
    
    def test_category_str(self):
        """Test category string representation."""
        self.assertEqual(str(self.category), 'Programming')
    
    def test_get_active_courses_count(self):
        """Test getting active courses count."""
        user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            first_name='Admin',
            last_name='User',
            role='ADMIN'
        )
        
        Course.objects.create(
            title='Python Basics',
            description='Learn Python',
            duration=40,
            price=Decimal('10000.00'),
            level='BEGINNER',
            category=self.category,
            is_active=True,
            created_by=user
        )
        
        Course.objects.create(
            title='Advanced Python',
            description='Advanced Python',
            duration=60,
            price=Decimal('15000.00'),
            level='ADVANCED',
            category=self.category,
            is_active=False,
            created_by=user
        )
        
        self.assertEqual(self.category.get_active_courses_count(), 1)


class CourseModelTest(TestCase):
    """Test cases for Course model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            first_name='Admin',
            last_name='User',
            role='ADMIN'
        )
        
        self.category = Category.objects.create(
            name='Programming',
            description='Programming courses'
        )
        
        self.course = Course.objects.create(
            title='Python Programming',
            description='Learn Python from scratch',
            duration=40,
            price=Decimal('10000.00'),
            level='BEGINNER',
            category=self.category,
            is_active=True,
            created_by=self.user
        )
    
    def test_course_creation(self):
        """Test course is created correctly."""
        self.assertEqual(self.course.title, 'Python Programming')
        self.assertEqual(self.course.level, 'BEGINNER')
        self.assertEqual(self.course.price, Decimal('10000.00'))
        self.assertEqual(self.course.duration, 40)
        self.assertEqual(self.course.category, self.category)
        self.assertEqual(self.course.created_by, self.user)
    
    def test_course_str(self):
        """Test course string representation."""
        expected = 'Python Programming (Beginner)'
        self.assertEqual(str(self.course), expected)
    
    def test_prerequisites_relationship(self):
        """Test many-to-many prerequisites relationship."""
        advanced_course = Course.objects.create(
            title='Advanced Python',
            description='Advanced Python concepts',
            duration=60,
            price=Decimal('15000.00'),
            level='ADVANCED',
            category=self.category,
            created_by=self.user
        )
        
        advanced_course.prerequisites.add(self.course)
        
        self.assertTrue(advanced_course.has_prerequisite(self.course))
        self.assertTrue(self.course.is_prerequisite_for(advanced_course))
        self.assertEqual(advanced_course.prerequisites.count(), 1)
    
    def test_get_prerequisite_titles(self):
        """Test getting list of prerequisite titles."""
        prereq1 = Course.objects.create(
            title='Prerequisite 1',
            description='First prereq',
            duration=20,
            price=Decimal('5000.00'),
            level='BEGINNER',
            created_by=self.user
        )
        
        prereq2 = Course.objects.create(
            title='Prerequisite 2',
            description='Second prereq',
            duration=20,
            price=Decimal('5000.00'),
            level='BEGINNER',
            created_by=self.user
        )
        
        self.course.prerequisites.add(prereq1, prereq2)
        
        titles = self.course.get_prerequisite_titles()
        self.assertEqual(len(titles), 2)
        self.assertIn('Prerequisite 1', titles)
        self.assertIn('Prerequisite 2', titles)
    
    def test_enrollment_count_methods(self):
        """Test enrollment counting methods."""
        # Initially should be 0
        self.assertEqual(self.course.get_enrollment_count(), 0)
        self.assertEqual(self.course.get_active_enrollment_count(), 0)
        self.assertEqual(self.course.get_completion_count(), 0)
        self.assertEqual(self.course.get_completion_rate(), 0)