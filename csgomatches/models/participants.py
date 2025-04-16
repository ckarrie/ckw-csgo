from csgomatches.models.base_models import BaseLineup, BasePlayer
from csgomatches.models.global_models import Game


class CsPlayer(BasePlayer):
    class Meta:
        verbose_name = "CS Player"
        verbose_name_plural = "CS Players"

    def save(self, *args, **kwargs):
        # Ensure the game is set to Counter-Strike
        if not self.game:
            self.game = Game.objects.get(name_short="cs")
        super().save(*args, **kwargs)


class CsLineup(BaseLineup):
    class Meta:
        verbose_name = "CS Lineup"
        verbose_name_plural = "CS Lineups"

    def save(self, *args, **kwargs):
        # Ensure the game is set to Counter-Strike
        if not self.game:
            self.game = Game.objects.get(name_short="cs")
        super().save(*args, **kwargs)

    def get_hltv_id_from_name(self):
        from csgomatches.utils.scrapers.hltv import get_hltv_id_from_team_name
        return get_hltv_id_from_team_name(team_mdl=self)


class TrackManiaPlayer(BasePlayer):
    class Meta:
        verbose_name = "TrackMania Player"
        verbose_name_plural = "TrackMania Players"

    def save(self, *args, **kwargs):
        # Ensure the game is set to TrackMania
        if not self.game:
            self.game = Game.objects.get(name_short="tm")
        super().save(*args, **kwargs)


class TrackManiaLineup(BaseLineup):
    class Meta:
        verbose_name = "TrackMania Lineup"
        verbose_name_plural = "TrackMania Lineups"

    def save(self, *args, **kwargs):
        # Ensure the game is set to TrackMania
        if not self.game:
            self.game = Game.objects.get(name_short="tm")
        super().save(*args, **kwargs)
