# 🎓 Courses App Setup Guide

## 📋 Step-by-Step Setup Instructions

### 1. Create the Courses App Directory Structure

```bash
# Create the courses app directory
mkdir courses
cd courses

# Create necessary files
touch __init__.py
touch models.py
touch serializers.py
touch views.py
touch urls.py
touch admin.py
touch apps.py
touch permissions.py
touch filters.py
touch tests.py
```

### 2. Copy the Files

Copy the content of each file from the artifacts into your project:

- `courses/__init__.py`
- `courses/models.py`
- `courses/serializers.py`
- `courses/views.py`
- `courses/urls.py`
- `courses/admin.py`
- `courses/apps.py`
- `courses/permissions.py`
- `courses/filters.py`
- `courses/tests.py`

### 3. Update Settings.py

Add `'courses'` to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ... other apps
    'accounts',
    'courses',  # Add this line
]
```

### 4. Update Main URLs (ITA_Platform/urls.py)

Add the courses URLs to your main URL configuration:

```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/accounts/', include('accounts.urls')),
    path('api/courses/', include('courses.urls')),  # Add this line
    path('api-auth/', include('rest_framework.urls')),
]
```

### 5. Create and Run Migrations

```bash
# Create migrations for the courses app
python manage.py makemigrations courses

# Apply migrations
python manage.py migrate

# If you see any issues, you can check migration status
python manage.py showmigrations
```

### 6. Create Test Data (Optional)

Create a management command or use Django shell to add test data:

```python
# Run Django shell
python manage.py shell

# In the shell, create test data:
from accounts.models import User
from courses.models import Category, Course
from decimal import Decimal

# Create an admin user if you haven't
admin = User.objects.create_user(
    username='admin',
    email='admin@institute.com',
    password='admin123',
    first_name='Admin',
    last_name='User',
    role='ADMIN',
    is_staff=True
)

# Create categories
programming = Category.objects.create(
    name='Programming',
    description='Programming and software development courses'
)

design = Category.objects.create(
    name='Design',
    description='Graphic and web design courses'
)

business = Category.objects.create(
    name='Business',
    description='Business and management courses'
)

# Create courses
python_basics = Course.objects.create(
    title='Python Programming Basics',
    description='Learn Python from scratch with hands-on projects',
    duration=40,
    price=Decimal('10000.00'),
    level='BEGINNER',
    category=programming,
    created_by=admin
)

python_advanced = Course.objects.create(
    title='Advanced Python Development',
    description='Master advanced Python concepts and frameworks',
    duration=60,
    price=Decimal('15000.00'),
    level='ADVANCED',
    category=programming,
    created_by=admin
)

# Set prerequisites
python_advanced.prerequisites.add(python_basics)

web_design = Course.objects.create(
    title='Web Design Fundamentals',
    description='Learn HTML, CSS, and responsive design',
    duration=35,
    price=Decimal('8000.00'),
    level='BEGINNER',
    category=design,
    created_by=admin
)

print("Test data created successfully!")
```

### 7. Test the API Endpoints

#### Get Authentication Token (if using Token Auth)

```bash
# Login to get token
curl -X POST http://localhost:8000/api/accounts/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

#### Test Admin Endpoints (requires authentication)

```bash
# List all categories
curl http://localhost:8000/api/courses/admin/categories/ \
  -H "Authorization: Token YOUR_TOKEN_HERE"

# List all courses
curl http://localhost:8000/api/courses/admin/courses/ \
  -H "Authorization: Token YOUR_TOKEN_HERE"

# Create a new category
curl -X POST http://localhost:8000/api/courses/admin/categories/ \
  -H "Authorization: Token YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"name":"Data Science","description":"Data science courses","is_active":true}'

# Create a new course
curl -X POST http://localhost:8000/api/courses/admin/courses/ \
  -H "Authorization: Token YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "title":"JavaScript Essentials",
    "description":"Learn JavaScript programming",
    "duration":45,
    "price":"12000.00",
    "level":"BEGINNER",
    "category":1,
    "is_active":true
  }'

# Get course statistics
curl http://localhost:8000/api/courses/admin/courses/statistics/ \
  -H "Authorization: Token YOUR_TOKEN_HERE"
```

#### Test Public Endpoints (no authentication required)

```bash
# Browse public course catalog
curl http://localhost:8000/api/courses/public/courses/

# Get specific course details
curl http://localhost:8000/api/courses/public/courses/1/

# Filter courses by level
curl http://localhost:8000/api/courses/public/courses/?level=BEGINNER

# Filter courses by category
curl http://localhost:8000/api/courses/public/courses/?category=1

# Search courses
curl http://localhost:8000/api/courses/public/courses/?search=python

# Get categories
curl http://localhost:8000/api/courses/public/courses/categories/
```

### 8. Access Django Admin

1. Start the development server:

   ```bash
   python manage.py runserver
   ```

2. Visit: `http://localhost:8000/admin/`

3. Login with your admin credentials

4. You should see:
   - **Course Management** section with:
     - Categories
     - Courses

### 9. Run Tests

```bash
# Run all courses app tests
python manage.py test courses

# Run with verbose output
python manage.py test courses --verbosity=2

# Run specific test class
python manage.py test courses.tests.CourseModelTest
```

## 📊 Available API Endpoints

### Admin Endpoints (Authentication Required)

