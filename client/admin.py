from django.contrib import admin
from client.models import Track, Playlist, TrackInPlaylist

# Register your models here.
class TrackAdmin(admin.ModelAdmin):
    list_display = ('track_id',)

class PlaylistAdmin(admin.ModelAdmin):
    list_display = ('playlist_id',)

class TrackInPlaylistAdmin(admin.ModelAdmin):
    list_display = ('playlist', 'position', 'track', 'sublist')

admin.site.register(Track, TrackAdmin)
admin.site.register(Playlist, PlaylistAdmin)
admin.site.register(TrackInPlaylist, TrackInPlaylistAdmin)
