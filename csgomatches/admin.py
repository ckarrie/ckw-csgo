from django.contrib import admin
from . import models

class MatchMapAdmin(admin.ModelAdmin):
    list_display = ['match', 'rounds_won_team_a', 'rounds_won_team_b', 'played_map', 'has_ended', 'is_live', 'delay_minutes', 'starting_at']
    list_editable = ['rounds_won_team_a', 'rounds_won_team_b', 'played_map']
    list_filter = ['match__tournament', 'match__lineup_a', 'match__lineup_b']

    ordering = ['-starting_at']

    def has_ended(self, obj):
        return obj.has_ended()
    has_ended.boolean = True

    def is_live(self, obj):
        return obj.is_live()
    is_live.boolean = True

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