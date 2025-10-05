from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Enrollment


@receiver(pre_save, sender=Enrollment)
def enrollment_status_change(sender, instance, **kwargs):
    """
    Signal to handle enrollment status changes.
    You can add custom logic here, such as:
    - Sending notifications
    - Logging status changes
    - Triggering other actions
    """
    if instance.pk:  # Only for existing enrollments
        try:
            old_instance = Enrollment.objects.get(pk=instance.pk)
            
            # Check if status changed
            if old_instance.status != instance.status:
                # Log status change
                print(f"Enrollment {instance.id} status changed from {old_instance.status} to {instance.status}")
                
                # Add custom logic here
                # For example: send email notification, create audit log, etc.
                
        except Enrollment.DoesNotExist:
            pass


@receiver(post_save, sender=Enrollment)
def enrollment_created(sender, instance, created, **kwargs):
    """
    Signal triggered after enrollment is created.
    """
    if created:
        # Log enrollment creation
        print(f"New enrollment created: {instance.student.get_full_name()} enrolled in {instance.course.title}")
        
        # Add custom logic here
        # For example: send welcome email, create initial notifications, etc.