# courses app
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, CourseViewSet, PublicCourseViewSet

# Create routers
admin_router = DefaultRouter()
admin_router.register(r'categories', CategoryViewSet, basename='category')
admin_router.register(r'courses', CourseViewSet, basename='course')

public_router = DefaultRouter()
public_router.register(r'courses', PublicCourseViewSet, basename='public-course')

app_name = 'courses'

urlpatterns = [
    # Admin endpoints (protected)
    path('admin/', include(admin_router.urls)),
    
    # Public endpoints (open access)
    path('public/', include(public_router.urls)),
]