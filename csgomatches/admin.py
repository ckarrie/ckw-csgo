from django.contrib import admin
from . import models

class MatchMapAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'has_ended', 'score', 'is_live']

    def has_ended(self, obj):
        return obj.has_ended()

    def score(self, obj):
        return '{}:{}'.format(obj.rounds_won_team_a, obj.rounds_won_team_b)

    def is_live(self, obj):
        return obj.is_live()

admin.site.register(models.Team)
admin.site.register(models.Lineup)
admin.site.register(models.LineupPlayer)
admin.site.register(models.Cast)
admin.site.register(models.Map)
admin.site.register(models.Match)
admin.site.register(models.MatchMap, MatchMapAdmin)
admin.site.register(models.Player)
admin.site.register(models.PlayerRole)
admin.site.register(models.Tournament)