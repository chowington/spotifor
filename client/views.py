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

class PlaylistSublists(APIView):
    """
    List all sublists of a playlist or add a new sublist
    to a playlist.
    """
    def post(self, request, playlist_id, format=None):
        serializer = serializers.SublistSerializer(data=request.data)

        if serializer.is_valid():
            # Get playlist tracks from Spotify
            url = 'https://api.spotify.com/v1/playlists/' + playlist_id + '/tracks'
            
            playlist_tracks = self.fetch_list(url)

            # Check to see whether playlist object exists
            try:
                playlist_obj = Playlist.objects.get(playlist_id=playlist_id)

                # If it does, check whether it's up to date
                # Make sure all tracks in same order are there
                # If not, return error
                curr_playlist_tracks = [track_obj.track_id for track_obj in playlist_obj.tracks.all()]

                if playlist_tracks != curr_playlist_tracks:
                    data = {
                        'error': 'resource out of date',
                        'resource': playlist_id
                    }
                    return Response(data, status=status.HTTP_409_CONFLICT)

            # If it doesn't, make it
            except Playlist.DoesNotExist:
                # Save playlist object
                playlist_obj = Playlist.objects.create(playlist_id=playlist_id)

                # Save track objects if needed
                for index, track_id in enumerate(playlist_tracks):
                    try:
                        track_obj = Track.objects.get(track_id=track_id)
                    except Track.DoesNotExist:
                        track_obj = Track.objects.create(track_id=track_id)
                    finally:
                        TrackInPlaylist.objects.create(track=track_obj, playlist=playlist_obj, position=index)

            # Add sublist
            # Get sublist tracks from Spotify

            # Add to playlist track list

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def fetch_list(self, url):
        headers = {'Authorization': 'Bearer ' + 'BQBQE6htZzd-QHNZFrEtl4NTo30gWts-OJTATDfa0NevfNRZqJyJErpLhQI7nBGhw4PjFyhyRooto3xA80hzreE7xlm9GeTK-BskZG74lbmbCVzHIFbvRQ25H3pvTCRRcoT31V_udu6pc7VLJ9L2deaTlsknbgoNoIwp6EuSLqQQNBDNyLW9HszsBQ'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        js = response.json()

        playlist_tracks = [item['track']['id'] for item in js['items']]
        next_url = js['next']

        if next_url:
            return playlist_tracks + self.fetch_list(next_url)
        else:
            return playlist_tracks
