from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'movies'

urlpatterns = [
    # API ROUTES - MUST BE FIRST
    path('api/search/', views.api_search, name='api_search'),
    path('api/reply/add/', views.ajax_add_reply, name='ajax_add_reply'),
    path('api/comment/edit/<int:comment_id>/', views.api_edit_comment, name='api_edit_comment'),
    path('api/comment/delete/<int:comment_id>/', views.api_delete_comment, name='api_delete_comment'),
    path('api/reply/edit/<int:reply_id>/', views.api_edit_reply, name='api_edit_reply'),
    path('api/reply/delete/<int:reply_id>/', views.api_delete_reply, name='api_delete_reply'),
    
    # Regular routes
    path('', views.home, name='home'),
    path('login/', RedirectView.as_view(url='/accounts/login/'), name='login'),
    path('about/', views.about, name='about'),
    path('search/', views.search, name='search'),
    path('category/<slug:slug>/', views.category_view, name='category'),
    path('watch-later/', views.watch_later_list, name='watch_later_list'),
    path('continue-watching/', views.continue_watching, name='continue_watching'),
    path('my-notifications/', views.my_notifications, name='my_notifications'),
    path('category/<slug:slug>/follow/', views.follow_category, name='follow_category'),
    path('category/<slug:slug>/unfollow/', views.unfollow_category, name='unfollow_category'),
    path('category/<slug:slug>/toggle-notifications/', views.toggle_notification_settings, name='toggle_notifications'),
    path('test-notification/', views.test_notification, name='test_notification'),
    path('comment/<int:comment_id>/reply/', views.add_reply, name='add_reply'),
    path('reply/<int:reply_id>/delete/', views.delete_reply, name='delete_reply'),
    path('reply/<int:reply_id>/edit/', views.edit_reply, name='edit_reply'),
    path('<slug:slug>/comment/', views.add_comment, name='add_comment'),
    path('<slug:slug>/add-to-watch-later/', views.add_to_watch_later, name='add_to_watch_later'),
    path('<slug:slug>/remove-from-watch-later/', views.remove_from_watch_later, name='remove_from_watch_later'),
    path('<slug:slug>/rate/', views.rate_movie, name='rate_movie'),
    path('<slug:slug>/update-progress/', views.update_watch_progress, name='update_watch_progress'),
    path('<slug:slug>/', views.detail, name='detail'),
]