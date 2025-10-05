from csgomatches.models.base_models import BaseOneOnOneMatch
from csgomatches.models.global_models import Game

class CsMatch(BaseOneOnOneMatch):
    class Meta:
        verbose_name = "CS Match"
        verbose_name_plural = "CS Matches"

    def __str__(self):
        return f"{self.participant_1} vs {self.participant_2} on {self.starts_at}"

    def save(self, *args, **kwargs):
        # Ensure the game is set to Counter-Strike
        if not self.game:
            self.game = Game.objects.get(name_short="cs")
        super().save(*args, **kwargs)
