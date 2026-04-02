from django.shortcuts import render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db.models import Sum, Count, Avg, Q, F
from django.utils import timezone
from datetime import datetime, timedelta
import json
import uuid
import logging

# Correct imports
from .models import WatchSession, DownloadTracking, UserEngagementStats, MovieAnalytics
from movies.models import Movie, Comment

logger = logging.getLogger(__name__)


@staff_member_required
def analytics_dashboard(request):
    """Professional analytics dashboard for admins"""
    
    # ==================== REAL-TIME ACTIVE VIEWERS ====================
    active_threshold = timezone.now() - timedelta(seconds=60)
    active_sessions = WatchSession.objects.filter(
        is_active=True,
        last_heartbeat__gte=active_threshold
    ).select_related('user', 'movie').order_by('-last_heartbeat')
    
    active_viewers = []
    for session in active_sessions:
        watch_duration_minutes = round(session.watch_duration / 60, 1) if session.watch_duration else 0
        
        active_viewers.append({
            'username': session.user.username if session.user else 'Guest',
            'movie_title': session.movie.title if session.movie else 'Unknown',
            'movie_slug': session.movie.slug if session.movie else '',
            'started_at': session.started_at,
            'duration_minutes': watch_duration_minutes,
            'device_type': session.device_type or 'unknown',
            'session_id': session.session_id,
            'last_heartbeat': session.last_heartbeat,
        })
    
    # ==================== TODAY'S STATISTICS ====================
    today = timezone.now().date()
    
    sessions_today = WatchSession.objects.filter(started_at__date=today)
    watch_time_today = sessions_today.aggregate(total=Sum('watch_duration'))['total'] or 0
    unique_viewers_today = sessions_today.values('user').distinct().count()
    
    downloads_today = DownloadTracking.objects.filter(download_started__date=today)
    total_downloads_today = downloads_today.count()
    completed_downloads_today = downloads_today.filter(status='completed').count()
    failed_downloads_today = downloads_today.filter(status='failed').count()
    in_progress_downloads_today = downloads_today.filter(status='in_progress').count()
    interrupted_downloads_today = downloads_today.filter(status='interrupted').count()
    pending_downloads_today = downloads_today.filter(status='pending').count()
    
    completed_or_failed = completed_downloads_today + failed_downloads_today
    download_success_rate_today = round((completed_downloads_today / completed_or_failed * 100), 1) if completed_or_failed > 0 else 0
    
    # ==================== TOP MOVIES ====================
    top_movies = MovieAnalytics.objects.filter(
        total_watch_time__gt=0
    ).select_related('movie').order_by('-total_watch_time')[:10]
    
    top_movies_list = []
    for idx, m in enumerate(top_movies, 1):
        top_movies_list.append({
            'rank': idx,
            'movie': m.movie,
            'total_watch_hours': round(m.total_watch_time / 3600, 1),
            'unique_viewers': m.unique_viewers,
            'total_sessions': m.total_sessions,
            'total_downloads': m.total_downloads,
            'average_watch_minutes': round(m.average_watch_duration / 60, 1) if m.average_watch_duration else 0,
        })
    
    # ==================== TOP USERS ====================
    top_users = UserEngagementStats.objects.filter(
        total_watch_time__gt=0
    ).select_related('user').order_by('-total_watch_time')[:10]
    
    top_users_list = []
    for idx, u in enumerate(top_users, 1):
        top_users_list.append({
            'rank': idx,
            'user': u.user,
            'watch_hours': round(u.total_watch_time / 3600, 1),
            'movies_watched': u.movies_watched,
            'total_downloads': u.total_downloads,
            'comments': u.comments_count,
            'success_rate': u.download_success_rate(),
        })
    
    # ==================== TOP DOWNLOADERS ====================
    top_downloaders = UserEngagementStats.objects.filter(
        completed_downloads__gt=0
    ).select_related('user').order_by('-completed_downloads')[:10]
    
    top_downloaders_list = []
    for idx, d in enumerate(top_downloaders, 1):
        top_downloaders_list.append({
            'rank': idx,
            'user': d.user,
            'downloads': d.completed_downloads,
            'failed_downloads': d.failed_downloads,
            'success_rate': d.download_success_rate(),
            'watch_hours': round(d.total_watch_time / 3600, 1),
        })
    
    # ==================== PLATFORM STATISTICS ====================
    platform_stats = {
        'mobile': WatchSession.objects.filter(device_type='mobile').count(),
        'desktop': WatchSession.objects.filter(device_type='desktop').count(),
        'tablet': WatchSession.objects.filter(device_type='tablet').count(),
        'guest_sessions': WatchSession.objects.filter(user__isnull=True).count(),
        'registered_sessions': WatchSession.objects.filter(user__isnull=False).count(),
    }
    
    # ==================== LAST 7 DAYS ====================
    last_7_days = []
    for i in range(6, -1, -1):
        date = timezone.now().date() - timedelta(days=i)
        
        sessions = WatchSession.objects.filter(started_at__date=date).count()
        watch_time = WatchSession.objects.filter(started_at__date=date).aggregate(total=Sum('watch_duration'))['total'] or 0
        downloads = DownloadTracking.objects.filter(download_started__date=date).count()
        completed = DownloadTracking.objects.filter(download_started__date=date, status='completed').count()
        failed = DownloadTracking.objects.filter(download_started__date=date, status='failed').count()
        unique_viewers = WatchSession.objects.filter(started_at__date=date).values('user').distinct().count()
        
        last_7_days.append({
            'date': date.strftime('%a'),
            'full_date': date.strftime('%b %d'),
            'sessions': sessions,
            'watch_hours': round(watch_time / 3600, 1),
            'watch_minutes': round(watch_time / 60, 1),
            'downloads': downloads,
            'completed_downloads': completed,
            'failed_downloads': failed,
            'unique_viewers': unique_viewers,
        })
    
    # ==================== LAST 24 HOURS ====================
    last_24_hours = []
    for hour in range(23, -1, -1):
        hour_time = timezone.now() - timedelta(hours=hour)
        hour_start = hour_time.replace(minute=0, second=0, microsecond=0)
        hour_end = hour_start + timedelta(hours=1)
        
        sessions = WatchSession.objects.filter(
            started_at__gte=hour_start,
            started_at__lt=hour_end
        ).count()
        
        downloads = DownloadTracking.objects.filter(
            download_started__gte=hour_start,
            download_started__lt=hour_end
        ).count()
        
        last_24_hours.append({
            'hour': hour_time.strftime('%H:00'),
            'sessions': sessions,
            'downloads': downloads,
        })
    
    # ==================== RECENT ACTIVITY ====================
    recent_sessions = WatchSession.objects.select_related('user', 'movie').order_by('-started_at')[:15]
    recent_downloads = DownloadTracking.objects.select_related('user', 'movie').order_by('-download_started')[:15]
    
    # ==================== OVERALL PERFORMANCE ====================
    movie_performance = MovieAnalytics.objects.all().aggregate(
        total_movies_with_views=Count('id'),
        total_watch_time_all=Sum('total_watch_time'),
        total_unique_viewers=Sum('unique_viewers'),
        total_downloads_all=Sum('total_downloads'),
    )
    
    total_watch_hours_all = round((movie_performance['total_watch_time_all'] or 0) / 3600, 1)
    total_unique_viewers_all = movie_performance['total_unique_viewers'] or 0
    total_movies_with_views = movie_performance['total_movies_with_views'] or 0
    total_downloads_all = movie_performance['total_downloads_all'] or 0
    
    context = {
        'active_viewers': active_viewers,
        'active_count': len(active_viewers),
        'watch_time_today_minutes': round(watch_time_today / 60, 1),
        'watch_time_today_hours': round(watch_time_today / 3600, 1),
        'unique_viewers_today': unique_viewers_today,
        'sessions_today': sessions_today.count(),
        'total_downloads_today': total_downloads_today,
        'completed_downloads_today': completed_downloads_today,
        'failed_downloads_today': failed_downloads_today,
        'in_progress_downloads': in_progress_downloads_today,
        'download_success_rate_today': download_success_rate_today,
        'top_movies': top_movies_list,
        'top_users': top_users_list,
        'top_downloaders': top_downloaders_list,
        'platform_stats': platform_stats,
        'last_7_days': last_7_days,
        'last_24_hours': last_24_hours,
        'recent_sessions': recent_sessions,
        'recent_downloads': recent_downloads,
        'total_movies_with_views': total_movies_with_views,
        'total_watch_hours_all': total_watch_hours_all,
        'total_unique_viewers_all': total_unique_viewers_all,
        'total_downloads_all': total_downloads_all,
    }
    
    return render(request, 'analytics/dashboard.html', context)


