from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

def send_assessment_notification(assessment, recipient):
    subject = f'New Assessment Available: {assessment.title}'
    message = render_to_string('assessment_notification_email.html', {
        'assessment': assessment,
        'recipient': recipient,
    })
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [recipient],
        fail_silently=False,
    )