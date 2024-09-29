from django.db import models

from csgomatches.models import Player


class CsPlayer(Player):
    hltv_id = models.IntegerField(null=True, blank=True)
    esea_user_id = models.IntegerField(null=True, blank=True)
