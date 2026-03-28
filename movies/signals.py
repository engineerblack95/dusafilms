from django.db import models  # Keep this import
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .models import Comment, Movie, UserCategoryFollow, NotificationLog
import logging

logger = logging.getLogger(__name__)

# ============================================
# EXISTING SIGNALS (Comment counting)
# ============================================

@receiver(post_save, sender=Comment)
def inc_comment(sender, instance, created, **kwargs):
    if created:
        Movie.objects.filter(pk=instance.movie_id).update(
            comments_count=models.F('comments_count') + 1
        )

@receiver(post_delete, sender=Comment)
def dec_comment(sender, instance, **kwargs):
    Movie.objects.filter(pk=instance.movie_id).update(
        comments_count=models.F('comments_count') - 1
    )


# ============================================
# NEW SIGNAL: Email notifications for new movies
# ============================================

@receiver(post_save, sender=Movie)
def send_new_movie_notifications(sender, instance, created, **kwargs):
    """
    Send email notifications when a new movie is uploaded
    Only sends if the movie was just created (not updated)
    """
    if not created:
        return  # Only send for new movies, not updates
    
    try:
        # Find all users who follow this movie's category
        followers = UserCategoryFollow.objects.filter(
            category=instance.category,
            receive_emails=True
        ).select_related('user')
        
        if not followers.exists():
            logger.info(f"No followers for category: {instance.category.name}")
            return
        
        # Prepare email content
        subject = f"🎬 New Movie Added: {instance.title} in {instance.category.name}"
        
        # Prepare context for email template
        context = {
            'movie': instance,
            'category': instance.category,
            'site_url': 'https://dusafilms.onrender.com',  # Your site URL
            'movie_url': f'https://dusafilms.onrender.com/movies/{instance.slug}/',
            'unsubscribe_url': 'https://dusafilms.onrender.com/accounts/notifications/',
        }
        
        # Send emails to each follower
        successful_sends = 0
        failed_sends = 0
        
        for follow in followers:
            try:
                user = follow.user
                if user.email:  # Only send if user has email
                    context['user'] = user
                    
                    # Render HTML email
                    html_message = render_to_string('emails/new_movie_notification.html', context)
                    plain_message = strip_tags(html_message)
                    
                    # Send email using Brevo (configured in settings)
                    send_mail(
                        subject=subject,
                        message=plain_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        html_message=html_message,
                        fail_silently=False,
                    )
                    successful_sends += 1
                    logger.info(f"Email sent to {user.email} for movie: {instance.title}")
                    
                    # Log successful notification
                    try:
                        NotificationLog.objects.create(
                            user=user,
                            notification_type='new_movie',
                            movie=instance,
                            category=instance.category,
                            status='sent'
                        )
                    except Exception as log_error:
                        logger.warning(f"Could not log notification: {log_error}")
                    
            except Exception as e:
                failed_sends += 1
                logger.error(f"Failed to send email to {user.email}: {str(e)}")
                
                # Log failed notification
                try:
                    NotificationLog.objects.create(
                        user=user,
                        notification_type='new_movie',
                        movie=instance,
                        category=instance.category,
                        status='failed',
                        error_message=str(e)
                    )
                except Exception as log_error:
                    logger.warning(f"Could not log failed notification: {log_error}")
                continue
        
        logger.info(f"New movie '{instance.title}' - Sent {successful_sends} emails, Failed: {failed_sends}")
        
    except Exception as e:
        logger.error(f"Error in send_new_movie_notifications: {str(e)}")


# ============================================
# OPTIONAL: Signal to update movie rating averages
# ============================================

from .models import MovieRating

@receiver(post_save, sender=MovieRating)
@receiver(post_delete, sender=MovieRating)
def update_movie_rating_avg(sender, instance, **kwargs):
    """
    Update movie's average rating when a rating is added/deleted
    Note: This requires a 'average_rating' field in Movie model
    If you don't have this field, you can skip this signal
    """
    movie = instance.movie
    ratings = movie.ratings.all()
    
    if ratings.exists():
        avg_rating = sum(r.rating for r in ratings) / ratings.count()
        # If you add an 'average_rating' field to Movie model, uncomment below:
        # Movie.objects.filter(pk=movie.pk).update(average_rating=avg_rating)
        pass  # Remove this if you add the average_rating field