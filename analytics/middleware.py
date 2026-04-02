from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
import uuid


class WatchSessionMiddleware(MiddlewareMixin):
    """Track user sessions for analytics"""
    
    def process_request(self, request):
        # ==========================================
        # SKIP ADMIN PATHS - NO OTP FOR ADMIN
        # ==========================================
        if request.path.startswith('/admin'):
            return None  # Skip completely for admin
        
        # ==========================================
        # SKIP STATIC FILES
        # ==========================================
        if request.path.startswith('/static'):
            return None
        
        # ==========================================
        # YOUR ORIGINAL CODE (unchanged)
        # ==========================================
        # Generate or get session ID
        if not request.session.get('watch_session_id'):
            request.session['watch_session_id'] = str(uuid.uuid4())
        
        # Continue normal flow
        return None