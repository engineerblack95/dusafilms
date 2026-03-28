from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_test_notification(user, category, movie=None):
    """Helper function to test email notifications"""
    try:
        subject = f"Test Notification: {category.name}"
        context = {
            'user': user,
            'category': category,
            'site_url': 'https://dusafilms.onrender.com',
            'movie': movie,
            'movie_url': f'https://dusafilms.onrender.com/movies/{movie.slug}/' if movie else None,
        }
        
        html_message = render_to_string('emails/test_notification.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Test email sent to {user.email}")
        return True
    except Exception as e:
        logger.error(f"Test email failed: {str(e)}")
        return False