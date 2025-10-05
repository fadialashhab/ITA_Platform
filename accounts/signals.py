from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from .models import User


@receiver(post_save, sender=User)
def add_user_to_group(sender, instance, created, **kwargs):
    """
    Automatically add users to their corresponding Django group based on role.
    This is for future role separation using Django's built-in groups.
    """
    if created or instance.role:
        # Remove user from all groups first
        instance.groups.clear()
        
        # Map roles to group names
        role_group_mapping = {
            'ADMIN': 'Admin',
            'REGISTRAR': 'Registrar',
            'ACADEMIC': 'Academic Staff',
            'FINANCE': 'Finance Staff',
            'STUDENT': 'Student',
            'TUTOR': 'Tutor',
        }
        
        group_name = role_group_mapping.get(instance.role)
        if group_name:
            group, created = Group.objects.get_or_create(name=group_name)
            instance.groups.add(group)


@receiver(post_save, sender=User)
def set_staff_status(sender, instance, created, **kwargs):
    """
    Automatically set is_staff based on role.
    Staff members need is_staff=True to access admin panel.
    """
    staff_roles = ['ADMIN', 'REGISTRAR', 'ACADEMIC', 'FINANCE']
    should_be_staff = instance.role in staff_roles
    
    if instance.is_staff != should_be_staff:
        # Avoid recursion by using update instead of save
        User.objects.filter(pk=instance.pk).update(is_staff=should_be_staff)