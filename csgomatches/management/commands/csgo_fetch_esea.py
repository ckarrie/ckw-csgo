import asyncio
from json import JSONDecodeError

import dateutil.parser
import requests
from bs4 import BeautifulSoup
from django.apps import apps
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from csgomatches.utils.scrapers.esea import get_bracket_match, get_esea_match


class Command(BaseCommand):
    help = 'Update Weather infos for Logo Access Projects'

    def add_arguments(self, parser):
        parser.add_argument('--esea_ids', nargs='+', type=int)
        parser.add_argument('--match_id', nargs='+', type=int)
        parser.add_argument('--update_matchmap_id', nargs='+', type=int)
        parser.add_argument('--reverse_score', action='store_true', dest='reverse_score', default=False)

    def handle(self, *args, **options):
        """
        usage:

        python manage.py csgo_fetch_esea --esea_ids 532 33579 --match_id 1177 --reverse_score


        :param args:
        :param options:
        :return:
        """

        updated_records = 0

        # hltv
        # hltv_url = 'https://www.hltv.org/team/7532/big'
        # response = requests.get(hltv_url)
        # soup = BeautifulSoup(response.text, "html.parser")
        # matchesBox = soup.select('#matchesBox')[0]
        # for teamrow in matchesBox.select('.team-row'):
        #    print(teamrow)

        bracket_id, match_id = options['esea_ids']
        update_id = options['match_id'][0]
        reverse_score = options['reverse_score']

        #print(options)

        if bracket_id and match_id:
            get_bracket_match(bracket_id=bracket_id, match_id=match_id, update_id=update_id)

        elif match_id:
            get_esea_match(match_id=match_id, update_id=update_id)


