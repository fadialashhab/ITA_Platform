# Accounts App

The accounts app handles user authentication, authorization, and user management for the institute platform.

## Features

### User Model
- Custom user model with role-based access control
- Roles: ADMIN, REGISTRAR, ACADEMIC, FINANCE, STUDENT, TUTOR
- Personal information: name, email, phone
- Audit trail: created_by, timestamps
- Helper methods for role and permission checking

### Authentication
- Login/Logout with token-based authentication
- Password management (change own password)
- Admin password reset for users
- Session and token authentication support

### User Management
- Create/update/delete users (admin/registrar only)
- Role-based permissions
- User activation/deactivation
- List students and staff separately
- Search and filter capabilities

### Permissions
Custom permission classes:
- `IsAdmin` - Admin only access
- `IsAdminOrRegistrar` - Admin or Registrar access
- `IsAdminOrAcademic` - Admin or Academic staff access
- `IsAdminOrFinance` - Admin or Finance staff access
- `IsStudent` - Student only access
- `IsOwnerOrAdmin` - Object owner or admin access
- Plus permission helper methods on User model

## API Endpoints

### Authentication
```
POST   /api/accounts/auth/login/              - Login
POST   /api/accounts/auth/logout/             - Logout
GET    /api/accounts/auth/me/                 - Get current user
POST   /api/accounts/auth/password/change/    - Change own password
```

### User Management (Admin/Registrar)
```
GET    /api/accounts/users/                   - List all users
POST   /api/accounts/users/                   - Create new user
GET    /api/accounts/users/{id}/              - Get user details
PATCH  /api/accounts/users/{id}/              - Update user
DELETE /api/accounts/users/{id}/              - Delete user
GET    /api/accounts/users/students/          - List students
GET    /api/accounts/users/staff/             - List staff (admin only)
POST   /api/accounts/users/{id}/reset_password/  - Reset password (admin only)
POST   /api/accounts/users/{id}/activate/     - Activate user
POST   /api/accounts/users/{id}/deactivate/   - Deactivate user
```

### Profile
```
GET    /api/accounts/profile/                 - Get own profile
PATCH  /api/accounts/profile/                 - Update own profile
```

## Setup Instructions

### 1. Add to INSTALLED_APPS
```python
INSTALLED_APPS = [
    ...
    'rest_framework',
    'rest_framework.authtoken',
    'django_filters',
    'accounts',
]
```

### 2. Configure Custom User Model
```python
# settings.py
AUTH_USER_MODEL = 'accounts.User'
```

### 3. Configure REST Framework
```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}
```

### 4. Include URLs
```python
# project/urls.py
from django.urls import path, include

urlpatterns = [
    path('api/accounts/', include('accounts.urls')),
    ...
]
```

### 5. Run Migrations
```bash
python manage.py makemigrations accounts
python manage.py migrate
```

### 6. Create Groups
```bash
python manage.py create_groups
```

### 7. Create Superuser
```bash
python manage.py createsuperuser
```

## Usage Examples

### Creating a Student Account
```bash
curl -X POST http://localhost:8000/api/accounts/users/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+1234567890",
    "role": "STUDENT"
  }'
```

### Login
```bash
curl -X POST http://localhost:8000/api/accounts/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "SecurePass123!"
  }'
```

### Get Current User
```bash
curl -X GET http://localhost:8000/api/accounts/auth/me/ \
  -H "Authorization: Token YOUR_TOKEN"
```

### List Students
```bash
curl -X GET "http://localhost:8000/api/accounts/users/students/?search=john" \
  -H "Authorization: Token YOUR_TOKEN"
```

### Reset User Password (Admin)
```bash
curl -X POST http://localhost:8000/api/accounts/users/5/reset_password/ \
  -H "Authorization: Token ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "new_password": "NewPass123!",
    "new_password_confirm": "NewPass123!"
  }'
```

## Role Permissions Matrix

| Action | Admin | Registrar | Academic | Finance | Student |
|--------|-------|-----------|----------|---------|---------|
| Create users | ✅ | ✅ (students/tutors only) | ❌ | ❌ | ❌ |
| View all users | ✅ | ✅ (students/tutors only) | ❌ | ❌ | ❌ |
| Update users | ✅ | ❌ | ❌ | ❌ | Own only |
| Delete users | ✅ | ❌ | ❌ | ❌ | ❌ |
| Reset passwords | ✅ | ❌ | ❌ | ❌ | ❌ |
| Activate/Deactivate | ✅ | ❌ | ❌ | ❌ | ❌ |

## Testing

Run tests:
```bash
python manage.py test accounts
```

Run specific test class:
```bash
python manage.py test accounts.tests.UserModelTest
```

## Models Reference

### User Model Fields
- **Authentication**: username, email, password
- **Personal**: first_name, last_name, phone_number
- **Role**: role (choices: ADMIN/REGISTRAR/ACADEMIC/FINANCE/STUDENT/TUTOR)
- **Status**: is_active, is_staff, is_superuser
- **Timestamps**: date_joined, last_login, created_at, updated_at
- **Audit**: created_by (FK to User)

### Helper Methods
- `get_full_name()` - Returns first_name + last_name
- `is_admin()` - Check if user is admin
- `is_student()` - Check if user is student
- `is_staff_member()` - Check if user is any staff role
- `can_create_users()` - Check if user can create accounts
- `can_manage_courses()` - Check if user can manage courses
- `can_verify_completion()` - Check if user can verify completions
- `can_issue_certificates()` - Check if user can issue certificates
- `can_record_payments()` - Check if user can record payments
- `can_view_financial_reports()` - Check if user can view reports

## Signals

### Auto Group Assignment
When a user is created or their role changes, they are automatically added to the corresponding Django group.

### Auto Staff Status
Users with staff roles (ADMIN, REGISTRAR, ACADEMIC, FINANCE) automatically get `is_staff=True`.