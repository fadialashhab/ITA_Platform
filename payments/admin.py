from django.contrib import admin
from django.utils.html import format_html
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin interface for Payment model."""
    
    list_display = [
        'receipt_number',
        'get_student_name',
        'get_course_title',
        'amount_display',
        'payment_date',
        'payment_method',
        'received_by',
        'created_at'
    ]
    
    list_filter = [
        'payment_method',
        'payment_date',
        'created_at',
        'enrollment__course',
        'received_by'
    ]
    
    search_fields = [
        'receipt_number',
        'enrollment__student__username',
        'enrollment__student__email',
        'enrollment__student__first_name',
        'enrollment__student__last_name',
        'enrollment__course__title',
        'notes'
    ]
    
    readonly_fields = [
        'receipt_number',
        'created_at',
        'updated_at',
        'get_remaining_balance'
    ]
    
    fieldsets = (
        ('Payment Information', {
            'fields': (
                'enrollment',
                'amount',
                'payment_date',
                'payment_method',
                'receipt_number'
            )
        }),
        ('Additional Information', {
            'fields': (
                'notes',
                'received_by',
                'get_remaining_balance'
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    date_hierarchy = 'payment_date'
    
    def get_student_name(self, obj):
        """Display student name."""
        return obj.enrollment.student.get_full_name()
    get_student_name.short_description = 'Student'
    get_student_name.admin_order_field = 'enrollment__student__first_name'
    
    def get_course_title(self, obj):
        """Display course title."""
        return obj.enrollment.course.title
    get_course_title.short_description = 'Course'
    get_course_title.admin_order_field = 'enrollment__course__title'
    
    def amount_display(self, obj):
        """Display amount with currency symbol."""
        return format_html('<strong>${:,.2f}</strong>', obj.amount)
    amount_display.short_description = 'Amount'
    amount_display.admin_order_field = 'amount'
    
    def get_remaining_balance(self, obj):
        """Display remaining balance."""
        balance = obj.get_remaining_balance()
        color = 'green' if balance <= 0 else 'red'
        return format_html(
            '<span style="color: {};">${:,.2f}</span>',
            color,
            balance
        )
    get_remaining_balance.short_description = 'Remaining Balance'
    
    def save_model(self, request, obj, form, change):
        """Set received_by to current user if not set."""
        if not change and not obj.received_by:
            obj.received_by = request.user
        super().save_model(request, obj, form, change)