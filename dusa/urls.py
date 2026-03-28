from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView

urlpatterns = [
    # Handle admin with and without trailing slash
    path('admin', RedirectView.as_view(url='/admin/', permanent=True)),
    path('admin/', admin.site.urls),

    # Apps
    path('accounts/', include('accounts.urls')),
    path('contact/', include('contact.urls')),
    path('announcements/', include('announcements.urls')),
    path('analytics/', include('analytics.urls')),
    
    # Movies - this will handle all movie-related URLs including home
    path('', include('movies.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)