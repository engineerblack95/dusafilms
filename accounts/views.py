from django.shortcuts import render, redirect
from movies.models import Movie, Comment, WatchedMovie
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.conf import settings
from django.http import JsonResponse  
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import random

from .models import Profile
from .forms import UserRegisterForm, OTPLoginForm, ProfilePhotoForm

from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.conf import settings



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
# Send OTP (UPDATED WITH BEAUTIFUL HTML EMAIL)
# ----------------------------
def send_otp(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip().lower()

        if not username:
            messages.error(request, "Please enter your username.")
            return redirect("accounts:otp_login")

        try:
            user = User.objects.get(username__iexact=username)
        except User.DoesNotExist:
            messages.error(request, "User does not exist.")
            return redirect("accounts:otp_login")

        otp = str(random.randint(100000, 999999)).zfill(6)
        profile = user.profile
        profile.otp = otp
        profile.otp_created_at = timezone.now()
        profile.save()
        
        # Create beautiful HTML email content
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Your Dusa Films OTP</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                    background-color: #f5f5f5;
                    margin: 0;
                    padding: 20px;
                }}
                .email-container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 16px;
                    overflow: hidden;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                }}
                .email-header {{
                    background: linear-gradient(135deg, #0b0b0b, #1a1a1a);
                    padding: 30px 20px;
                    text-align: center;
                }}
                .logo-section {{
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 15px;
                    margin-bottom: 20px;
                }}
                .logo-text {{
                    font-size: 28px;
                    font-weight: 900;
                    color: white;
                    letter-spacing: 1px;
                }}
                .brand-text {{
                    color: #1e90ff;
                    font-weight: 900;
                }}
                .email-title {{
                    color: white;
                    font-size: 22px;
                    margin: 15px 0;
                    font-weight: 600;
                }}
                .otp-container {{
                    background: linear-gradient(135deg, #1e3c72, #2a5298);
                    padding: 40px 20px;
                    text-align: center;
                }}
                .otp-label {{
                    color: rgba(255,255,255,0.9);
                    font-size: 16px;
                    margin-bottom: 10px;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }}
                .otp-code {{
                    font-size: 48px;
                    font-weight: 900;
                    color: white;
                    letter-spacing: 8px;
                    margin: 20px 0;
                    text-shadow: 0 2px 10px rgba(0,0,0,0.3);
                    font-family: 'Courier New', monospace;
                }}
                .user-greeting {{
                    background: #f8f9fa;
                    padding: 25px;
                    text-align: center;
                    border-bottom: 1px solid #eaeaea;
                }}
                .greeting-text {{
                    color: #333;
                    font-size: 18px;
                    margin: 0;
                }}
                .username {{
                    color: #1e90ff;
                    font-weight: 700;
                }}
                .instructions {{
                    padding: 30px;
                    background: white;
                }}
                .instructions h3 {{
                    color: #333;
                    margin-top: 0;
                }}
                .instructions ul {{
                    padding-left: 20px;
                    color: #555;
                    line-height: 1.6;
                }}
                .instructions li {{
                    margin-bottom: 10px;
                }}
                .expiry-note {{
                    background: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 4px;
                }}
                .email-footer {{
                    background: #0b0b0b;
                    padding: 25px;
                    text-align: center;
                    color: #aaa;
                    font-size: 14px;
                }}
                .footer-links {{
                    margin-top: 15px;
                }}
                .footer-links a {{
                    color: #1e90ff;
                    text-decoration: none;
                    margin: 0 10px;
                }}
                .warning-note {{
                    background: #f8d7da;
                    color: #721c24;
                    padding: 12px;
                    border-radius: 6px;
                    margin: 20px 0;
                    font-size: 14px;
                    border-left: 4px solid #dc3545;
                }}
                .otp-digits {{
                    display: flex;
                    justify-content: center;
                    gap: 15px;
                    margin: 25px 0;
                }}
                .otp-digit {{
                    width: 60px;
                    height: 80px;
                    background: white;
                    border-radius: 12px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 40px;
                    font-weight: 900;
                    color: #1e3c72;
                    box-shadow: 0 5px 15px rgba(0,0,0,0.2);
                }}
                @media (max-width: 480px) {{
                    .otp-digit {{
                        width: 50px;
                        height: 70px;
                        font-size: 32px;
                    }}
                    .otp-code {{
                        font-size: 36px;
                        letter-spacing: 6px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="email-header">
                    <div class="logo-section">
                        <span class="logo-text">Dusa <span class="brand-text">Films 🔥</span></span>
                    </div>
                    <div class="email-title">Your One-Time Password (OTP)</div>
                </div>
                
                <div class="user-greeting">
                    <p class="greeting-text">Hello <span class="username">{user.username}</span>,</p>
                </div>
                
                <div class="otp-container">
                    <div class="otp-label">Your Verification Code</div>
                    <div class="otp-digits">
                        <div class="otp-digit">{otp[0]}</div>
                        <div class="otp-digit">{otp[1]}</div>
                        <div class="otp-digit">{otp[2]}</div>
                        <div class="otp-digit">{otp[3]}</div>
                        <div class="otp-digit">{otp[4]}</div>
                        <div class="otp-digit">{otp[5]}</div>
                    </div>
                    <div class="otp-code">{otp}</div>
                    <div style="color: rgba(255,255,255,0.8); font-size: 14px;">Use this code to complete your login</div>
                </div>
                
                <div class="instructions">
                    <h3>📱 How to use this OTP:</h3>
                    <ul>
                        <li>Go back to Dusa Films login page</li>
                        <li>Enter the 6-digit code above</li>
                        <li>Click "Verify OTP" to access your account</li>
                    </ul>
                    
                    <div class="expiry-note">
                        ⏰ <strong>This OTP expires in 5 minutes</strong> for security reasons.
                    </div>
                    
                    <div class="warning-note">
                        ⚠️ <strong>Security Notice:</strong> Never share this code with anyone. 
                        Dusa Films staff will never ask for your OTP.
                    </div>
                    
                    <p style="color: #666; margin-top: 25px; font-size: 14px;">
                        If you didn't request this OTP, please ignore this email or contact our support.
                    </p>
                </div>
                
                <div class="email-footer">
                    <p>© {timezone.now().year} Dusa Films — All Rights Reserved</p>
                    <p>Cinematic Excellence & Film Community</p>
                    <div class="footer-links">
                        <a href="{request.scheme}://{request.get_host()}/">Website</a> | 
                        <a href="{request.scheme}://{request.get_host()}/contact/">Support</a> | 
                        <a href="{request.scheme}://{request.get_host()}/about/">About Us</a>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version for email clients that don't support HTML
        text_content = f"""
        DUSA FILMS - Your Login OTP
        
        Hello {user.username},
        
        Your One-Time Password (OTP) is: {otp}
        
        ⏰ This OTP expires in 5 minutes.
        
        To complete your login:
        1. Return to Dusa Films login page
        2. Enter the 6-digit code: {otp}
        3. Click "Verify OTP"
        
        ⚠️ SECURITY NOTICE:
        - Never share this OTP with anyone
        - Dusa Films staff will never ask for your OTP
        - If you didn't request this, please ignore this email
        
        Need help? Contact us: {request.scheme}://{request.get_host()}/contact/
        
        © {timezone.now().year} Dusa Films
        {request.scheme}://{request.get_host()}/
        """
        
        subject = f"🔐 Your Dusa Films OTP: {otp} | Login Verification"
        
        try:
            # Create email with both HTML and plain text versions
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
                reply_to=[settings.DEFAULT_FROM_EMAIL]
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=False)

            messages.success(request, f"OTP sent to {user.email}. Check your inbox!")
            return redirect(f"/accounts/verify-otp/?username={username}")

        except Exception as e:
            print("OTP email failed:", e)
            messages.error(
                request,
                "OTP could not be sent. Email service is currently unavailable."
            )
            return redirect("accounts:otp_login")

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
    username = (request.GET.get("username") or request.POST.get("username") or "").strip().lower()

    if not username:
        messages.error(request, "Username missing. Please try again.")
        return redirect("accounts:otp_login")

    try:
        user = User.objects.get(username__iexact=username)
        profile = user.profile
    except User.DoesNotExist:
        messages.error(request, "Invalid username.")
        return redirect("accounts:otp_login")

    if request.method == "POST":
        otp_input = request.POST.get("otp", "").strip()

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


@staff_member_required
def debug_admin_users(request):
    users = list(
        User.objects.values(
            "id", "username", "email", "is_staff", "is_superuser"
        )
    )
    return JsonResponse(users, safe=False)

# Temporary view to list all users (safe for free Render plan)
def list_users(request):
    users = list(
        User.objects.values("id", "username", "email", "is_staff", "is_superuser")
    )
    return JsonResponse(users, safe=False)

def list_users_debug(request):
    # Simple protection with secret key
    token = request.GET.get("token")
    if token != settings.SECRET_KEY:
        return HttpResponse("Forbidden", status=403)

    User = get_user_model()
    users = User.objects.all()

    output = []
    for u in users:
        output.append(
            f"ID: {u.id} | email: {getattr(u, 'email', '')} | username: {getattr(u, 'username', '')} | is_staff: {u.is_staff}"
        )

    return HttpResponse("<br>".join(output))

User = get_user_model()