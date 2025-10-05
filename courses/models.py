# courses app
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class Category(models.Model):
    """Course category model."""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'courses_category'
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_active_courses_count(self):
        """Return count of active courses in this category."""
        return self.courses.filter(is_active=True).count()


class Course(models.Model):
    """Course model with prerequisites support."""
    
    LEVEL_CHOICES = [
        ('BEGINNER', 'Beginner'),
        ('INTERMEDIATE', 'Intermediate'),
        ('ADVANCED', 'Advanced'),
    ]
    
    # Basic information
    title = models.CharField(max_length=200)
    description = models.TextField()
    duration = models.PositiveIntegerField(
        help_text="Duration in hours",
        validators=[MinValueValidator(1)]
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Academic information
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='BEGINNER')
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses'
    )
    
    # Prerequisites (many-to-many to self)
    prerequisites = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='required_for'
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Audit fields
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_courses'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'courses_course'
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['level', 'is_active']),
            models.Index(fields=['category', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_level_display()})"
    
    def get_enrollment_count(self):
        """Return total number of enrollments for this course."""
        return self.enrollments.count()
    
    def get_active_enrollment_count(self):
        """Return number of active (in-progress) enrollments."""
        return self.enrollments.filter(status='IN_PROGRESS').count()
    
    def get_completion_count(self):
        """Return number of completed enrollments."""
        return self.enrollments.filter(status='COMPLETED').count()
    
    def get_completion_rate(self):
        """Calculate completion rate as percentage."""
        total = self.get_enrollment_count()
        if total == 0:
            return 0
        completed = self.get_completion_count()
        return round((completed / total) * 100, 2)
    
    def has_prerequisite(self, course):
        """Check if given course is a prerequisite for this course."""
        return self.prerequisites.filter(id=course.id).exists()
    
    def get_prerequisite_titles(self):
        """Return list of prerequisite course titles."""
        return list(self.prerequisites.values_list('title', flat=True))
    
    def is_prerequisite_for(self, course):
        """Check if this course is a prerequisite for given course."""
        return course.prerequisites.filter(id=self.id).exists()