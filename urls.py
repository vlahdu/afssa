from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .forms import LoginForm

app_name = 'core'

urlpatterns = [
    path('', views.index, name='index'),  # Home page
    path('signup/', views.signup, name='signup'),  # User signup
    path('rate/<int:video_id>/', views.rate_private_video, name='rate_private_video'),  # Rate a private video
    path('rate_public/<int:video_id>/', views.rate_public_video, name='rate_public_video'),  # Rate a public video
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html', authentication_form=LoginForm), name='login'),  # User login
    path('logout/', views.logout_view, name='logout'),  # User logout
    path('generate_video/', views.generate_video, name='generate_video'),  # Generate a video
    path('toggle_visibility/<int:video_id>/', views.toggle_visibility, name='toggle_visibility'),  # Toggle video visibility
    path('public_videos/', views.public_videos, name='public_videos'),  # List of public videos
    path('delete_video/<int:video_id>/', views.delete_video, name='delete_video'),  # Delete a video
]
