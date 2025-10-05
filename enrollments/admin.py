from django.contrib import admin
from django.utils.html import format_html
from .models import Enrollment


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    """Admin interface for Enrollment model."""
    
    list_display = [
        'id', 'student_name', 'course_title', 'enrollment_date',
        'status_badge', 'completion_date', 'verified_by_name'
    ]
    list_filter = ['status', 'enrollment_date', 'completion_date', 'course__category']
    search_fields = [
        'student__username', 'student__email',
        'student__first_name', 'student__last_name',
        'course__title'
    ]
    readonly_fields = ['created_at', 'updated_at', 'payment_summary_display']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('student', 'course', 'enrollment_date')
        }),
        ('Status', {
            'fields': ('status', 'completion_date', 'verified_by')
        }),
        ('Additional Information', {
            'fields': ('notes', 'payment_summary_display')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    autocomplete_fields = ['student', 'course', 'verified_by']
    date_hierarchy = 'enrollment_date'
    
    def student_name(self, obj):
        """Display student full name."""
        return obj.student.get_full_name()
    student_name.short_description = 'Student'
    student_name.admin_order_field = 'student__first_name'
    
    def course_title(self, obj):
        """Display course title."""
        return obj.course.title
    course_title.short_description = 'Course'
    course_title.admin_order_field = 'course__title'
    
    def status_badge(self, obj):
        """Display status with color badge."""
        colors = {
            'IN_PROGRESS': '#FFA500',
            'COMPLETED': '#28A745',
            'CANCELLED': '#DC3545'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, '#6C757D'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'
    
    def verified_by_name(self, obj):
        """Display verifier name."""
        return obj.verified_by.get_full_name() if obj.verified_by else '-'
    verified_by_name.short_description = 'Verified By'
    verified_by_name.admin_order_field = 'verified_by__first_name'
    
    def payment_summary_display(self, obj):
        """Display payment summary."""
        summary = obj.get_payment_summary()
        return format_html(
            '<strong>Course Price:</strong> ${}<br>'
            '<strong>Total Paid:</strong> ${}<br>'
            '<strong>Outstanding:</strong> ${}<br>'
            '<strong>Status:</strong> {}',
            summary['course_price'],
            summary['total_paid'],
            summary['outstanding_balance'],
            '<span style="color: green;">Fully Paid</span>' if summary['is_fully_paid'] 
            else '<span style="color: red;">Outstanding Balance</span>'
        )
    payment_summary_display.short_description = 'Payment Summary'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        queryset = super().get_queryset(request)
        return queryset.select_related('student', 'course', 'verified_by')
    
    actions = ['mark_completed', 'mark_cancelled']
    
    def mark_completed(self, request, queryset):
        """Mark selected enrollments as completed."""
        from django.utils import timezone
        count = 0
        for enrollment in queryset:
            if enrollment.status == 'IN_PROGRESS':
                enrollment.status = 'COMPLETED'
                enrollment.completion_date = timezone.now().date()
                enrollment.verified_by = request.user
                enrollment.save()
                count += 1
        
        self.message_user(request, f'{count} enrollment(s) marked as completed.')
    mark_completed.short_description = 'Mark selected as completed'
    
    def mark_cancelled(self, request, queryset):
        """Mark selected enrollments as cancelled."""
        count = queryset.filter(status='IN_PROGRESS').update(status='CANCELLED')
        self.message_user(request, f'{count} enrollment(s) marked as cancelled.')
    mark_cancelled.short_description = 'Mark selected as cancelled'