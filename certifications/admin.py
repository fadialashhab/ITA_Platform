# certifications app
from django.contrib import admin
from .models import Certificate


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    """Admin interface for Certificate model."""
    
    list_display = [
        'certificate_number',
        'get_student_name',
        'get_course_title',
        'issue_date',
        'is_public',
        'issued_by'
    ]
    
    list_filter = [
        'is_public',
        'issue_date',
        'enrollment__course__level',
        'enrollment__course__category'
    ]
    
    search_fields = [
        'certificate_number',
        'verification_code',
        'enrollment__student__username',
        'enrollment__student__email',
        'enrollment__student__first_name',
        'enrollment__student__last_name',
        'enrollment__course__title'
    ]
    
    readonly_fields = [
        'certificate_number',
        'verification_code',
        'created_at',
        'get_student_name',
        'get_course_title',
        'get_completion_date'
    ]
    
    fieldsets = (
        ('Certificate Information', {
            'fields': (
                'certificate_number',
                'verification_code',
                'enrollment',
                'issue_date',
                'is_public'
            )
        }),
        ('Related Information', {
            'fields': (
                'get_student_name',
                'get_course_title',
                'get_completion_date'
            )
        }),
        ('File', {
            'fields': ('certificate_file',)
        }),
        ('Audit Information', {
            'fields': (
                'issued_by',
                'created_at'
            )
        }),
    )
    
    date_hierarchy = 'issue_date'
    
    def get_student_name(self, obj):
        """Display student name."""
        return obj.get_student_name()
    get_student_name.short_description = 'Student'
    
    def get_course_title(self, obj):
        """Display course title."""
        return obj.get_course_title()
    get_course_title.short_description = 'Course'
    
    def get_completion_date(self, obj):
        """Display completion date."""
        return obj.get_completion_date()
    get_completion_date.short_description = 'Completion Date'
    
    def save_model(self, request, obj, form, change):
        """Set issued_by to current user if not set."""
        if not change:  # New object
            obj.issued_by = request.user
        super().save_model(request, obj, form, change)