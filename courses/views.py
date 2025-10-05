# courses app
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q, Avg
from .models import Category, Course
from .serializers import (
    CategorySerializer, CategoryListSerializer,
    CourseSerializer, CourseListSerializer,
    CourseCreateUpdateSerializer, PublicCourseSerializer,
    CourseStatisticsSerializer
)
from .permissions import IsAdminOrAcademic, IsAdminOrReadOnly


class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for managing course categories."""
    
    queryset = Category.objects.all()
    permission_classes = [IsAdminOrAcademic]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return CategoryListSerializer
        return CategorySerializer
    
    def get_queryset(self):
        queryset = Category.objects.all()
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active categories."""
        categories = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(categories, many=True)
        return Response(serializer.data)


class CourseViewSet(viewsets.ModelViewSet):
    """ViewSet for managing courses."""
    
    queryset = Course.objects.select_related('category', 'created_by').prefetch_related('prerequisites')
    permission_classes = [IsAdminOrAcademic]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['level', 'category', 'is_active']
    search_fields = ['title', 'description']
    ordering_fields = ['title', 'price', 'duration', 'created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return CourseListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return CourseCreateUpdateSerializer
        return CourseSerializer
    
    def get_queryset(self):
        queryset = Course.objects.select_related('category', 'created_by').prefetch_related('prerequisites')
        
        # Filter by price range
        min_price = self.request.query_params.get('min_price', None)
        max_price = self.request.query_params.get('max_price', None)
        
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # Filter by duration range
        min_duration = self.request.query_params.get('min_duration', None)
        max_duration = self.request.query_params.get('max_duration', None)
        
        if min_duration:
            queryset = queryset.filter(duration__gte=min_duration)
        if max_duration:
            queryset = queryset.filter(duration__lte=max_duration)
        
        return queryset
    
    def perform_create(self, serializer):
        """Set created_by to current user."""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    def enrollments(self, request, pk=None):
        """Get all enrollments for a specific course."""
        course = self.get_object()
        enrollments = course.enrollments.select_related('student').all()
        
        # Simple enrollment data
        data = {
            'course': course.title,
            'total_enrollments': enrollments.count(),
            'in_progress': enrollments.filter(status='IN_PROGRESS').count(),
            'completed': enrollments.filter(status='COMPLETED').count(),
            'cancelled': enrollments.filter(status='CANCELLED').count(),
            'enrollments': [
                {
                    'id': e.id,
                    'student_name': e.student.get_full_name(),
                    'student_email': e.student.email,
                    'enrollment_date': e.enrollment_date,
                    'status': e.status,
                    'completion_date': e.completion_date
                }
                for e in enrollments
            ]
        }
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get comprehensive course statistics."""
        courses = Course.objects.all()
        
        # Basic counts
        total_courses = courses.count()
        active_courses = courses.filter(is_active=True).count()
        inactive_courses = total_courses - active_courses
        
        # Enrollments count
        total_enrollments = sum(course.get_enrollment_count() for course in courses)
        
        # Courses by level
        courses_by_level = dict(
            courses.values('level').annotate(count=Count('id')).values_list('level', 'count')
        )
        
        # Courses by category
        courses_by_category = {}
        for course in courses.select_related('category'):
            if course.category:
                cat_name = course.category.name
                courses_by_category[cat_name] = courses_by_category.get(cat_name, 0) + 1
        
        # Average completion rate
        completion_rates = [course.get_completion_rate() for course in courses if course.get_enrollment_count() > 0]
        avg_completion_rate = sum(completion_rates) / len(completion_rates) if completion_rates else 0
        
        # Top enrolled courses
        top_enrolled = [
            {
                'id': course.id,
                'title': course.title,
                'enrollment_count': course.get_enrollment_count()
            }
            for course in sorted(courses, key=lambda c: c.get_enrollment_count(), reverse=True)[:5]
        ]
        
        data = {
            'total_courses': total_courses,
            'active_courses': active_courses,
            'inactive_courses': inactive_courses,
            'total_enrollments': total_enrollments,
            'courses_by_level': courses_by_level,
            'courses_by_category': courses_by_category,
            'avg_completion_rate': round(avg_completion_rate, 2),
            'top_enrolled_courses': top_enrolled
        }
        
        serializer = CourseStatisticsSerializer(data)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle course active status."""
        course = self.get_object()
        course.is_active = not course.is_active
        course.save()
        
        serializer = self.get_serializer(course)
        return Response({
            'message': f"Course {'activated' if course.is_active else 'deactivated'} successfully.",
            'course': serializer.data
        })


class PublicCourseViewSet(viewsets.ReadOnlyModelViewSet):
    """Public-facing course catalog (read-only)."""
    
    queryset = Course.objects.filter(is_active=True).select_related('category').prefetch_related('prerequisites')
    serializer_class = PublicCourseSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['level', 'category']
    search_fields = ['title', 'description']
    ordering_fields = ['title', 'price', 'duration']
    ordering = ['title']
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def categories(self, request):
        """Get all active categories for public view."""
        categories = Category.objects.filter(is_active=True)
        serializer = CategoryListSerializer(categories, many=True)
        return Response(serializer.data)