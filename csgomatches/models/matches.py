from django.db import models

from csgomatches.models.base_models import BaseMatch, BaseOneOnOneMatch
from csgomatches.models.global_models import Game
from csgomatches.models.participants import CsParticipant

class CsMatch(BaseOneOnOneMatch):
    match_type = models.CharField(
        max_length=60,
        choices=BaseMatch.MatchType.choices,
        default=BaseMatch.MatchType.BO1,  # Default to BO1
        verbose_name="Match Type",
    )

    starts_at = models.DateTimeField(
        verbose_name="Match Start Time",
        help_text="The time when the match starts.",
    )
    participant_1 = models.ForeignKey(
        CsParticipant,
        on_delete=models.CASCADE,
        related_name="participant_1",
        verbose_name="Participant 1",
    )
    participant_2 = models.ForeignKey(
        CsParticipant,
        on_delete=models.CASCADE,
        related_name="participant_2",
        verbose_name="Participant 2",
    )

    def __str__(self):
        return f"{self.participant_1} vs {self.participant_2} on {self.starts_at}"

    def save(self, *args, **kwargs):
        # Ensure the game is set to Counter-Strike
        if not self.game:
            self.game = Game.objects.get(name_short="cs")

        # set slug
        if not self.slug:
            self.slug = f"{self.participant_1.slug}_{self.participant_2.slug}_{self.starts_at.strftime('%Y%m%d%H%M%S')}"
        super().save(*args, **kwargs)
