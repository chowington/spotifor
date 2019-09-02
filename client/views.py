from django.shortcuts import render

# Create your views here.
def player(request):
    return render(request, 'client/player.html')

