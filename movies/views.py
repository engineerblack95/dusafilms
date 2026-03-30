from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Q, Avg 
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json

from .models import (
    Movie, Category, Comment, Reply, WatchedMovie, 
    UserCategoryFollow, WatchLater, MovieRating, WatchProgress,
    TeamMember  # Add TeamMember import
)
from announcements.models import Announcement
from .utils import send_test_notification


# -----------------------------
# HOME PAGE
# -----------------------------
def home(request):
    latest = Movie.objects.order_by('-upload_time')[:12]

    top = Movie.objects.annotate(
        num_comments=Count('movie_comments')
    ).order_by('-num_comments')[:12]

    categories = Category.objects.all()

    # ✅ FETCH ACTIVE ANNOUNCEMENTS (CREATED BY ADMIN ONLY)
    announcements = Announcement.objects.filter(
        is_active=True
    ).order_by('-created_at')
    
    # Get continue watching for logged-in users
    continue_watching = []
    if request.user.is_authenticated:
        continue_watching = WatchProgress.objects.filter(
            user=request.user,
            progress_percent__lt=100  # Not completed
        ).select_related('movie')[:6]

    return render(request, "movies/home.html", {
        'latest': latest,
        'top': top,
        'categories': categories,
        'announcements': announcements,
        'continue_watching': continue_watching,
    })


# -----------------------------
# MOVIE DETAIL PAGE (Guest allowed)
# -----------------------------
def detail(request, slug):
    movie = get_object_or_404(Movie, slug=slug)

    # Save watch history ONLY for logged-in users
    if request.user.is_authenticated:
        WatchedMovie.objects.get_or_create(
            user=request.user,
            movie=movie
        )
        
        # Get or create watch progress
        progress, created = WatchProgress.objects.get_or_create(
            user=request.user,
            movie=movie,
            defaults={'progress_percent': 0}
        )
        
        # Check if movie is in watch later
        is_in_watch_later = WatchLater.objects.filter(
            user=request.user,
            movie=movie
        ).exists()
        
        # Get user's rating
        user_rating = MovieRating.objects.filter(
            user=request.user,
            movie=movie
        ).first()
        
        # Check if user follows this category
        follows_category = UserCategoryFollow.objects.filter(
            user=request.user,
            category=movie.category
        ).exists()
        
    else:
        is_in_watch_later = False
        user_rating = None
        follows_category = False
        progress = None

    comments = movie.movie_comments.all().order_by('-created_at').prefetch_related('replies__user', 'replies__likes')

    # Get related movies (same category, excluding current) - for display
    related = Movie.objects.filter(
        category=movie.category
    ).exclude(pk=movie.pk)[:8]
    
    # Get ALL movies in the same category for continuous playback playlist
    # This allows the playlist to continue beyond the first 8 related movies
    category_playlist = Movie.objects.filter(
        category=movie.category
    ).order_by('-upload_time')
    
    # Find the index of current movie in the full playlist
    playlist_index = -1
    for idx, m in enumerate(category_playlist):
        if m.id == movie.id:
            playlist_index = idx
            break

    return render(request, "movies/detail.html", {
        'movie': movie,
        'related': related,
        'comments': comments,
        'is_in_watch_later': is_in_watch_later,
        'user_rating': user_rating,
        'follows_category': follows_category,
        'progress': progress,
        'category_playlist': category_playlist,
        'playlist_index': playlist_index,
    })


