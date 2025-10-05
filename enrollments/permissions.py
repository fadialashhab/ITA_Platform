from rest_framework import permissions


class IsAdminOrRegistrar(permissions.BasePermission):
    """
    Permission class that allows access to administrators and registrars.
    """
    
    def has_permission(self, request, view):
        """Check if user is admin or registrar."""
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in ['ADMIN', 'REGISTRAR']
        )


class IsAdminOrAcademic(permissions.BasePermission):
    """
    Permission class that allows access to administrators and academic staff.
    """
    
    def has_permission(self, request, view):
        """Check if user is admin or academic staff."""
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in ['ADMIN', 'ACADEMIC']
        )


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission class that allows full access to admins,
    read-only access to others.
    """
    
    def has_permission(self, request, view):
        """Check permissions based on request method."""
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'ADMIN'
        )


class IsStudent(permissions.BasePermission):
    """
    Permission class that allows access only to students.
    """
    
    def has_permission(self, request, view):
        """Check if user is a student."""
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'STUDENT'
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission class that allows access to the owner of the object or admin.
    """
    
    def has_object_permission(self, request, view, obj):
        """Check if user is owner or admin."""
        # Admin has full access
        if request.user.role == 'ADMIN':
            return True
        
        # Check if user is the student in the enrollment
        return obj.student == request.user