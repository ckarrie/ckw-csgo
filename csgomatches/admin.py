from django.contrib import admin, messages
from django.utils.safestring import mark_safe

from . import models


# Inlines
class LineupPlayerInline(admin.TabularInline):
    model = models.LineupPlayer
    autocomplete_fields = ['player']
    extra = 5
    max_num = 5


class LineupInline(admin.TabularInline):
    model = models.Lineup
    extra = 0


class MatchMapInline(admin.TabularInline):
    model = models.MatchMap
    extra = 0
    verbose_name = 'Map'
    verbose_name_plural = 'Match Maps'


class ExternalLinkInline(admin.TabularInline):
    model = models.ExternalLink
    extra = 0


# Models
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


class TeamAdmin(admin.ModelAdmin):
    search_fields = ['name', 'name_long', 'name_alt']
    list_display = ['name', 'name_long', 'name_alt', 'hltv_id', 'hltv_link', 'lineup_logo']
    list_editable = ['name_alt', 'hltv_id']
    actions = [
        #'merge',  # deactivated - need fix
        'get_hltv_id_from_name',
        'build_players'
    ]
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

            # for lu i

    def get_hltv_id_from_name(self, request, queryset):
        for obj in queryset.filter(hltv_id__isnull=True):
            obj.hltv_id = obj.get_hltv_id_from_name()
            if obj.hltv_id:
                obj.save()
                self.message_user(
                    request,
                    f"Found HLTV ID {obj.hltv_id} for {obj.name}",
                    level=messages.SUCCESS
                )

    def hltv_link(self, obj):
        url = obj.get_hltv_team_link()
        if url:
            return mark_safe(f'<a href="{url}" target="_blank">{obj.name}</a>')
        return ''

    def lineup_logo(self, obj):
        current_lineup = obj.lineup_set.filter(team_logo_url__isnull=False).active_lineups().first()
        if current_lineup:
            url = current_lineup.team_logo_url
            if url.startswith("https://static.hltv.org/images/team/logo/"):
                hltv_static, url_part = url.split("https://static.hltv.org/images/team/logo/")
                if url_part == str(obj.hltv_id):
                    return mark_safe('<img style="width: 35px" src="{url}" alt="{url}" title="{url}"> SAME ID'.format(url=url))
                else:
                    return mark_safe('<img style="width: 35px" src="{url}" alt="{url}" title="{url}"> DIFFERENT ID'.format(url=url))
            return mark_safe('<img style="width: 35px" src="{url}" alt="{url}" title="{url}">'.format(url=url))

    def build_players(self, request, queryset):
        for obj in queryset:
            from csgomatches.utils.scrapers.hltv import build_players
            build_players(team_mdl=obj)
            self.message_user(
                request,
                f"Build player for Team {obj.name}",
                level=messages.SUCCESS
            )


class LineupAdmin(admin.ModelAdmin):
    search_fields = ['team__name', 'team__name_long', 'team__name_alt']
    list_display = ['team', 'game', 'team_logo_url', 'active_from', 'get_is_active', 'is_active']
    autocomplete_fields = ['team']
    list_filter = ['game', 'is_active']
    inlines = [LineupPlayerInline]

    def get_is_active(self, obj):
        return obj.get_is_active()
    get_is_active.boolean = True


class MatchAdmin(admin.ModelAdmin):
    list_display = ['tournament', 'lineup_a', 'lineup_b', 'bestof', 'first_map_at', 'overall_score', 'slug', ]
    list_filter = ['lineup_a', 'lineup_b']
    search_fields = ['lineup_b__team__name', 'lineup_b__team__name_long', 'tournament__name']
    autocomplete_fields = ['lineup_a', 'lineup_b', 'tournament']
    inlines = [MatchMapInline, ExternalLinkInline]
    # replace "Save and add another" button with "Save as new" to use previous matches as template
    # https://docs.djangoproject.com/en/5.1/ref/contrib/admin/#django.contrib.admin.ModelAdmin.save_as
    save_as = True

    def overall_score(self, obj):
        score = obj.get_overall_score()
        return '{}:{}'.format(*score)


class PlayerAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'ingame_name', 'first_name', 'last_name']
    search_fields = ['ingame_name', 'first_name', 'last_name']
    list_editable = ['ingame_name', 'first_name', 'last_name']


class LineupPlayerAdmin(admin.ModelAdmin):
    list_display = ['player', 'role', 'lineup']
    list_editable = ['role']
    list_filter = ['role']
    search_fields = ['player__ingame_name', 'lineup__team__name']


class ExternalLinkAdmin(admin.ModelAdmin):
    list_display = ['match', 'link_type', 'title', 'url', 'link_flag']
    list_filter = ['link_flag']
    raw_id_fields = ['match']
    list_editable = ['url', 'title']
    search_fields = ['url']
    # autocomplete_fields = ['match']


class GameAdmin(admin.ModelAdmin):
    list_display = ['name', 'name_short', 'slug']
    search_fields = ['name', 'name_short']
    prepopulated_fields = {'slug': ('name_short',), }


def save_global(modeladmin, request, queryset):
    for obj in queryset:
        obj.save()


admin.site.register(models.Team, TeamAdmin)
admin.site.register(models.Lineup, LineupAdmin)
admin.site.register(models.LineupPlayer, LineupPlayerAdmin)
admin.site.register(models.ExternalLink, ExternalLinkAdmin)
admin.site.register(models.Map)
admin.site.register(models.Match, MatchAdmin)
admin.site.register(models.MatchMap, MatchMapAdmin)
admin.site.register(models.CsPlayer, PlayerAdmin)
admin.site.register(models.PlayerRole)
admin.site.register(models.Tournament, TournamentAdmin)
admin.site.register(models.Game, GameAdmin)
admin.site.register(models.StaticPage)

admin.site.add_action(save_global, 'save_selected')
