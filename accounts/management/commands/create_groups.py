from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Create default user groups with permissions'

    def handle(self, *args, **kwargs):
        """Create groups and assign permissions."""
        
        # Define groups and their permissions
        groups_permissions = {
            'Admin': {
                'description': 'Full access to all system features',
                'permissions': 'all'  # Will get all permissions
            },
            'Registrar': {
                'description': 'Can manage users and enrollments',
                'permissions': [
                    # User permissions
                    'add_user', 'view_user', 'change_user',
                    # Enrollment permissions (will be added when that app exists)
                    # 'add_enrollment', 'view_enrollment',
                    # Payment permissions
                    # 'add_payment', 'view_payment',
                ]
            },
            'Academic Staff': {
                'description': 'Can manage courses and verify completions',
                'permissions': [
                    # Course permissions (will be added when that app exists)
                    # 'add_course', 'change_course', 'view_course',
                    # Enrollment permissions
                    # 'view_enrollment', 'change_enrollment',
                    # Certificate permissions
                    # 'add_certificate', 'view_certificate', 'change_certificate',
                ]
            },
            'Finance Staff': {
                'description': 'Can manage payments and view financial reports',
                'permissions': [
                    # Payment permissions (will be added when that app exists)
                    # 'add_payment', 'view_payment', 'change_payment',
                    # View user for payment context
                    'view_user',
                ]
            },
            'Student': {
                'description': 'Can view own enrollments and certificates',
                'permissions': [
                    # Students don't need model permissions
                    # They use custom permissions in views
                ]
            },
            'Tutor': {
                'description': 'Can view assigned courses and students',
                'permissions': [
                    # Tutor permissions (for future expansion)
                    # 'view_course', 'view_enrollment',
                ]
            },
        }
        
        created_count = 0
        updated_count = 0
        
        for group_name, group_data in groups_permissions.items():
            group, created = Group.objects.get_or_create(name=group_name)
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created group: {group_name}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'→ Updated group: {group_name}')
                )
            
            # Clear existing permissions
            group.permissions.clear()
            
            # Assign permissions
            if group_data['permissions'] == 'all':
                # Admin gets all permissions
                all_permissions = Permission.objects.all()
                group.permissions.set(all_permissions)
                self.stdout.write(f'  Added all permissions to {group_name}')
            else:
                # Add specific permissions
                for perm_codename in group_data['permissions']:
                    try:
                        # Try to find the permission
                        permission = Permission.objects.get(codename=perm_codename)
                        group.permissions.add(permission)
                        self.stdout.write(f'  Added permission: {perm_codename}')
                    except Permission.DoesNotExist:
                        self.stdout.write(
                            self.style.WARNING(
                                f'  Permission not found: {perm_codename} (may not exist yet)'
                            )
                        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Groups setup complete! Created: {created_count}, Updated: {updated_count}'
            )
        )
        self.stdout.write(
            self.style.NOTICE(
                '\nNote: Some permissions may not exist yet. Run this command again after creating other apps.'
            )
        )