from django.db import models

# Create your models here.
class Track(models.Model):
    track_id = models.CharField(max_length=30, unique=True)

class Playlist(models.Model):
    playlist_id = models.CharField(max_length=30, unique=True)
    tracks = models.ManyToManyField(Track, through='TrackInPlaylist', through_fields=('playlist', 'track'))

class TrackInPlaylist(models.Model):
    track = models.ForeignKey(Track, on_delete=models.CASCADE)
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    position = models.IntegerField()
    sublist = models.ForeignKey(Playlist, on_delete=models.CASCADE, blank=True, related_name='sublist_set')

    class Meta:
        ordering = ['playlist', 'position']
        constraints = [
            models.UniqueConstraint(fields=['playlist', 'position'], name='unique_position_in_playlist')
        ]
