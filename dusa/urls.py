from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),

    # Static pages / sections FIRST
    path('contact/', include('contact.urls')),
    path('announcements/', include('announcements.urls')),

    # Movies LAST (because it has <slug>)
    path('', include('movies.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
