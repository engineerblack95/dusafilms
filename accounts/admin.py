from django.contrib import admin
from .models import Profile, WatchedMovie

# -----------------------------
# Profile Admin
# -----------------------------
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "otp", "otp_created_at")
    search_fields = ("user__username", "user__email")


# -----------------------------
# WatchedMovie Admin
# -----------------------------
@admin.register(WatchedMovie)
class WatchedMovieAdmin(admin.ModelAdmin):
    list_display = ("user", "movie", "watched_at")
    search_fields = ("user__username", "movie__title")
    list_filter = ("watched_at",)
