from django.db import models
#from django.db.models import Q, F

# Create your models here.
class Track(models.Model):
    track_id = models.CharField(max_length=30, unique=True)

class Playlist(models.Model):
    playlist_id = models.CharField(max_length=30, unique=True)
    tracks = models.ManyToManyField(Track, through='TrackInPlaylist', through_fields=('playlist', 'track'))
    #sublists = models.ManyToManyField('self', through='Sublist', through_fields=('parent_list', 'sublist'))
    sublists = models.ManyToManyField('self', symmetrical=False, related_name='parent_list_set')
    has_local_changes = models.BooleanField(default=False)

    '''class Meta:
        constraints = [
            models.CheckConstraint(check=~Q(sublists__contains=F('playlist_id')), name='sublist_not_same_as_parent')
            #models.CheckConstraint(check=~Q(playlist_id__in=sublists, name='sublist_not_same_as_parent'))
        ]'''

class TrackInPlaylist(models.Model):
    track = models.ForeignKey(Track, on_delete=models.CASCADE)
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    position = models.IntegerField()

    # The sublist a song came from, if any
    # Can be used to handle when there are multiple copies of a song in a playlist
    #sublist = models.ForeignKey(Playlist, on_delete=models.CASCADE, blank=True, null=True, related_name='sublist_set')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['playlist', 'position'], name='unique_position_in_playlist')
        ]

'''class Sublist(models.Model):
    parent_list = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    sublist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name='sublist_set')

    class Meta:
        constraints = [
            models.CheckConstraint(check=~Q(parent_list=F('sublist')), name='sublist_not_same_as_parent')
        ]'''