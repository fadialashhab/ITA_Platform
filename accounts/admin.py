from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from .models import User


class CustomUserCreationForm(UserCreationForm):
    """Custom form for creating users in admin."""
    
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')


class CustomUserChangeForm(UserChangeForm):
    """Custom form for updating users in admin."""
    
    class Meta(UserChangeForm.Meta):
        model = User
        fields = '__all__'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom admin for User model."""
    
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    
    list_display = [
        'username', 'email', 'full_name', 'role', 
        'is_active', 'date_joined', 'created_by'
    ]
    list_filter = ['role', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone_number']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone_number')
        }),
        ('Role & Permissions', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined')
        }),
        ('Audit Information', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'email', 'password1', 'password2',
                'first_name', 'last_name', 'phone_number', 'role', 'is_active'
            ),
        }),
    )
    
    readonly_fields = ['date_joined', 'last_login', 'created_at', 'updated_at', 'created_by']
    
    def full_name(self, obj):
        """Display full name in list view."""
        return obj.get_full_name()
    full_name.short_description = 'Full Name'
    
    def save_model(self, request, obj, form, change):
        """Set created_by when creating a new user through admin."""
        if not change:  # Only set on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)