"""
Signal handlers for payment-related events.
"""

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from .models import Payment


@receiver(post_save, sender=Payment)
def payment_created_handler(sender, instance, created, **kwargs):
    """
    Handle actions after a payment is created.
    """
    if created:
        # Log payment creation
        print(f"Payment created: {instance.receipt_number} - ${instance.amount}")
        
        # TODO: Send payment confirmation email
        # from .utils import send_payment_confirmation_email
        # send_payment_confirmation_email(instance)
        
        # TODO: Check if enrollment is now fully paid and trigger notifications
        # if Payment.is_enrollment_fully_paid(instance.enrollment):
        #     print(f"Enrollment {instance.enrollment.id} is now fully paid!")


@receiver(pre_delete, sender=Payment)
def payment_delete_handler(sender, instance, **kwargs):
    """
    Handle actions before a payment is deleted.
    """
    # Log payment deletion
    print(f"Payment being deleted: {instance.receipt_number} - ${instance.amount}")
    
    # TODO: Add any cleanup or notification logic here