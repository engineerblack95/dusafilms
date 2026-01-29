from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required
from django.core import serializers
import json

from .models import Movie, Category, Comment, WatchedMovie
from announcements.models import Announcement  # ✅ ANNOUNCEMENTS IMPORT


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

    return render(request, "movies/home.html", {
        'latest': latest,
        'top': top,
        'categories': categories,
        'announcements': announcements,  # ✅ PASSED TO TEMPLATE
    })


# -----------------------------
# MOVIE DETAIL PAGE (Guest allowed) - UPDATED for Autoplay Next
# -----------------------------
def detail(request, slug):
    movie = get_object_or_404(Movie, slug=slug)

    # Save watch history ONLY for logged-in users
    if request.user.is_authenticated:
        WatchedMovie.objects.get_or_create(
            user=request.user,
            movie=movie
        )

    comments = movie.movie_comments.all().order_by('-created_at')

    related = Movie.objects.filter(
        category=movie.category
    ).exclude(pk=movie.pk)[:8]

    # ✅ NEW: Get playlist for autoplay next feature
    # Get all movies in same category (excluding current) for the playlist
    playlist_movies = Movie.objects.filter(
        category=movie.category
    ).exclude(pk=movie.pk).order_by('-upload_time')[:20]  # Limit to 20 movies

    # Prepare playlist data for JSON
    playlist_data = []
    for m in playlist_movies:
        playlist_data.append({
            'id': m.id,
            'title': m.title,
            'slug': m.slug,
            'video_url': m.video_url,
            'thumbnail': m.thumbnail.url if m.thumbnail else '',
            'time_ago': m.time_ago,  # Assuming you have this method in model
            'comments_count': m.movie_comments.count()
        })

    return render(request, "movies/detail.html", {
        'movie': movie,
        'related': related,
        'comments': comments,
        'playlist_json': json.dumps(playlist_data),  # ✅ For JavaScript autoplay
    })


# -----------------------------
# ADD COMMENT (Guest allowed)
# -----------------------------
def add_comment(request, slug):
    movie = get_object_or_404(Movie, slug=slug)

    if request.method == "POST":
        text = (request.POST.get("text") or "").strip()

        if text:
            if request.user.is_authenticated:
                # Logged-in user
                Comment.objects.create(
                    movie=movie,
                    user=request.user,
                    text=text
                )
            else:
                # Guest user
                Comment.objects.create(
                    movie=movie,
                    guest_name="Guest",
                    text=text
                )

    return redirect("movies:detail", slug=slug)


# -----------------------------
# CATEGORY PAGE
# -----------------------------
def category_view(request, slug):
    category = get_object_or_404(Category, slug=slug)
    movies = Movie.objects.filter(category=category)

    return render(request, "movies/category.html", {
        "category": category,
        "movies": movies
    })


# -----------------------------
# SEARCH PAGE
# -----------------------------
def search(request):
    q = request.GET.get("q", "")

    results = Movie.objects.filter(
        Q(title__icontains=q) |
        Q(description__icontains=q) |
        Q(category__name__icontains=q)
    ).order_by('-upload_time')

    return render(request, "movies/search.html", {
        "results": results,
        "q": q,
    })


# -----------------------------
# ABOUT PAGE
# -----------------------------
def about(request):
    return render(request, "movies/about.html")