# ==================== CRITICAL FIX: CORRECTED track_watch_session ====================
@login_required
@require_POST
def track_watch_session(request):
    """API endpoint to track watch sessions (called by JavaScript)"""
    try:
        data = json.loads(request.body)
        movie_slug = data.get('movie_slug')
        action = data.get('action')
        watch_duration = data.get('duration', 0)
        client_session_id = data.get('session_id')  # IMPORTANT: Get session_id from client
        
        logger.info(f"Track session request: action={action}, client_session_id={client_session_id}, movie={movie_slug}")
        
        # PRIORITIZE client session ID over server session
        session_id = client_session_id
        
        # If no client session ID and this is a start action, create new one
        if not session_id and action == 'start':
            session_id = str(uuid.uuid4())
            request.session['analytics_session_id'] = session_id
            logger.info(f"Created new session ID: {session_id}")
        
        if not session_id:
            return JsonResponse({'status': 'error', 'message': 'No session ID provided'}, status=400)
        
        movie = get_object_or_404(Movie, slug=movie_slug)
        
        # Detect device type from user agent
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        device_type = 'desktop'
        if 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent:
            device_type = 'mobile'
        elif 'tablet' in user_agent or 'ipad' in user_agent:
            device_type = 'tablet'
        
        if action == 'start':
            # Check if session already exists (for page refresh case)
            existing_session = WatchSession.objects.filter(
                session_id=session_id,
                movie=movie
            ).first()
            
            if existing_session:
                # Reactivate existing session
                existing_session.is_active = True
                existing_session.last_heartbeat = timezone.now()
                existing_session.ended_at = None
                existing_session.watch_duration = watch_duration
                existing_session.user = request.user if request.user.is_authenticated else None
                existing_session.device_type = device_type
                existing_session.save()
                logger.info(f"Session REACTIVATED: {session_id} for {movie.title}")
                return JsonResponse({
                    'status': 'success', 
                    'session_id': session_id,
                    'reactivated': True
                })
            else:
                # Create new session
                session = WatchSession.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    movie=movie,
                    session_id=session_id,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                    device_type=device_type,
                    is_active=True,
                    watch_duration=0
                )
                request.session['analytics_session_id'] = session_id
                logger.info(f"New session CREATED: {session_id} for {movie.title}")
                return JsonResponse({
                    'status': 'success', 
                    'session_id': session_id,
                    'reactivated': False
                })
        
        elif action == 'heartbeat':
            # Find existing session (active or inactive)
            session = WatchSession.objects.filter(
                session_id=session_id,
                movie=movie
            ).first()
            
            if session:
                # Update session
                session.watch_duration = watch_duration
                session.last_heartbeat = timezone.now()
                if not session.is_active:
                    session.is_active = True
                    session.ended_at = None
                    logger.info(f"Session REACTIVATED via heartbeat: {session_id}")
                session.save()
                return JsonResponse({'status': 'success'})
            
            logger.warning(f"Heartbeat failed - session not found: {session_id}")
            return JsonResponse({'status': 'error', 'message': 'Session not found'}, status=404)
        
        elif action == 'end':
            # End session
            session = WatchSession.objects.filter(
                session_id=session_id,
                movie=movie,
                is_active=True
            ).first()
            
            if session:
                session.watch_duration = watch_duration
                session.ended_at = timezone.now()
                session.is_active = False
                session.save()
                
                # Update user engagement stats
                if request.user.is_authenticated:
                    stats, created = UserEngagementStats.objects.get_or_create(user=request.user)
                    stats.total_watch_time += watch_duration
                    stats.movies_watched = WatchSession.objects.filter(
                        user=request.user
                    ).values('movie').distinct().count()
                    stats.last_active = timezone.now()
                    stats.save()
                
                # Update movie analytics
                movie_stats, created = MovieAnalytics.objects.get_or_create(movie=movie)
                movie_stats.total_watch_time += watch_duration
                movie_stats.total_sessions += 1
                movie_stats.unique_viewers = WatchSession.objects.filter(
                    movie=movie
                ).values('user').distinct().count()
                
                all_sessions = WatchSession.objects.filter(movie=movie)
                avg_duration = all_sessions.aggregate(avg=Avg('watch_duration'))['avg'] or 0
                movie_stats.average_watch_duration = int(avg_duration)
                movie_stats.last_watched = timezone.now()
                movie_stats.save()
                
                logger.info(f"Session ended: {session_id} for {movie.title}, duration: {watch_duration}s")
                return JsonResponse({'status': 'success'})
            
            return JsonResponse({'status': 'error', 'message': 'Session not found'}, status=404)
        
        return JsonResponse({'status': 'error', 'message': 'Invalid action'}, status=400)
        
    except Exception as e:
        logger.error(f"Error in track_watch_session: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@require_POST
def track_download(request):
    """API endpoint to track download start"""
    try:
        data = json.loads(request.body)
        movie_slug = data.get('movie_slug')
        
        if not movie_slug:
            return JsonResponse({
                'status': 'error',
                'message': 'movie_slug is required'
            }, status=400)
        
        movie = get_object_or_404(Movie, slug=movie_slug)
        
        session_id = request.session.get('analytics_session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            request.session['analytics_session_id'] = session_id
        
        download_id = str(uuid.uuid4())
        
        download = DownloadTracking.objects.create(
            user=request.user if request.user.is_authenticated else None,
            movie=movie,
            download_id=download_id,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            status='in_progress'
        )
        
        if request.user.is_authenticated:
            stats, created = UserEngagementStats.objects.get_or_create(user=request.user)
            stats.total_downloads += 1
            stats.last_active = timezone.now()
            stats.save()
        
        movie_stats, created = MovieAnalytics.objects.get_or_create(movie=movie)
        movie_stats.total_downloads += 1
        movie_stats.save()
        
        logger.info(f"Download tracked: {download_id} for {movie.title}")
        
        return JsonResponse({
            'status': 'success',
            'message': 'Download tracked successfully',
            'download_id': download.id
        })
        
    except Exception as e:
        logger.error(f"Error in track_download: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@require_POST
def update_download_status(request):
    """API endpoint to update download status"""
    try:
        data = json.loads(request.body)
        download_id = data.get('download_id')
        status = data.get('status')
        error_message = data.get('error_message', '')
        
        if not download_id or not status:
            return JsonResponse({
                'status': 'error',
                'message': 'download_id and status are required'
            }, status=400)
        
        if status not in ['completed', 'failed']:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid status. Must be completed or failed'
            }, status=400)
        
        try:
            download = DownloadTracking.objects.get(id=download_id)
        except DownloadTracking.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': f'Download with ID {download_id} not found'
            }, status=404)
        
        download.status = status
        download.error_message = error_message[:500] if error_message else ''
        
        if status == 'completed':
            download.download_completed = timezone.now()
            download.download_duration = (download.download_completed - download.download_started).total_seconds()
            
            if download.user:
                stats, created = UserEngagementStats.objects.get_or_create(user=download.user)
                stats.completed_downloads += 1
                stats.save()
                
        elif status == 'failed':
            if download.user:
                stats, created = UserEngagementStats.objects.get_or_create(user=download.user)
                stats.failed_downloads += 1
                stats.save()
        
        download.save()
        
        movie_stats, created = MovieAnalytics.objects.get_or_create(movie=download.movie)
        if status == 'completed':
            movie_stats.completed_downloads += 1
        elif status == 'failed':
            movie_stats.failed_downloads += 1
        movie_stats.save()
        
        logger.info(f"Download status updated: {download_id} - {status}")
        
        return JsonResponse({
            'status': 'success',
            'message': f'Download status updated to {status}'
        })
        
    except Exception as e:
        logger.error(f"Error in update_download_status: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@staff_member_required
def movie_details_analytics(request, movie_id):
    """Detailed analytics for a specific movie"""
    movie = get_object_or_404(Movie, id=movie_id)
    analytics, created = MovieAnalytics.objects.get_or_create(movie=movie)
    
    sessions = WatchSession.objects.filter(movie=movie).select_related('user').order_by('-started_at')[:100]
    downloads = DownloadTracking.objects.filter(movie=movie).select_related('user').order_by('-download_started')[:100]
    
    context = {
        'movie': movie,
        'analytics': analytics,
        'sessions': sessions,
        'downloads': downloads,
        'total_viewers': sessions.values('user').distinct().count(),
        'total_sessions': sessions.count(),
        'total_downloads': downloads.count(),
        'completed_downloads': downloads.filter(status='completed').count(),
        'failed_downloads': downloads.filter(status='failed').count(),
    }
    
    return render(request, 'analytics/movie_details.html', context)


@staff_member_required
def user_analytics(request, user_id):
    """Detailed analytics for a specific user"""
    from django.contrib.auth.models import User
    user = get_object_or_404(User, id=user_id)
    stats, created = UserEngagementStats.objects.get_or_create(user=user)
    
    sessions = WatchSession.objects.filter(user=user).select_related('movie').order_by('-started_at')[:100]
    downloads = DownloadTracking.objects.filter(user=user).select_related('movie').order_by('-download_started')[:100]
    
    top_movies = sessions.values('movie__id', 'movie__title', 'movie__slug').annotate(
        total_time=Sum('watch_duration'),
        session_count=Count('id')
    ).order_by('-total_time')[:10]
    
    total_downloads = stats.completed_downloads + stats.failed_downloads
    success_rate = round((stats.completed_downloads / total_downloads * 100), 1) if total_downloads > 0 else 0
    
    context = {
        'profile_user': user,
        'stats': stats,
        'sessions': sessions,
        'downloads': downloads,
        'top_movies': top_movies,
        'total_watch_hours': round(stats.total_watch_time / 3600, 1),
        'download_success_rate': success_rate,
    }
    
    return render(request, 'analytics/user_details.html', context)


@staff_member_required
def export_analytics(request, report_type):
    """Export analytics data as JSON"""
    if report_type == 'movies':
        data = MovieAnalytics.objects.select_related('movie').values(
            'movie__title', 'movie__slug', 'total_watch_time', 
            'unique_viewers', 'total_sessions', 'total_downloads',
            'completed_downloads', 'failed_downloads', 'average_watch_duration'
        )
    elif report_type == 'users':
        data = UserEngagementStats.objects.select_related('user').values(
            'user__username', 'user__email', 'total_watch_time',
            'total_downloads', 'completed_downloads', 'failed_downloads',
            'movies_watched', 'last_active'
        )
    elif report_type == 'sessions':
        data = WatchSession.objects.select_related('user', 'movie').values(
            'session_id', 'user__username', 'movie__title', 
            'watch_duration', 'started_at', 'device_type'
        )[:1000]
    else:
        return JsonResponse({'error': 'Invalid report type'}, status=400)
    
    return JsonResponse(list(data), safe=False)