from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from client.models import Track, Playlist, TrackInPlaylist
from urllib.parse import urlencode
from uuid import uuid4
from base64 import b64encode
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from . import serializers
import os
import requests
import environs

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ENV = environs.Env()
ENV.read_env(os.path.join(BASE_DIR, '.env'))

redirect_uri = 'https://chowington.pythonanywhere.com/spotivore/client'
client_id = '1f9f77385be84819a18e2af962f839ba'

with open(os.path.join(BASE_DIR, 'spotify_client_secret.txt')) as f:
    client_secret = f.read().strip()

if ENV('DJANGO_HOST') == 'local':
    with open(os.path.join(BASE_DIR, 'spotify_access_token.txt')) as f:
        access_token = f.read().strip()

# Create your views here.
def login_view(request):
    scopes = [
        'playlist-read-collaborative',
        'playlist-modify-private',
        'streaming',
        'playlist-modify-public',
        'playlist-read-private',
        'user-read-email',
        'user-read-private',
        'user-modify-playback-state'
    ]

    session_id = str(uuid4())
    request.session['session_id'] = session_id

    data = {
        'client_id': client_id,
        'response_type': 'code',
        'redirect_uri': redirect_uri,
        'scope': ' '.join(scopes),
        'state': session_id
    }

    url = 'https://accounts.spotify.com/authorize?' + urlencode(data)

    return HttpResponseRedirect(url)

def client_view(request):
    if ENV('DJANGO_HOST') != 'local':
        if ('session_id' in request.session and 
                request.GET['state'] == request.session['session_id']):
            request.session.flush()

            data = {
                'grant_type': 'authorization_code',
                'code': request.GET['code'],
                'redirect_uri': redirect_uri
            }

            b64_string = b64encode('{}:{}'.format(client_id, client_secret).encode()).decode()

            headers = {
                'Authorization': 'Basic ' + b64_string
            }

            response = requests.post('https://accounts.spotify.com/api/token', data=data, headers=headers)
            response.raise_for_status()

            js = {'data': response.json()}

            return render(request, 'client/client.html', js)

        else:
            return HttpResponse('Invalid request')

    else:
        with open(os.path.join(BASE_DIR, 'spotify_access_token.txt')) as f:
            access_token = f.read().strip()

        js = {'data': {'access_token': access_token}}

        return render(request, 'client/client.html', js)

class Playlists(APIView):
    def get(self, request, format=None):
        playlist_ids = request.GET.getlist('id[]')
        playlist_objs = Playlist.objects.filter(playlist_id__in=playlist_ids)
        serializer = serializers.PlaylistSerializer(playlist_objs, many=True)
        return Response(serializer.data)

class PlaylistTracks(APIView):
    def get(self, request, playlist_id, format=None):
        try:
            playlist_obj = Playlist.objects.get(playlist_id=playlist_id)

            if playlist_obj.has_local_changes:
                tracklist = get_spotivore_playlist_tracks(playlist_id)
                send = True
            else:
                send = False

        except Playlist.DoesNotExist:
            send = False

        if send:
            return Response(tracklist)
        else:
            data = {
                'error': 'resource not found in Spotivore',
                'resource': playlist_id
            }
            return Response(data, status=status.HTTP_404_NOT_FOUND)

