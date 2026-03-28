from django.contrib import admin
from django import forms
from .models import (
    Category, Movie, Comment, WatchedMovie, 
    UserCategoryFollow, WatchLater, MovieRating, WatchProgress, 
    NotificationLog, TeamMember
)


# Add this custom form for Movie
class MovieAdminForm(forms.ModelForm):
    class Meta:
        model = Movie
        fields = '__all__'
    
    def clean_thumbnail(self):
        """Validate that thumbnail is an image and not too large"""
        thumbnail = self.cleaned_data.get('thumbnail')
        
        if thumbnail:
            # Check if it's a file upload
            if hasattr(thumbnail, 'size'):
                # Limit thumbnail to 5MB
                if thumbnail.size > 5 * 1024 * 1024:  # 5MB
                    raise forms.ValidationError(
                        'Thumbnail image must be less than 5MB. '
                        'Current file size: {:.2f} MB'.format(thumbnail.size / (1024 * 1024))
                    )
                
                # Check file extension
                ext = thumbnail.name.split('.')[-1].lower()
                allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
                if ext not in allowed_extensions:
                    raise forms.ValidationError(
                        f'Invalid file type. Allowed: {", ".join(allowed_extensions)}'
                    )
        
        return thumbnail
    
    def clean_video_url(self):
        """Clean and validate video URL"""
        video_url = self.cleaned_data.get('video_url')
        
        if video_url:
            # Check if it's a URL
            if not video_url.startswith(('http://', 'https://')):
                raise forms.ValidationError('Enter a valid URL starting with http:// or https://')
        
        return video_url


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "followers_count")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)
    
    def followers_count(self, obj):
        """Display number of users following this category"""
        return obj.followers.count()
    followers_count.short_description = "Followers"


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    form = MovieAdminForm
    list_display = ("title", "category", "upload_time", "display_comments_count", "display_ratings_count", "display_average_rating")
    list_filter = ("category", "upload_time")
    search_fields = ("title", "description")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("upload_time",)
    
    # Add help text for fields
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['thumbnail'].help_text = "Upload a thumbnail image (JPG, PNG, GIF) - Max 5MB. DO NOT upload videos here."
        form.base_fields['video_url'].help_text = "Enter the video URL (YouTube, Vimeo, or direct video link)."
        form.base_fields['download_link'].help_text = "Optional: Add a download link for this movie."
        return form
    
    def display_comments_count(self, obj):
        """Display number of comments"""
        return obj.comments_count
    display_comments_count.short_description = "Comments"
    display_comments_count.admin_order_field = "upload_time"
    
    def display_ratings_count(self, obj):
        """Display number of ratings"""
        return obj.ratings_count
    display_ratings_count.short_description = "Ratings"
    display_ratings_count.admin_order_field = "upload_time"
    
    def display_average_rating(self, obj):
        """Display average rating with stars"""
        avg = obj.average_rating
        if avg > 0:
            return f"{avg} ⭐"
        return "No ratings"
    display_average_rating.short_description = "Avg Rating"
    display_average_rating.admin_order_field = "upload_time"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("movie", "user_name", "created_at", "is_approved", "likes_count")
    search_fields = ("user__username", "text", "guest_name")
    list_filter = ("movie", "is_approved", "created_at")
    list_editable = ("is_approved",)
    
    def user_name(self, obj):
        """
        Display the username of the commenter safely.
        Handles deleted or anonymous users.
        """
        if obj.user:
            return obj.user.username
        return obj.guest_name or "Anonymous"
    user_name.admin_order_field = "user"
    user_name.short_description = "User Name"
    
    def likes_count(self, obj):
        """Display number of likes"""
        return obj.likes.count()
    likes_count.short_description = "Likes"
    
    actions = ['approve_comments', 'disapprove_comments']
    
    def approve_comments(self, request, queryset):
        """Approve selected comments"""
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"{updated} comments approved.")
    approve_comments.short_description = "Approve selected comments"
    
    def disapprove_comments(self, request, queryset):
        """Disapprove selected comments"""
        updated = queryset.update(is_approved=False)
        self.message_user(request, f"{updated} comments disapproved.")
    disapprove_comments.short_description = "Disapprove selected comments"


@admin.register(WatchedMovie)
class WatchedMovieAdmin(admin.ModelAdmin):
    list_display = ("user", "movie", "watched_at")
    list_filter = ("watched_at",)
    search_fields = ("user__username", "movie__title")
    readonly_fields = ("watched_at",)


# ============================================
# ADMIN REGISTRATIONS FOR NOTIFICATIONS & FEATURES
# ============================================

@admin.register(UserCategoryFollow)
class UserCategoryFollowAdmin(admin.ModelAdmin):
    list_display = ("user", "category", "followed_at", "receive_emails")
    list_filter = ("receive_emails", "category", "followed_at")
    search_fields = ("user__username", "user__email", "category__name")
    readonly_fields = ("followed_at",)
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('user', 'category')


@admin.register(WatchLater)
class WatchLaterAdmin(admin.ModelAdmin):
    list_display = ("user", "movie", "added_at")
    search_fields = ("user__username", "movie__title")
    list_filter = ("added_at",)
    readonly_fields = ("added_at",)
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('user', 'movie')


@admin.register(MovieRating)
class MovieRatingAdmin(admin.ModelAdmin):
    list_display = ("user", "movie", "rating", "created_at", "updated_at")
    list_filter = ("rating", "created_at")
    search_fields = ("user__username", "movie__title")
    readonly_fields = ("created_at", "updated_at")
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('user', 'movie')


@admin.register(WatchProgress)
class WatchProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "movie", "progress_percent", "last_watched")
    list_filter = ("progress_percent", "last_watched")
    search_fields = ("user__username", "movie__title")
    readonly_fields = ("last_watched",)
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('user', 'movie')


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ("user", "notification_type", "movie", "category", "sent_at", "status")
    list_filter = ("notification_type", "status", "sent_at")
    search_fields = ("user__email", "movie__title", "category__name")
    readonly_fields = ("sent_at", "error_message")
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('user', 'movie', 'category')
    
    def has_add_permission(self, request):
        """Disable adding notification logs manually"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing notification logs"""
        return False


# ============================================
# TEAM MEMBER ADMIN REGISTRATION
# ============================================

@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'job_title', 'display_order', 'is_active', 'created_at')
    list_filter = ('role', 'is_active')
    search_fields = ('name', 'bio', 'email', 'phone')
    list_editable = ('display_order', 'is_active')
    list_display_links = ('name',)
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('name', 'role', 'job_title', 'bio', 'photo')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'whatsapp', 'linkedin')
        }),
        ('Display Settings', {
            'fields': ('display_order', 'is_active')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).order_by('display_order', 'name')