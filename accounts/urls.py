from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuthViewSet, UserViewSet, ProfileViewSet

app_name = 'accounts'

# Create router
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    # Authentication endpoints
    path('auth/login/', AuthViewSet.as_view({'post': 'login'}), name='login'),
    path('auth/logout/', AuthViewSet.as_view({'post': 'logout'}), name='logout'),
    path('auth/me/', AuthViewSet.as_view({'get': 'me'}), name='me'),
    path('auth/password/change/', AuthViewSet.as_view({'post': 'change_password'}), name='change-password'),
    
    # Profile endpoints
    path('profile/', ProfileViewSet.as_view({'get': 'me', 'patch': 'update_profile'}), name='profile'),
    
    # Include router URLs
    path('', include(router.urls)),
]