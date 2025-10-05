from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import authenticate, login, logout
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView

from .models import User
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    UserListSerializer, StudentSerializer, PasswordResetSerializer,
    PasswordChangeSerializer, ProfileSerializer, LoginSerializer
)
from .permissions import IsAdmin, IsAdminOrRegistrar


class AuthViewSet(viewsets.ViewSet):
    """ViewSet for authentication operations."""
    permission_classes = [AllowAny]
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """Login endpoint."""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        user = authenticate(username=username, password=password)
        
        if user is not None:
            if not user.is_active:
                return Response(
                    {'error': 'This account is inactive.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            login(request, user)
            
            # Create or get token for token-based authentication
            token, created = Token.objects.get_or_create(user=user)
            
            return Response({
                'token': token.key,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'full_name': user.get_full_name(),
                    'role': user.role,
                }
            })
        else:
            return Response(
                {'error': 'Invalid credentials.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """Logout endpoint."""
        try:
            # Delete the user's token
            request.user.auth_token.delete()
        except:
            pass
        
        logout(request)
        return Response({'message': 'Successfully logged out.'})
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Get current user's profile."""
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        """Change user's own password."""
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        # Set new password
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        
        return Response({'message': 'Password changed successfully.'})


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing users.
    Accessible by administrators and registrars.
    """
    queryset = User.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['role', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone_number']
    ordering_fields = ['date_joined', 'username', 'role']
    ordering = ['-date_joined']
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create', 'students', 'staff']:
            permission_classes = [IsAdminOrRegistrar]
        elif self.action in ['update', 'partial_update', 'destroy', 'reset_password']:
            permission_classes = [IsAdmin]
        else:
            permission_classes = [IsAdminOrRegistrar]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        elif self.action == 'list':
            return UserListSerializer
        elif self.action == 'students':
            return StudentSerializer
        return UserSerializer
    
    def get_queryset(self):
        """Filter queryset based on user role."""
        queryset = User.objects.all()
        
        # Registrars can only see students and tutors
        if self.request.user.is_registrar():
            queryset = queryset.filter(role__in=['STUDENT', 'TUTOR'])
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def students(self, request):
        """Get list of all students."""
        students = self.get_queryset().filter(role='STUDENT')
        
        # Apply search and filters
        students = self.filter_queryset(students)
        
        page = self.paginate_queryset(students)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(students, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def staff(self, request):
        """Get list of all staff members. Admin only."""
        if not request.user.is_admin():
            return Response(
                {'error': 'Only administrators can view staff members.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        staff = User.objects.filter(role__in=['ADMIN', 'REGISTRAR', 'ACADEMIC', 'FINANCE'])
        
        # Apply search and filters
        staff = self.filter_queryset(staff)
        
        page = self.paginate_queryset(staff)
        if page is not None:
            serializer = UserListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = UserListSerializer(staff, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        """Reset a user's password. Admin only."""
        user = self.get_object()
        
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Set new password
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({
            'message': f'Password reset successfully for user {user.username}.'
        })
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a user account."""
        user = self.get_object()
        user.is_active = True
        user.save()
        
        return Response({
            'message': f'User {user.username} activated successfully.'
        })
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a user account."""
        user = self.get_object()
        
        # Prevent self-deactivation
        if user.id == request.user.id:
            return Response(
                {'error': 'You cannot deactivate your own account.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.is_active = False
        user.save()
        
        return Response({
            'message': f'User {user.username} deactivated successfully.'
        })


class ProfileViewSet(viewsets.ViewSet):
    """ViewSet for user profile operations."""
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's profile."""
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['patch'])
    def update_profile(self, request):
        """Update current user's profile."""
        serializer = ProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data)