from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

from .models import Announcement, AnnouncementRead


# -----------------------------
# ANNOUNCEMENTS LIST (PUBLIC)
# -----------------------------
def announcements_list(request):
    announcements = Announcement.objects.filter(
        is_active=True
    ).order_by('-created_at')

    read_ids = []

    # If user is logged in, get announcements already read
    if request.user.is_authenticated:
        read_ids = AnnouncementRead.objects.filter(
            user=request.user
        ).values_list('announcement_id', flat=True)

    return render(request, "announcements/announcements_list.html", {
        "announcements": announcements,
        "read_ids": read_ids,   # used for red/unread styling
    })


# -----------------------------
# ANNOUNCEMENT DETAIL
# (MARK AS READ)
# -----------------------------
@login_required
def announcement_detail(request, id):
    announcement = get_object_or_404(
        Announcement,
        id=id,
        is_active=True
    )

    # Mark as read (if not already)
    AnnouncementRead.objects.get_or_create(
        user=request.user,
        announcement=announcement
    )

    return render(request, "announcements/detail_list.html", {
        "announcement": announcement
    })
