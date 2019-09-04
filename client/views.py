from django.shortcuts import render
from django.http import HttpResponseRedirect
from urllib.parse import urlencode

# Create your views here.
def login_view(request):
    scopes = [
        'playlist-read-collaborative',
        'playlist-modify-private',
        'streaming',
        'playlist-modify-public',
        'playlist-read-private',
    ]

    payload = {
        'client_id': '1f9f77385be84819a18e2af962f839ba',
        'response_type': 'code',
        'redirect_uri': 'https://chowington.pythonanywhere.com/spotifor/client',
        'scope': ' '.join(scopes),
    }

    url = 'https://accounts.spotify.com/authorize?' + urlencode(payload)

    return HttpResponseRedirect(url)

def client_view(request):
    return render(request, 'client/client.html')
