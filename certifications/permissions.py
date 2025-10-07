# certifications app
from rest_framework import permissions


class IsAdminOrAcademic(permissions.BasePermission):
    """
    Permission class that allows access to admin and academic staff only.
    """
    
    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Allow admin and academic staff
        return request.user.role in ['ADMIN', 'ACADEMIC']


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission class that allows read-only access to authenticated users,
    but only admins can create/update/delete.
    """
    
    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Read permissions for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for admin
        return request.user.role == 'ADMIN'


class CanIssueCertificates(permissions.BasePermission):
    """
    Permission class for users who can issue certificates.
    Only admins and academic staff can issue certificates.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.can_issue_certificates()


class CanViewCertificate(permissions.BasePermission):
    """
    Permission class for viewing certificates.
    - Admin/Academic: Can view all certificates
    - Students: Can only view their own certificates
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Admin and academic staff can view all certificates
        if request.user.role in ['ADMIN', 'ACADEMIC']:
            return True
        
        # Students can only view their own certificates
        if request.user.role == 'STUDENT':
            return obj.enrollment.student == request.user
        
        return False