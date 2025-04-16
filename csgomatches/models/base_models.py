from typing import Optional, Tuple
from django.db import models
from django.utils.translation import gettext_lazy
from polymorphic.models import PolymorphicModel
from abc import abstractmethod

# Note: We're using a lot of polymorphic models here to allow for dynamic participant types.
# This makes querying and filtering easier in the future.


class BaseParticipant(PolymorphicModel):
    """
    Abstract model for a participant in a match.
    """
    game = models.ForeignKey(
        "csgomatches.Game",
        on_delete=models.SET_NULL,
        editable=False,  # The game will be set by the subclass
        null=True,
    )
    organization = models.ForeignKey(
        "csgomatches.Organization",
        on_delete=models.CASCADE,
        related_name="%(class)ss",
    )
    name = models.CharField(
        max_length=255,
        verbose_name="Participant Name (Lineup / Ingame Name)",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Participant"
        verbose_name_plural = "Participants"

    def __str__(self):
        return f"{self.__class__.__name__} for {self.organization}"


class BaseLineup(BaseParticipant):
    """
    Abstract model for a lineup in a match.
    A lineup is a collection of players that represent an organization in a match.
    """
    class Meta:
        ordering = ["name"]
        verbose_name = "Lineup"
        verbose_name_plural = "Lineups"

    def __str__(self):
        return f"{self.organization.name} - {self.game.name_short if self.game else 'Unknown Game'} - {self.name}"


class BasePlayer(BaseParticipant):
    """
    Abstract model for a player in a match.
    This is a subclass of BaseParticipant, so it can directly be used in matches.
    """
    first_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )
    last_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )
    lineup = models.ForeignKey(
        BaseLineup,
        on_delete=models.CASCADE,
        related_name="%(class)ss",
        null=True,
        blank=True,
        help_text="The lineup this player belongs to. Can be null if the player is not part of a lineup.",
    )

    class Meta:
        abstract = True
        ordering = ["name"]
        verbose_name = "Player"
        verbose_name_plural = "Players"

    def __str__(self):
        if self.first_name and self.last_name:
            return f'{self.first_name} "{self.name}" {self.last_name}'
        return f"{self.name}"


class BaseWinCondition(PolymorphicModel):
    name = models.CharField(max_length=255, editable=False)

    class Meta:
        verbose_name = "Win Condition"
        verbose_name_plural = "Win Conditions"
        ordering = ["name"]

    @abstractmethod
    def has_ended(self, *args, **kwargs) -> bool:
        """
        Abstract method to determine if the match has ended.
        This should be implemented in subclasses.
        """
        raise NotImplementedError("This method should be implemented in subclasses.")

    @abstractmethod
    def get_winner(self, *args, **kwargs) -> Optional[BaseParticipant]:
        """
        Abstract method to get the winner of the match.
        This should be implemented in subclasses.
        """
        raise NotImplementedError("This method should be implemented in subclasses.")

    @abstractmethod
    def save(self, *args, **kwargs):
        """
        Abstract method to save the win condition.
        This should be implemented in subclasses.
        This is abstract to ensure the subclass implements logic to set the name.
        """
        super().save(*args, **kwargs)


class BaseMatch(PolymorphicModel):
    class MatchType(models.TextChoices):
        BO1 = "bo1", gettext_lazy("Best of 1")
        BO3 = "bo3", gettext_lazy("Best of 3")
        BO5 = "bo5", gettext_lazy("Best of 5")
        BO7 = "bo7", gettext_lazy("Best of 7")

    slug = models.SlugField(
        max_length=255,
        unique=True,
        verbose_name="Match Slug",
        help_text="A unique identifier for the match.",
        editable=False
    )
    starting_at = models.DateTimeField(
        verbose_name="Match Start Time",
        help_text="The time when the match starts.",
    )
    match_type = models.CharField(
        max_length=60,
        choices=MatchType,
        verbose_name="Match Type",
    )
    win_condition_map = models.ForeignKey(
        BaseWinCondition,
        on_delete=models.CASCADE,
        related_name="%(class)ses",
        verbose_name="Map Win Condition",
        help_text="The win condition for each map of the match.",
    )

    class Meta:
        ordering = ["-starting_at"]
        verbose_name = "Match"
        verbose_name_plural = "Matches"

    @abstractmethod
    def save(self, *args, **kwargs):
        """
        Abstract method to save the match.
        This should be implemented in subclasses.
        This is abstract to ensure the subclass implements logic to set the slug.
        """
        super().save(*args, **kwargs)


class BaseOneOnOneMatch(BaseMatch):
    participant_1 = models.ForeignKey(
        BaseParticipant,
        on_delete=models.CASCADE,
        related_name="one_on_one_matches_p1",
    )
    participant_2 = models.ForeignKey(
        BaseParticipant,
        on_delete=models.CASCADE,
        related_name="one_on_one_matches_p2",
    )

    @property
    def maps(self):
        """
        Returns the maps for the match.
        """
        return self.match_maps.all()

    def get_score(self) -> Tuple[int, int]:
        """
        Returns the score of the match.
        """
        from csgomatches.models.global_models import WinType
        score_participant_1 = 0
        score_participant_2 = 0
        for match_map in self.maps:
            winner = match_map.get_winner()
            if not winner:
                return score_participant_1, score_participant_2
            if winner == WinType.PARTICIPANT_1:
                score_participant_1 += 1
            elif winner == WinType.PARTICIPANT_2:
                score_participant_2 += 1
            elif winner == WinType.DRAW:
                score_participant_1 += 1
                score_participant_2 += 1
        return score_participant_1, score_participant_2

    def has_ended(self) -> bool:
        """
        Check if the match has ended.
        """
        score = self.get_score()
        match self.match_type:
            case self.MatchType.BO1:
                return score[0] == 1 or score[1] == 1
            case self.MatchType.BO3:
                return score[0] == 2 or score[1] == 2
            case self.MatchType.BO5:
                return score[0] == 3 or score[1] == 3
            case self.MatchType.BO7:
                return score[0] == 4 or score[1] == 4
            case _:
                raise ValueError(f"Invalid match type: {self.match_type}.")


class BaseMatchMap(PolymorphicModel):
    """
    Abstract model for a match map.
    This is a subclass of BaseMatch, so it can directly be used in matches.
    """
    match = models.ForeignKey(
        BaseMatch,
        on_delete=models.CASCADE,
        related_name="%(class)ss",
    )
    map = models.ForeignKey(
        "csgomatches.Map",
        on_delete=models.CASCADE,
        related_name="maps",
    )
    map_number = models.PositiveSmallIntegerField(verbose_name="Map Number")
    starting_at = models.DateTimeField(
        verbose_name="Map Start Time",
        help_text="The time when the map starts.",
    )

    class Meta:
        ordering = ["map_number"]
        verbose_name = "Match Map"
        verbose_name_plural = "Match Maps"

    def __str__(self):
        return f"{self.map} - {self.match}"

    @property
    def win_condition(self):
        return self.match.win_condition_map

    def has_ended(self) -> bool:
        """
        Check if the match map has ended.
        """
        return self.win_condition.has_ended(self)

    def get_winner(self) -> BaseParticipant:
        """
        Get the winner of the match map.
        """
        return self.win_condition.get_winner(self)
