# certifications app
import django_filters
from .models import Certificate


class CertificateFilter(django_filters.FilterSet):
    """Filter set for Certificate model."""
    
    # Date range filters
    issue_date_from = django_filters.DateFilter(
        field_name='issue_date',
        lookup_expr='gte',
        label='Issue date from'
    )
    issue_date_to = django_filters.DateFilter(
        field_name='issue_date',
        lookup_expr='lte',
        label='Issue date to'
    )
    
    # Student filters
    student = django_filters.NumberFilter(
        field_name='enrollment__student_id',
        label='Student ID'
    )
    student_name = django_filters.CharFilter(
        field_name='enrollment__student__first_name',
        lookup_expr='icontains',
        label='Student first name'
    )
    
    # Course filters
    course = django_filters.NumberFilter(
        field_name='enrollment__course_id',
        label='Course ID'
    )
    course_level = django_filters.ChoiceFilter(
        field_name='enrollment__course__level',
        choices=[
            ('BEGINNER', 'Beginner'),
            ('INTERMEDIATE', 'Intermediate'),
            ('ADVANCED', 'Advanced'),
        ],
        label='Course level'
    )
    course_category = django_filters.NumberFilter(
        field_name='enrollment__course__category_id',
        label='Course category ID'
    )
    
    # Certificate fields
    is_public = django_filters.BooleanFilter(
        field_name='is_public',
        label='Is public'
    )
    has_file = django_filters.BooleanFilter(
        method='filter_has_file',
        label='Has certificate file'
    )
    
    # Issued by filter
    issued_by = django_filters.NumberFilter(
        field_name='issued_by_id',
        label='Issued by user ID'
    )
    
    class Meta:
        model = Certificate
        fields = [
            'is_public', 'issue_date_from', 'issue_date_to',
            'student', 'course', 'course_level', 'course_category',
            'issued_by'
        ]
    
    def filter_has_file(self, queryset, name, value):
        """Filter certificates that have or don't have a file."""
        if value:
            return queryset.exclude(certificate_file='')
        else:
            return queryset.filter(certificate_file='')