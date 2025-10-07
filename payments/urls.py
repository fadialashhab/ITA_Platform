from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentViewSet, StudentPaymentViewSet

# Create routers
admin_router = DefaultRouter()
admin_router.register(r'payments', PaymentViewSet, basename='payment')

student_router = DefaultRouter()
student_router.register(r'payments', StudentPaymentViewSet, basename='student-payment')

app_name = 'payments'

urlpatterns = [
    # Admin endpoints (protected - admin/finance/registrar)
    path('admin/', include(admin_router.urls)),
    
    # Student endpoints (protected - students view their own)
    path('student/', include(student_router.urls)),
]