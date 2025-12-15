from django.urls import path
from . import views

app_name = 'movies'

urlpatterns = [
    # Home
    path('', views.home, name='home'),

    # Static / specific pages FIRST
    path('about/', views.about, name='about'),
    path('search/', views.search, name='search'),
    path('category/<slug:slug>/', views.category_view, name='category'),

    # Movie actions
    path('<slug:slug>/comment/', views.add_comment, name='add_comment'),

    # Movie detail LAST (most generic)
    path('<slug:slug>/', views.detail, name='detail'),
]
