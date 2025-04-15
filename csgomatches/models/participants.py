from csgomatches.models.base_models import BaseLineup, BasePlayer, BaseParticipant
from csgomatches.models.global_models import Game


class CsParticipant(BaseParticipant):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # Ensure the game is set to Counter-Strike
        if not self.game:
            self.game = Game.objects.get(name_short="cs")
        super().save(*args, **kwargs)


class CsPlayer(CsParticipant, BasePlayer):
    class Meta:
        verbose_name = "CS Player"
        verbose_name_plural = "CS Players"


class CsLineup(CsParticipant, BaseLineup):
    class Meta:
        verbose_name = "CS Lineup"
        verbose_name_plural = "CS Lineups"

    def get_hltv_id_from_name(self):
        from csgomatches.utils.scrapers.hltv import get_hltv_id_from_team_name
        return get_hltv_id_from_team_name(team_mdl=self)


class TrackManiaParticipant(BaseParticipant):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # Ensure the game is set to TrackMania
        if not self.game:
            self.game = Game.objects.get(name_short="tm")
        super().save(*args, **kwargs)


class TrackManiaPlayer(TrackManiaParticipant, BasePlayer):
    class Meta:
        verbose_name = "TrackMania Player"
        verbose_name_plural = "TrackMania Players"


class TrackManiaLineup(TrackManiaParticipant, BaseLineup):
    class Meta:
        verbose_name = "TrackMania Lineup"
        verbose_name_plural = "TrackMania Lineups"
