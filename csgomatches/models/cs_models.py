from enum import Enum
from django.db import models
from django.db.models import QuerySet
from django.urls import reverse
import requests

import csgomatches.models.global_models as global_models


class CsPlayer(global_models.Player):
    hltv_id = models.IntegerField(null=True, blank=True)
    esea_user_id = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = "CS Player"
        verbose_name_plural = "CS Players"


class CsTournament(global_models.Tournament):
    name_hltv = models.CharField(max_length=255, null=True, blank=True)
    name_99dmg = models.CharField(max_length=255, null=True, blank=True)
    esea_bracket_id = models.IntegerField(null=True, blank=True)
    esea_bracket_team_ids = models.CharField(max_length=255, null=True, blank=True, help_text='Comma Separated')

    class Meta(global_models.Tournament.Meta):
        verbose_name = "CS Tournament"
        verbose_name_plural = "CS Tournaments"


class CsLineup(global_models.Lineup):
    team = models.ForeignKey(global_models.Team, on_delete=models.CASCADE, related_name='lineup_set')
    class Meta(global_models.Lineup.Meta):
        verbose_name = "CS Lineup"
        verbose_name_plural = "CS Lineups"


class CsMap(global_models.Map):
    class Meta:
        verbose_name = "CS Map"
        verbose_name_plural = "CS Maps"


class CsMatch(global_models.OneOnOneMatch):
    tournament = models.ForeignKey(CsTournament, on_delete=models.CASCADE, related_name='match_set')
    lineup_a = models.ForeignKey(CsLineup, on_delete=models.CASCADE, related_name='matches_as_lineup_a_set', null=True, blank=True)
    lineup_b = models.ForeignKey(CsLineup, on_delete=models.CASCADE, related_name='matches_as_lineup_b_set', null=True, blank=True)

    hltv_match_id = models.CharField(max_length=20, null=True, blank=True, help_text='For HLTV Livescore during match')
    esea_match_id = models.CharField(max_length=255, null=True, blank=True)
    enable_99dmg = models.BooleanField(default=False)
    enable_hltv = models.BooleanField(default=True)

    matchmap_set: QuerySet['CsMatchMap']

    class Meta(global_models.OneOnOneMatch.Meta):
        verbose_name = "CS Match"
        verbose_name_plural = "CS Matches"

    def get_livescore_url(self, request):
        if self.hltv_match_id:
            url = reverse('match_livescore-detail', kwargs={'pk': self.hltv_match_id})
            return request.build_absolute_uri(url)

    def update_hltv_livescore(self, request) -> None:
        # Guard clause in case lineup_a is None
        if not self.lineup_a:
            return

        url = self.get_livescore_url(request=request)
        if url:
            response = requests.get(url=url, params={'format': 'json'}).json()
            maps = response.get('maps', [])
            for map_data in maps:
                map_nr = map_data.get('map_nr')
                mm_obj = self.matchmap_set.filter(map_nr=map_nr).first()
                if mm_obj:
                    mm_obj.map = CsMap.objects.filter(
                        models.Q(name=map_data.get('map_name')) |
                        models.Q(cs_name=map_data.get('map_name'))
                    ).first()
                    score_a, score_b = map_data.get('score_a'), map_data.get('score_b')
                    swap_score = False
                    team_a_hltv_id = response.get('team_a_id')
                    if team_a_hltv_id != self.lineup_a.team.hltv_id:
                        swap_score = True

                    if swap_score:
                        score_b, score_a = score_a, score_b

                    mm_obj.rounds_won_team_a = score_a
                    mm_obj.rounds_won_team_b = score_b
                    mm_obj.save()


class CSLineupPlayerRole(Enum):
    RIFLE = "rifle"
    IGL_RIFLE = "igl_rifle"
    AWP = "awp"
    IGL_AWP = "igl_awp"

    @classmethod
    def choices(cls):
        return [(key.name, key.value) for key in cls]


class CsLineupPlayer(global_models.LineupPlayer):
    player = models.ForeignKey(CsPlayer, on_delete=models.CASCADE)
    lineup = models.ForeignKey(CsLineup, on_delete=models.CASCADE)
    role = models.CharField(
        max_length=20,
        choices=CSLineupPlayerRole.choices(),
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = "CS Lineup Player"
        verbose_name_plural = "CS Lineup Players"

    def __str__(self):
        if self.role:
            return f'{self.player.ingame_name} ({self.role}) @ {self.lineup.team.name}'
        return f'{self.player.ingame_name} @ {self.lineup.team.name}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class CsMatchMap(global_models.OneOnOneMatchMap):
    match = models.ForeignKey(CsMatch, on_delete=models.CASCADE, related_name='matchmap_set')
    map = models.ForeignKey(CsMap, on_delete=models.CASCADE, null=True, blank=True)
    map_pick_of = models.ForeignKey(CsLineup, null=True, blank=True, on_delete=models.CASCADE)

    class Meta(global_models.OneOnOneMatchMap.Meta):
        verbose_name = "CS Match Map"
        verbose_name_plural = "CS Match Maps"

    def has_ended(self) -> bool:
        return (self.rounds_won_team_a >= 13 or self.rounds_won_team_b >= 13) and abs(self.rounds_won_team_a - self.rounds_won_team_b) >= 2
