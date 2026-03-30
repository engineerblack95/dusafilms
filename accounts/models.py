from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from cloudinary.models import CloudinaryField  # Add this if using Cloudinary


# -----------------------------
# Profile model
# -----------------------------
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    # Use CloudinaryField for production, ImageField for local
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True, default=None)
    # Or use CloudinaryField:
    # profile_photo = CloudinaryField('image', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_otp_valid(self, minutes=5):
        if not self.otp_created_at:
            return False
        return (timezone.now() - self.otp_created_at).total_seconds() <= minutes * 60

    def clear_otp(self):
        self.otp = None
        self.otp_created_at = None
        self.save()

    def __str__(self):
        return f"profile of {self.user.username}"


# -----------------------------
# REMOVED: UserWatchedMovie
# This is now handled by movies.WatchedMovie to avoid duplication
# -----------------------------
# The WatchedMovie model in movies app handles tracking watched movies
# If you need to reference watched movies from accounts, use:
# user.user_watched_movies.all() or user.account_user_watched_movies.all()
# depending on your related_name