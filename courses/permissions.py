from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """Permission class for Admin users only."""
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_admin()
        )


class IsAdminOrAcademic(permissions.BasePermission):
    """Permission class for Admin or Academic staff."""
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Admin and Academic staff have full access
        if request.user.is_admin() or request.user.is_academic_staff():
            return True
        
        # Other staff can view only
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_staff_member()
        
        return False


class IsAdminOrReadOnly(permissions.BasePermission):
    """Permission class allowing Admin full access, others read-only."""
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Admin has full access
        if request.user.is_admin():
            return True
        
        # Others can only read
        return request.method in permissions.SAFE_METHODS


class CanManageCourses(permissions.BasePermission):
    """Permission for users who can manage courses."""
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        return request.user.can_manage_courses()