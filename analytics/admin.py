from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import WatchSession, DownloadTracking, UserEngagementStats, MovieAnalytics


@admin.register(WatchSession)
class WatchSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_display', 'movie_display', 'watch_duration_display', 
                    'is_active', 'device_type', 'last_heartbeat', 'started_at')
    list_filter = ('is_active', 'device_type', 'started_at', 'last_heartbeat')
    search_fields = ('user__username', 'user__email', 'movie__title', 'session_id')
    readonly_fields = ('session_id', 'started_at', 'last_heartbeat', 'ended_at', 
                       'watch_duration', 'ip_address', 'user_agent')
    list_select_related = ('user', 'movie')
    list_per_page = 50
    
    fieldsets = (
        ('Session Information', {
            'fields': ('session_id', 'user', 'movie', 'is_active')
        }),
        ('Timing', {
            'fields': ('started_at', 'last_heartbeat', 'ended_at', 'watch_duration')
        }),
        ('Device Information', {
            'fields': ('device_type', 'ip_address', 'user_agent')
        }),
    )
    
    def user_display(self, obj):
        if obj.user:
            return format_html(
                '<a href="/admin/auth/user/{}/change/">{}</a>',
                obj.user.id, obj.user.username
            )
        return 'Guest'
    user_display.short_description = 'User'
    user_display.admin_order_field = 'user'
    
    def movie_display(self, obj):
        return format_html(
            '<a href="/admin/movies/movie/{}/change/">{}</a>',
            obj.movie.id, obj.movie.title
        )
    movie_display.short_description = 'Movie'
    movie_display.admin_order_field = 'movie'
    
    def watch_duration_display(self, obj):
        minutes = obj.watch_duration / 60
        if minutes < 1:
            return f"{obj.watch_duration} sec"
        elif minutes < 60:
            return f"{round(minutes, 1)} min"
        else:
            hours = minutes / 60
            return f"{round(hours, 1)} hrs"
    watch_duration_display.short_description = 'Duration'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'movie')
    
    actions = ['mark_inactive', 'mark_active']
    
    def mark_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} sessions marked as inactive.")
    mark_inactive.short_description = "Mark selected sessions as inactive"
    
    def mark_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} sessions marked as active.")
    mark_active.short_description = "Mark selected sessions as active"


@admin.register(DownloadTracking)
class DownloadTrackingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_display', 'movie_display', 'progress_display', 
                    'status_display', 'download_speed_display', 'download_started')
    list_filter = ('status', 'failure_reason', 'download_started')
    search_fields = ('user__username', 'user__email', 'movie__title', 'download_id')
    readonly_fields = ('download_id', 'download_started', 'download_completed', 
                       'file_size', 'downloaded_size', 'download_speed', 
                       'download_duration', 'ip_address', 'user_agent')
    list_select_related = ('user', 'movie')
    list_per_page = 50
    
    fieldsets = (
        ('Download Information', {
            'fields': ('download_id', 'user', 'movie', 'status')
        }),
        ('Progress', {
            'fields': ('file_size', 'downloaded_size', 'download_speed', 'download_duration')
        }),
        ('Timing', {
            'fields': ('download_started', 'download_completed')
        }),
        ('Failure Details', {
            'fields': ('failure_reason', 'error_message')
        }),
        ('Technical Details', {
            'fields': ('ip_address', 'user_agent', 'retry_count')
        }),
    )
    
    def user_display(self, obj):
        if obj.user:
            return format_html(
                '<a href="/admin/auth/user/{}/change/">{}</a>',
                obj.user.id, obj.user.username
            )
        return 'Guest'
    user_display.short_description = 'User'
    user_display.admin_order_field = 'user'
    
    def movie_display(self, obj):
        return format_html(
            '<a href="/admin/movies/movie/{}/change/">{}</a>',
            obj.movie.id, obj.movie.title
        )
    movie_display.short_description = 'Movie'
    movie_display.admin_order_field = 'movie'
    
    def progress_display(self, obj):
        progress = obj.progress_percent()
        if progress > 0:
            color = '#10b981' if progress == 100 else '#f59e0b'
            return format_html(
                '<div style="width: 100px; background: #e5e7eb; border-radius: 10px; overflow: hidden;">'
                '<div style="width: {}%; background: {}; color: white; text-align: center; font-size: 10px; padding: 2px;">{}%</div>'
                '</div>',
                progress, color, progress
            )
        return '0%'
    progress_display.short_description = 'Progress'
    
    def status_display(self, obj):
        status_colors = {
            'pending': '#6b7280',
            'in_progress': '#3b82f6',
            'completed': '#10b981',
            'failed': '#ef4444',
            'cancelled': '#6b7280',
            'interrupted': '#f59e0b',
        }
        color = status_colors.get(obj.status, '#6b7280')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', 
                          color, obj.get_status_display())
    status_display.short_description = 'Status'
    
    def download_speed_display(self, obj):
        if obj.download_speed:
            return f"{obj.download_speed:.1f} KB/s"
        return '-'
    download_speed_display.short_description = 'Speed'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'movie')
    
    actions = ['mark_completed', 'mark_failed', 'retry_downloads']
    
    def mark_completed(self, request, queryset):
        updated = 0
        for download in queryset:
            if download.status != 'completed':
                download.status = 'completed'
                download.download_completed = timezone.now()
                if download.download_started:
                    download.download_duration = int((download.download_completed - download.download_started).total_seconds())
                download.save()
                updated += 1
        self.message_user(request, f"{updated} downloads marked as completed.")
    mark_completed.short_description = "Mark selected downloads as completed"
    
    def mark_failed(self, request, queryset):
        updated = queryset.update(status='failed', failure_reason='admin_override')
        self.message_user(request, f"{updated} downloads marked as failed.")
    mark_failed.short_description = "Mark selected downloads as failed"
    
    def retry_downloads(self, request, queryset):
        updated = 0
        for download in queryset:
            if download.status in ['failed', 'interrupted']:
                download.status = 'pending'
                download.retry_count += 1
                download.save()
                updated += 1
        self.message_user(request, f"{updated} downloads queued for retry.")
    retry_downloads.short_description = "Retry selected failed downloads"


