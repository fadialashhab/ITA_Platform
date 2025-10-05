from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q, Avg, F
from django.utils import timezone
from datetime import timedelta

from .models import Enrollment
from .serializers import (
    EnrollmentSerializer, EnrollmentListSerializer,
    EnrollmentCreateSerializer, EnrollmentUpdateSerializer,
    EnrollmentCompleteSerializer, StudentEnrollmentSerializer,
    EnrollmentStatisticsSerializer
)
from .permissions import IsAdminOrRegistrar, IsAdminOrAcademic
from .filters import EnrollmentFilter


class EnrollmentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing enrollments."""
    
    queryset = Enrollment.objects.select_related(
        'student', 'course', 'verified_by'
    ).prefetch_related('course__category')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = EnrollmentFilter
    search_fields = [
        'student__username', 'student__email',
        'student__first_name', 'student__last_name',
        'course__title'
    ]
    ordering_fields = ['enrollment_date', 'completion_date', 'status']
    ordering = ['-enrollment_date']
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create', 'list', 'retrieve']:
            permission_classes = [IsAdminOrRegistrar]
        elif self.action in ['complete', 'pending_completion']:
            permission_classes = [IsAdminOrAcademic]
        elif self.action in ['update', 'partial_update', 'destroy', 'cancel']:
            permission_classes = [IsAdminOrRegistrar]
        else:
            permission_classes = [IsAdminOrRegistrar]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return EnrollmentListSerializer
        elif self.action == 'create':
            return EnrollmentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return EnrollmentUpdateSerializer
        elif self.action == 'complete':
            return EnrollmentCompleteSerializer
        return EnrollmentSerializer
    
    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = Enrollment.objects.select_related(
            'student', 'course', 'verified_by'
        ).prefetch_related('course__category')
        
        # Filter by student
        student_id = self.request.query_params.get('student', None)
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        
        # Filter by course
        course_id = self.request.query_params.get('course', None)
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if start_date:
            queryset = queryset.filter(enrollment_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(enrollment_date__lte=end_date)
        
        # Filter by payment status
        payment_status = self.request.query_params.get('payment_status', None)
        if payment_status == 'paid':
            # This requires a more complex query with payment aggregation
            pass
        elif payment_status == 'unpaid':
            pass
        
        return queryset
    
    def perform_create(self, serializer):
        """Create enrollment with validation."""
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark enrollment as completed."""
        enrollment = self.get_object()
        
        if enrollment.status == 'COMPLETED':
            return Response(
                {'error': 'Enrollment is already completed.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if enrollment.status == 'CANCELLED':
            return Response(
                {'error': 'Cannot complete a cancelled enrollment.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = EnrollmentCompleteSerializer(
            data=request.data,
            context={'enrollment': enrollment}
        )
        serializer.is_valid(raise_exception=True)
        
        # Mark as completed
        enrollment.status = 'COMPLETED'
        enrollment.completion_date = serializer.validated_data.get(
            'completion_date',
            timezone.now().date()
        )
        enrollment.verified_by = request.user
        
        if serializer.validated_data.get('notes'):
            enrollment.notes = serializer.validated_data['notes']
        
        enrollment.save()
        
        return Response({
            'message': 'Enrollment marked as completed successfully.',
            'enrollment': EnrollmentSerializer(enrollment).data
        })
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an enrollment."""
        enrollment = self.get_object()
        
        if enrollment.status == 'COMPLETED':
            return Response(
                {'error': 'Cannot cancel a completed enrollment.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        enrollment.status = 'CANCELLED'
        if request.data.get('notes'):
            enrollment.notes = request.data.get('notes')
        enrollment.save()
        
        return Response({
            'message': 'Enrollment cancelled successfully.',
            'enrollment': EnrollmentSerializer(enrollment).data
        })
    
    @action(detail=True, methods=['get'])
    def payments(self, request, pk=None):
        """Get all payments for this enrollment."""
        enrollment = self.get_object()
        
        # Import Payment model here to avoid circular import
        from payments.models import Payment
        from payments.serializers import PaymentSerializer
        
        payments = Payment.objects.filter(enrollment=enrollment).order_by('-payment_date')
        serializer = PaymentSerializer(payments, many=True)
        
        payment_summary = enrollment.get_payment_summary()
        
        return Response({
            'enrollment': {
                'id': enrollment.id,
                'student_name': enrollment.student.get_full_name(),
                'course_title': enrollment.course.title,
                'status': enrollment.status
            },
            'payment_summary': payment_summary,
            'payments': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def pending_completion(self, request):
        """Get enrollments pending completion verification."""
        enrollments = self.get_queryset().filter(
            status='IN_PROGRESS'
        ).order_by('enrollment_date')
        
        # Filter by course if provided
        course_id = request.query_params.get('course', None)
        if course_id:
            enrollments = enrollments.filter(course_id=course_id)
        
        page = self.paginate_queryset(enrollments)
        if page is not None:
            serializer = EnrollmentListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = EnrollmentListSerializer(enrollments, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get comprehensive enrollment statistics."""
        queryset = self.get_queryset()
        
        # Basic counts
        total_enrollments = queryset.count()
        active_enrollments = queryset.filter(status='IN_PROGRESS').count()
        completed_enrollments = queryset.filter(status='COMPLETED').count()
        cancelled_enrollments = queryset.filter(status='CANCELLED').count()
        
        # Enrollments by status
        enrollments_by_status = dict(
            queryset.values('status').annotate(
                count=Count('id')
            ).values_list('status', 'count')
        )
        
        # Enrollments by month (last 6 months)
        six_months_ago = timezone.now().date() - timedelta(days=180)
        monthly_enrollments = []
        
        for i in range(6):
            month_start = six_months_ago + timedelta(days=30*i)
            month_end = month_start + timedelta(days=30)
            count = queryset.filter(
                enrollment_date__gte=month_start,
                enrollment_date__lt=month_end
            ).count()
            monthly_enrollments.append({
                'month': month_start.strftime('%Y-%m'),
                'count': count
            })
        
        # Completion rate
        completion_rate = 0
        if total_enrollments > 0:
            completion_rate = (completed_enrollments / total_enrollments) * 100
        
        # Average completion time (in days)
        completed = queryset.filter(
            status='COMPLETED',
            completion_date__isnull=False
        )
        avg_completion_time = 0
        if completed.exists():
            total_days = sum([
                (e.completion_date - e.enrollment_date).days
                for e in completed
            ])
            avg_completion_time = total_days / completed.count()
        
        # Top enrolled courses
        from courses.models import Course
        courses = Course.objects.annotate(
            enrollment_count=Count('enrollments')
        ).order_by('-enrollment_count')[:5]
        
        top_enrolled_courses = [
            {
                'id': course.id,
                'title': course.title,
                'enrollment_count': course.enrollment_count
            }
            for course in courses
        ]
        
        # Recent enrollments
        recent = queryset.order_by('-enrollment_date')[:5]
        recent_enrollments = [
            {
                'id': e.id,
                'student_name': e.student.get_full_name(),
                'course_title': e.course.title,
                'enrollment_date': e.enrollment_date,
                'status': e.status
            }
            for e in recent
        ]
        
        data = {
            'total_enrollments': total_enrollments,
            'active_enrollments': active_enrollments,
            'completed_enrollments': completed_enrollments,
            'cancelled_enrollments': cancelled_enrollments,
            'enrollments_by_status': enrollments_by_status,
            'enrollments_by_month': monthly_enrollments,
            'completion_rate': round(completion_rate, 2),
            'avg_completion_time': round(avg_completion_time, 2),
            'top_enrolled_courses': top_enrolled_courses,
            'recent_enrollments': recent_enrollments
        }
        
        serializer = EnrollmentStatisticsSerializer(data)
        return Response(serializer.data)


class StudentEnrollmentViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for students to view their own enrollments."""
    
    serializer_class = StudentEnrollmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['enrollment_date', 'status']
    ordering = ['-enrollment_date']
    
    def get_queryset(self):
        """Return only the current user's enrollments."""
        return Enrollment.objects.filter(
            student=self.request.user
        ).select_related('course', 'course__category')
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get student's active enrollments."""
        enrollments = self.get_queryset().filter(status='IN_PROGRESS')
        serializer = self.get_serializer(enrollments, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def completed(self, request):
        """Get student's completed enrollments."""
        enrollments = self.get_queryset().filter(status='COMPLETED')
        serializer = self.get_serializer(enrollments, many=True)
        return Response(serializer.data)