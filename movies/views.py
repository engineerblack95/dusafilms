from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required
from .models import Movie, Category, Comment, WatchedMovie


# -----------------------------
# HOME PAGE
# -----------------------------
def home(request):
    latest = Movie.objects.order_by('-upload_time')[:12]

    top = Movie.objects.annotate(
        num_comments=Count('movie_comments')
    ).order_by('-num_comments')[:12]

    categories = Category.objects.all()

    return render(request, "movies/home.html", {
        'latest': latest,
        'top': top,
        'categories': categories,
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
