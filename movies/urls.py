from django.urls import path
from . import views

app_name = 'movies'

urlpatterns = [
    path('', views.home, name='home'),

    # Movie detail & actions
    path('<slug:slug>/', views.detail, name='detail'),
    path('<slug:slug>/comment/', views.add_comment, name='add_comment'),

    # Other pages
    path('search/', views.search, name='search'),
    path('category/<slug:slug>/', views.category_view, name='category'),
    path('about/', views.about, name='about'),
]
