from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.views.decorators.cache import cache_page
from rest_framework import viewsets, mixins, pagination, views, routers, renderers
from django.apps import apps

from . import ser
from . import ser_objects
from . import renderer as cs_renderer


class CSGOPagination(pagination.LimitOffsetPagination):
    max_limit = 50
    default_limit = 20

class CSGOView(views.APIView):
    pagination_class = CSGOPagination
    def get_renderers(self):
        rend = super(CSGOView, self).get_renderers()
        for r in rend:
            if isinstance(r, renderers.BrowsableAPIRenderer):
                r.template = 'csgomatches/rest_framework/csgo_api.html'

        return rend

    @property
    def name(self):
        return "API für " + self.request.build_absolute_uri()


class CSGOAPIRootView(CSGOView, routers.APIRootView):
    def get_view_description(self, html=False):
        if html:
            return mark_safe('Willkommen! API made by <a href="https://xn--karri-fsa.de">'
                             'karri&eacute;.de</a> with the power of '
                             '<a href="https://www.django-rest-framework.org/">'
                             'django-rest-framework.org</a>')
        return "Willkommen"

    def get_view_name(self):
        return "Browse API"

    def get_renderers(self):
        rend = super(CSGOAPIRootView, self).get_renderers()
        for r in rend:
            if isinstance(r, renderers.BrowsableAPIRenderer):
                r.template = 'csgomatches/rest_framework/csgo_api.html'

        return rend


class TeamViewSet(CSGOView, viewsets.ReadOnlyModelViewSet):
    """
    CSGO Teams
    """
    queryset = apps.get_model('csgomatches.Team').objects.all()
    serializer_class = ser.CSGOTeamSerializer

    def get_view_name(self):
        return 'Teams'

class TournamentViewSet(CSGOView, viewsets.ReadOnlyModelViewSet):
    queryset = apps.get_model('csgomatches.Tournament').objects.all()
    serializer_class = ser.CSGOTournamentSerializer

    def get_view_name(self):
        return 'Tournaments'

class MatchViewSet(CSGOView, viewsets.ReadOnlyModelViewSet):
    queryset = apps.get_model('csgomatches.Match').objects.all()
    serializer_class = ser.CSGOMatchSerializer

    def get_view_name(self):
        return 'Matches (all)'

    @method_decorator(cache_page(60 * 5))
    def list(self, request, *args, **kwargs):
        return super(MatchViewSet, self).list(request, *args, **kwargs)
        

class MatchUpcomingViewSet(CSGOView, viewsets.ReadOnlyModelViewSet):
    queryset = apps.get_model('csgomatches.Match').objects.filter(first_map_at__gte=timezone.now())
    serializer_class = ser.CSGOMatchSerializer

    def get_view_name(self):
        return 'Matches (upcoming)'

    @method_decorator(cache_page(10))
    def list(self, request, *args, **kwargs):
        return super(MatchUpcomingViewSet, self).list(request, *args, **kwargs)

class LineupViewSet(CSGOView, viewsets.ReadOnlyModelViewSet):
    queryset = apps.get_model('csgomatches.Lineup').objects.all()
    serializer_class = ser.CSGOLineupSerializer

    def get_view_name(self):
        return 'Team Lineups'

    @method_decorator(cache_page(60 * 5))
    def list(self, request, *args, **kwargs):
        return super(LineupViewSet, self).list(request, *args, **kwargs)


class HLTVLiveScoreViewSet(CSGOView, mixins.RetrieveModelMixin, mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    Get HLTV Live Score from any Match
    """
    def get_view_name(self):
        return 'Matches (mit HLTV.org Scoreboard)'

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



