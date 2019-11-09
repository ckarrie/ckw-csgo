from django_ical.views import ICalFeed
from django.utils import timezone
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


