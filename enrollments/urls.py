from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EnrollmentViewSet, StudentEnrollmentViewSet

# Create routers
admin_router = DefaultRouter()
admin_router.register(r'enrollments', EnrollmentViewSet, basename='enrollment')

student_router = DefaultRouter()
student_router.register(r'enrollments', StudentEnrollmentViewSet, basename='student-enrollment')

app_name = 'enrollments'

urlpatterns = [
    # Admin endpoints (protected - admin/registrar/academic)
    path('admin/', include(admin_router.urls)),
    
    # Student endpoints (protected - students view their own)
    path('student/', include(student_router.urls)),
]