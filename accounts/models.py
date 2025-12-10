from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# -----------------------------
# Profile model
# -----------------------------
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True, default=None)
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


# ----------------------------------------------------
# REMOVE duplicate Comment model (use movies.Comment)
# ----------------------------------------------------


# -----------------------------
# User Watched Movies
# -----------------------------
class WatchedMovie(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="account_user_watched_movies")
    movie = models.ForeignKey('movies.Movie', on_delete=models.CASCADE, related_name="account_movie_watched")
    watched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-watched_at']

    def __str__(self):
        return f"{self.user.username} watched {self.movie.title}"
