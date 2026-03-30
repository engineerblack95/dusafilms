from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    # Dashboard
    path('', views.analytics_dashboard, name='dashboard'),
    path('dashboard/', views.analytics_dashboard, name='dashboard'),
    
    # Watch session tracking
    path('api/track-session/', views.track_watch_session, name='track_session'),
    
    # Download tracking endpoints (updated to match your views)
    path('api/track-download/', views.track_download, name='track_download'),
    path('api/update-download-status/', views.update_download_status, name='update_download_status'),
    
    # Analytics views
    path('movie/<int:movie_id>/', views.movie_details_analytics, name='movie_details'),
    path('user/<int:user_id>/', views.user_analytics, name='user_details'),
    path('export/<str:report_type>/', views.export_analytics, name='export'),
]