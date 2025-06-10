from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import os

def send_welcome_email(user_email, username):
    """
    Send a welcome email to newly registered users
    """
    subject = 'Welcome to Code Snippets!'
    html_message = render_to_string('email/welcome_email.html', {
        'username': username,
        'frontend_url': os.environ.get('FRONTEND_URL', 'http://localhost:3000'),
    })
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False 