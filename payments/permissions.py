from rest_framework import permissions


class IsAdminOrFinance(permissions.BasePermission):
    """
    Permission class that allows access only to Admin and Finance staff.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['ADMIN', 'FINANCE']
        )


class IsAdminOrRegistrarOrFinance(permissions.BasePermission):
    """
    Permission class that allows access to Admin, Registrar, and Finance staff.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['ADMIN', 'REGISTRAR', 'FINANCE']
        )


class IsStudent(permissions.BasePermission):
    """
    Permission class that allows access only to students.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role == 'STUDENT'
        )