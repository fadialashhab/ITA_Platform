# certifications app
from rest_framework import serializers
from django.utils import timezone
from .models import Certificate
from enrollments.serializers import EnrollmentListSerializer


class CertificateSerializer(serializers.ModelSerializer):
    """Full serializer for Certificate model."""
    
    student_name = serializers.CharField(source='enrollment.student.get_full_name', read_only=True)
    student_email = serializers.CharField(source='enrollment.student.email', read_only=True)
    course_title = serializers.CharField(source='enrollment.course.title', read_only=True)
    course_level = serializers.CharField(source='enrollment.course.get_level_display', read_only=True)
    completion_date = serializers.DateField(source='enrollment.completion_date', read_only=True)
    enrollment_date = serializers.DateField(source='enrollment.enrollment_date', read_only=True)
    issued_by_name = serializers.CharField(source='issued_by.get_full_name', read_only=True)
    duration_days = serializers.SerializerMethodField()
    certificate_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Certificate
        fields = [
            'id', 'enrollment', 'certificate_number', 'verification_code',
            'issue_date', 'is_public', 'certificate_file', 'certificate_url',
            'student_name', 'student_email', 'course_title', 'course_level',
            'completion_date', 'enrollment_date', 'duration_days',
            'issued_by', 'issued_by_name', 'created_at'
        ]
        read_only_fields = [
            'id', 'certificate_number', 'verification_code', 'created_at',
            'issued_by', 'student_name', 'student_email', 'course_title',
            'course_level', 'completion_date', 'enrollment_date'
        ]
    
    def get_duration_days(self, obj):
        """Get enrollment duration in days."""
        return obj.get_duration_days()
    
    def get_certificate_url(self, obj):
        """Get certificate file URL if exists."""
        if obj.certificate_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.certificate_file.url)
        return None


class CertificateListSerializer(serializers.ModelSerializer):
    """Simplified serializer for certificate listing."""
    
    student_name = serializers.CharField(source='enrollment.student.get_full_name', read_only=True)
    course_title = serializers.CharField(source='enrollment.course.title', read_only=True)
    course_level = serializers.CharField(source='enrollment.course.get_level_display', read_only=True)
    
    class Meta:
        model = Certificate
        fields = [
            'id', 'certificate_number', 'student_name', 'course_title',
            'course_level', 'issue_date', 'is_public'
        ]


class CertificateCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new certificates."""
    
    class Meta:
        model = Certificate
        fields = ['enrollment', 'issue_date', 'is_public']
    
    def validate_enrollment(self, value):
        """Validate that enrollment is completed and doesn't have a certificate."""
        # Check if enrollment is completed
        if value.status != 'COMPLETED':
            raise serializers.ValidationError(
                "Certificate can only be issued for completed enrollments."
            )
        
        # Check if enrollment has completion date
        if not value.completion_date:
            raise serializers.ValidationError(
                "Enrollment must have a completion date before issuing certificate."
            )
        
        # Check if certificate already exists
        if hasattr(value, 'certificate'):
            raise serializers.ValidationError(
                "A certificate already exists for this enrollment."
            )
        
        return value
    
    def validate_issue_date(self, value):
        """Validate issue date."""
        if value > timezone.now().date():
            raise serializers.ValidationError(
                "Issue date cannot be in the future."
            )
        return value
    
    def validate(self, attrs):
        """Cross-field validation."""
        enrollment = attrs.get('enrollment')
        issue_date = attrs.get('issue_date')
        
        # Check if issue date is not before completion date
        if issue_date < enrollment.completion_date:
            raise serializers.ValidationError({
                'issue_date': 'Issue date cannot be before completion date.'
            })
        
        return attrs
    
    def create(self, validated_data):
        """Create certificate with issued_by from request."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['issued_by'] = request.user
        
        return Certificate.objects.create(**validated_data)


class CertificateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating certificates."""
    
    class Meta:
        model = Certificate
        fields = ['is_public', 'certificate_file']


