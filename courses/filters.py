import django_filters
from .models import Course, Category


class CourseFilter(django_filters.FilterSet):
    """Advanced filtering for courses."""
    
    title = django_filters.CharFilter(lookup_expr='icontains')
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    min_duration = django_filters.NumberFilter(field_name='duration', lookup_expr='gte')
    max_duration = django_filters.NumberFilter(field_name='duration', lookup_expr='lte')
    category_name = django_filters.CharFilter(field_name='category__name', lookup_expr='icontains')
    
    class Meta:
        model = Course
        fields = ['level', 'category', 'is_active']


class CategoryFilter(django_filters.FilterSet):
    """Filtering for categories."""
    
    name = django_filters.CharFilter(lookup_expr='icontains')
    
    class Meta:
        model = Category
        fields = ['is_active']