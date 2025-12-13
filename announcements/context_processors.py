from .models import Announcement, AnnouncementRead

def unread_announcements(request):
    if not request.user.is_authenticated:
        return {}

    read_ids = AnnouncementRead.objects.filter(
        user=request.user
    ).values_list('announcement_id', flat=True)

    unread_count = Announcement.objects.filter(
        is_active=True
    ).exclude(id__in=read_ids).count()

    return {
        'unread_announcements_count': unread_count
    }
