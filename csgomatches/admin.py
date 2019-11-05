from django.contrib import admin
from . import models

admin.site.register(models.Team)
admin.site.register(models.Lineup)
admin.site.register(models.LineupPlayer)
admin.site.register(models.Cast)
admin.site.register(models.Map)
admin.site.register(models.Match)
admin.site.register(models.MatchMap)
admin.site.register(models.Player)
admin.site.register(models.PlayerRole)
admin.site.register(models.Tournament)