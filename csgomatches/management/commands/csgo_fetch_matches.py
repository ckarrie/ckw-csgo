import datetime

from django.db.models import Q
from django.utils import timezone, dateparse

from django.apps import apps
from django.core.management.base import BaseCommand

import dateutil.parser

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

        # hltv
        #hltv_url = 'https://www.hltv.org/team/7532/big'
        #response = requests.get(hltv_url)
        #soup = BeautifulSoup(response.text, "html.parser")
        #matchesBox = soup.select('#matchesBox')[0]
        #for teamrow in matchesBox.select('.team-row'):
        #    print(teamrow)

        # hltv via y0fl0w.de
        y_url = 'https://big.y0fl0w.de'
        response_json = requests.get(y_url).json()
        for event_data in response_json:
            event_name = event_data.get('event')
            event_matches = event_data.get('matches', [])
            tournament = apps.get_model('csgomatches.Tournament').objects.filter(
                Q(name=event_name) | Q(name_alt=event_name)
            ).first()
            if not tournament:
                tournament = apps.get_model('csgomatches.Tournament')(name=event_name)
                tournament.save()

            for match_data in event_matches:
                lineup_a = apps.get_model('csgomatches.Lineup').objects.filter(team__name=match_data.get('t1')).first()
                lineup_b = apps.get_model('csgomatches.Lineup').objects.filter(team__name=match_data.get('t2')).first()

                if not lineup_a:
                    team_lineup_a = apps.get_model('csgomatches.Team')(name=match_data.get('t1'))
                    team_lineup_a.save()
                    lineup_a = apps.get_model('csgomatches.Lineup')(team=team_lineup_a, active_from=timezone.now())
                    lineup_a.save()

                if not lineup_b:
                    team_lineup_b = apps.get_model('csgomatches.Team')(name=match_data.get('t2'))
                    team_lineup_b.save()
                    lineup_b = apps.get_model('csgomatches.Lineup')(team=team_lineup_b, active_from=timezone.now())
                    lineup_b.save()


                first_match_start = dateutil.parser.parse(match_data.get('time'))
                aware_first_match_start = timezone.make_aware(first_match_start)

                print("first_match_start", lineup_a, lineup_b, tournament, first_match_start, aware_first_match_start)

                bestof = 3
                if "1" in match_data.get('mType', ''):
                    bestof = 1
                elif "2" in match_data.get('mType', ''):
                    bestof = 2
                elif "3" in match_data.get('mType', ''):
                    bestof = 3
                elif "5" in match_data.get('mType', ''):
                    bestof = 5

                match = apps.get_model('csgomatches.Match').objects.filter(
                    tournament=tournament,
                    lineup_a=lineup_a,
                    lineup_b=lineup_b,
                ).first()

                if not match:
                    match = apps.get_model('csgomatches.Match')(
                        tournament=tournament,
                        lineup_a=lineup_a,
                        lineup_b=lineup_b,
                        bestof=bestof
                    )
                    match.save()

                existing_matchmaps = apps.get_model('csgomatches.MatchMap').objects.filter(
                    match=match
                )

                maps_data = match_data.get('maps', [])

                #if existing_matchmaps.count() != len(maps_data):

                if not existing_matchmaps.exists():
                    for i, map_data in enumerate(maps_data):
                        matchmap = apps.get_model('csgomatches.MatchMap')(
                            match=match,
                            starting_at=aware_first_match_start + timezone.timedelta(hours=i),
                            map_nr=i + 1,

                        )
                        matchmap.save()

                else:
                    for i, map_data in enumerate(maps_data):
                        results = map_data.get('result')
                        name = map_data.get('name')
                        matchmap = apps.get_model('csgomatches.MatchMap').objects.filter(
                            match=match,
                            map_nr=i + 1,
                        ).first()
                        if matchmap:
                            if results and ':' in results:
                                t1_res, t2_res = results.split(":")
                                t1_res, t2_res = int(t1_res), int(t2_res)

                                matchmap.rounds_won_team_a = t1_res
                                matchmap.rounds_won_team_b = t2_res
                                matchmap.save()

                            if name and 'TBA' not in name:
                                # set map
                                print("TBD Setting Map name", name, match)


                        else:
                            print("Cannot find MatchMap", match, map_data)








