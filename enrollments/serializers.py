# enrollment
from rest_framework import serializers
from django.utils import timezone
from .models import Enrollment
from accounts.serializers import StudentSerializer
from courses.serializers import CourseListSerializer


class EnrollmentSerializer(serializers.ModelSerializer):
    """Full serializer for Enrollment model."""
    
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    student_email = serializers.CharField(source='student.email', read_only=True)
    student_detail = StudentSerializer(source='student', read_only=True)
    
    course_title = serializers.CharField(source='course.title', read_only=True)
    course_price = serializers.DecimalField(
        source='course.price',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    course_detail = CourseListSerializer(source='course', read_only=True)
    
    verified_by_name = serializers.CharField(
        source='verified_by.get_full_name',
        read_only=True
    )
    
    payment_summary = serializers.SerializerMethodField()
    duration_days = serializers.SerializerMethodField()
    prerequisites_met = serializers.SerializerMethodField()
    
    class Meta:
        model = Enrollment
        fields = [
            'id', 'student', 'student_name', 'student_email', 'student_detail',
            'course', 'course_title', 'course_price', 'course_detail',
            'enrollment_date', 'completion_date', 'status',
            'verified_by', 'verified_by_name', 'notes',
            'payment_summary', 'duration_days', 'prerequisites_met',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'verified_by',
            'student_name', 'student_email', 'course_title', 'course_price'
        ]
    
    def get_payment_summary(self, obj):
        """Get payment summary for enrollment."""
        return obj.get_payment_summary()
    
    def get_duration_days(self, obj):
        """Get enrollment duration in days."""
        return obj.get_duration_days()
    
    def get_prerequisites_met(self, obj):
        """Check if prerequisites are met."""
        met, missing = obj.check_prerequisites()
        return {
            'met': met,
            'missing_prerequisites': [
                {'id': p.id, 'title': p.title} for p in missing
            ]
        }


class EnrollmentListSerializer(serializers.ModelSerializer):
    """Simplified serializer for enrollment listing."""
    
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    course_price = serializers.DecimalField(
        source='course.price',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    payment_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Enrollment
        fields = [
            'id', 'student', 'student_name', 'course', 'course_title',
            'course_price', 'enrollment_date', 'completion_date',
            'status', 'payment_status'
        ]
    
    def get_payment_status(self, obj):
        """Get simplified payment status."""
        summary = obj.get_payment_summary()
        return {
            'is_fully_paid': summary['is_fully_paid'],
            'outstanding_balance': summary['outstanding_balance']
        }


class EnrollmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new enrollments."""
    
    class Meta:
        model = Enrollment
        fields = [
            'student', 'course', 'enrollment_date', 'notes'
        ]
    
    def validate_student(self, value):
        """Validate that the user is a student."""
        if value.role != 'STUDENT':
            raise serializers.ValidationError(
                "Only users with STUDENT role can be enrolled."
            )
        if not value.is_active:
            raise serializers.ValidationError(
                "Cannot enroll inactive students."
            )
        return value
    
    def validate_course(self, value):
        """Validate that the course is active."""
        if not value.is_active:
            raise serializers.ValidationError(
                "Cannot enroll in inactive courses."
            )
        return value
    
    def validate(self, attrs):
        """Validate enrollment business rules."""
        student = attrs.get('student')
        course = attrs.get('course')
        
        # Check for duplicate enrollment
        existing = Enrollment.objects.filter(
            student=student,
            course=course
        ).exclude(status='CANCELLED').exists()
        
        if existing:
            raise serializers.ValidationError({
                'course': 'Student is already enrolled in this course.'
            })
        
        # Check prerequisites
        prerequisites = course.prerequisites.all()
        if prerequisites.exists():
            completed_courses = Enrollment.objects.filter(
                student=student,
                status='COMPLETED'
            ).values_list('course_id', flat=True)
            
            missing_prerequisites = []
            for prereq in prerequisites:
                if prereq.id not in completed_courses:
                    missing_prerequisites.append(prereq.title)
            
            if missing_prerequisites:
                raise serializers.ValidationError({
                    'course': f"Missing prerequisites: {', '.join(missing_prerequisites)}"
                })
        
        return attrs


class EnrollmentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating enrollments."""
    
    class Meta:
        model = Enrollment
        fields = ['status', 'completion_date', 'notes']
    
    def validate(self, attrs):
        """Validate status transitions."""
        instance = self.instance
        new_status = attrs.get('status', instance.status)
        
        # Prevent invalid status transitions
        if instance.status == 'COMPLETED' and new_status != 'COMPLETED':
            raise serializers.ValidationError(
                "Cannot change status of a completed enrollment."
            )
        
        # Require completion_date for COMPLETED status
        if new_status == 'COMPLETED':
            if not attrs.get('completion_date') and not instance.completion_date:
                attrs['completion_date'] = timezone.now().date()
        
        return attrs


class EnrollmentCompleteSerializer(serializers.Serializer):
    """Serializer for marking enrollment as complete."""
    
    completion_date = serializers.DateField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_completion_date(self, value):
        """Validate completion date."""
        enrollment = self.context.get('enrollment')
        if enrollment and value < enrollment.enrollment_date:
            raise serializers.ValidationError(
                "Completion date cannot be before enrollment date."
            )
        return value


class StudentEnrollmentSerializer(serializers.ModelSerializer):
    """Serializer for student viewing their own enrollments."""
    
    course_detail = CourseListSerializer(source='course', read_only=True)
    payment_summary = serializers.SerializerMethodField()
    duration_days = serializers.SerializerMethodField()
    
    class Meta:
        model = Enrollment
        fields = [
            'id', 'course_detail', 'enrollment_date', 
            'completion_date', 'status', 'payment_summary',
            'duration_days', 'notes'
        ]
    
    def get_payment_summary(self, obj):
        """Get payment summary."""
        return obj.get_payment_summary()
    
    def get_duration_days(self, obj):
        """Get duration in days."""
        return obj.get_duration_days()


class EnrollmentStatisticsSerializer(serializers.Serializer):
    """Serializer for enrollment statistics."""
    
    total_enrollments = serializers.IntegerField()
    active_enrollments = serializers.IntegerField()
    completed_enrollments = serializers.IntegerField()
    cancelled_enrollments = serializers.IntegerField()
    enrollments_by_status = serializers.DictField()
    enrollments_by_month = serializers.ListField()
    completion_rate = serializers.FloatField()
    avg_completion_time = serializers.FloatField()
    top_enrolled_courses = serializers.ListField()
    recent_enrollments = serializers.ListField()