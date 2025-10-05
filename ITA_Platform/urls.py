"""
URL configuration for the institute management project.
Replace 'config' with your actual project name.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter

# Main URL patterns
urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/accounts/', include('accounts.urls')),
    path('api/courses/', include('courses.urls')),
    path('api/enrollments/', include('enrollments.urls')),
    # path('api/certifications/', include('certifications.urls')),  # Add when created
    # path('api/payments/', include('payments.urls')),  # Add when created
    
    # REST Framework browsable API login/logout
    path('api-auth/', include('rest_framework.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Customize admin site
admin.site.site_header = "Institute Management System"
admin.site.site_title = "Institute Admin"
admin.site.index_title = "Welcome to Institute Management System"