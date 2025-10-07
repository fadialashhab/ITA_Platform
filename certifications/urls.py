# certifications app
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CertificateViewSet, StudentCertificateViewSet, PublicCertificateViewSet

# Create routers
admin_router = DefaultRouter()
admin_router.register(r'certificates', CertificateViewSet, basename='certificate')

student_router = DefaultRouter()
student_router.register(r'certificates', StudentCertificateViewSet, basename='student-certificate')

public_router = DefaultRouter()
public_router.register(r'certificates', PublicCertificateViewSet, basename='public-certificate')

app_name = 'certifications'

urlpatterns = [
    # Admin endpoints (protected - admin/academic)
    path('admin/', include(admin_router.urls)),
    
    # Student endpoints (protected - students view their own)
    path('student/', include(student_router.urls)),
    
    # Public endpoints (open access for verification)
    path('public/', include(public_router.urls)),
]