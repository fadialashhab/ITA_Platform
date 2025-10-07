import django_filters
from .models import Payment


class PaymentFilter(django_filters.FilterSet):
    """Filter class for Payment model."""
    
    # Date range filters
    payment_date_from = django_filters.DateFilter(
        field_name='payment_date',
        lookup_expr='gte',
        label='Payment Date From'
    )
    payment_date_to = django_filters.DateFilter(
        field_name='payment_date',
        lookup_expr='lte',
        label='Payment Date To'
    )
    
    # Amount range filters
    amount_min = django_filters.NumberFilter(
        field_name='amount',
        lookup_expr='gte',
        label='Minimum Amount'
    )
    amount_max = django_filters.NumberFilter(
        field_name='amount',
        lookup_expr='lte',
        label='Maximum Amount'
    )
    
    # Student filter
    student = django_filters.NumberFilter(
        field_name='enrollment__student__id',
        label='Student ID'
    )
    student_name = django_filters.CharFilter(
        field_name='enrollment__student__first_name',
        lookup_expr='icontains',
        label='Student Name'
    )
    
    # Course filter
    course = django_filters.NumberFilter(
        field_name='enrollment__course__id',
        label='Course ID'
    )
    course_title = django_filters.CharFilter(
        field_name='enrollment__course__title',
        lookup_expr='icontains',
        label='Course Title'
    )
    
    # Payment method filter
    payment_method = django_filters.ChoiceFilter(
        choices=Payment.PAYMENT_METHOD_CHOICES,
        label='Payment Method'
    )
    
    # Enrollment filter
    enrollment = django_filters.NumberFilter(
        field_name='enrollment__id',
        label='Enrollment ID'
    )
    
    # Received by filter
    received_by = django_filters.NumberFilter(
        field_name='received_by__id',
        label='Received By (User ID)'
    )
    
    # Receipt number filter
    receipt_number = django_filters.CharFilter(
        field_name='receipt_number',
        lookup_expr='icontains',
        label='Receipt Number'
    )
    
    class Meta:
        model = Payment
        fields = [
            'payment_method',
            'enrollment',
            'student',
            'course',
            'received_by',
            'receipt_number'
        ]