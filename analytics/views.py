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

# Correct imports - only import models from .models
from .models import WatchSession, DownloadTracking, UserEngagementStats, MovieAnalytics
from movies.models import Movie, Comment

logger = logging.getLogger(__name__)


@staff_member_required
def analytics_dashboard(request):
    """Professional analytics dashboard for admins"""
    
    # ==================== REAL-TIME ACTIVE VIEWERS ====================
    active_threshold = timezone.now() - timedelta(seconds=30)
    active_sessions = WatchSession.objects.filter(
        is_active=True,
        last_heartbeat__gte=active_threshold
    ).select_related('user', 'movie')
    
    active_viewers = []
    for session in active_sessions:
        active_viewers.append({
            'username': session.user.username if session.user else 'Guest',
            'movie_title': session.movie.title,
            'movie_slug': session.movie.slug,
            'started_at': session.started_at,
            'duration_minutes': round(session.watch_duration / 60, 1),
            'device_type': session.device_type,
            'session_id': session.session_id,
            'last_heartbeat': session.last_heartbeat,
        })
    
    # ==================== TODAY'S STATISTICS ====================
    today = timezone.now().date()
    
    # Watch sessions today
    sessions_today = WatchSession.objects.filter(started_at__date=today)
    watch_time_today = sessions_today.aggregate(total=Sum('watch_duration'))['total'] or 0
    unique_viewers_today = sessions_today.values('user').distinct().count()
    
    # Downloads today - Enhanced tracking
    downloads_today = DownloadTracking.objects.filter(download_started__date=today)
    total_downloads_today = downloads_today.count()
    completed_downloads_today = downloads_today.filter(status='completed').count()
    failed_downloads_today = downloads_today.filter(status='failed').count()
    interrupted_downloads_today = downloads_today.filter(status='interrupted').count()
    in_progress_downloads = downloads_today.filter(status='in_progress').count()
    pending_downloads = downloads_today.filter(status='pending').count()
    
    # Download failure breakdown
    failure_breakdown = downloads_today.filter(status='failed').values('failure_reason').annotate(
        count=Count('id')
    )
    
    # Average download speed
    avg_speed = downloads_today.filter(download_speed__isnull=False).aggregate(avg=Avg('download_speed'))['avg'] or 0
    
    # ==================== TOP MOVIES BY WATCH TIME ====================
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
            'completed_downloads': m.completed_downloads,
            'failed_downloads': m.failed_downloads,
            'interrupted_downloads': m.interrupted_downloads,
            'average_watch_minutes': round(m.average_watch_duration / 60, 1) if m.average_watch_duration else 0,
            'download_success_rate': m.download_success_rate(),
        })
    
    # ==================== TOP USERS BY WATCH TIME ====================
    top_users = UserEngagementStats.objects.filter(
        total_watch_time__gt=0
    ).select_related('user').order_by('-total_watch_time')[:10]
    
    top_users_list = []
    for idx, u in enumerate(top_users, 1):
        top_users_list.append({
            'rank': idx,
            'user': u.user,
            'watch_hours': round(u.total_watch_time / 3600, 1),
            'downloads': u.completed_downloads,
            'failed_downloads': u.failed_downloads,
            'interrupted_downloads': u.interrupted_downloads,
            'movies_watched': u.movies_watched,
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
            'interrupted_downloads': d.interrupted_downloads,
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
    
    # ==================== LAST 7 DAYS ENGAGEMENT ====================
    last_7_days = []
    for i in range(6, -1, -1):
        date = timezone.now().date() - timedelta(days=i)
        
        sessions = WatchSession.objects.filter(started_at__date=date).count()
        watch_time = WatchSession.objects.filter(started_at__date=date).aggregate(total=Sum('watch_duration'))['total'] or 0
        downloads = DownloadTracking.objects.filter(download_started__date=date).count()
        completed = DownloadTracking.objects.filter(download_started__date=date, status='completed').count()
        failed = DownloadTracking.objects.filter(download_started__date=date, status='failed').count()
        interrupted = DownloadTracking.objects.filter(download_started__date=date, status='interrupted').count()
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
            'interrupted_downloads': interrupted,
            'unique_viewers': unique_viewers,
        })
    
    # ==================== LAST 24 HOURS ENGAGEMENT ====================
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
        total_completed_downloads_all=Sum('completed_downloads'),
        total_failed_downloads_all=Sum('failed_downloads'),
        total_interrupted_downloads_all=Sum('interrupted_downloads'),
    )
    
    total_watch_hours_all = round((movie_performance['total_watch_time_all'] or 0) / 3600, 1)
    total_unique_viewers_all = movie_performance['total_unique_viewers'] or 0
    total_movies_with_views = movie_performance['total_movies_with_views'] or 0
    total_downloads_all = movie_performance['total_downloads_all'] or 0
    total_completed_downloads_all = movie_performance['total_completed_downloads_all'] or 0
    total_failed_downloads_all = movie_performance['total_failed_downloads_all'] or 0
    total_interrupted_downloads_all = movie_performance['total_interrupted_downloads_all'] or 0
    
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
        'interrupted_downloads_today': interrupted_downloads_today,
        'in_progress_downloads': in_progress_downloads,
        'pending_downloads': pending_downloads,
        'download_success_rate_today': round((completed_downloads_today / total_downloads_today * 100), 1) if total_downloads_today > 0 else 0,
        'avg_download_speed': round(avg_speed, 1),
        'failure_breakdown': failure_breakdown,
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
        'total_completed_downloads_all': total_completed_downloads_all,
        'total_failed_downloads_all': total_failed_downloads_all,
        'total_interrupted_downloads_all': total_interrupted_downloads_all,
        'overall_success_rate': round((total_completed_downloads_all / total_downloads_all * 100), 1) if total_downloads_all > 0 else 0,
    }
    
    return render(request, 'analytics/dashboard.html', context)


