from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import timezone
from django_ical.views import ICalFeed

from . import models


class UpcomingEventsFeed(ICalFeed):
    """
    A simple event calender
    """
    product_id = '-//wannspieltbig.de//Upcoming Matches//DE'
    timezone = 'Europe/Berlin'
    file_name = "big_upcoming.ics"

    def items(self):
        return models.Match.objects.filter(
            first_map_at__date__gte=timezone.now().date() - timezone.timedelta(days=2)
        ).order_by('first_map_at')

    def item_title(self, item):
        score_a, score_b = item.get_overall_score()
        if item.is_live() or item.has_ended():
            #score_a, score_b = item.get_overall_score()
            current_matchmap = None
            current_map_name = ''
            for mm in item.matchmap_set.all():
                if mm.played_map:
                    current_map_name = mm.played_map.name
                if mm.is_live():
                    return f"{item} - {current_map_name} {mm.rounds_won_team_a}:{mm.rounds_won_team_b} ({score_a}:{score_b})"
        return f"{item} - {score_a}:{score_b}"
        #return str(item)

    def item_description(self, item):
        d = {
            'cover_url': "https://www.roaringbears.de/Event_Cover.png",
            'item_url': 'https://wannspieltbig.de/' + item.slug,
            'event': item.tournament.name,
        }
        return '+++\ncover="{cover_url}"\n+++\n\n\n{event}\n\n{item_url}'.format(**d)

    def item_location(self, item):
        return item.get_block_voice_channel_display()

    def item_start_datetime(self, item):
        return item.first_map_at

    def item_end_datetime(self, item):
        last_map = item.get_last_matchmap()
        if last_map:
            return last_map.starting_at + timezone.timedelta(hours=1)

    def item_link(self, item):
        return item.get_absolute_url()


class FilteredUpcomingEventsFeed(UpcomingEventsFeed):
     def items(self):
         qs = super(FilteredUpcomingEventsFeed, self).items()
         qs = qs.filter(lineup_a__game__slug='cs')
         return qs


class UpcomingMatchesSitemap(Sitemap):
    changefreq = "hourly"
    priority = 1.0

    def items(self):
        return models.Match.objects.filter(
            first_map_at__date__gte=timezone.now().date()
        ).order_by('first_map_at')

    def location(self, obj):
        return obj.get_absolute_url()

    def lastmod(self, obj):
        return obj.first_map_at


class ArchiveMatchesSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.5

    def items(self):
        return models.Match.objects.filter(
            first_map_at__date__lt=timezone.now().date()
        ).order_by('-first_map_at')

    def location(self, obj):
        return obj.get_absolute_url()

    def lastmod(self, obj):
        return obj.first_map_at
