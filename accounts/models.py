# accountsapp
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator


class UserManager(BaseUserManager):
    """Custom user manager for User model."""
    
    def create_user(self, username, email, password=None, **extra_fields):
        """Create and save a regular user."""
        if not email:
            raise ValueError('Users must have an email address')
        if not username:
            raise ValueError('Users must have a username')
        
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email, password=None, **extra_fields):
        """Create and save a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'ADMIN')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(username, email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model with role-based access control."""
    
    ROLE_CHOICES = [
        ('ADMIN', 'Administrator'),
        ('REGISTRAR', 'Registrar'),
        ('ACADEMIC', 'Academic Staff'),
        ('FINANCE', 'Finance Staff'),
        ('STUDENT', 'Student'),
        ('TUTOR', 'Tutor'),
    ]
    
    # Authentication fields
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    
    # Personal information
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    phone_validator = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(validators=[phone_validator], max_length=17, blank=True)
    
    # Role and permissions
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='STUDENT')
    
    # Status fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    # Timestamps
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)
    
    # Audit fields
    created_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_users'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']
    
    class Meta:
        db_table = 'accounts_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"
    
    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name
    
    # Role checking helper methods
    def is_admin(self):
        """Check if user is an administrator."""
        return self.role == 'ADMIN'
    
    def is_registrar(self):
        """Check if user is a registrar."""
        return self.role == 'REGISTRAR'
    
    def is_academic_staff(self):
        """Check if user is academic staff."""
        return self.role == 'ACADEMIC'
    
    def is_finance_staff(self):
        """Check if user is finance staff."""
        return self.role == 'FINANCE'
    
    def is_student(self):
        """Check if user is a student."""
        return self.role == 'STUDENT'
    
    def is_tutor(self):
        """Check if user is a tutor."""
        return self.role == 'TUTOR'
    
    def is_staff_member(self):
        """Check if user is any type of staff member."""
        return self.role in ['ADMIN', 'REGISTRAR', 'ACADEMIC', 'FINANCE']
    
    # Permission helper methods
    def can_create_users(self):
        """Check if user can create other users."""
        return self.role in ['ADMIN', 'REGISTRAR']
    
    def can_manage_courses(self):
        """Check if user can manage courses."""
        return self.role in ['ADMIN', 'ACADEMIC']
    
    def can_verify_completion(self):
        """Check if user can verify course completion."""
        return self.role in ['ADMIN', 'ACADEMIC']
    
    def can_issue_certificates(self):
        """Check if user can issue certificates."""
        return self.role in ['ADMIN', 'ACADEMIC']
    
    def can_record_payments(self):
        """Check if user can record payments."""
        return self.role in ['ADMIN', 'REGISTRAR', 'FINANCE']
    
    def can_view_financial_reports(self):
        """Check if user can view financial reports."""
        return self.role in ['ADMIN', 'FINANCE']