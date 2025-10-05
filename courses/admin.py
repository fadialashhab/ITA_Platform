from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Course


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin configuration for Category model."""
    
    list_display = ['name', 'active_courses_count', 'is_active_badge', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def active_courses_count(self, obj):
        """Display count of active courses."""
        count = obj.get_active_courses_count()
        return format_html(
            '<span style="font-weight: bold;">{}</span>',
            count
        )
    active_courses_count.short_description = 'Active Courses'
    
    def is_active_badge(self, obj):
        """Display active status as badge."""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #28a745; color: white; '
                'padding: 3px 10px; border-radius: 3px;">Active</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; '
            'padding: 3px 10px; border-radius: 3px;">Inactive</span>'
        )
    is_active_badge.short_description = 'Status'


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """Admin configuration for Course model."""
    
    list_display = [
        'title', 'level_badge', 'category', 'price_display',
        'duration_display', 'enrollment_stats', 'is_active_badge', 'created_at'
    ]
    list_filter = ['level', 'category', 'is_active', 'created_at']
    search_fields = ['title', 'description']
    ordering = ['-created_at']
    filter_horizontal = ['prerequisites']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'category')
        }),
        ('Course Details', {
            'fields': ('level', 'duration', 'price')
        }),
        ('Prerequisites', {
            'fields': ('prerequisites',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Audit Information', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_by', 'created_at', 'updated_at']
    
    def save_model(self, request, obj, form, change):
        """Set created_by to current user if creating new course."""
        if not change:  # Only for new courses
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def level_badge(self, obj):
        """Display level as colored badge."""
        colors = {
            'BEGINNER': '#17a2b8',
            'INTERMEDIATE': '#ffc107',
            'ADVANCED': '#dc3545'
        }
        color = colors.get(obj.level, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_level_display()
        )
    level_badge.short_description = 'Level'
    
    def price_display(self, obj):
        """Display formatted price."""
        return format_html(
            '<span style="font-weight: bold; color: #28a745;">${:,.2f}</span>',
            obj.price
        )
    price_display.short_description = 'Price'
    
    def duration_display(self, obj):
        """Display duration in hours."""
        return f"{obj.duration} hrs"
    duration_display.short_description = 'Duration'
    
    def enrollment_stats(self, obj):
        """Display enrollment statistics."""
        total = obj.get_enrollment_count()
        active = obj.get_active_enrollment_count()
        completed = obj.get_completion_count()
        
        return format_html(
            '<div style="font-size: 11px;">'
            '<strong>Total:</strong> {} | '
            '<strong>Active:</strong> {} | '
            '<strong>Completed:</strong> {}'
            '</div>',
            total, active, completed
        )
    enrollment_stats.short_description = 'Enrollments'
    
    def is_active_badge(self, obj):
        """Display active status as badge."""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #28a745; color: white; '
                'padding: 3px 10px; border-radius: 3px;">Active</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; '
            'padding: 3px 10px; border-radius: 3px;">Inactive</span>'
        )
    is_active_badge.short_description = 'Status'