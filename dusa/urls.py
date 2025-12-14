from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static


# --------------------------------------------------
# Root health check (IMPORTANT for Render)
# --------------------------------------------------
def home(request):
    return HttpResponse("Dusa Films is running")


urlpatterns = [
    # Root (must return 200)
    path('', home),

    # Admin
    path('admin/', admin.site.urls),

    # Apps
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),
    path('movies/', include('movies.urls')),
    path('contact/', include('contact.urls')),
    path('announcements/', include('announcements.urls')),
]


# --------------------------------------------------
# Media files (development only)
# --------------------------------------------------
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
