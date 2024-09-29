from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.views.decorators.cache import cache_page
from rest_framework import viewsets, mixins, pagination, views, routers, renderers, permissions, authentication
from django.apps import apps
from rest_framework.response import Response

from . import ser
from . import ser_objects
from . import renderer as cs_renderer

from csgomatches.utils.scrapers.faceit import check_hubs_for_matches


class CsPagination(pagination.LimitOffsetPagination):
    max_limit = 50
    default_limit = 20


class CsView(views.APIView):
    pagination_class = CsPagination

    def get_renderers(self):
        rend = super(CsView, self).get_renderers()
        for r in rend:
            if isinstance(r, renderers.BrowsableAPIRenderer):
                r.template = 'csgomatches/rest_framework/csgo_api.html'

        return rend

    @property
    def name(self):
        return "API für " + self.request.build_absolute_uri()


class CsAPIRootView(CsView, routers.APIRootView):
    def get_view_description(self, html=False):
        if html:
            return mark_safe('<p>Willkommen! API made by <a href="https://karrie.software" target="_blank">'
                             'karrie.software</a> with the power of '
                             '<a href="https://www.django-rest-framework.org/">'
                             'django-rest-framework.org</a><p>')
        return "Willkommen"

    def get_view_name(self):
        return "Browse API"

    def get_renderers(self):
        rend = super(CsAPIRootView, self).get_renderers()
        for r in rend:
            if isinstance(r, renderers.BrowsableAPIRenderer):
                r.template = 'csgomatches/rest_framework/csgo_api.html'

        return rend


class TeamViewSet(CsView, viewsets.ReadOnlyModelViewSet):
    """
    Cs Teams
    """
    queryset = apps.get_model('csgomatches.Team').objects.all()
    serializer_class = ser.TeamSerializer

    def get_view_name(self):
        return 'Teams'


class TournamentViewSet(CSGOView, viewsets.ReadOnlyModelViewSet):
    queryset = apps.get_model('csgomatches.CsTournament').objects.all()
    serializer_class = ser.CSGOTournamentSerializer

    def get_view_name(self):
        return 'Tournaments'


class MatchViewSet(CSGOView, viewsets.ReadOnlyModelViewSet):
    queryset = apps.get_model('csgomatches.CsMatch').objects.all()
    serializer_class = ser.CSGOMatchSerializer

    def get_view_name(self):
        return 'Matches (all)'

    @method_decorator(cache_page(60 * 5))
    def list(self, request, *args, **kwargs):
        return super(MatchViewSet, self).list(request, *args, **kwargs)


class MatchUpcomingViewSet(CSGOView, viewsets.ReadOnlyModelViewSet):
    queryset = apps.get_model('csgomatches.CsMatch').objects.filter(first_map_at__gte=timezone.now())
    serializer_class = ser.CSGOMatchSerializer

    def get_view_name(self):
        return 'Matches (upcoming)'

    @method_decorator(cache_page(10))
    def list(self, request, *args, **kwargs):
        return super(MatchUpcomingViewSet, self).list(request, *args, **kwargs)


class LineupViewSet(CsView, viewsets.ReadOnlyModelViewSet):
    queryset = apps.get_model('csgomatches.CsLineup').objects.all()
    serializer_class = ser.CsLineupSerializer

    def get_view_name(self):
        return 'Team Lineups'

    @method_decorator(cache_page(60 * 5))
    def list(self, request, *args, **kwargs):
        return super(LineupViewSet, self).list(request, *args, **kwargs)


class HLTVLiveScoreViewSet(CsView, mixins.RetrieveModelMixin, mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    Get HLTV Live Score from any Match
    """

    def get_view_name(self):
        return 'Matches (mit HLTV.org Scoreboard)'

    def get_queryset(self):
        last_7_days = timezone.now() - timezone.timedelta(days=7)
        return apps.get_model('csgomatches.CsMatch').objects.filter(
            hltv_match_id__isnull=False,
            first_map_at__gte=last_7_days
        )

    def get_serializer(self, *args, **kwargs):
        ser_by_action = {
            'list': ser.CsMatchSerializer,
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

class MatchMapUpdateView(CsView, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    permission_classes = (permissions.IsAdminUser, )
    authentication_classes = (authentication.BasicAuthentication, )
    queryset = apps.get_model('csgomatches.CsMatchMap').objects.all()
    serializer_class = ser.CsMatchMapUpdateSerializer

class FaceitProLeagueMatchesView(CsView, viewsets.ViewSet):
    serializer_class = ser.FaceitProLeagueMatchesSerializer

    def get_instances(self):
        m_instances = []
        faceit_dict = check_hubs_for_matches()
        looked_up_nicknames = faceit_dict.get('looked_up_nicknames', [])
        matches_dict = faceit_dict.get('matches', [])
        for match_nr, match_data in matches_dict.items():
            if match_data.get('players', []):
                faceit_match = ser_objects.FPLMatch(nr=match_nr, match_data=match_data, looked_up_nicknames=looked_up_nicknames)
                m_instances.append(faceit_match)
        return m_instances

    def list(self, request):
        serializer = ser.FaceitProLeagueMatchesSerializer(
            instance=self.get_instances(),
            many=True
        )
        return Response(serializer.data)
