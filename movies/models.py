from django.db import models
from django.utils.text import slugify
from django.utils.timezone import now
from django.contrib.auth.models import User
from cloudinary.models import CloudinaryField


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(blank=True, unique=True)
    image = CloudinaryField('image', blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
    @property
    def followers_count(self):
        """Get the number of users following this category"""
        return self.followers.count()


class Movie(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="movies"
    )

    thumbnail = CloudinaryField('image', null=True, blank=True)

    # VIDEO AS URL (NOT FILE UPLOAD)
    video_url = models.URLField(max_length=500, blank=True, null=True)
    download_link = models.URLField(max_length=500, blank=True, null=True)

    slug = models.SlugField(blank=True, unique=True)
    upload_time = models.DateTimeField(default=now)
    
    # Database field for comment count (cached value)
    comments_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['-upload_time']

    def update_comments_count(self):
        """Update the cached comments count from actual comments"""
        self.comments_count = self.movie_comments.filter(is_approved=True).count()
        self.save(update_fields=['comments_count'])
    
    def get_comments_count(self):
        """Return the cached comment count from database"""
        return self.comments_count
    
    @property
    def total_comments(self):
        """Alternative property name for templates"""
        return self.comments_count

    @property
    def related_movies(self):
        return Movie.objects.filter(category=self.category).exclude(id=self.id)[:6]

    @property
    def time_ago(self):
        from django.utils.timesince import timesince
        return timesince(self.upload_time)
    
    @property
    def average_rating(self):
        """Calculate average rating for the movie"""
        ratings = self.ratings.all()
        if ratings.exists():
            total = sum(r.rating for r in ratings)
            return round(total / ratings.count(), 1)
        return 0
    
    @property
    def ratings_count(self):
        """Get total number of ratings"""
        return self.ratings.count()

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Comment(models.Model):
    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name="movie_comments"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="user_comments",
        null=True,
        blank=True
    )

    guest_name = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        default="Guest"
    )

    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Enhanced comment features
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    is_approved = models.BooleanField(default=True)  # For moderation
    likes = models.ManyToManyField(User, related_name="liked_comments", blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        if self.user:
            return f"{self.user.username} - {self.movie.title}"
        return f"{self.guest_name} - {self.movie.title}"

    @property
    def time_ago(self):
        from django.utils.timesince import timesince
        return timesince(self.created_at)
    
    @property
    def likes_count(self):
        return self.likes.count()
    
    @property
    def replies_count(self):
        """Get the number of replies to this comment"""
        return self.replies.count()
    
    def save(self, *args, **kwargs):
        """Update movie's comments_count when comment is saved"""
        super().save(*args, **kwargs)
        # Update the movie's cached comment count
        if self.is_approved:
            self.movie.update_comments_count()


class Reply(models.Model):
    """Reply to a comment - enables nested conversations"""
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name="replies"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="user_replies",
        null=True,
        blank=True
    )
    guest_name = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    is_approved = models.BooleanField(default=True)
    likes = models.ManyToManyField(User, related_name="liked_replies", blank=True)

    class Meta:
        ordering = ['created_at']  # Oldest first for chronological order

    @property
    def time_ago(self):
        from django.utils.timesince import timesince
        return timesince(self.created_at)
    
    @property
    def likes_count(self):
        return self.likes.count()
    
    def __str__(self):
        if self.user:
            return f"{self.user.username} replied to comment {self.comment.id}"
        return f"{self.guest_name} replied to comment {self.comment.id}"
    
    def save(self, *args, **kwargs):
        """Update movie's comments_count when reply is saved"""
        super().save(*args, **kwargs)
        # Update the movie's cached comment count via the parent comment
        if self.is_approved:
            self.comment.movie.update_comments_count()


