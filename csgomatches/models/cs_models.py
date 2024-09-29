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

    class Meta:
        verbose_name = "CS Tournament"
        verbose_name_plural = "CS Tournaments"


class CsMatch(global_models.Match):
    tournament = models.ForeignKey(CsTournament, on_delete=models.CASCADE, related_name='match_set')

    hltv_match_id = models.CharField(max_length=20, null=True, blank=True, help_text='For HLTV Livescore during match')
    esea_match_id = models.CharField(max_length=255, null=True, blank=True)
    enable_99dmg = models.BooleanField(default=False)
    enable_hltv = models.BooleanField(default=True)

    class Meta:
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
                    mm_obj.played_map = global_models.Map.objects.filter(
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
