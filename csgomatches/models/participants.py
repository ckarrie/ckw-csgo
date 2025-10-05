from django.core.exceptions import ValidationError

from csgomatches.models.base_models import BaseLineup, BasePlayer
from csgomatches.models.global_models import Game


class CsPlayer(BasePlayer):
    class Meta:
        verbose_name = "CS Player"
        verbose_name_plural = "CS Players"

    def save(self, *args, **kwargs):
        if self.lineup and not isinstance(self.lineup, CsLineup):
            raise ValidationError({"lineup": "CS players can only join CS lineups."})

        if self.lineup:
            self.organization = self.lineup.organization

        if self.game and self.game.name_short != "cs":
            raise ValidationError({"game": "CS players must be associated with the Counter-Strike game."})

        lineup_game = self.lineup.game if self.lineup and self.lineup.game else None
        # Ensure the game is set to Counter-Strike
        if lineup_game:
            self.game = lineup_game
        elif not self.game:
            self.game = Game.objects.get(name_short="cs")

        super().save(*args, **kwargs)


class CsLineup(BaseLineup):
    class Meta:
        verbose_name = "CS Lineup"
        verbose_name_plural = "CS Lineups"

    def save(self, *args, **kwargs):
        if self.game and self.game.name_short != "cs":
            raise ValidationError({"game": "CS lineups must be associated with the Counter-Strike game."})
        # Ensure the game is set to Counter-Strike
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
        if self.lineup and not isinstance(self.lineup, TrackManiaLineup):
            raise ValidationError({"lineup": "TrackMania players can only join TrackMania lineups."})

        if self.lineup:
            self.organization = self.lineup.organization

        if self.game and self.game.name_short != "tm":
            raise ValidationError({"game": "TrackMania players must be associated with the TrackMania game."})

        lineup_game = self.lineup.game if self.lineup and self.lineup.game else None
        # Ensure the game is set to TrackMania
        if lineup_game:
            self.game = lineup_game
        elif not self.game:
            self.game = Game.objects.get(name_short="tm")
        super().save(*args, **kwargs)


class TrackManiaLineup(BaseLineup):
    class Meta:
        verbose_name = "TrackMania Lineup"
        verbose_name_plural = "TrackMania Lineups"

    def save(self, *args, **kwargs):
        if self.game and self.game.name_short != "tm":
            raise ValidationError({"game": "TrackMania lineups must be associated with the TrackMania game."})
        # Ensure the game is set to TrackMania
        self.game = Game.objects.get(name_short="tm")
        super().save(*args, **kwargs)
