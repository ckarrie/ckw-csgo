from django.contrib import admin, messages
from . import models

class MatchMapAdmin(admin.ModelAdmin):
    list_display = ['match', 'rounds_won_team_a', 'rounds_won_team_b', 'played_map', 'has_ended', 'is_live', 'delay_minutes', 'starting_at', 'unplayed', 'map_nr']
    list_editable = ['rounds_won_team_a', 'rounds_won_team_b', 'played_map', 'map_nr']
    list_filter = ['match__tournament', 'match__lineup_a', 'match__lineup_b', 'map_nr']

    ordering = ['-starting_at']

    def has_ended(self, obj):
        return obj.has_ended()
    has_ended.boolean = True

    def is_live(self, obj):
        return obj.is_live()
    is_live.boolean = True


class TournamentAdmin(admin.ModelAdmin):
    search_fields = ['name', 'name_alt', 'name_hltv', 'name_99dmg']
    list_display = ['name', 'name_alt', 'name_hltv', 'name_99dmg']
    actions = ['cleanup']

    def cleanup(self, request, queryset):
        for obj in queryset:
            if " - " in obj.name:
                obj.name = obj.name.split(" - ")[0]
                obj.save()
            if obj.name_alt and " - " in obj.name_alt:
                obj.name_alt = obj.name_alt.split(" - ")[0]
                obj.save()
            if obj.name_99dmg and " - " in obj.name_99dmg:
                obj.name_99dmg = obj.name_99dmg.split(" - ")[0]
                obj.save()


class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'name_long',]
    actions = ['merge']

    def merge(self, request, queryset):
        merge_1 = queryset[0]
        merge_2 = queryset[1]

        if queryset.count() != 2:
            self.message_user(request, "Only 2 selections allowed", level=messages.ERROR)
            return

        if merge_1.name[0] != merge_2.name[0]:
            self.message_user(request, "Must start with same Symbol", level=messages.ERROR)
            return

        new_name, new_long = "", ""

        if len(merge_1.name) > len(merge_2.name):
            new_long = merge_1.name
            new_name = merge_2.name

        elif len(merge_2.name) > len(merge_1.name):
            new_long = merge_2.name
            new_name = merge_1.name

        if new_long and new_name:
            merge_1.name = new_name
            merge_1.name_long = new_long
            merge_1.save()
            merge_2.lineup_set.all().update(team=merge_1)
            merge_2.delete()


admin.site.register(models.Team, TeamAdmin)
admin.site.register(models.Lineup)
admin.site.register(models.LineupPlayer)
admin.site.register(models.Cast)
admin.site.register(models.Map)
admin.site.register(models.Match)
admin.site.register(models.MatchMap, MatchMapAdmin)
admin.site.register(models.Player)
admin.site.register(models.PlayerRole)
admin.site.register(models.Tournament, TournamentAdmin)