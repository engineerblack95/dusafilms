from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication URLs
    path('register/', views.register, name='register'),
    path('login/', views.otp_login, name='otp_login'),
    path('send-otp/', views.send_otp, name='send_otp'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Comment Management (NEW)
    path('comment/delete/<int:comment_id>/', views.delete_comment, name='delete_comment'),
    path('comment/edit/<int:comment_id>/', views.edit_comment, name='edit_comment'),
    
    # Profile Management (optional - if you have these)
    # path('profile/edit/', views.edit_profile, name='edit_profile'),
    # path('change-password/', views.change_password, name='change_password'),
    
    # DEBUG / ADMIN
    path('debug-admins/', views.debug_admin_users),
    path('list-users/', views.list_users, name='list_users'),
    path('debug-users/', views.list_users_debug),
]