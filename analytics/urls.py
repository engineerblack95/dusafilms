from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.analytics_dashboard, name='dashboard'),
    path('dashboard/', views.analytics_dashboard, name='dashboard'),
    
    # Watch session tracking
    path('api/track-session/', views.track_watch_session, name='track_session'),
    
    # Download tracking endpoints
    path('api/download/start/', views.track_download_start, name='download_start'),
    path('api/download/progress/', views.track_download_progress, name='download_progress'),
    path('api/download/complete/', views.track_download_complete, name='download_complete'),
    path('api/download/failure/', views.track_download_failure, name='download_failure'),
    path('api/download/interrupt/', views.track_download_interrupt, name='download_interrupt'),
    
    # Analytics views
    path('movie/<int:movie_id>/', views.movie_details_analytics, name='movie_details'),
    path('user/<int:user_id>/', views.user_analytics, name='user_details'),
    path('export/<str:report_type>/', views.export_analytics, name='export'),
]