from django.db import models
from django.utils.text import slugify
from django.utils.timezone import now
from django.contrib.auth.models import User


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(blank=True, unique=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Movie(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="movies"
    )
    thumbnail = models.ImageField(upload_to="thumbnails/", null=True, blank=True)

    # Updated fields
    video_url = models.URLField(max_length=500)
    download_link = models.URLField(max_length=500, blank=True, null=True)

    slug = models.SlugField(blank=True, unique=True)
    upload_time = models.DateTimeField(default=now)

    class Meta:
        ordering = ['-upload_time']

    @property
    def comments_count(self):
        return self.movie_comments.count()

    @property
    def related_movies(self):
        return Movie.objects.filter(category=self.category).exclude(id=self.id)[:6]

    @property
    def time_ago(self):
        from django.utils.timesince import timesince
        return timesince(self.upload_time)

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

    # Logged-in user (optional)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="user_comments",
        null=True,
        blank=True
    )

    # Guest commenter name
    guest_name = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        default="Guest"
    )

    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

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

    def __str__(self):
        return f"{self.user.username} watched {self.movie.title}"
