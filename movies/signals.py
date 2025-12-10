from django.db import models       # <-- You forgot this import
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Comment, Movie

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
