from .models import Game

def games(request):
    return {
        'games': Game.objects.all()
    }