class PlaylistSublists(APIView):
    """
    List all sublists of a playlist or add a new sublist
    to a playlist.
    """
    def post(self, request, playlist_id, format=None):
        serializer = serializers.SublistSerializer(data=request.data)

        if serializer.is_valid():
            # Get playlist tracks from Spotify
            playlist_tracks = get_spotify_playlist_tracks(playlist_id)

            # Check to see whether playlist object exists
            try:
                playlist_obj = Playlist.objects.get(playlist_id=playlist_id)

                # If it does, check whether it's up to date
                # Make sure all tracks in same order are there
                # If not, return error
                curr_playlist_tracks = get_spotivore_playlist_tracks(playlist_id)

                if playlist_tracks != curr_playlist_tracks:
                    if not playlist_obj.has_local_changes:
                        # If we don't match with Spotify but we don't have local changes,
                        # we're just out-of-date, so update
                        TrackInPlaylist.objects.filter(playlist=playlist_obj).delete()
                        add_tracks_to_playlist(playlist_id, playlist_tracks)

                    else:
                        data = {
                            'error': 'resource has local changes',
                            'resource': playlist_id
                        }
                        return Response(data, status=status.HTTP_409_CONFLICT)

            # If it doesn't, make it
            except Playlist.DoesNotExist:
                # Create playlist object
                playlist_obj = Playlist.objects.create(playlist_id=playlist_id)
                # Add tracks to it
                add_tracks_to_playlist(playlist_id, playlist_tracks)

            # Add sublist
            add_sublist(playlist_id, serializer.validated_data['sublist_id'])

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Sync a playlist object with Spotify's version of the playlist
def sync_playlist(playlist_id):
    # Get track list from Spotify
    spotify_tracklist = get_spotify_playlist_tracks(playlist_id)
    # Get the tracks in Spotivore's version
    spotivore_track_objs = TrackInPlaylist.objects.filter(playlist__playlist_id=playlist_id)
    # Get the ordered tracklist from the tracks
    spotivore_tracklist = spotivore_track_objs.order_by('position').values_list('track', flat=True)
    # If there are differences, overwrite Spotivore's version
    if spotify_tracklist != spotivore_tracklist:
        spotivore_track_objs.delete()
        add_tracks_to_playlist(playlist_id, spotify_tracklist)

        playlist_obj = Playlist.objects.get(playlist_id=playlist_id)
        playlist_obj.has_local_changes = False
        playlist_obj.save()

        return spotify_tracklist

    else:
        return None

# Add a sublist to a playlist
def add_sublist(parent_list_id, sublist_id):
    if parent_list_id == sublist_id:
        raise ValueError('Cannot add a playlist as its own sublist.')
    elif parent_list_id in get_sublists_deep(sublist_id):
        raise ValueError("Parent playlist exists in sublist's sublist tree.")
    else:
        try:
            sublist_obj = Playlist.objects.get(playlist_id=sublist_id)
        except Playlist.DoesNotExist:
            sublist_obj = create_new_playlist_obj(sublist_id)

        playlist_obj = Playlist.objects.get(playlist_id=parent_list_id)
        playlist_obj.sublists.add(sublist_obj)

# Return a list of a playlist's first-level sublists
def get_sublists(playlist_id):
    try:
        return list(Playlist.objects.get(playlist_id=playlist_id).sublists.all().values_list('playlist_id', flat=True))
    except Playlist.DoesNotExist:
        return []

# Return a list of all sublists of a playlist recursively
def get_sublists_deep(playlist_id):
    all_sublists = first_level_sublists = get_sublists(playlist_id)

    for sublist in first_level_sublists:
        all_sublists.extend(get_sublists_deep(sublist))

    return all_sublists

# Get a playlist's tracklist from Spotify
def get_spotify_playlist_tracks(playlist_id):
    url = 'https://api.spotify.com/v1/playlists/' + playlist_id + '/tracks'
    return fetch_tracklist(url)

def get_spotivore_playlist_tracks(playlist_id):
    return list(TrackInPlaylist.objects.filter(playlist__playlist_id=playlist_id).order_by('position').values_list('track__track_id', flat=True))

