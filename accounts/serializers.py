# accountsapp
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Full user serializer for admin operations."""
    
    full_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'phone_number', 'role', 'is_active', 'date_joined', 'last_login',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login', 'created_at', 'updated_at']
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    
    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else None


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new users (admin/registrar)."""
    
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone_number', 'role', 'is_active'
        ]
    
    def validate(self, attrs):
        """Validate password confirmation matches."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def validate_role(self, value):
        """Validate role assignment based on creator's permissions."""
        request = self.context.get('request')
        if request and request.user:
            # Registrars can only create students and tutors
            if request.user.is_registrar() and value not in ['STUDENT', 'TUTOR']:
                raise serializers.ValidationError(
                    "Registrars can only create student and tutor accounts."
                )
            # Only admins can create other staff members
            if value in ['ADMIN', 'REGISTRAR', 'ACADEMIC', 'FINANCE'] and not request.user.is_admin():
                raise serializers.ValidationError(
                    "Only administrators can create staff accounts."
                )
        return value
    
    def create(self, validated_data):
        """Create a new user with hashed password."""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        # Set created_by from request
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        
        # Create user
        user = User.objects.create_user(password=password, **validated_data)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating existing users."""
    
    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'phone_number', 
            'role', 'is_active'
        ]
    
    def validate_role(self, value):
        """Validate role changes based on requester's permissions."""
        request = self.context.get('request')
        if request and request.user:
            # Only admins can change roles to/from staff positions
            if value in ['ADMIN', 'REGISTRAR', 'ACADEMIC', 'FINANCE'] and not request.user.is_admin():
                raise serializers.ValidationError(
                    "Only administrators can assign staff roles."
                )
        return value


class UserListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for user lists."""
    
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'full_name', 'role', 
            'is_active', 'date_joined'
        ]
    
    def get_full_name(self, obj):
        return obj.get_full_name()


class StudentSerializer(serializers.ModelSerializer):
    """Serializer specifically for student users."""
    
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'full_name', 'phone_number', 'date_joined', 'is_active'
        ]
    
    def get_full_name(self, obj):
        return obj.get_full_name()


class PasswordResetSerializer(serializers.Serializer):
    """Serializer for admin password reset."""
    
    new_password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True, required=True)
    
    def validate(self, attrs):
        """Validate password confirmation matches."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return attrs


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for user changing their own password."""
    
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True, required=True)
    
    def validate_old_password(self, value):
        """Validate old password is correct."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value
    
    def validate(self, attrs):
        """Validate new password confirmation matches."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return attrs


class ProfileSerializer(serializers.ModelSerializer):
    """Serializer for user viewing/updating their own profile."""
    
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'full_name', 'phone_number', 'role', 'date_joined'
        ]
        read_only_fields = ['id', 'username', 'role', 'date_joined']
    
    def get_full_name(self, obj):
        return obj.get_full_name()


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    
    username = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)