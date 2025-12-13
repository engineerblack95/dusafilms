from django.urls import path
from . import views

app_name = "announcements"

urlpatterns = [
    path("", views.announcements_list, name="list"),
    path("<int:id>/", views.announcement_detail, name="detail"),
]
