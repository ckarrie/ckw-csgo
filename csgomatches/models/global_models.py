from enum import Enum
from django.db import models

from csgomatches.models.base_models import BaseMatch, BaseParticipant, BaseMatchMap


class WinType(Enum):
    PARTICIPANT_1 = "Participant 1"
    PARTICIPANT_2 = "Participant 2"
    DRAW = "Draw"


class Game(models.Model):
    name = models.CharField(max_length=255, help_text='i.e. "TrackMania" or "Counter-Strike"')
    name_short = models.CharField(max_length=4, help_text='i.e. "tm", "cs"')
    game_logo_url = models.URLField(null=True, blank=True)
    game_logo_width = models.IntegerField(null=True, blank=True, help_text="i.e. 50 for 50px")
    slug = models.SlugField()

    def __str__(self):
        return self.name


class Organization(models.Model):  # this replaces the old Team model
    name = models.CharField(max_length=255)
    name_long = models.CharField(max_length=255, null=True, blank=True)
    logo_url = models.URLField(null=True, blank=True)
    slug = models.SlugField()

    def __str__(self):
        return self.name

    def all_participants(self) -> models.QuerySet[BaseParticipant]:
        return self.participants.all()  # type: ignore


class Map(models.Model):
    name = models.CharField(max_length=255)
    ingame_name = models.CharField(max_length=255, default='de_', null=True, blank=True)

    def __str__(self):
        return self.name

class OneOnOneMatchMap(BaseMatchMap):
    score_participant_1 = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Score Participant 1",
    )
    score_participant_2 = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Score Participant 2",
    )