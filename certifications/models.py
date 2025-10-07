# certifications/models.py
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid


class Certificate(models.Model):
    """Model for student certificates."""
    
    # Relations
    enrollment = models.OneToOneField(
        'enrollments.Enrollment',
        on_delete=models.CASCADE,
        related_name='certificate'
    )
    
    # Certificate identification
    certificate_number = models.CharField(
        max_length=50,
        unique=True,
        editable=False
    )
    verification_code = models.CharField(
        max_length=100,
        unique=True,
        editable=False
    )
    
    # Dates
    issue_date = models.DateField(default=timezone.now)
    
    # Visibility
    is_public = models.BooleanField(
        default=True,
        help_text="Allow public verification of this certificate"
    )
    
    # File storage (optional - for PDF certificates)
    certificate_file = models.FileField(
        upload_to='certificates/%Y/%m/',
        null=True,
        blank=True,
        help_text="Generated PDF certificate file"
    )
    
    # Audit fields
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='issued_certificates'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'certifications_certificate'
        verbose_name = 'Certificate'
        verbose_name_plural = 'Certificates'
        ordering = ['-issue_date']
        indexes = [
            models.Index(fields=['certificate_number']),
            models.Index(fields=['verification_code']),
            models.Index(fields=['issue_date']),
            models.Index(fields=['enrollment']),
        ]
    
    def __str__(self):
        return f"{self.certificate_number} - {self.enrollment.student.get_full_name()}"
    
    def save(self, *args, **kwargs):
        """Generate certificate number, verification code, and PDF on creation."""
        is_new = not self.pk
        
        if is_new:
            # Generate certificate number
            if not self.certificate_number:
                year = timezone.now().year
                count = Certificate.objects.filter(
                    issue_date__year=year
                ).count() + 1
                self.certificate_number = f"CERT-{year}-{count:06d}"
            
            # Generate verification code
            if not self.verification_code:
                self.verification_code = str(uuid.uuid4())
        
        # Run validations
        self.clean()
        
        # Save first to get an ID (needed for file field)
        super().save(*args, **kwargs)
        
        # Generate PDF after initial save (only for new certificates)
        if is_new and not self.certificate_file:
            self._generate_and_attach_pdf()
    
    def _generate_and_attach_pdf(self):
        """Generate PDF certificate and attach it to the model."""
        from .utils import generate_certificate_pdf
        
        try:
            # Generate PDF
            pdf_file = generate_certificate_pdf(self)
            
            # Attach to model
            self.certificate_file = pdf_file
            
            # Save again to update the file field (without triggering infinite loop)
            super().save(update_fields=['certificate_file'])
        except Exception as e:
            # Log error but don't fail the certificate creation
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to generate PDF for certificate {self.certificate_number}: {str(e)}")
    
    def regenerate_pdf(self):
        """Regenerate the certificate PDF file."""
        from .utils import generate_certificate_pdf
        
        # Delete old file if exists
        if self.certificate_file:
            self.certificate_file.delete(save=False)
        
        # Generate new PDF
        pdf_file = generate_certificate_pdf(self)
        self.certificate_file = pdf_file
        self.save(update_fields=['certificate_file'])
        
        return True
    
    def clean(self):
        """Validate certificate business rules."""
        # Check if enrollment is completed
        if self.enrollment.status != 'COMPLETED':
            raise ValidationError({
                'enrollment': 'Certificate can only be issued for completed enrollments.'
            })
        
        # Check if enrollment has completion date
        if not self.enrollment.completion_date:
            raise ValidationError({
                'enrollment': 'Enrollment must have a completion date before issuing certificate.'
            })
        
        # Check if issue date is not before completion date
        if self.issue_date < self.enrollment.completion_date:
            raise ValidationError({
                'issue_date': 'Issue date cannot be before completion date.'
            })
        
        # Check for duplicate certificate (besides the OneToOne constraint)
        if not self.pk:
            existing = Certificate.objects.filter(enrollment=self.enrollment).exists()
            if existing:
                raise ValidationError({
                    'enrollment': 'A certificate already exists for this enrollment.'
                })
    
    def get_student_name(self):
        """Return the student's full name."""
        return self.enrollment.student.get_full_name()
    
    def get_course_title(self):
        """Return the course title."""
        return self.enrollment.course.title
    
    def get_course_level(self):
        """Return the course level."""
        return self.enrollment.course.get_level_display()
    
    def get_completion_date(self):
        """Return the enrollment completion date."""
        return self.enrollment.completion_date
    
    def get_duration_days(self):
        """Return the duration of the course in days."""
        return self.enrollment.get_duration_days()
    
    def is_verified(self, verification_code):
        """Verify if the provided code matches."""
        return self.verification_code == verification_code
    
    def toggle_public(self):
        """Toggle the public visibility of the certificate."""
        self.is_public = not self.is_public
        self.save()
        return self.is_public
    
    @classmethod
    def verify_certificate(cls, verification_code):
        """
        Verify a certificate by its verification code.
        Returns the certificate if valid and public, None otherwise.
        """
        try:
            certificate = cls.objects.select_related(
                'enrollment__student',
                'enrollment__course'
            ).get(
                verification_code=verification_code,
                is_public=True
            )
            return certificate
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def get_pending_certificates(cls):
        """
        Get enrollments that are completed but don't have certificates yet.
        """
        from enrollments.models import Enrollment
        
        completed_enrollments = Enrollment.objects.filter(
            status='COMPLETED'
        ).exclude(
            certificate__isnull=False
        ).select_related('student', 'course')
        
        return completed_enrollments