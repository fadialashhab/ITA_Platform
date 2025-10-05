from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone


class Enrollment(models.Model):
    """Model for tracking student enrollments in courses."""
    
    STATUS_CHOICES = [
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    # Relations
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrollments',
        limit_choices_to={'role': 'STUDENT'}
    )
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    
    # Dates
    enrollment_date = models.DateField(default=timezone.now)
    completion_date = models.DateField(null=True, blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='IN_PROGRESS'
    )
    
    # Verification
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_enrollments'
    )
    
    # Notes
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'enrollments_enrollment'
        verbose_name = 'Enrollment'
        verbose_name_plural = 'Enrollments'
        ordering = ['-enrollment_date']
        unique_together = ['student', 'course']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['course', 'status']),
            models.Index(fields=['enrollment_date']),
        ]
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.course.title} ({self.status})"
    
    def clean(self):
        """Validate enrollment business rules."""
        # Check if student role is correct
        if self.student and self.student.role != 'STUDENT':
            raise ValidationError({
                'student': 'Only users with STUDENT role can be enrolled.'
            })
        
        # Check for duplicate enrollment
        if not self.pk:  # Only for new enrollments
            existing = Enrollment.objects.filter(
                student=self.student,
                course=self.course
            ).exclude(status='CANCELLED').exists()
            
            if existing:
                raise ValidationError({
                    'course': 'Student is already enrolled in this course.'
                })
        
        # Validate completion date
        if self.status == 'COMPLETED' and not self.completion_date:
            raise ValidationError({
                'completion_date': 'Completion date is required for completed enrollments.'
            })
        
        if self.completion_date and self.completion_date < self.enrollment_date:
            raise ValidationError({
                'completion_date': 'Completion date cannot be before enrollment date.'
            })
    
    def save(self, *args, **kwargs):
        """Override save to run validations."""
        self.clean()
        super().save(*args, **kwargs)
    
    def mark_completed(self, verified_by=None):
        """Mark enrollment as completed."""
        if self.status == 'COMPLETED':
            raise ValidationError('Enrollment is already completed.')
        
        if self.status == 'CANCELLED':
            raise ValidationError('Cannot complete a cancelled enrollment.')
        
        self.status = 'COMPLETED'
        self.completion_date = timezone.now().date()
        if verified_by:
            self.verified_by = verified_by
        self.save()
    
    def mark_cancelled(self):
        """Mark enrollment as cancelled."""
        if self.status == 'COMPLETED':
            raise ValidationError('Cannot cancel a completed enrollment.')
        
        self.status = 'CANCELLED'
        self.save()
    
    def get_payment_summary(self):
        """Get payment summary for this enrollment."""
        from payments.models import Payment
        
        payments = Payment.objects.filter(enrollment=self)
        total_paid = sum(p.amount for p in payments)
        outstanding = self.course.price - total_paid
        
        return {
            'course_price': self.course.price,
            'total_paid': total_paid,
            'outstanding_balance': max(outstanding, 0),
            'is_fully_paid': outstanding <= 0,
            'payment_count': payments.count()
        }
    
    def is_fully_paid(self):
        """Check if enrollment is fully paid."""
        return self.get_payment_summary()['is_fully_paid']
    
    def check_prerequisites(self):
        """Check if student has completed all prerequisites."""
        prerequisites = self.course.prerequisites.all()
        
        if not prerequisites.exists():
            return True, []
        
        # Get completed courses by this student
        completed_courses = Enrollment.objects.filter(
            student=self.student,
            status='COMPLETED'
        ).values_list('course_id', flat=True)
        
        missing_prerequisites = []
        for prereq in prerequisites:
            if prereq.id not in completed_courses:
                missing_prerequisites.append(prereq)
        
        return len(missing_prerequisites) == 0, missing_prerequisites
    
    def get_duration_days(self):
        """Calculate enrollment duration in days."""
        if self.completion_date:
            return (self.completion_date - self.enrollment_date).days
        return (timezone.now().date() - self.enrollment_date).days