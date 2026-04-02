from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from analytics.models import WatchSession

class Command(BaseCommand):
    help = 'Clean up stale watch sessions'
    
    def handle(self, *args, **options):
        # Mark sessions inactive if no heartbeat for 2 minutes
        stale_threshold = timezone.now() - timedelta(minutes=2)
        stale_sessions = WatchSession.objects.filter(
            is_active=True,
            last_heartbeat__lt=stale_threshold
        )
        
        count = stale_sessions.update(is_active=False, ended_at=timezone.now())
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully cleaned up {count} stale sessions')
        )