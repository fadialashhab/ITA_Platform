# certifications app
"""
Signals for automatic certificate-related actions.
Uncomment and modify based on your business requirements.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from enrollments.models import Enrollment
from .models import Certificate


# Example: Auto-issue certificate when enrollment is completed
# Uncomment if you want automatic certificate generation

# @receiver(post_save, sender=Enrollment)
# def auto_issue_certificate(sender, instance, created, **kwargs):
#     """
#     Automatically issue a certificate when an enrollment is marked as completed.
#     Only runs if enrollment status is COMPLETED and no certificate exists yet.
#     """
#     if instance.status == 'COMPLETED' and not hasattr(instance, 'certificate'):
#         # Check if enrollment has completion date
#         if instance.completion_date:
#             try:
#                 Certificate.objects.create(
#                     enrollment=instance,
#                     issue_date=instance.completion_date,
#                     issued_by=instance.verified_by,  # Use the person who verified completion
#                     is_public=True
#                 )
#             except Exception as e:
#                 # Log error or handle it appropriately
#                 print(f"Error auto-issuing certificate: {e}")


# Example: Send notification when certificate is issued
# @receiver(post_save, sender=Certificate)
# def notify_certificate_issued(sender, instance, created, **kwargs):
#     """
#     Send notification to student when their certificate is issued.
#     Requires email/notification system to be set up.
#     """
#     if created:
#         student = instance.enrollment.student
#         # Send email notification
#         # send_mail(
#         #     subject='Certificate Issued',
#         #     message=f'Your certificate for {instance.get_course_title()} has been issued.',
#         #     from_email='noreply@institute.com',
#         #     recipient_list=[student.email],
#         # )
#         pass