@admin.register(UserEngagementStats)
class UserEngagementStatsAdmin(admin.ModelAdmin):
    list_display = ('user_link', 'total_watch_hours_display', 'total_downloads', 
                    'completed_downloads', 'failed_downloads', 'interrupted_downloads',
                    'success_rate_display', 'movies_watched', 'comments_count', 'last_active')
    list_filter = ('last_active', 'total_downloads')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('total_watch_time', 'total_downloads', 'completed_downloads', 
                       'failed_downloads', 'interrupted_downloads', 'movies_watched', 
                       'comments_count', 'last_active')
    list_select_related = ('user',)
    list_per_page = 50
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Watch Statistics', {
            'fields': ('total_watch_time', 'movies_watched')
        }),
        ('Download Statistics', {
            'fields': ('total_downloads', 'completed_downloads', 'failed_downloads', 'interrupted_downloads')
        }),
        ('Engagement', {
            'fields': ('comments_count', 'last_active')
        }),
    )
    
    def user_link(self, obj):
        return format_html(
            '<a href="/admin/auth/user/{}/change/">{}</a>',
            obj.user.id, obj.user.username
        )
    user_link.short_description = 'User'
    user_link.admin_order_field = 'user'
    
    def total_watch_hours_display(self, obj):
        hours = obj.total_watch_hours()
        if hours > 0:
            return f"{hours} hrs"
        return '0 hrs'
    total_watch_hours_display.short_description = 'Watch Time'
    total_watch_hours_display.admin_order_field = 'total_watch_time'
    
    def success_rate_display(self, obj):
        rate = obj.download_success_rate()
        if rate >= 80:
            color = '#10b981'
        elif rate >= 50:
            color = '#f59e0b'
        else:
            color = '#ef4444'
        return format_html('<span style="color: {}; font-weight: bold;">{}%</span>', color, rate)
    success_rate_display.short_description = 'Success Rate'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    actions = ['reset_stats']
    
    def reset_stats(self, request, queryset):
        updated = queryset.update(
            total_watch_time=0,
            total_downloads=0,
            completed_downloads=0,
            failed_downloads=0,
            interrupted_downloads=0,
            movies_watched=0,
            comments_count=0
        )
        self.message_user(request, f"{updated} user stats have been reset.")
    reset_stats.short_description = "Reset selected user statistics"


@admin.register(MovieAnalytics)
class MovieAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('movie_link', 'total_watch_hours_display', 'unique_viewers', 
                    'total_sessions', 'total_downloads', 'success_rate_display', 
                    'average_watch_minutes_display', 'last_watched')
    list_filter = ('last_watched', 'total_downloads', 'unique_viewers')
    search_fields = ('movie__title',)
    readonly_fields = ('total_watch_time', 'unique_viewers', 'total_sessions', 
                       'total_downloads', 'completed_downloads', 'failed_downloads',
                       'interrupted_downloads', 'average_watch_duration', 'last_watched')
    list_select_related = ('movie',)
    list_per_page = 50
    
    fieldsets = (
        ('Movie', {
            'fields': ('movie',)
        }),
        ('Watch Statistics', {
            'fields': ('total_watch_time', 'unique_viewers', 'total_sessions', 'average_watch_duration')
        }),
        ('Download Statistics', {
            'fields': ('total_downloads', 'completed_downloads', 'failed_downloads', 'interrupted_downloads')
        }),
        ('Timing', {
            'fields': ('last_watched',)
        }),
    )
    
    def movie_link(self, obj):
        return format_html(
            '<a href="/admin/movies/movie/{}/change/">{}</a>',
            obj.movie.id, obj.movie.title
        )
    movie_link.short_description = 'Movie'
    movie_link.admin_order_field = 'movie'
    
    def total_watch_hours_display(self, obj):
        hours = obj.total_watch_hours()
        if hours > 0:
            return f"{hours} hrs"
        return '0 hrs'
    total_watch_hours_display.short_description = 'Watch Time'
    total_watch_hours_display.admin_order_field = 'total_watch_time'
    
    def average_watch_minutes_display(self, obj):
        minutes = obj.average_watch_minutes()
        if minutes > 0:
            return f"{minutes} min"
        return '-'
    average_watch_minutes_display.short_description = 'Avg Duration'
    
    def success_rate_display(self, obj):
        rate = obj.download_success_rate()
        if rate >= 80:
            color = '#10b981'
        elif rate >= 50:
            color = '#f59e0b'
        else:
            color = '#ef4444'
        return format_html('<span style="color: {}; font-weight: bold;">{}%</span>', color, rate)
    success_rate_display.short_description = 'Download Success Rate'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('movie')
    
    actions = ['reset_movie_stats']
    
    def reset_movie_stats(self, request, queryset):
        updated = queryset.update(
            total_watch_time=0,
            unique_viewers=0,
            total_sessions=0,
            total_downloads=0,
            completed_downloads=0,
            failed_downloads=0,
            interrupted_downloads=0,
            average_watch_duration=0
        )
        self.message_user(request, f"{updated} movie analytics have been reset.")
    reset_movie_stats.short_description = "Reset selected movie statistics"