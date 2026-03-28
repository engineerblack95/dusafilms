from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from movies.models import Movie


class WatchSession(models.Model):
    """Track individual watch sessions with real-time user presence"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='watch_sessions')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='watch_sessions')
    session_id = models.CharField(max_length=100, unique=True)
    started_at = models.DateTimeField(auto_now_add=True)
    last_heartbeat = models.DateTimeField(auto_now=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    watch_duration = models.IntegerField(default=0)  # in seconds
    is_active = models.BooleanField(default=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    device_type = models.CharField(max_length=50, blank=True)  # mobile, desktop, tablet
    
    class Meta:
        ordering = ['-last_heartbeat']
        indexes = [
            models.Index(fields=['is_active', 'last_heartbeat']),
            models.Index(fields=['movie', 'is_active']),
        ]
    
    def duration_minutes(self):
        return round(self.watch_duration / 60, 1)
    
    def duration_hours(self):
        return round(self.watch_duration / 3600, 1)
    
    def __str__(self):
        user_name = self.user.username if self.user else "Guest"
        return f"{user_name} watching {self.movie.title} ({self.duration_minutes()} min)"
    
    def save(self, *args, **kwargs):
        if self.user_agent:
            # Detect device type
            ua = self.user_agent.lower()
            if 'mobile' in ua or 'android' in ua or 'iphone' in ua:
                self.device_type = 'mobile'
            elif 'tablet' in ua or 'ipad' in ua:
                self.device_type = 'tablet'
            else:
                self.device_type = 'desktop'
        super().save(*args, **kwargs)


class DownloadTracking(models.Model):
    """Track download attempts with real progress monitoring"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('interrupted', 'Interrupted'),
    ]
    
    FAILURE_REASONS = [
        ('network_error', 'Network Error'),
        ('server_error', 'Server Error'),
        ('user_cancelled', 'User Cancelled'),
        ('connection_lost', 'Connection Lost'),
        ('timeout', 'Timeout'),
        ('storage_full', 'Storage Full'),
        ('file_not_found', 'File Not Found'),
        ('access_denied', 'Access Denied'),
        ('unknown', 'Unknown Error'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='downloads')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='downloads')
    download_id = models.CharField(max_length=100, unique=True)
    download_started = models.DateTimeField(auto_now_add=True)
    download_completed = models.DateTimeField(null=True, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    downloaded_size = models.BigIntegerField(default=0)
    download_speed = models.FloatField(null=True, blank=True)  # KB/s
    download_duration = models.IntegerField(null=True, blank=True)  # in seconds
    status = models.CharField(max_length=20, default='pending', choices=STATUS_CHOICES)
    failure_reason = models.CharField(max_length=50, null=True, blank=True, choices=FAILURE_REASONS)
    error_message = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-download_started']
        indexes = [
            models.Index(fields=['status', 'download_started']),
            models.Index(fields=['user', 'status']),
        ]
    
    def progress_percent(self):
        """Calculate download progress percentage"""
        if self.file_size and self.file_size > 0:
            return round((self.downloaded_size / self.file_size) * 100, 1)
        return 0
    
    def remaining_size(self):
        """Calculate remaining bytes to download"""
        if self.file_size:
            return max(0, self.file_size - self.downloaded_size)
        return 0
    
    def estimated_time_remaining(self):
        """Estimate time remaining based on current speed"""
        if self.download_speed and self.download_speed > 0:
            remaining_mb = self.remaining_size() / (1024 * 1024)
            return round(remaining_mb / self.download_speed, 1)  # in seconds
        return None
    
    def __str__(self):
        user_name = self.user.username if self.user else "Guest"
        return f"{user_name} - {self.movie.title} - {self.progress_percent()}% - {self.status}"


class UserEngagementStats(models.Model):
    """Aggregated user engagement statistics"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='engagement_stats')
    total_watch_time = models.BigIntegerField(default=0)  # in seconds
    total_downloads = models.IntegerField(default=0)
    completed_downloads = models.IntegerField(default=0)
    failed_downloads = models.IntegerField(default=0)
    interrupted_downloads = models.IntegerField(default=0)
    movies_watched = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    last_active = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-total_watch_time']
    
    def total_watch_hours(self):
        return round(self.total_watch_time / 3600, 1)
    
    def total_watch_minutes(self):
        return round(self.total_watch_time / 60, 1)
    
    def download_success_rate(self):
        """Calculate user's download success rate"""
        if self.total_downloads > 0:
            return round((self.completed_downloads / self.total_downloads) * 100, 1)
        return 0
    
    def download_failure_rate(self):
        """Calculate user's download failure rate"""
        if self.total_downloads > 0:
            return round(((self.failed_downloads + self.interrupted_downloads) / self.total_downloads) * 100, 1)
        return 0
    
    def __str__(self):
        return f"{self.user.username} - {self.total_watch_hours()} hours, {self.completed_downloads} downloads"


class MovieAnalytics(models.Model):
    """Aggregated movie performance analytics"""
    movie = models.OneToOneField(Movie, on_delete=models.CASCADE, related_name='analytics')
    total_watch_time = models.BigIntegerField(default=0)  # in seconds
    unique_viewers = models.IntegerField(default=0)
    total_sessions = models.IntegerField(default=0)
    total_downloads = models.IntegerField(default=0)
    completed_downloads = models.IntegerField(default=0)
    failed_downloads = models.IntegerField(default=0)
    interrupted_downloads = models.IntegerField(default=0)
    average_watch_duration = models.IntegerField(default=0)  # in seconds
    last_watched = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-total_watch_time']
        verbose_name_plural = "Movie Analytics"
    
    def total_watch_hours(self):
        return round(self.total_watch_time / 3600, 1)
    
    def average_watch_minutes(self):
        return round(self.average_watch_duration / 60, 1)
    
    def download_success_rate(self):
        """Calculate download success rate for this movie"""
        if self.total_downloads > 0:
            return round((self.completed_downloads / self.total_downloads) * 100, 1)
        return 0
    
    def __str__(self):
        return f"{self.movie.title} - {self.total_watch_hours()} hours, {self.unique_viewers} viewers"