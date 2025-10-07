# certifications app
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from django.utils import timezone
from django.http import FileResponse, Http404
from datetime import timedelta

from .models import Certificate
from .serializers import (
    CertificateSerializer, CertificateListSerializer,
    CertificateCreateSerializer, CertificateUpdateSerializer,
    BulkCertificateIssueSerializer, PublicCertificateSerializer,
    CertificateVerificationSerializer, StudentCertificateSerializer,
    PendingCertificateSerializer, CertificateStatisticsSerializer
)
from .permissions import IsAdminOrAcademic
from .filters import CertificateFilter


class CertificateViewSet(viewsets.ModelViewSet):
    """ViewSet for managing certificates (Admin/Academic staff)."""
    
    queryset = Certificate.objects.select_related(
        'enrollment__student',
        'enrollment__course',
        'issued_by'
    )
    permission_classes = [IsAdminOrAcademic]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CertificateFilter
    search_fields = [
        'certificate_number',
        'verification_code',
        'enrollment__student__username',
        'enrollment__student__email',
        'enrollment__student__first_name',
        'enrollment__student__last_name',
        'enrollment__course__title'
    ]
    ordering_fields = ['issue_date', 'certificate_number']
    ordering = ['-issue_date']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return CertificateListSerializer
        elif self.action == 'create':
            return CertificateCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return CertificateUpdateSerializer
        elif self.action == 'bulk_issue':
            return BulkCertificateIssueSerializer
        elif self.action == 'pending':
            return PendingCertificateSerializer
        return CertificateSerializer
    
    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = Certificate.objects.select_related(
            'enrollment__student',
            'enrollment__course',
            'issued_by'
        )
        
        # Filter by student
        student_id = self.request.query_params.get('student', None)
        if student_id:
            queryset = queryset.filter(enrollment__student_id=student_id)
        
        # Filter by course
        course_id = self.request.query_params.get('course', None)
        if course_id:
            queryset = queryset.filter(enrollment__course_id=course_id)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if start_date:
            queryset = queryset.filter(issue_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(issue_date__lte=end_date)
        
        # Filter by public status
        is_public = self.request.query_params.get('is_public', None)
        if is_public is not None:
            is_public = is_public.lower() == 'true'
            queryset = queryset.filter(is_public=is_public)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download certificate file."""
        certificate = self.get_object()
        
        if not certificate.certificate_file:
            return Response(
                {'error': 'No certificate file available for download.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            return FileResponse(
                certificate.certificate_file.open('rb'),
                as_attachment=True,
                filename=f"{certificate.certificate_number}.pdf"
            )
        except Exception as e:
            return Response(
                {'error': f'Error downloading file: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def toggle_public(self, request, pk=None):
        """Toggle certificate public visibility."""
        certificate = self.get_object()
        is_public = certificate.toggle_public()
        
        return Response({
            'message': f"Certificate is now {'public' if is_public else 'private'}.",
            'is_public': is_public
        })
    
    @action(detail=False, methods=['post'])
    def bulk_issue(self, request):
        """Issue certificates for multiple enrollments at once."""
        serializer = BulkCertificateIssueSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        from enrollments.models import Enrollment
        
        enrollment_ids = serializer.validated_data['enrollment_ids']
        issue_date = serializer.validated_data['issue_date']
        is_public = serializer.validated_data['is_public']
        
        # Get enrollments
        enrollments = Enrollment.objects.filter(id__in=enrollment_ids)
        
        # Create certificates
        certificates_created = []
        errors = []
        
        for enrollment in enrollments:
            try:
                certificate = Certificate.objects.create(
                    enrollment=enrollment,
                    issue_date=issue_date,
                    is_public=is_public,
                    issued_by=request.user
                )
                certificates_created.append(certificate)
            except Exception as e:
                errors.append({
                    'enrollment_id': enrollment.id,
                    'error': str(e)
                })
        
        response_data = {
            'message': f'Successfully issued {len(certificates_created)} certificate(s).',
            'certificates_created': len(certificates_created),
            'certificates': CertificateListSerializer(certificates_created, many=True).data
        }
        
        if errors:
            response_data['errors'] = errors
        
        return Response(response_data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get enrollments that are completed but don't have certificates yet."""
        pending_enrollments = Certificate.get_pending_certificates()
        
        # Filter by course if provided
        course_id = request.query_params.get('course', None)
        if course_id:
            pending_enrollments = pending_enrollments.filter(course_id=course_id)
        
        # Search by student name or email
        search = request.query_params.get('search', None)
        if search:
            pending_enrollments = pending_enrollments.filter(
                Q(student__first_name__icontains=search) |
                Q(student__last_name__icontains=search) |
                Q(student__email__icontains=search)
            )
        
        page = self.paginate_queryset(pending_enrollments)
        if page is not None:
            serializer = PendingCertificateSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = PendingCertificateSerializer(pending_enrollments, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get comprehensive certificate statistics."""
        queryset = self.get_queryset()
        
        # Basic counts
        total_certificates = queryset.count()
        public_certificates = queryset.filter(is_public=True).count()
        private_certificates = total_certificates - public_certificates
        
        # Certificates this month
        today = timezone.now().date()
        first_day_of_month = today.replace(day=1)
        certificates_this_month = queryset.filter(
            issue_date__gte=first_day_of_month
        ).count()
        
        # Certificates this year
        first_day_of_year = today.replace(month=1, day=1)
        certificates_this_year = queryset.filter(
            issue_date__gte=first_day_of_year
        ).count()
        
        # Certificates by month (last 6 months)
        six_months_ago = today - timedelta(days=180)
        monthly_certificates = []
        
        for i in range(6):
            month_start = six_months_ago + timedelta(days=30*i)
            month_end = month_start + timedelta(days=30)
            count = queryset.filter(
                issue_date__gte=month_start,
                issue_date__lt=month_end
            ).count()
            monthly_certificates.append({
                'month': month_start.strftime('%Y-%m'),
                'count': count
            })
        
        # Certificates by course
        from courses.models import Course
        courses_with_certs = Course.objects.filter(
            enrollments__certificate__isnull=False
        ).annotate(
            certificate_count=Count('enrollments__certificate')
        ).order_by('-certificate_count')[:10]
        
        certificates_by_course = [
            {
                'course_id': course.id,
                'course_title': course.title,
                'certificate_count': course.certificate_count
            }
            for course in courses_with_certs
        ]
        
        # Recent certificates
        recent = queryset.order_by('-issue_date')[:5]
        recent_certificates = [
            {
                'id': cert.id,
                'certificate_number': cert.certificate_number,
                'student_name': cert.get_student_name(),
                'course_title': cert.get_course_title(),
                'issue_date': cert.issue_date
            }
            for cert in recent
        ]
        
        # Pending certificates count
        pending_count = Certificate.get_pending_certificates().count()
        
        data = {
            'total_certificates': total_certificates,
            'public_certificates': public_certificates,
            'private_certificates': private_certificates,
            'certificates_this_month': certificates_this_month,
            'certificates_this_year': certificates_this_year,
            'certificates_by_month': monthly_certificates,
            'certificates_by_course': certificates_by_course,
            'recent_certificates': recent_certificates,
            'pending_count': pending_count
        }
        
        serializer = CertificateStatisticsSerializer(data)
        return Response(serializer.data)


class StudentCertificateViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for students to view their own certificates."""
    
    serializer_class = StudentCertificateSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['issue_date']
    ordering = ['-issue_date']
    
    def get_queryset(self):
        """Return only the current user's certificates."""
        return Certificate.objects.filter(
            enrollment__student=self.request.user
        ).select_related('enrollment__course')
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download certificate file."""
        certificate = self.get_object()
        
        if not certificate.certificate_file:
            return Response(
                {'error': 'No certificate file available for download.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            return FileResponse(
                certificate.certificate_file.open('rb'),
                as_attachment=True,
                filename=f"{certificate.certificate_number}.pdf"
            )
        except Exception as e:
            return Response(
                {'error': f'Error downloading file: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PublicCertificateViewSet(viewsets.ViewSet):
    """Public-facing certificate verification endpoint."""
    
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['get', 'post'])
    def verify(self, request):
        """Verify a certificate by verification code."""
        if request.method == 'GET':
            verification_code = request.query_params.get('code', None)
        else:  # POST
            serializer = CertificateVerificationSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            verification_code = serializer.validated_data['verification_code']
        
        if not verification_code:
            return Response(
                {'error': 'Verification code is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        certificate = Certificate.verify_certificate(verification_code)
        
        if certificate:
            serializer = PublicCertificateSerializer(certificate)
            return Response({
                'valid': True,
                'certificate': serializer.data
            })
        else:
            return Response({
                'valid': False,
                'message': 'Certificate not found or is not publicly available.'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'], url_path='verify/(?P<verification_code>[^/.]+)')
    def verify_by_code(self, request, verification_code=None):
        """Alternative endpoint: verify certificate by code in URL."""
        if not verification_code:
            return Response(
                {'error': 'Verification code is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        certificate = Certificate.verify_certificate(verification_code)
        
        if certificate:
            serializer = PublicCertificateSerializer(certificate)
            return Response({
                'valid': True,
                'certificate': serializer.data
            })
        else:
            return Response({
                'valid': False,
                'message': 'Certificate not found or is not publicly available.'
            }, status=status.HTTP_404_NOT_FOUND)