class WatchedMovie(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="user_watched_movies"
    )
    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name="movie_watched"
    )
    watched_at = models.DateTimeField(default=now)

    class Meta:
        ordering = ['-watched_at']
        unique_together = ('user', 'movie')

    def __str__(self):
        return f"{self.user.username} watched {self.movie.title}"


# ============================================
# MODELS FOR EMAIL NOTIFICATIONS & FEATURES
# ============================================

class UserCategoryFollow(models.Model):
    """
    Track which categories a user wants notifications for
    This enables the email notification system for new movies
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="followed_categories"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="followers"
    )
    followed_at = models.DateTimeField(default=now)
    receive_emails = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('user', 'category')
        ordering = ['-followed_at']
    
    def __str__(self):
        return f"{self.user.email} follows {self.category.name}"


class WatchLater(models.Model):
    """
    Allow users to save movies to watch later
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="watch_later_movies"
    )
    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name="in_watch_later"
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'movie')
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.user.username} saved {self.movie.title}"


class MovieRating(models.Model):
    """
    Rating system for movies (1-5 stars)
    """
    RATING_CHOICES = [(i, i) for i in range(1, 6)]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="movie_ratings"
    )
    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name="ratings"
    )
    rating = models.IntegerField(choices=RATING_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'movie')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} rated {self.movie.title}: {self.rating}/5"


class WatchProgress(models.Model):
    """
    Track watch progress for continue watching feature
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="watch_progress"
    )
    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name="watch_progress"
    )
    progress_percent = models.FloatField(default=0)
    last_watched = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'movie')
        ordering = ['-last_watched']

    def __str__(self):
        return f"{self.user.username} watched {self.movie.title}: {self.progress_percent}%"


class NotificationLog(models.Model):
    """
    Log all email notifications sent for debugging
    """
    NOTIFICATION_TYPES = [
        ('new_movie', 'New Movie Added'),
        ('test', 'Test Notification'),
        ('weekly_digest', 'Weekly Digest'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications"
    )
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notification_logs"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notification_logs"
    )
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='sent')
    error_message = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-sent_at']
    
    def __str__(self):
        return f"{self.notification_type} to {self.user.email} at {self.sent_at}"


# ============================================
# TEAM MEMBER MODEL FOR ABOUT PAGE
# ============================================

class TeamMember(models.Model):
    """Team member information for About page"""
    
    ROLE_CHOICES = [
        ('founder', 'Founder & CEO'),
        ('manager', 'Website Manager'),
        ('developer', 'Lead Developer'),
        ('designer', 'UI/UX Designer'),
        ('support', 'Customer Support'),
        ('content', 'Content Manager'),
        ('marketing', 'Marketing Director'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=100, help_text="Full name of the team member")
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, help_text="Select the role/job title")
    job_title = models.CharField(max_length=100, blank=True, null=True, help_text="Custom job title (if 'Other' role selected)")
    bio = models.TextField(help_text="Short biography of the team member")
    photo = CloudinaryField('image', blank=True, null=True, help_text="Profile photo of team member")
    email = models.EmailField(blank=True, null=True, help_text="Email address for contact")
    phone = models.CharField(max_length=20, blank=True, null=True, help_text="Phone number with country code")
    whatsapp = models.CharField(max_length=20, blank=True, null=True, help_text="WhatsApp number with country code")
    linkedin = models.URLField(blank=True, null=True, help_text="LinkedIn profile URL")
    display_order = models.IntegerField(default=0, help_text="Lower numbers appear first")
    is_active = models.BooleanField(default=True, help_text="Show this team member on the about page")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = "Team Member"
        verbose_name_plural = "Team Members"
    
    def __str__(self):
        return f"{self.name} - {self.get_role_display()}"
    
    def get_display_role(self):
        """Get the display role (custom job title if 'other', otherwise the choice label)"""
        if self.role == 'other' and self.job_title:
            return self.job_title
        return self.get_role_display()
    
    def get_photo_url(self):
        """Get the photo URL or return None"""
        if self.photo:
            return self.photo.url
        return None