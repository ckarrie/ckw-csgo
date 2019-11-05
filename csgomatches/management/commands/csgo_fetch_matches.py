import datetime

from django.db.models import Q
from django.utils import timezone

from django.apps import apps
from django.core.management.base import BaseCommand

from bs4 import BeautifulSoup
import requests


class Command(BaseCommand):
    help = 'Update Weather infos for Logo Access Projects'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fake',
            action='store_true',
            dest='fake',
            default=False,
            help='Fake',
        )

    def handle(self, *args, **options):
        updated_records = 0
        fake = options['fake']

        hltv_url = 'https://www.hltv.org/team/7532/big'
        response = requests.get(hltv_url)
        soup = BeautifulSoup(response.text, "html.parser")
        matchesBox = soup.select('#matchesBox')[0]
        for teamrow in matchesBox.select('.team-row'):
            print(teamrow)
