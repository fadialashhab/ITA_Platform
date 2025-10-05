from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """Permission class for administrators only."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_admin()


class IsAdminOrRegistrar(permissions.BasePermission):
    """Permission class for administrators and registrars."""
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['ADMIN', 'REGISTRAR']
        )


class IsAdminOrAcademic(permissions.BasePermission):
    """Permission class for administrators and academic staff."""
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['ADMIN', 'ACADEMIC']
        )


class IsAdminOrFinance(permissions.BasePermission):
    """Permission class for administrators and finance staff."""
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['ADMIN', 'FINANCE']
        )


class IsStudent(permissions.BasePermission):
    """Permission class for students only."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_student()


class IsTutor(permissions.BasePermission):
    """Permission class for tutors only."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_tutor()


class IsStaffMember(permissions.BasePermission):
    """Permission class for any staff member (not students)."""
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_staff_member()
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission class that allows owners to view/edit their own data,
    or administrators to view/edit any data.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admins can access everything
        if request.user.is_admin():
            return True
        
        # Check if the object is the user themselves
        if hasattr(obj, 'id') and obj.id == request.user.id:
            return True
        
        # Check if the object has a 'user' or 'student' attribute
        if hasattr(obj, 'user') and obj.user == request.user:
            return True
        
        if hasattr(obj, 'student') and obj.student == request.user:
            return True
        
        return False


class CanCreateUsers(permissions.BasePermission):
    """Permission class for creating user accounts."""
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.can_create_users()
        )


class CanManageCourses(permissions.BasePermission):
    """Permission class for managing courses."""
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.can_manage_courses()
        )


class CanVerifyCompletion(permissions.BasePermission):
    """Permission class for verifying course completion."""
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.can_verify_completion()
        )


class CanIssueCertificates(permissions.BasePermission):
    """Permission class for issuing certificates."""
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.can_issue_certificates()
        )


class CanRecordPayments(permissions.BasePermission):
    """Permission class for recording payments."""
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.can_record_payments()
        )


class CanViewFinancialReports(permissions.BasePermission):
    """Permission class for viewing financial reports."""
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.can_view_financial_reports()
        )