# -----------------------------
# ADD COMMENT (UPDATED - Guests must provide name, logged-in users auto-filled)
# -----------------------------
def add_comment(request, slug):
    movie = get_object_or_404(Movie, slug=slug)

    if request.method == "POST":
        text = (request.POST.get("text") or "").strip()
        name = (request.POST.get("name") or "").strip()

        if text:
            if request.user.is_authenticated:
                # Logged-in user - use their username from the system
                comment = Comment.objects.create(
                    movie=movie,
                    user=request.user,
                    text=text,
                    guest_name=request.user.username
                )
                messages.success(request, "Your comment has been added!")
                return JsonResponse({
                    'status': 'success',
                    'comment_id': comment.id,
                    'message': 'Comment added successfully'
                })
            else:
                # Guest user - must provide a name
                if not name:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'status': 'error', 'message': 'Please enter your name'}, status=400)
                    messages.error(request, "Please enter your name to comment.")
                    return redirect("movies:detail", slug=slug)
                
                comment = Comment.objects.create(
                    movie=movie,
                    user=None,
                    guest_name=name,
                    text=text
                )
                messages.success(request, f"Thank you for your comment, {name}!")
                return JsonResponse({
                    'status': 'success',
                    'comment_id': comment.id,
                    'message': 'Comment added successfully'
                })
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': 'Comment cannot be empty'}, status=400)
            messages.error(request, "Comment cannot be empty.")

    return redirect("movies:detail", slug=slug)


# ============================================
# REPLY VIEWS
# ============================================

def add_reply(request, comment_id):
    """Add a reply to a comment"""
    comment = get_object_or_404(Comment, id=comment_id)
    
    if request.method == "POST":
        text = (request.POST.get("text") or "").strip()
        name = (request.POST.get("name") or "").strip()

        if text:
            if request.user.is_authenticated:
                # Logged-in user - use their username
                Reply.objects.create(
                    comment=comment,
                    user=request.user,
                    text=text,
                    guest_name=request.user.username
                )
                messages.success(request, "Your reply has been added!")
            else:
                # Guest user - must provide a name
                if not name:
                    messages.error(request, "Please enter your name to reply.")
                    return redirect("movies:detail", slug=comment.movie.slug)
                
                Reply.objects.create(
                    comment=comment,
                    user=None,
                    guest_name=name,
                    text=text
                )
                messages.success(request, f"Thank you for your reply, {name}!")
        else:
            messages.error(request, "Reply cannot be empty.")
    
    return redirect("movies:detail", slug=comment.movie.slug)


@login_required
def delete_reply(request, reply_id):
    """Delete a reply (only for the author)"""
    reply = get_object_or_404(Reply, id=reply_id, user=request.user)
    movie_slug = reply.comment.movie.slug
    reply.delete()
    messages.success(request, "Your reply has been deleted.")
    return redirect("movies:detail", slug=movie_slug)


@login_required
def edit_reply(request, reply_id):
    """Edit a reply (only for the author)"""
    reply = get_object_or_404(Reply, id=reply_id, user=request.user)
    
    if request.method == 'POST':
        new_text = request.POST.get('text', '').strip()
        if new_text:
            reply.text = new_text
            reply.save()
            messages.success(request, "Reply updated successfully!")
            return redirect('movies:detail', slug=reply.comment.movie.slug)
        else:
            messages.error(request, "Reply cannot be empty.")
    
    return render(request, 'movies/edit_reply.html', {'reply': reply})


# ============================================
# AJAX REPLY HANDLER (For instant replies)
# ============================================

