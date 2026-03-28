from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
import uuid


class WatchSessionMiddleware(MiddlewareMixin):
    """Track user sessions for analytics"""
    
    def process_request(self, request):
        # Generate or get session ID
        if not request.session.get('watch_session_id'):
            request.session['watch_session_id'] = str(uuid.uuid4())