from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import viewsets, mixins
from django.apps import apps

from . import ser
from . import ser_objects

class TeamViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = apps.get_model('csgomatches.Team').objects.all()
    serializer_class = ser.CSGOTeamSerializer

class TournamentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = apps.get_model('csgomatches.Tournament').objects.all()
    serializer_class = ser.CSGOTournamentSerializer

class MatchViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = apps.get_model('csgomatches.Match').objects.all()
    serializer_class = ser.CSGOMatchSerializer

    @method_decorator(cache_page(60 * 5))
    def list(self, request, *args, **kwargs):
        return super(MatchViewSet, self).list(request, *args, **kwargs)
        

class MatchUpcomingViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = apps.get_model('csgomatches.Match').objects.filter(first_map_at__gte=timezone.now())
    serializer_class = ser.CSGOMatchSerializer

    @method_decorator(cache_page(10))
    def list(self, request, *args, **kwargs):
        return super(MatchUpcomingViewSet, self).list(request, *args, **kwargs)

class LineupViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = apps.get_model('csgomatches.Lineup').objects.all()
    serializer_class = ser.CSGOLineupSerializer

    @method_decorator(cache_page(60 * 5))
    def list(self, request, *args, **kwargs):
        return super(LineupViewSet, self).list(request, *args, **kwargs)


class HLTVLiveScoreViewSet(mixins.RetrieveModelMixin,
                           mixins.ListModelMixin,
                           mixins.CreateModelMixin,
                           viewsets.GenericViewSet):

    def get_queryset(self):
        last_7_days = timezone.now() - timezone.timedelta(days=7)
        return apps.get_model('csgomatches.Match').objects.filter(
            hltv_match_id__isnull=False,
            first_map_at__gte=last_7_days
        )

    def get_serializer(self, *args, **kwargs):
        ser_by_action = {
            'list': ser.CSGOMatchSerializer,
            'retrieve': ser.HLTVMatchSerializer,
            'create': ser.HLTVMatchSerializer,
        }
        ser_class = ser_by_action[self.action]
        kwargs['context'] = self.get_serializer_context()
        return ser_class(*args, **kwargs)

    def get_renderer_context(self):
        ctx = super(HLTVLiveScoreViewSet, self).get_renderer_context()
        indent = 2
        if not ctx.get('indent'):
            ctx.update({'indent': indent})
        return ctx

    def get_object(self):
        hltv_match_id = int(self.kwargs.get('pk'))
        hltv_match_instance = ser_objects.HLTVMatch(hltv_match_id=hltv_match_id)
        return hltv_match_instance



