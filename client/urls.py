from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('client/', views.client_view, name='client'),
    path('api/playlists/<str:playlist_id>/sublists', views.PlaylistSublists.as_view())
]
