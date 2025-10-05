from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

User = get_user_model()


class UserModelTest(TestCase):
    """Test cases for User model."""
    
    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            first_name='Admin',
            last_name='User',
            role='ADMIN'
        )
        
        self.student_user = User.objects.create_user(
            username='student',
            email='student@test.com',
            password='testpass123',
            first_name='Student',
            last_name='User',
            role='STUDENT'
        )
    
    def test_user_creation(self):
        """Test creating a user."""
        self.assertEqual(self.student_user.username, 'student')
        self.assertEqual(self.student_user.email, 'student@test.com')
        self.assertTrue(self.student_user.check_password('testpass123'))
    
    def test_get_full_name(self):
        """Test get_full_name method."""
        self.assertEqual(self.student_user.get_full_name(), 'Student User')
    
    def test_role_checking_methods(self):
        """Test role checking helper methods."""
        self.assertTrue(self.admin_user.is_admin())
        self.assertFalse(self.admin_user.is_student())
        
        self.assertTrue(self.student_user.is_student())
        self.assertFalse(self.student_user.is_admin())
    
    def test_permission_methods(self):
        """Test permission checking methods."""
        self.assertTrue(self.admin_user.can_create_users())
        self.assertTrue(self.admin_user.can_manage_courses())
        
        self.assertFalse(self.student_user.can_create_users())
        self.assertFalse(self.student_user.can_manage_courses())
    
    def test_staff_member_check(self):
        """Test is_staff_member method."""
        self.assertTrue(self.admin_user.is_staff_member())
        self.assertFalse(self.student_user.is_staff_member())


class AuthenticationAPITest(APITestCase):
    """Test cases for authentication endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            role='STUDENT'
        )
    
    def test_login_success(self):
        """Test successful login."""
        response = self.client.post('/api/accounts/auth/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertIn('user', response.data)
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        response = self.client.post('/api/accounts/auth/login/', {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_login_inactive_user(self):
        """Test login with inactive user."""
        self.user.is_active = False
        self.user.save()
        
        response = self.client.post('/api/accounts/auth/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_logout(self):
        """Test logout."""
        # Login first
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post('/api/accounts/auth/logout/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_get_current_user(self):
        """Test getting current user profile."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get('/api/accounts/auth/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')


class UserManagementAPITest(APITestCase):
    """Test cases for user management endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            first_name='Admin',
            last_name='User',
            role='ADMIN'
        )
        
        self.registrar_user = User.objects.create_user(
            username='registrar',
            email='registrar@test.com',
            password='testpass123',
            first_name='Registrar',
            last_name='User',
            role='REGISTRAR'
        )
        
        self.student_user = User.objects.create_user(
            username='student',
            email='student@test.com',
            password='testpass123',
            first_name='Student',
            last_name='User',
            role='STUDENT'
        )
    
    def test_create_user_as_admin(self):
        """Test creating a user as admin."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.post('/api/accounts/users/', {
            'username': 'newstudent',
            'email': 'newstudent@test.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'first_name': 'New',
            'last_name': 'Student',
            'role': 'STUDENT'
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='newstudent').exists())
    
    def test_create_user_unauthorized(self):
        """Test creating a user without authentication."""
        response = self.client.post('/api/accounts/users/', {
            'username': 'newstudent',
            'email': 'newstudent@test.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'first_name': 'New',
            'last_name': 'Student',
            'role': 'STUDENT'
        })
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_users_as_admin(self):
        """Test listing users as admin."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get('/api/accounts/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_get_students_list(self):
        """Test getting students list."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get('/api/accounts/users/students/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_reset_password_as_admin(self):
        """Test resetting user password as admin."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.post(
            f'/api/accounts/users/{self.student_user.id}/reset_password/',
            {
                'new_password': 'newpassword123',
                'new_password_confirm': 'newpassword123'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify password was changed
        self.student_user.refresh_from_db()
        self.assertTrue(self.student_user.check_password('newpassword123'))
    
    def test_deactivate_user(self):
        """Test deactivating a user."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.post(
            f'/api/accounts/users/{self.student_user.id}/deactivate/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.student_user.refresh_from_db()
        self.assertFalse(self.student_user.is_active)
    
    def test_cannot_deactivate_self(self):
        """Test that user cannot deactivate themselves."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.post(
            f'/api/accounts/users/{self.admin_user.id}/deactivate/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PasswordChangeTest(APITestCase):
    """Test cases for password change functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='oldpassword123',
            first_name='Test',
            last_name='User',
            role='STUDENT'
        )
    
    def test_change_password_success(self):
        """Test successful password change."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post('/api/accounts/auth/password/change/', {
            'old_password': 'oldpassword123',
            'new_password': 'newpassword123',
            'new_password_confirm': 'newpassword123'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify new password works
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpassword123'))
    
    def test_change_password_wrong_old_password(self):
        """Test password change with wrong old password."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post('/api/accounts/auth/password/change/', {
            'old_password': 'wrongpassword',
            'new_password': 'newpassword123',
            'new_password_confirm': 'newpassword123'
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_change_password_mismatch(self):
        """Test password change with mismatched new passwords."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post('/api/accounts/auth/password/change/', {
            'old_password': 'oldpassword123',
            'new_password': 'newpassword123',
            'new_password_confirm': 'differentpassword123'
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)