class BulkCertificateIssueSerializer(serializers.Serializer):
    """Serializer for bulk certificate issuance."""
    
    enrollment_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )
    issue_date = serializers.DateField(default=timezone.now().date)
    is_public = serializers.BooleanField(default=True)
    
    def validate_enrollment_ids(self, value):
        """Validate that all enrollments exist and are eligible."""
        from enrollments.models import Enrollment
        
        # Check if all enrollments exist
        enrollments = Enrollment.objects.filter(id__in=value)
        if enrollments.count() != len(value):
            raise serializers.ValidationError(
                "One or more enrollment IDs are invalid."
            )
        
        # Check if all are completed
        not_completed = enrollments.exclude(status='COMPLETED')
        if not_completed.exists():
            raise serializers.ValidationError(
                f"Enrollments {list(not_completed.values_list('id', flat=True))} are not completed."
            )
        
        # Check if any already have certificates
        with_certificates = enrollments.filter(certificate__isnull=False)
        if with_certificates.exists():
            raise serializers.ValidationError(
                f"Enrollments {list(with_certificates.values_list('id', flat=True))} already have certificates."
            )
        
        return value


class PublicCertificateSerializer(serializers.ModelSerializer):
    """Public-facing serializer for certificate verification."""
    
    student_name = serializers.CharField(source='enrollment.student.get_full_name', read_only=True)
    course_title = serializers.CharField(source='enrollment.course.title', read_only=True)
    course_level = serializers.CharField(source='enrollment.course.get_level_display', read_only=True)
    course_duration = serializers.IntegerField(source='enrollment.course.duration', read_only=True)
    completion_date = serializers.DateField(source='enrollment.completion_date', read_only=True)
    
    class Meta:
        model = Certificate
        fields = [
            'certificate_number', 'student_name', 'course_title',
            'course_level', 'course_duration', 'issue_date', 'completion_date'
        ]


class CertificateVerificationSerializer(serializers.Serializer):
    """Serializer for certificate verification request."""
    
    verification_code = serializers.CharField(required=True)
    
    def validate_verification_code(self, value):
        """Validate that verification code is not empty."""
        if not value or value.strip() == '':
            raise serializers.ValidationError("Verification code cannot be empty.")
        return value.strip()


class StudentCertificateSerializer(serializers.ModelSerializer):
    """Serializer for students viewing their own certificates."""
    
    course_title = serializers.CharField(source='enrollment.course.title', read_only=True)
    course_level = serializers.CharField(source='enrollment.course.get_level_display', read_only=True)
    course_duration = serializers.IntegerField(source='enrollment.course.duration', read_only=True)
    completion_date = serializers.DateField(source='enrollment.completion_date', read_only=True)
    enrollment_date = serializers.DateField(source='enrollment.enrollment_date', read_only=True)
    duration_days = serializers.SerializerMethodField()
    certificate_url = serializers.SerializerMethodField()
    can_download = serializers.SerializerMethodField()
    
    class Meta:
        model = Certificate
        fields = [
            'id', 'certificate_number', 'verification_code', 'course_title',
            'course_level', 'course_duration', 'issue_date', 'completion_date',
            'enrollment_date', 'duration_days', 'is_public', 'certificate_file',
            'certificate_url', 'can_download'
        ]
    
    def get_duration_days(self, obj):
        """Get enrollment duration in days."""
        return obj.get_duration_days()
    
    def get_certificate_url(self, obj):
        """Get certificate file URL if exists."""
        if obj.certificate_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.certificate_file.url)
        return None
    
    def get_can_download(self, obj):
        """Check if certificate file is available for download."""
        return bool(obj.certificate_file)


class PendingCertificateSerializer(serializers.Serializer):
    """Serializer for enrollments pending certificate issuance."""
    
    enrollment_id = serializers.IntegerField(source='id')
    student_id = serializers.IntegerField(source='student.id')
    student_name = serializers.CharField(source='student.get_full_name')
    student_email = serializers.CharField(source='student.email')
    course_id = serializers.IntegerField(source='course.id')
    course_title = serializers.CharField(source='course.title')
    course_level = serializers.CharField(source='course.get_level_display')
    enrollment_date = serializers.DateField()
    completion_date = serializers.DateField()
    duration_days = serializers.SerializerMethodField()
    verified_by_name = serializers.CharField(source='verified_by.get_full_name', allow_null=True)
    
    def get_duration_days(self, obj):
        """Get enrollment duration in days."""
        if obj.completion_date:
            return (obj.completion_date - obj.enrollment_date).days
        return None


class CertificateStatisticsSerializer(serializers.Serializer):
    """Serializer for certificate statistics."""
    
    total_certificates = serializers.IntegerField()
    public_certificates = serializers.IntegerField()
    private_certificates = serializers.IntegerField()
    certificates_this_month = serializers.IntegerField()
    certificates_this_year = serializers.IntegerField()
    certificates_by_month = serializers.ListField()
    certificates_by_course = serializers.ListField()
    recent_certificates = serializers.ListField()
    pending_count = serializers.IntegerField()