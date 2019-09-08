from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from urllib.parse import urlencode
from uuid import uuid4
from base64 import b64encode
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
        'user-read-private'
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