@login_required
@require_POST
def track_watch_session(request):
    """API endpoint to track watch sessions (called by JavaScript)"""
    try:
        data = json.loads(request.body)
        movie_slug = data.get('movie_slug')
        action = data.get('action')
        watch_duration = data.get('duration', 0)
        
        # Get or create session ID
        session_id = request.session.get('analytics_session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            request.session['analytics_session_id'] = session_id
        
        movie = get_object_or_404(Movie, slug=movie_slug)
        
        logger.info(f"Track session: {action} for {movie_slug}")
        
        if action == 'start':
            # Create new watch session
            session = WatchSession.objects.create(
                user=request.user if request.user.is_authenticated else None,
                movie=movie,
                session_id=session_id,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                is_active=True,
                watch_duration=0
            )
            return JsonResponse({'status': 'success', 'session_id': session_id})
        
        elif action == 'heartbeat':
            # Update existing session
            session = WatchSession.objects.filter(session_id=session_id, is_active=True).first()
            if session:
                session.watch_duration = watch_duration
                session.last_heartbeat = timezone.now()
                session.save()
                return JsonResponse({'status': 'success'})
            return JsonResponse({'status': 'error', 'message': 'Session not found'}, status=404)
        
        elif action == 'end':
            # End session and update stats
            session = WatchSession.objects.filter(session_id=session_id, is_active=True).first()
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
                
                # Calculate average watch duration
                all_sessions = WatchSession.objects.filter(movie=movie)
                avg_duration = all_sessions.aggregate(avg=Avg('watch_duration'))['avg'] or 0
                movie_stats.average_watch_duration = int(avg_duration)
                movie_stats.last_watched = timezone.now()
                movie_stats.save()
                
                return JsonResponse({'status': 'success'})
            return JsonResponse({'status': 'error', 'message': 'Session not found'}, status=404)
        
        return JsonResponse({'status': 'error', 'message': 'Invalid action'}, status=400)
        
    except Exception as e:
        logger.error(f"Error in track_watch_session: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@require_POST
def track_download_start(request):
    """API endpoint to start tracking a download"""
    try:
        data = json.loads(request.body)
        movie_slug = data.get('movie_slug')
        file_size = data.get('file_size')
        download_url = data.get('download_url', '')
        
        movie = get_object_or_404(Movie, slug=movie_slug)
        
        # Get file size from URL if not provided
        if not file_size and download_url:
            try:
                import requests
                response = requests.head(download_url, timeout=5)
                if response.status_code == 200:
                    file_size = int(response.headers.get('content-length', 0))
            except:
                pass
        
        download_id = str(uuid.uuid4())
        download = DownloadTracking.objects.create(
            user=request.user if request.user.is_authenticated else None,
            movie=movie,
            download_id=download_id,
            file_size=file_size if file_size and file_size > 0 else None,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            status='in_progress'
        )
        
        logger.info(f"Download started: {download_id} for {movie.title}")
        
        return JsonResponse({
            'status': 'success',
            'download_id': download_id,
            'file_size': file_size
        })
        
    except Exception as e:
        logger.error(f"Error in track_download_start: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@require_POST
def track_download_progress(request):
    """API endpoint to update download progress"""
    try:
        data = json.loads(request.body)
        download_id = data.get('download_id')
        downloaded_bytes = data.get('downloaded_bytes', 0)
        download_speed = data.get('download_speed')
        
        download = get_object_or_404(DownloadTracking, download_id=download_id)
        
        download.downloaded_size = downloaded_bytes
        if download_speed:
            download.download_speed = download_speed
        download.save()
        
        return JsonResponse({'status': 'success'})
        
    except Exception as e:
        logger.error(f"Error in track_download_progress: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@require_POST
def track_download_complete(request):
    """API endpoint to mark download as completed"""
    try:
        data = json.loads(request.body)
        download_id = data.get('download_id')
        final_size = data.get('final_size')
        
        download = get_object_or_404(DownloadTracking, download_id=download_id)
        
        download.download_completed = timezone.now()
        download.status = 'completed'
        download.download_duration = int((download.download_completed - download.download_started).total_seconds())
        
        if final_size:
            download.downloaded_size = final_size
            if not download.file_size:
                download.file_size = final_size
        
        download.save()
        
        # Update user stats
        if download.user:
            stats, created = UserEngagementStats.objects.get_or_create(user=download.user)
            stats.total_downloads += 1
            stats.completed_downloads += 1
            stats.save()
        
        # Update movie stats
        movie_stats, created = MovieAnalytics.objects.get_or_create(movie=download.movie)
        movie_stats.total_downloads += 1
        movie_stats.completed_downloads += 1
        movie_stats.save()
        
        logger.info(f"Download completed: {download_id}")
        
        return JsonResponse({'status': 'success'})
        
    except Exception as e:
        logger.error(f"Error in track_download_complete: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@require_POST
def track_download_failure(request):
    """API endpoint to mark download as failed with reason"""
    try:
        data = json.loads(request.body)
        download_id = data.get('download_id')
        failure_reason = data.get('failure_reason', 'unknown')
        error_message = data.get('error_message', '')
        
        download = get_object_or_404(DownloadTracking, download_id=download_id)
        
        download.status = 'failed'
        download.failure_reason = failure_reason
        download.error_message = error_message
        download.save()
        
        # Update user stats
        if download.user:
            stats, created = UserEngagementStats.objects.get_or_create(user=download.user)
            stats.total_downloads += 1
            stats.failed_downloads += 1
            stats.save()
        
        # Update movie stats
        movie_stats, created = MovieAnalytics.objects.get_or_create(movie=download.movie)
        movie_stats.total_downloads += 1
        movie_stats.failed_downloads += 1
        movie_stats.save()
        
        logger.info(f"Download failed: {download_id} - {failure_reason}")
        
        return JsonResponse({'status': 'success'})
        
    except Exception as e:
        logger.error(f"Error in track_download_failure: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@require_POST
def track_download_interrupt(request):
    """API endpoint to mark download as interrupted (network issues, user left, etc.)"""
    try:
        data = json.loads(request.body)
        download_id = data.get('download_id')
        downloaded_bytes = data.get('downloaded_bytes', 0)
        reason = data.get('reason', 'connection_lost')
        
        download = get_object_or_404(DownloadTracking, download_id=download_id)
        
        download.status = 'interrupted'
        download.failure_reason = reason
        download.downloaded_size = downloaded_bytes
        download.error_message = f"Download interrupted at {downloaded_bytes} bytes"
        download.save()
        
        # Update user stats
        if download.user:
            stats, created = UserEngagementStats.objects.get_or_create(user=download.user)
            stats.total_downloads += 1
            stats.interrupted_downloads += 1
            stats.save()
        
        # Update movie stats
        movie_stats, created = MovieAnalytics.objects.get_or_create(movie=download.movie)
        movie_stats.total_downloads += 1
        movie_stats.interrupted_downloads += 1
        movie_stats.save()
        
        logger.info(f"Download interrupted: {download_id} - {reason} at {downloaded_bytes} bytes")
        
        return JsonResponse({'status': 'success'})
        
    except Exception as e:
        logger.error(f"Error in track_download_interrupt: {str(e)}")
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
        'interrupted_downloads': downloads.filter(status='interrupted').count(),
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
    
    context = {
        'profile_user': user,
        'stats': stats,
        'sessions': sessions,
        'downloads': downloads,
        'top_movies': top_movies,
        'total_watch_hours': round(stats.total_watch_time / 3600, 1),
        'download_success_rate': stats.download_success_rate(),
        'download_failure_rate': stats.download_failure_rate(),
    }
    
    return render(request, 'analytics/user_details.html', context)


@staff_member_required
def export_analytics(request, report_type):
    """Export analytics data as JSON"""
    if report_type == 'movies':
        data = MovieAnalytics.objects.select_related('movie').values(
            'movie__title', 'movie__slug', 'total_watch_time', 
            'unique_viewers', 'total_sessions', 'total_downloads',
            'completed_downloads', 'failed_downloads', 'interrupted_downloads'
        )
    elif report_type == 'users':
        data = UserEngagementStats.objects.select_related('user').values(
            'user__username', 'user__email', 'total_watch_time',
            'total_downloads', 'completed_downloads', 'failed_downloads', 'interrupted_downloads'
        )
    elif report_type == 'sessions':
        data = WatchSession.objects.select_related('user', 'movie').values(
            'session_id', 'user__username', 'movie__title', 
            'watch_duration', 'started_at', 'device_type'
        )[:1000]
    else:
        return JsonResponse({'error': 'Invalid report type'}, status=400)
    
    return JsonResponse(list(data), safe=False)