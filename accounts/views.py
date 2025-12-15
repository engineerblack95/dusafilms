from django.shortcuts import render, redirect
from movies.models import Movie, Comment, WatchedMovie
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.core.mail import EmailMessage  # ✅ CHANGED
from django.conf import settings
import random

from .models import Profile
from .forms import UserRegisterForm, OTPLoginForm, ProfilePhotoForm

from django.db.models import Count
from django.contrib.auth.decorators import login_required


# ----------------------------
# User Registration
# ----------------------------
def register(request):
    if request.user.is_authenticated:
        return redirect("movies:home")

    if request.method == "POST":
        form = UserRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Account created! Please login with OTP.")
            return redirect("accounts:otp_login")
    else:
        form = UserRegisterForm()

    return render(request, "accounts/register.html", {"form": form})


# ----------------------------
# OTP Login Page
# ----------------------------
def otp_login(request):
    if request.user.is_authenticated:
        return redirect("movies:home")
    form = OTPLoginForm()
    return render(request, "accounts/otp_login.html", {"form": form})


# ----------------------------
# Send OTP
# ----------------------------
def send_otp(request):
    if request.method == "POST":
        username = request.POST.get("username")
        if not username:
            messages.error(request, "Please enter your username.")
            return redirect("accounts:otp_login")

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, "User does not exist.")
            return redirect("accounts:otp_login")

        otp = str(random.randint(100000, 999999)).zfill(6)
        profile = user.profile
        profile.otp = otp
        profile.otp_created_at = timezone.now()
        profile.save()

        subject = "Dusa Films — Your OTP"
        message = f"Hello {user.username},\n\nYour OTP is: {otp}\nIt expires in 5 minutes."
        from_email = getattr(settings, "EMAIL_HOST_USER", None)

        # ✅ FIXED EMAIL SENDING (NO WORKER TIMEOUT)
        try:
            email = EmailMessage(
                subject=subject,
                body=message,
                from_email=from_email,
                to=[user.email],
            )
            email.connection.timeout = 10
            email.send(fail_silently=True)
        except Exception as e:
            print("OTP email failed:", e)

        messages.success(request, f"OTP sent to {user.email}.")
        return redirect(f"/accounts/verify-otp/?username={username}")

    return redirect("accounts:otp_login")


# ----------------------------
# Resend OTP
# ----------------------------
def resend_otp(request):
    return send_otp(request)


# ----------------------------
# Verify OTP
# ----------------------------
def verify_otp(request):
    username = request.GET.get("username") or request.POST.get("username")
    if not username:
        messages.error(request, "Username missing. Please try again.")
        return redirect("accounts:otp_login")

    try:
        user = User.objects.get(username=username)
        profile = user.profile
    except Exception:
        messages.error(request, "Invalid username.")
        return redirect("accounts:otp_login")

    if request.method == "POST":
        otp_input = request.POST.get("otp")
        if profile.otp and profile.otp == otp_input and profile.is_otp_valid():
            login(request, user)
            profile.clear_otp()
            messages.success(request, f"Welcome {user.username}!")
            return redirect("accounts:dashboard")
        else:
            messages.error(request, "Invalid or expired OTP.")
            return redirect(f"/accounts/verify-otp/?username={username}")

    return render(request, "accounts/verify_otp.html", {"username": username})


# ----------------------------
# Dashboard
# ----------------------------
@login_required
def dashboard(request):
    profile = request.user.profile

    if request.method == "POST":
        photo_form = ProfilePhotoForm(request.POST, request.FILES, instance=profile)
        if photo_form.is_valid():
            photo_form.save()
            messages.success(request, "Profile photo updated successfully!")
            return redirect("accounts:dashboard")
    else:
        photo_form = ProfilePhotoForm(instance=profile)

    all_comments = Comment.objects.filter(user=request.user).order_by('-created_at')
    all_watched = WatchedMovie.objects.filter(user=request.user).order_by('-watched_at')

    total_comments = all_comments.count()

    movies_watched = (
        all_watched
        .values("movie")
        .distinct()
        .count()
    )

    recent_comments = all_comments[:5]
    recent_watched = all_watched[:5]

    top_commented = (
        all_comments
        .values('movie__title', 'movie__slug')
        .annotate(cnt=Count('id'))
        .order_by('-cnt')[:6]
    )

    context = {
        "profile": profile,
        "photo_form": photo_form,
        "total_comments": total_comments,
        "movies_watched": movies_watched,
        "recent_comments": recent_comments,
        "recent_watched": recent_watched,
        "top_commented": top_commented,
    }

    return render(request, "accounts/dashboard.html", context)


# ----------------------------
# Logout
# ----------------------------
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("accounts:otp_login")
