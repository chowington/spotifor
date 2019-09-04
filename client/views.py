from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from urllib.parse import urlencode
from uuid import uuid4

# Create your views here.
def login_view(request):
    scopes = [
        'playlist-read-collaborative',
        'playlist-modify-private',
        'streaming',
        'playlist-modify-public',
        'playlist-read-private',
    ]

    session_id = str(uuid4())
    request.session['session_id'] = session_id

    payload = {
        'client_id': '1f9f77385be84819a18e2af962f839ba',
        'response_type': 'code',
        'redirect_uri': 'https://chowington.pythonanywhere.com/spotifor/client',
        'scope': ' '.join(scopes),
        'state': session_id
    }

    url = 'https://accounts.spotify.com/authorize?' + urlencode(payload)

    return HttpResponseRedirect(url)

def client_view(request):
    if request.GET['session_id'] == request.session['session_id']:
        request.session.flush()
        return render(request, 'client/client.html')
    else:
        return HttpResponse('Invalid request')
