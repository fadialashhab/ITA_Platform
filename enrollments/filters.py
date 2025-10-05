import django_filters
from django.db.models import Q
from .models import Enrollment


class EnrollmentFilter(django_filters.FilterSet):
    """Advanced filtering for enrollments."""
    
    student_name = django_filters.CharFilter(method='filter_student_name')
    course_title = django_filters.CharFilter(field_name='course__title', lookup_expr='icontains')
    start_date = django_filters.DateFilter(field_name='enrollment_date', lookup_expr='gte')
    end_date = django_filters.DateFilter(field_name='enrollment_date', lookup_expr='lte')
    completion_start = django_filters.DateFilter(field_name='completion_date', lookup_expr='gte')
    completion_end = django_filters.DateFilter(field_name='completion_date', lookup_expr='lte')
    
    class Meta:
        model = Enrollment
        fields = ['status', 'student', 'course']
    
    def filter_student_name(self, queryset, name, value):
        """Filter by student name (first or last name)."""
        return queryset.filter(
            Q(student__first_name__icontains=value) |
            Q(student__last_name__icontains=value)
        )