# Add tracks from all sublists to this playlist
# Also recursively add tracks to sublists from their own sublists
class add_tracks_from_sublists(APIView):
    def patch(self, request, playlist_id, format=None):
        try:
            playlist_obj = Playlist.objects.get(playlist_id=playlist_id)

            if playlist_obj.has_local_changes:
                raise ValueError('Parent playlist has local changes.')

            # Check to see whether any playlist in the sublist tree has local changes
            for sublist_id in get_sublists_deep(playlist_id):
                if Playlist.objects.get(playlist_id=sublist_id).has_local_changes:
                    raise ValueError(f'Sublist {sublist_id} has local changes.')

            add_tracks_from_sublists_recursive(playlist_id)
            new_tracklist = get_spotivore_playlist_tracks(playlist_id)

            return Response(new_tracklist, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response([str(e)], status=status.HTTP_400_BAD_REQUEST)

def add_tracks_from_sublists_recursive(playlist_id):
    sync_playlist(playlist_id)
    playlist_obj = Playlist.objects.get(playlist_id=playlist_id)
    playlist_tracks = playlist_obj.tracks.all()
    sublists = playlist_obj.sublists.all()
    playlist_changed = False

    for sublist in sublists:
        add_tracks_from_sublists_recursive(sublist.playlist_id)
        sublist_tracks = sublist.tracks.all()

        for track_obj in sublist_tracks:
            if track_obj not in playlist_tracks:
                TrackInPlaylist.objects.create(track=track_obj, playlist=playlist_obj, position=len(playlist_tracks) + 1)
                playlist_changed = True
                playlist_obj.refresh_from_db()
                playlist_tracks = playlist_obj.tracks.all()

    if playlist_changed:
        playlist_obj.has_local_changes = True
        playlist_obj.save()

class save_playlist_changes_to_spotify(APIView):
    def put(self, request, playlist_id, format=None):
        try:
            # Get track list from Spotify
            spotify_tracklist = get_spotify_playlist_tracks(playlist_id)
            # Get the tracks in Spotivore's version
            spotivore_track_objs = TrackInPlaylist.objects.filter(playlist__playlist_id=playlist_id)
            # Get the ordered tracklist from the tracks
            spotivore_tracklist = spotivore_track_objs.order_by('position').values_list('track', flat=True)

            if len(spotify_tracklist) != len(set(spotify_tracklist)) or len(spotivore_tracklist) != len(set(spotivore_tracklist)):
                raise ValueError('Cannot currently handle duplicate tracks in a playlist.')

            if spotify_tracklist != spotivore_tracklist:
                # Determine the tracks to delete and add
                deleted_tracks = [track for track in spotify_tracklist if track not in spotivore_tracklist]
                added_tracks = [track for track in spotivore_tracklist if track not in spotify_tracklist]

                # Set request metadata
                url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
                headers = {
                    'Authorization': 'Bearer ' + access_token,
                    'Content-Type': 'application/json'
                }

                # Delete from Spotify the tracks that Spotivore deleted
                data = {
                    'tracks': [{'uri': f'spotify:track:{track_id}'} for track_id in deleted_tracks]
                }
                response = requests.delete(url, headers=headers, data=data)
                response.raise_for_status()

                # Add to Spotify the tracks that Spotivore added
                data = {
                    'uris': [f'spotify:track:{track_id}' for track_id in added_tracks]
                }
                response = requests.post(url, headers=headers, data=data)
                response.raise_for_status()

                # Reorder tracks to match Spotivore's ordering
                current_spotify_tracklist = [track for track in spotify_tracklist if track in spotivore_tracklist].extend(added_tracks)

                for correct_index, track_id in enumerate(spotivore_tracklist):
                    spotify_index = current_spotify_tracklist.index(track_id)

                    if spotify_index != correct_index:
                        data = {
                            'range_start': spotify_index,
                            'insert_before': correct_index
                        }
                        response = requests.put(url, headers=headers, data=data)
                        response.raise_for_status()

                        # Update our replica
                        current_spotify_tracklist.insert(correct_index, current_spotify_tracklist.pop(spotify_index))

            return Response(status=status.HTTP_201_CREATED)

        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)

# Recursively fetch a tracklist using the given URL
def fetch_tracklist(url):
    # Need to receive this from the client (or maybe from session?)
    headers = {'Authorization': 'Bearer ' + access_token}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    js = response.json()

    playlist_tracks = [item['track']['id'] for item in js['items']]
    next_url = js['next']

    if next_url:
        return playlist_tracks + fetch_tracklist(next_url)
    else:
        return playlist_tracks

def add_tracks_to_playlist(playlist_id, track_ids):
    playlist_obj = Playlist.objects.get(playlist_id=playlist_id)
    num_tracks = playlist_obj.tracks.count()

    for index, track_id in enumerate(track_ids):
        try:
            track_obj = Track.objects.get(track_id=track_id)
        except Track.DoesNotExist:
            track_obj = Track.objects.create(track_id=track_id)
        finally:
            TrackInPlaylist.objects.create(track=track_obj, playlist=playlist_obj, position=num_tracks + index + 1)

def create_new_playlist_obj(playlist_id):
    playlist_obj = Playlist.objects.create(playlist_id=playlist_id)
    tracklist = get_spotify_playlist_tracks(playlist_id)
    add_tracks_to_playlist(playlist_id, tracklist)

    return playlist_obj.refresh_from_db()
