import dateutil.parser
import requests
from bs4 import BeautifulSoup
from django.apps import apps
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

HLTV_MAP_NAMES_TO_CS_NAME = {
    'Nuke': 'de_nuke',
    'Overpass': 'de_overpass',
    'Mirage': 'de_mirage',
    'Train': 'de_train',
    'Dust2': 'de_dust2',
    'Inferno': 'de_inferno',
    'Cache': 'de_cache',
    'Vertigo': 'de_vertigo',
}


class Command(BaseCommand):
    help = 'Update Weather infos for Logo Access Projects'

    def add_arguments(self, parser):
        parser.add_argument(
            '--include_archive_pages',
            action='store_true',
            dest='include_archive_pages',
            default=False,
            help='Include Archive Pages',
        )

        parser.add_argument(
            '--fake',
            action='store_true',
            dest='fake',
            default=False,
            help='Fake',
        )

        parser.add_argument(
            '--y0fl0w',
            action='store_true',
            dest='y0fl0w',
            default=False,
            help='Use y0fl0w',
        )

        parser.add_argument(
            '--dmg99',
            action='store_true',
            dest='dmg99',
            default=False,
            help='Use 99dmg',
        )

    def handle(self, *args, **options):
        """
        usage:

        python manage.py csgo_fetch_matches --y0fl0w
        python manage.py csgo_fetch_matches --dmg99

        :param args:
        :param options:
        :return:
        """

        updated_records = 0
        fake = options['fake']

        # hltv
        # hltv_url = 'https://www.hltv.org/team/7532/big'
        # response = requests.get(hltv_url)
        # soup = BeautifulSoup(response.text, "html.parser")
        # matchesBox = soup.select('#matchesBox')[0]
        # for teamrow in matchesBox.select('.team-row'):
        #    print(teamrow)



        if options['y0fl0w']:
            self.crawl_y0fl0w_de()
        if options['dmg99']:
            self.crawl_99damage_de(include_archive_pages=options['include_archive_pages'])

    def crawl_y0fl0w_de(self):
        map_to_left = ['BIG']
        y_url = 'https://big.y0fl0w.de'
        response_json = requests.get(y_url).json()
        for event_data in response_json:
            event_name = event_data.get('event')
            event_matches = event_data.get('matches', [])
            tournament = apps.get_model('csgomatches.Tournament').objects.filter(
                Q(name=event_name) | Q(name_alt=event_name) | Q(name_hltv=event_name) | Q(name_99dmg=event_name)
            ).first()
            if not tournament:
                tournament = apps.get_model('csgomatches.Tournament')(
                    name=event_name,
                    name_hltv=event_name
                )
                tournament.save()

            if not tournament.name_hltv:
                tournament.name_hltv = event_name
                tournament.save()

            for match_data in event_matches:
                lineup_a = apps.get_model('csgomatches.Lineup').objects.filter(
                    Q(team__name=match_data.get('t1')) | Q(team__name_long=match_data.get('t1'))
                ).first()
                lineup_b = apps.get_model('csgomatches.Lineup').objects.filter(
                    Q(team__name=match_data.get('t2')) | Q(team__name_long=match_data.get('t2'))
                ).first()

                if not lineup_a:
                    team_lineup_a = apps.get_model('csgomatches.Team')(name=match_data.get('t1'))
                    team_lineup_a.save()
                    lineup_a = apps.get_model('csgomatches.Lineup')(team=team_lineup_a, active_from=timezone.now())
                    lineup_a.save()

                if lineup_a and match_data.get('t1_hltvID') and not lineup_a.team_logo_url:
                    lineup_a.team_logo_url = 'https://static.hltv.org/images/team/logo/' + match_data.get('t1_hltvID')
                    lineup_a.save()

                if not lineup_b:
                    team_lineup_b = apps.get_model('csgomatches.Team')(name=match_data.get('t2'))
                    team_lineup_b.save()
                    lineup_b = apps.get_model('csgomatches.Lineup')(team=team_lineup_b, active_from=timezone.now())
                    lineup_b.save()

                if lineup_b and match_data.get('t2_hltvID') and not lineup_b.team_logo_url:
                    lineup_b.team_logo_url = 'https://static.hltv.org/images/team/logo/' + match_data.get('t2_hltvID')
                    lineup_b.save()

                swap_team_and_score = False
                if match_data.get('t1') not in map_to_left:
                    swap_team_and_score = True
                    lineup_a, lineup_b = lineup_b, lineup_a

                first_match_start = dateutil.parser.parse(match_data.get('time'), dayfirst=True)
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

                # if existing_matchmaps.count() != len(maps_data):

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

                                if swap_team_and_score:
                                    t1_res, t2_res = t2_res, t1_res


                                matchmap.rounds_won_team_a = t1_res
                                matchmap.rounds_won_team_b = t2_res
                                matchmap.save()

                            if name and 'TBA' not in name:
                                # set map
                                cs_name = HLTV_MAP_NAMES_TO_CS_NAME.get(name, None)
                                # not found in HLTV_MAP_NAMES_TO_CS_NAME
                                if cs_name:
                                    played_map, played_map_created = apps.get_model('csgomatches.Map').objects.get_or_create(
                                        cs_name=cs_name,
                                        defaults={
                                            'name': name
                                        }
                                    )
                                else:
                                    played_map, played_map_created = apps.get_model('csgomatches.Map').objects.get_or_create(
                                        cs_name='de_' + name.lower(),
                                        defaults={
                                            'name': name
                                        }
                                    )
                                print("TBD Setting Map name", name, match)
                                matchmap.played_map = played_map
                                matchmap.save()

                        else:
                            print("Cannot find MatchMap", match, map_data)

    def crawl_99damage_de(self, include_archive_pages=False):
        map_to_left = ['BIG', 'BIG.A']
        dmg_urls = [
            'https://csgo.99damage.de/de/matches&filter_team=13782',  # BIG
            'https://csgo.99damage.de/de/matches&filter_team=22961',  # BIG. OMEN Academy
        ]

        limit_subpages = 5

        if include_archive_pages:
            limit_subpages = None
            dmg_urls += [
                'https://csgo.99damage.de/de/matches&filter_team=13782&archiv_page=2',  # BIG
                'https://csgo.99damage.de/de/matches&filter_team=13782&archiv_page=3',  # BIG
                'https://csgo.99damage.de/de/matches&filter_team=13782&archiv_page=4',  # BIG
                'https://csgo.99damage.de/de/matches&filter_team=13782&archiv_page=5',  # BIG
                'https://csgo.99damage.de/de/matches&filter_team=13782&archiv_page=6',  # BIG
                'https://csgo.99damage.de/de/matches&filter_team=13782&archiv_page=7',  # BIG
                'https://csgo.99damage.de/de/matches&filter_team=13782&archiv_page=8',  # BIG
                'https://csgo.99damage.de/de/matches&filter_team=13782&archiv_page=9',  # BIG
                'https://csgo.99damage.de/de/matches&filter_team=22961&archiv_page=2',  # BIG. OMEN Academy
                'https://csgo.99damage.de/de/matches&filter_team=22961&archiv_page=3',  # BIG. OMEN Academy
                'https://csgo.99damage.de/de/matches&filter_team=22961&archiv_page=4',  # BIG. OMEN Academy
                'https://csgo.99damage.de/de/matches&filter_team=22961&archiv_page=5',  # BIG. OMEN Academy
            ]
        for dmg_url in dmg_urls:
            response = requests.get(dmg_url)
            soup = BeautifulSoup(response.text, "html.parser")
            links = soup.select('#content')[0].select('a.no')
            if limit_subpages:
                links = links[:limit_subpages]

            for link in links:
                spans = link.select('span')
                if len(spans) == 4:
                    date, team_left, score, team_right = spans
                    date = dateutil.parser.parse(date.text.strip(), dayfirst=True)
                    team_left = team_left.text.strip()
                    score_left, score_right = 0, 0
                    score = score.text.strip()
                    if score and ':' in score and 'h' not in score:
                        score_left, score_right = score.split(":")
                        score_left, score_right = int(score_left), int(score_right)
                    team_right = team_right.text.strip()

                    swap_team_and_score = False
                    if team_left not in map_to_left:
                        swap_team_and_score = True
                        team_left, team_right = team_right, team_left

                    matches_url = link.attrs.get('href').strip()
                    # print(" - Crawling URL...", matches_url)
                    sub_response = requests.get(matches_url)
                    sub_soup = BeautifulSoup(sub_response.text, "html.parser")
                    m_datetime = sub_soup.select('#content')[0].select('div.match_head')[0].select('div.right')[0]
                    m_datetime = dateutil.parser.parse(m_datetime.text.strip(), dayfirst=True)

                    m_tournament = sub_soup.select('#content')[0].select('div.match_head')[0].select('div.left')[0].text.strip()
                    # remove part behind " - ", " - Spieltag 1", " - Halbfinale", ...
                    m_tournament = m_tournament.split(" - ")[0]

                    overtime_counter = 0
                    sub_matchesmaps = sub_soup.select('#content')[0].select('div.match_subs')[0].select('div.map')
                    # print("Found .map", len(sub_matchesmaps))
                    map_indexes = []
                    map_index_cnt = 0
                    for s_map in sub_matchesmaps:
                        # print(s_map.attrs.get('title'))
                        if 'Overtime' in s_map.attrs.get('title'):
                            overtime_counter += 1
                        else:
                            map_indexes.append(map_index_cnt)
                        map_index_cnt += 1
                    map_cnt = len(map_indexes)

                    # Get or Create Tournament
                    tournament = apps.get_model('csgomatches.Tournament').objects.filter(
                        Q(name=m_tournament) | Q(name_alt=m_tournament) | Q(name_hltv=m_tournament) | Q(name_99dmg=m_tournament)
                    ).first()
                    if not tournament:
                        tournament = apps.get_model('csgomatches.Tournament')(
                            name=m_tournament,
                            name_99dmg=m_tournament
                        )
                        tournament.save()

                    if not tournament.name_99dmg:
                        tournament.name_99dmg = m_tournament
                        tournament.save()

                    # Get or Create Lineups
                    team_logos = []
                    team_logos_div = sub_soup.select('#content')[0].select('div.team_logo')
                    for team_logo_div in team_logos_div:
                        logo_url = team_logo_div.select('img')[0].attrs.get('src').strip()
                        team_logos.append(logo_url)
                    if swap_team_and_score:
                        team_logos.reverse()

                    lineup_a = apps.get_model('csgomatches.Lineup').objects.filter(
                        Q(team__name=team_left) | Q(team__name_long=team_left)
                    ).first()
                    lineup_b = apps.get_model('csgomatches.Lineup').objects.filter(
                        Q(team__name=team_right) | Q(team__name_long=team_right)
                    ).first()

                    if not lineup_b:
                        team_b = apps.get_model('csgomatches.Team').objects.filter(name=team_right).first()
                        if not team_b:
                            team_b = apps.get_model('csgomatches.Team')(name=team_right)
                            team_b.save()
                        lineup_b = apps.get_model('csgomatches.Lineup')(team=team_b, active_from=timezone.now(), team_logo_url=team_logos[1])
                        lineup_b.save()

                    match = apps.get_model('csgomatches.Match').objects.filter(
                        tournament=tournament,
                        lineup_a=lineup_a,
                        lineup_b=lineup_b,
                    ).first()

                    # Get or create Match
                    if not match:
                        bestof = 3
                        if 'Liga' in m_tournament:
                            bestof = 2
                        if 'Relegation' in m_tournament:
                            bestof = 3
                        if 'Sommermeisterschaft' in m_tournament:
                            bestof = 3

                        match = apps.get_model('csgomatches.Match')(
                            tournament=tournament,
                            lineup_a=lineup_a,
                            lineup_b=lineup_b,
                            bestof=bestof
                        )
                        match.save()

                    # Prepoulate Maps

                    for i in range(map_cnt):
                        i_without_overtime = map_indexes[i]
                        # print(map_cnt, overtime_counter, i, i_without_overtime)
                        sum_divs = sub_soup.select('#content')[0].select('div.match_subs')[0].select('div.sum')
                        if sum_divs:
                            map_score = sum_divs[i].text.strip()
                        else:
                            map_score = score

                        mapinfos = {
                            'name': sub_soup.select('#content')[0].select('div.match_subs')[0].select('div.map')[i_without_overtime].attrs.get('title'),
                            'score': map_score
                        }
                        if map_score and ':' in map_score and 'h' not in map_score:
                            score_left, score_right = map_score.split(":")
                            score_left, score_right = int(score_left), int(score_right)
                            if swap_team_and_score:
                                score_left, score_right = score_right, score_left
                        print(m_tournament, team_left, team_right, score_left, score_right, date, "sub=", m_datetime, mapinfos)

                        # get or create Maps
                        if 'de_tba' in mapinfos.get('name'):
                            played_map = None
                        else:
                            played_map, played_map_created = apps.get_model('csgomatches.Map').objects.get_or_create(
                                cs_name=mapinfos.get('name'),
                                defaults={
                                    'name': mapinfos.get('name')
                                }
                            )

                        matchmap = apps.get_model('csgomatches.MatchMap').objects.filter(
                            match=match,
                            map_nr=i_without_overtime + 1
                        ).first()

                        if matchmap:
                            if score_left > matchmap.rounds_won_team_a or score_right > matchmap.rounds_won_team_b:
                                matchmap.played_map = played_map
                                matchmap.rounds_won_team_a = score_left
                                matchmap.rounds_won_team_b = score_right
                                matchmap.save()

                        if not matchmap:
                            matchmap = apps.get_model('csgomatches.MatchMap')(
                                match=match,
                                map_nr=i_without_overtime + 1,
                                played_map=played_map,
                                rounds_won_team_a=score_left,
                                rounds_won_team_b=score_right,
                                starting_at=m_datetime + timezone.timedelta(hours=i_without_overtime),

                            )
                            matchmap.save()