| Method | Endpoint                                         | Description            | Permission     |
| ------ | ------------------------------------------------ | ---------------------- | -------------- |
| GET    | `/api/courses/admin/categories/`                 | List all categories    | Admin/Academic |
| POST   | `/api/courses/admin/categories/`                 | Create category        | Admin/Academic |
| GET    | `/api/courses/admin/categories/{id}/`            | Get category details   | Admin/Academic |
| PATCH  | `/api/courses/admin/categories/{id}/`            | Update category        | Admin/Academic |
| DELETE | `/api/courses/admin/categories/{id}/`            | Delete category        | Admin/Academic |
| GET    | `/api/courses/admin/categories/active/`          | Get active categories  | Admin/Academic |
|        |                                                  |                        |                |
| GET    | `/api/courses/admin/courses/`                    | List all courses       | Admin/Academic |
| POST   | `/api/courses/admin/courses/`                    | Create course          | Admin/Academic |
| GET    | `/api/courses/admin/courses/{id}/`               | Get course details     | Admin/Academic |
| PATCH  | `/api/courses/admin/courses/{id}/`               | Update course          | Admin/Academic |
| DELETE | `/api/courses/admin/courses/{id}/`               | Delete course          | Admin/Academic |
| GET    | `/api/courses/admin/courses/{id}/enrollments/`   | Get course enrollments | Admin/Academic |
| GET    | `/api/courses/admin/courses/statistics/`         | Get course statistics  | Admin/Academic |
| POST   | `/api/courses/admin/courses/{id}/toggle_active/` | Toggle course status   | Admin/Academic |

### Public Endpoints (No Authentication)

| Method | Endpoint                                  | Description           |
| ------ | ----------------------------------------- | --------------------- |
| GET    | `/api/courses/public/courses/`            | Browse course catalog |
| GET    | `/api/courses/public/courses/{id}/`       | Get course details    |
| GET    | `/api/courses/public/courses/categories/` | Get active categories |

### Query Parameters

**For course listing:**

- `?level=BEGINNER|INTERMEDIATE|ADVANCED` - Filter by level
- `?category=1` - Filter by category ID
- `?is_active=true|false` - Filter by active status
- `?search=python` - Search in title and description
- `?min_price=5000&max_price=15000` - Filter by price range
- `?min_duration=30&max_duration=60` - Filter by duration
- `?ordering=-created_at` - Order results

## 🔐 Permission Summary

| Role          | List        | Create | Update | Delete | Statistics |
| ------------- | ----------- | ------ | ------ | ------ | ---------- |
| **Admin**     | ✅          | ✅     | ✅     | ✅     | ✅         |
| **Academic**  | ✅          | ✅     | ✅     | ✅     | ✅         |
| **Registrar** | ✅          | ❌     | ❌     | ❌     | ✅         |
| **Finance**   | ✅          | ❌     | ❌     | ❌     | ❌         |
| **Student**   | ✅ (public) | ❌     | ❌     | ❌     | ❌         |
| **Public**    | ✅ (public) | ❌     | ❌     | ❌     | ❌         |

## 🐛 Troubleshooting

### Issue: Migration errors

**Solution:**

```bash
# Delete existing migrations (if any)
rm courses/migrations/0001_initial.py

# Create fresh migrations
python manage.py makemigrations courses
python manage.py migrate
```

### Issue: Import errors

**Solution:**
Make sure all dependencies are installed:

```bash
pip install djangorestframework django-filter django-cors-headers
```

### Issue: Permission denied errors

**Solution:**
Check that:

1. User is authenticated
2. User has the correct role (ADMIN or ACADEMIC for course management)
3. Token is included in Authorization header

### Issue: Circular prerequisite error

**Solution:**
This is by design. A course cannot:

- Be its own prerequisite
- Have a prerequisite that already lists it as a prerequisite

## ✅ Verification Checklist

- [ ] Courses app created and added to INSTALLED_APPS
- [ ] All files copied and in correct locations
- [ ] Migrations created and applied successfully
- [ ] Admin interface accessible and shows Categories/Courses
- [ ] Public API endpoints accessible without authentication
- [ ] Admin API endpoints require authentication
- [ ] Can create categories through API
- [ ] Can create courses with prerequisites
- [ ] Circular prerequisite validation works
- [ ] Course statistics endpoint returns correct data
- [ ] Tests pass successfully

## 📚 Next Steps

After setting up the courses app:

1. **Create Enrollments App** - Track student course enrollments
2. **Create Certifications App** - Generate and verify certificates
3. **Create Payments App** - Track course payments
4. **Implement Student Portal** - Allow students to view and enroll in courses

## 🎯 Key Features Implemented

✅ Category management with active/inactive status
✅ Course CRUD operations
✅ Course levels (Beginner, Intermediate, Advanced)
✅ Course prerequisites with circular dependency prevention
✅ Public course catalog (no auth required)
✅ Admin course management (auth required)
✅ Course statistics and analytics
✅ Advanced filtering and search
✅ Comprehensive permissions system
✅ Django admin integration with custom displays
✅ Unit tests for models

---

**Ready for Production?** Make sure to:

- Change DEBUG = False in settings
- Set proper SECRET_KEY
- Configure production database (PostgreSQL recommended)
- Set up proper static file serving
- Enable HTTPS
- Configure CORS for your frontend domain