@require_POST
def ajax_add_reply(request):
    """AJAX endpoint to add a reply instantly"""
    try:
        data = json.loads(request.body)
        comment_id = data.get('comment_id')
        text = data.get('text', '').strip()
        name = data.get('name', '').strip()
        
        comment = get_object_or_404(Comment, id=comment_id)
        
        if not text:
            return JsonResponse({'status': 'error', 'message': 'Reply cannot be empty'}, status=400)
        
        if request.user.is_authenticated:
            reply = Reply.objects.create(
                comment=comment,
                user=request.user,
                text=text,
                guest_name=request.user.username
            )
            user_name = request.user.username
            is_verified = True
        else:
            if not name:
                return JsonResponse({'status': 'error', 'message': 'Please enter your name'}, status=400)
            reply = Reply.objects.create(
                comment=comment,
                user=None,
                guest_name=name,
                text=text
            )
            user_name = name
            is_verified = False
        
        return JsonResponse({
            'status': 'success',
            'reply_id': reply.id,
            'user_name': user_name,
            'is_verified': is_verified,
            'text': reply.text,
            'time_ago': reply.time_ago,
            'comment_id': comment_id
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# ============================================
# API ENDPOINTS FOR EDIT/DELETE (AJAX)
# ============================================

@csrf_exempt
@login_required
def api_edit_comment(request, comment_id):
    """API endpoint to edit a comment via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        new_text = data.get('text', '').strip()
        
        if not new_text:
            return JsonResponse({'status': 'error', 'message': 'Comment cannot be empty'}, status=400)
        
        comment = get_object_or_404(Comment, id=comment_id, user=request.user)
        comment.text = new_text
        comment.save()
        
        return JsonResponse({'status': 'success', 'message': 'Comment updated successfully'})
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@login_required
def api_delete_comment(request, comment_id):
    """API endpoint to delete a comment via AJAX"""
    if request.method != 'DELETE':
        return JsonResponse({'status': 'error', 'message': 'Only DELETE allowed'}, status=405)
    
    try:
        comment = get_object_or_404(Comment, id=comment_id, user=request.user)
        comment.delete()
        
        return JsonResponse({'status': 'success', 'message': 'Comment deleted successfully'})
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@login_required
def api_edit_reply(request, reply_id):
    """API endpoint to edit a reply via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        new_text = data.get('text', '').strip()
        
        if not new_text:
            return JsonResponse({'status': 'error', 'message': 'Reply cannot be empty'}, status=400)
        
        reply = get_object_or_404(Reply, id=reply_id, user=request.user)
        reply.text = new_text
        reply.save()
        
        return JsonResponse({'status': 'success', 'message': 'Reply updated successfully'})
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@login_required
def api_delete_reply(request, reply_id):
    """API endpoint to delete a reply via AJAX"""
    if request.method != 'DELETE':
        return JsonResponse({'status': 'error', 'message': 'Only DELETE allowed'}, status=405)
    
    try:
        reply = get_object_or_404(Reply, id=reply_id, user=request.user)
        comment_id = reply.comment.id
        reply.delete()
        
        return JsonResponse({
            'status': 'success', 
            'message': 'Reply deleted successfully',
            'comment_id': comment_id
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# ============================================
# LIVE SEARCH API ENDPOINT - CORRECTED VERSION
# ============================================

def api_search(request):
    """AJAX API endpoint for live search"""
    q = request.GET.get('q', '').strip()
    
    if len(q) < 2:
        return JsonResponse({'results': []})
    
    # Search in title, description, and category name
    # Use annotate to get the actual comment count from the database
    results = Movie.objects.filter(
        Q(title__icontains=q) |
        Q(description__icontains=q) |
        Q(category__name__icontains=q)
    ).select_related('category').annotate(
        real_comments_count=Count('movie_comments', filter=Q(movie_comments__is_approved=True))
    ).order_by('-upload_time')[:20]
    
    results_data = []
    for movie in results:
        results_data.append({
            'id': movie.id,
            'title': movie.title,
            'slug': movie.slug,
            'thumbnail': movie.thumbnail.url if movie.thumbnail else None,
            'category': movie.category.name,
            'time_ago': movie.time_ago,
            'comments_count': movie.real_comments_count,  # This gets actual comment count from database
        })
    
    return JsonResponse({'results': results_data})


# -----------------------------
# CATEGORY PAGE
# -----------------------------
def category_view(request, slug):
    category = get_object_or_404(Category, slug=slug)
    movies = Movie.objects.filter(category=category)
    
    # Check if user follows this category
    user_follows = False
    if request.user.is_authenticated:
        user_follows = UserCategoryFollow.objects.filter(
            user=request.user,
            category=category
        ).exists()

    return render(request, "movies/category.html", {
        "category": category,
        "movies": movies,
        "user_follows": user_follows,
    })


# -----------------------------
# SEARCH PAGE
# -----------------------------
def search(request):
    q = request.GET.get("q", "").strip()
    
    # Get filter parameters
    category_filter = request.GET.get("category", "")
    sort_by = request.GET.get("sort", "-upload_time")
    
    # Start with base queryset
    results = Movie.objects.all()
    
    # Apply search filter if query exists
    if q:
        results = results.filter(
            Q(title__icontains=q) |
            Q(description__icontains=q) |
            Q(category__name__icontains=q)
        )
    
    # Annotate with comment count (using a unique name)
    results = results.select_related('category').annotate(
        approved_comments_count=Count('movie_comments', filter=Q(movie_comments__is_approved=True))
    )
    
    # Apply category filter
    if category_filter:
        results = results.filter(category__slug=category_filter)
    
    # Apply sorting
    if sort_by == "rating":
        results = results.annotate(avg_rating=Avg('ratings__rating')).order_by('-avg_rating')
    elif sort_by == "title":
        results = results.order_by('title')
    elif sort_by == "-title":
        results = results.order_by('-title')
    elif sort_by == "upload_time":
        results = results.order_by('upload_time')
    else:
        results = results.order_by('-upload_time')  # Default: newest first
    
    # Get all categories for filter dropdown
    categories = Category.objects.all()
    
    context = {
        "results": results,
        "q": q,
        "categories": categories,
        "selected_category": category_filter,
        "selected_sort": sort_by,
    }
    
    return render(request, "movies/search.html", context)
# -----------------------------
# ABOUT PAGE - UPDATED to fetch team members
# -----------------------------
def about(request):
    """About page with team members"""
    # Fetch all active team members ordered by display_order
    team_members = TeamMember.objects.filter(is_active=True).order_by('display_order', 'name')
    
    context = {
        'team_members': team_members,
    }
    return render(request, "movies/about.html", context)


# ============================================
# NOTIFICATION VIEWS
# ============================================

@login_required
def follow_category(request, slug):
    """Allow users to follow a category for notifications"""
    category = get_object_or_404(Category, slug=slug)
    
    follow, created = UserCategoryFollow.objects.get_or_create(
        user=request.user,
        category=category,
        defaults={'receive_emails': True}
    )
    
    if created:
        messages.success(request, f"You are now following {category.name}. You'll receive email notifications for new movies!")
    else:
        if follow.receive_emails:
            messages.info(request, f"You already follow {category.name}")
        else:
            follow.receive_emails = True
            follow.save()
            messages.success(request, f"Email notifications re-enabled for {category.name}")
    
    next_url = request.GET.get('next', request.META.get('HTTP_REFERER', '/'))
    return redirect(next_url)


@login_required
def unfollow_category(request, slug):
    """Allow users to unfollow a category"""
    category = get_object_or_404(Category, slug=slug)
    
    deleted = UserCategoryFollow.objects.filter(
        user=request.user,
        category=category
    ).delete()
    
    if deleted[0] > 0:
        messages.success(request, f"You have unfollowed {category.name}. You'll no longer receive notifications.")
    else:
        messages.warning(request, f"You were not following {category.name}")
    
    next_url = request.GET.get('next', request.META.get('HTTP_REFERER', '/'))
    return redirect(next_url)


@login_required
def toggle_notification_settings(request, slug):
    """Toggle email notifications for a specific category"""
    if request.method == 'POST':
        category = get_object_or_404(Category, slug=slug)
        follow = UserCategoryFollow.objects.filter(
            user=request.user,
            category=category
        ).first()
        
        if follow:
            follow.receive_emails = not follow.receive_emails
            follow.save()
            
            status = "enabled" if follow.receive_emails else "disabled"
            messages.success(request, f"Email notifications {status} for {category.name}")
        else:
            messages.warning(request, f"You don't follow {category.name}. Use the follow button to start receiving notifications.")
    
    return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
def my_notifications(request):
    """User's notification preferences page"""
    followed_categories = UserCategoryFollow.objects.filter(
        user=request.user
    ).select_related('category')
    
    all_categories = Category.objects.all()
    
    context = {
        'followed_categories': followed_categories,
        'all_categories': all_categories,
    }
    
    return render(request, 'movies/notifications.html', context)


@login_required
def test_notification(request):
    """Send test email to user (for debugging)"""
    if request.method == 'POST':
        category_slug = request.POST.get('category')
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug)
            movie = Movie.objects.filter(category=category).first()
            
            success = send_test_notification(request.user, category, movie)
            
            if success:
                messages.success(request, f"Test email sent to {request.user.email}!")
            else:
                messages.error(request, "Failed to send test email. Check logs.")
        else:
            messages.error(request, "Please select a category for test")
    
    return redirect('movies:my_notifications')


# ============================================
# WATCH LATER VIEWS
# ============================================

@login_required
def add_to_watch_later(request, slug):
    """Add a movie to user's watch later list"""
    movie = get_object_or_404(Movie, slug=slug)
    
    watch_later, created = WatchLater.objects.get_or_create(
        user=request.user,
        movie=movie
    )
    
    if created:
        messages.success(request, f"Added '{movie.title}' to your Watch Later list!")
    else:
        messages.info(request, f"'{movie.title}' is already in your Watch Later list")
    
    return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
def remove_from_watch_later(request, slug):
    """Remove a movie from user's watch later list"""
    movie = get_object_or_404(Movie, slug=slug)
    
    deleted = WatchLater.objects.filter(
        user=request.user,
        movie=movie
    ).delete()
    
    if deleted[0] > 0:
        messages.success(request, f"Removed '{movie.title}' from your Watch Later list")
    else:
        messages.warning(request, f"'{movie.title}' was not in your Watch Later list")
    
    return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
def watch_later_list(request):
    """Display user's watch later list"""
    watch_later_movies = WatchLater.objects.filter(
        user=request.user
    ).select_related('movie').order_by('-added_at')
    
    return render(request, 'movies/watch_later.html', {
        'watch_later_movies': watch_later_movies
    })


# ============================================
# RATING VIEWS
# ============================================

@login_required
@require_POST
def rate_movie(request, slug):
    """Rate a movie (1-5 stars)"""
    movie = get_object_or_404(Movie, slug=slug)
    rating_value = request.POST.get('rating')
    
    if rating_value and rating_value.isdigit():
        rating_value = int(rating_value)
        if 1 <= rating_value <= 5:
            rating, created = MovieRating.objects.update_or_create(
                user=request.user,
                movie=movie,
                defaults={'rating': rating_value}
            )
            
            if created:
                messages.success(request, f"You rated '{movie.title}' {rating_value} stars!")
            else:
                messages.success(request, f"Your rating for '{movie.title}' has been updated to {rating_value} stars!")
        else:
            messages.error(request, "Invalid rating value")
    else:
        messages.error(request, "Please select a rating")
    
    return redirect(request.META.get('HTTP_REFERER', '/'))


# ============================================
# WATCH PROGRESS VIEWS
# ============================================

@login_required
@require_POST
def update_watch_progress(request, slug):
    """Update watch progress for a movie"""
    movie = get_object_or_404(Movie, slug=slug)
    progress = request.POST.get('progress')
    
    if progress:
        try:
            progress_value = float(progress)
            progress_value = max(0, min(100, progress_value))
            
            watch_progress, created = WatchProgress.objects.update_or_create(
                user=request.user,
                movie=movie,
                defaults={'progress_percent': progress_value}
            )
            
            return JsonResponse({'status': 'success', 'progress': progress_value})
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Invalid progress value'}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'No progress provided'}, status=400)


@login_required
def continue_watching(request):
    """Display user's continue watching list"""
    watch_progress = WatchProgress.objects.filter(
        user=request.user,
        progress_percent__lt=100
    ).select_related('movie').order_by('-last_watched')
    
    return render(request, 'movies/continue_watching.html', {
        'watch_progress': watch_progress
    })