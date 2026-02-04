import django_filters
from django.db.models import Q
from django.apps import apps


class MatchTeamFilter(django_filters.FilterSet):
    # Wir definieren einen künstlichen Parameter "team"
    team = django_filters.CharFilter(method='filter_by_team', label="Filter by Team name", help_text="Examples: BIG, BIG Academy, BIG Equipa")
    game = django_filters.CharFilter(field_name='lineup_a__game__name_short', lookup_expr='iexact', label="Filter by Game", help_text="Examples: cs (Counterstrike), LoL (League of Legends), TM (Trackmainia)")

    class Meta:
        model = apps.get_model('csgomatches.Match')
        fields = []

    def filter_by_team(self, queryset, name, value):
        # Filtert in beiden Feldern gleichzeitig
        return queryset.filter(
            Q(lineup_a__team__name__iexact=value) | 
            Q(lineup_b__team__name__iexact=value)
        )