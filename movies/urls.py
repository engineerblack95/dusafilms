from django.urls import path
from . import views

app_name = 'movies'
urlpatterns = [
    path('', views.home, name='home'),
    path('movie/<slug:slug>/', views.detail, name='detail'),
    path('search/', views.search, name='search'),
    path("movie/<slug:slug>/comment/", views.add_comment, name="add_comment"),
    path("category/<slug:slug>/", views.category_view, name="category"),
    path("about/", views.about, name="about")

]

