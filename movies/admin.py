from django.contrib import admin
from .models import Category, Movie, Comment


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "upload_time", "comments_count")
    list_filter = ("category",)
    search_fields = ("title", "description")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("upload_time",)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("movie", "user_name", "created_at")
    search_fields = ("user__username", "text")
    list_filter = ("movie",)

    def user_name(self, obj):
        """Display the username of the commenter"""
        return obj.user.username

    user_name.admin_order_field = 'user'  # Allows sorting by user
    user_name.short_description = 'User Name'  # Column header
