from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required

from .models import Movie, Category, Comment, WatchedMovie
from announcements.models import Announcement  # ✅ ANNOUNCEMENTS IMPORT
from django.contrib.auth import get_user_model
from django.http import HttpResponse


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

    comments = movie.movie_comments.all().order_by('-created_at')

    related = Movie.objects.filter(
        category=movie.category
    ).exclude(pk=movie.pk)[:8]

    return render(request, "movies/detail.html", {
        'movie': movie,
        'related': related,
        'comments': comments,
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

def about(request):
    return render(request, "movies/about.html")

# -----------------------------
# TEMPORARY: VIEW ALL USERS (REMOVE AFTER CHECKING)
# -----------------------------
def temp_list_users(request):
    User = get_user_model()
    users = User.objects.all().order_by('date_joined')
    
    # Format as HTML table
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>All Users in Database</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            h1 { color: #333; }
            table { border-collapse: collapse; width: 100%; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
            th { background: #4CAF50; color: white; padding: 12px; text-align: left; }
            td { padding: 10px; border-bottom: 1px solid #ddd; }
            tr:hover { background: #f9f9f9; }
            .stats { background: white; padding: 15px; margin-top: 20px; border-radius: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
            .warning { background: #ffc107; padding: 10px; margin-bottom: 20px; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="warning">
            <strong>⚠️ TEMPORARY VIEW - REMOVE AFTER CHECKING USERS</strong>
        </div>
        <h1>📋 All Registered Users</h1>
    '''
    
    html += '<table>'
    html += '<tr><th>ID</th><th>Username</th><th>Email</th><th>Staff?</th><th>Superuser?</th><th>Active?</th><th>Date Joined</th><th>Last Login</th></tr>'
    
    for user in users:
        html += f'<tr>'
        html += f'<td>{user.id}</td>'
        html += f'<td><strong>{user.username}</strong></td>'
        html += f'<td>{user.email or "—"}</td>'
        html += f'<td>{"✅" if user.is_staff else "❌"}</td>'
        html += f'<td>{"✅" if user.is_superuser else "❌"}</td>'
        html += f'<td>{"✅" if user.is_active else "❌"}</td>'
        html += f'<td>{user.date_joined.strftime("%Y-%m-%d %H:%M")}</td>'
        html += f'<td>{user.last_login.strftime("%Y-%m-%d %H:%M") if user.last_login else "Never"}</td>'
        html += f'</tr>'
    
    html += '</table>'
    
    html += f'''
        <div class="stats">
            <strong>Total Users:</strong> {users.count()} | 
            <strong>Staff:</strong> {users.filter(is_staff=True).count()} | 
            <strong>Superusers:</strong> {users.filter(is_superuser=True).count()} | 
            <strong>Active:</strong> {users.filter(is_active=True).count()}
        </div>
    </body>
    </html>
    '''
    
    return HttpResponse(html)