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
            first_map_at__date__gte=timezone.now().date()
        ).order_by('first_map_at')

    def item_title(self, item):
        return str(item)

    def item_description(self, item):
        return item.tournament.name

    def item_start_datetime(self, item):
        return item.first_map_at

    def item_link(self, item):
        return '#matchup-{}'.format(item.pk)


class UpcomingMatchesSitemap(Sitemap):
    changefreq = "hourly"
    priority = 1.0

    def items(self):
        return models.Match.objects.filter(
            first_map_at__date__gte=timezone.now().date()
        ).order_by('first_map_at')

    def location(self, obj):
        return '/#matchup-{}'.format(obj.pk)

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
        archive_url = reverse('match_history', kwargs={'year': obj.first_map_at.year})
        return '{}#matchup-{}'.format(archive_url, obj.pk)

    def lastmod(self, obj):
        return obj.first_map_at
