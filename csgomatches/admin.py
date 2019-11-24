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
    actions = ['cleanup', 'merge_two']

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

        names = list(set(queryset.values_list('name', flat=True)))
        for name in names:
            name_qs = queryset.filter(name=name)
            obj_1 = name_qs[0]
            other_objs = name_qs[1:]
            if other_objs.exists():
                print(obj_1, "others:", other_objs.count(), other_objs.values_list('id', flat=True))
                for other_obj in other_objs:
                    other_obj.match_set.update(tournament=obj_1)
                    other_obj.delete()

    def merge_two(self, request, queryset):
        first = queryset[0]
        second = queryset[1]
        if second.name_hltv:
            first.name_hltv = second.name_hltv
        if second.name_99dmg:
            first.name_99dmg = second.name_99dmg

        existing_matches = second.match_set.all()
        for em in existing_matches:
            first_match = models.Match.objects.filter(tournament=first, lineup_a=em.lineup_a, lineup_b=em.lineup_b).first()
            if first_match:
                em.externallink_set.update(match=first_match)
                em.delete()

        first.save()
        second.delete()

class LineupInline(admin.TabularInline):
    model = models.Lineup
    extra = 0


class TeamAdmin(admin.ModelAdmin):
    search_fields = ['name', 'name_long', 'name_alt']
    list_display = ['name', 'name_long', 'name_alt', 'hltv_id']
    actions = ['merge']
    inlines = [LineupInline]

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
            merge_2.lineup_set.update(team=merge_1)
            merge_2.delete()

            #for lu i

class LineupAdmin(admin.ModelAdmin):
    search_fields = ['team__name', 'team__name_long', 'team__name_alt']
    list_display = ['team', 'team_logo_url', 'active_from']

class MatchMapInline(admin.TabularInline):
    model = models.MatchMap
    extra = 0
    verbose_name = 'Map'
    verbose_name_plural = 'Match Maps'

class ExternalLinkInline(admin.TabularInline):
    model = models.ExternalLink
    extra = 0

class MatchAdmin(admin.ModelAdmin):
    list_display = ['tournament', 'lineup_a', 'lineup_b', 'bestof', 'first_map_at', 'overall_score', 'slug',]
    list_filter = ['lineup_a', 'lineup_b']
    search_fields = ['lineup_b__team__name', 'lineup_b__team__name_long', 'tournament__name']
    autocomplete_fields = ['lineup_a', 'lineup_b', 'tournament']
    inlines = [MatchMapInline, ExternalLinkInline]

    def overall_score(self, obj):
        score = obj.get_overall_score()
        return '{}:{}'.format(*score)


class ExternalLinkAdmin(admin.ModelAdmin):
    list_display = ['match', 'link_type', 'title', 'url', 'link_flag']
    list_filter = ['link_flag']
    raw_id_fields = ['match']
    list_editable = ['url', 'title']
    search_fields = ['url']
    #autocomplete_fields = ['match']


def save_global(modeladmin, request, queryset):
    for obj in queryset:
        obj.save()


admin.site.register(models.Team, TeamAdmin)
admin.site.register(models.Lineup, LineupAdmin)
admin.site.register(models.LineupPlayer)
admin.site.register(models.ExternalLink, ExternalLinkAdmin)
admin.site.register(models.Map)
admin.site.register(models.Match, MatchAdmin)
admin.site.register(models.MatchMap, MatchMapAdmin)
admin.site.register(models.Player)
admin.site.register(models.PlayerRole)
admin.site.register(models.Tournament, TournamentAdmin)

admin.site.add_action(save_global, 'save_selected')