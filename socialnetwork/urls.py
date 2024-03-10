from django.urls import path
from socialnetwork import views

urlpatterns = [
    path('login', views.login_action, name='login'),
    path('logout', views.logout_action, name='logout'),
    path('register', views.register_action, name='register'),
    path('', views.global_stream, name='home'),
    path('get-global', views.get_global),
    path('add-post', views.add_post, name='add-post'),
    path('add-comment', views.add_comment, name='add-comment'),
    path('follower_stream', views.follower_stream_action, name='follower_stream'),
    path('get-follower', views.get_follower),
    path('profile', views.my_profile_action, name='profile'),
    path('other_profile/<int:id>', views.other_profile_action, name='other_profile'),
    path('unfollow/<int:id>', views.unfollow_action, name='unfollow'),
    path('follow/<int:id>', views.follow_action, name='follow'),
    path('photo/<int:id>', views.get_photo, name='photo'),
]
