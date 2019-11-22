from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'team', viewset=views.TeamViewSet)
router.register(r'tournament', viewset=views.TournamentViewSet)
router.register(r'lineup', viewset=views.LineupViewSet)
router.register(r'match_all', views.MatchViewSet, basename='match_all')
router.register(r'match_upcoming', views.MatchUpcomingViewSet, basename='match_upcoming')
router.register(r'match_livescore', views.HLTVLiveScoreViewSet, basename='match_livescore')
