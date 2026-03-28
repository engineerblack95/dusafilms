from django.contrib import admin
from .models import Profile

# -----------------------------
# Profile Admin
# -----------------------------
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "otp", "otp_created_at", "profile_photo_preview")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("created_at", "updated_at")
    
    def profile_photo_preview(self, obj):
        if obj.profile_photo:
            return f'<img src="{obj.profile_photo.url}" style="width: 50px; height: 50px; border-radius: 50%;" />'
        return "No photo"
    profile_photo_preview.allow_tags = True
    profile_photo_preview.short_description = "Photo"