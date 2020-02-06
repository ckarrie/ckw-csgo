import asyncio
from json import JSONDecodeError

import dateutil.parser
import requests
from bs4 import BeautifulSoup
from django.apps import apps
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from csgomatches.utils.scrapers.hltv import convert_to_score, get_hlvt_score

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

        parser.add_argument(
            '--esea',
            action='store_true',
            dest='esea',
            default=False,
            help='Use esea',
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

        if options['dmg99']:
            self.crawl_99damage_de(include_archive_pages=options['include_archive_pages'], fake=fake)

        if options['y0fl0w']:
            self.crawl_y0fl0w_de(include_archive_pages=True, fake=fake)

        if options['esea']:
            self.crawl_esea()

    def crawl_y0fl0w_de(self, include_archive_pages=True, fake=False):
        map_to_left = ['BIG', 'BIG Academy', 'BIG.A']
        json_urls = ['https://big.y0fl0w.de', ]
        if include_archive_pages:
            json_urls += [
                'https://big.y0fl0w.de/?finished=true'
            ]

        for y_url in json_urls:
            try:
                response = requests.get(y_url)
                response_json = response.json()
            except JSONDecodeError as json_error:
                print("[crawl_y0fl0w_de] ERROR reading {}, content={}".format(y_url, str(json_error)))
                continue
                # raise json_error

            for event_data in response_json:
                event_name = event_data.get('event')
                event_matches = event_data.get('matches', [])
                if ' - ' in event_name:
                    event_name = event_name.split(' - ')[0]
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
                    match_id = match_data.get('hltvMatchID')
                    if len(match_data.get('time')) >= 13 and match_data.get('time').isdigit():
                        first_match_timestamp = int(match_data.get('time')[:10])
                        first_match_start = timezone.datetime.fromtimestamp(first_match_timestamp)
                    else:
                        first_match_start = dateutil.parser.parse(match_data.get('time'), dayfirst=True)
                    aware_first_match_start = timezone.make_aware(first_match_start)

                    lineup_a = apps.get_model('csgomatches.Lineup').objects. \
                        search_lineups(name=match_data.get('t1'), hltv_id=match_data.get('t1_hltvID')). \
                        active_lineups(ref_dt=aware_first_match_start). \
                        first()

                    lineup_b = apps.get_model('csgomatches.Lineup').objects. \
                        search_lineups(name=match_data.get('t2'), hltv_id=match_data.get('t2_hltvID')). \
                        active_lineups(ref_dt=aware_first_match_start). \
                        first()

                    # lineup_b_qs1 = apps.get_model('csgomatches.Lineup').objects.search_lineups(name=match_data.get('t2'), hltv_id=match_data.get('t2_hltvID'))
                    # print("lineup_b_qs1", lineup_b_qs1)
                    # lineup_b_qs2 = lineup_b_qs1.active_lineups(ref_dt=aware_first_match_start)
                    # print("lineup_b_qs2", lineup_b_qs2)

                    #print("LINEUP A/B", lineup_a, lineup_b, aware_first_match_start)
                    #print('LINEUP A="{}" orig_value="{}" hltv_id="{}"'.format(str(lineup_a), match_data.get('t1'), match_data.get('t1_hltvID')))
                    #print('LINEUP B="{}" orig_value="{}" hltv_id="{}"'.format(str(lineup_b), match_data.get('t2'), match_data.get('t2_hltvID')))

                    if not lineup_a:
                        team_lineup_a = apps.get_model('csgomatches.Team')(name=match_data.get('t1'))
                        team_lineup_a.save()
                        lineup_a = apps.get_model('csgomatches.Lineup')(team=team_lineup_a, active_from=timezone.now())
                        lineup_a.save()

                    if lineup_a and match_data.get('t1_hltvID') and not lineup_a.team_logo_url:
                        lineup_a.team_logo_url = 'https://static.hltv.org/images/team/logo/' + match_data.get('t1_hltvID')
                        lineup_a.save()

                    if lineup_a and match_data.get('t1_hltvID') and not lineup_a.team.hltv_id:
                        lineup_a.team.hltv_id = int(match_data.get('t1_hltvID'))
                        lineup_a.team.save()

                    if not lineup_b:
                        team_lineup_b = apps.get_model('csgomatches.Team')(name=match_data.get('t2'))
                        team_lineup_b.save()
                        lineup_b = apps.get_model('csgomatches.Lineup')(team=team_lineup_b, active_from=timezone.now())
                        lineup_b.save()

                    if lineup_b and match_data.get('t2_hltvID') and not lineup_b.team_logo_url:
                        lineup_b.team_logo_url = 'https://static.hltv.org/images/team/logo/' + match_data.get('t2_hltvID')
                        lineup_b.save()

                    if lineup_b and match_data.get('t2_hltvID') and not lineup_b.team.hltv_id:
                        lineup_b.team.hltv_id = int(match_data.get('t2_hltvID'))
                        lineup_b.team.save()

                    swap_team_and_score = False
                    if match_data.get('t1') not in map_to_left:
                        swap_team_and_score = True
                        lineup_a, lineup_b = lineup_b, lineup_a

                    print("[crawl_y0fl0w_de] Current Match:", lineup_a, "vs", lineup_b, "@", tournament, aware_first_match_start)

                    bestof = 3
                    if "1" in match_data.get('mType', ''):
                        bestof = 1
                    elif "2" in match_data.get('mType', ''):
                        bestof = 2
                    elif "3" in match_data.get('mType', ''):
                        bestof = 3
                    elif "5" in match_data.get('mType', ''):
                        bestof = 5

                    if match_id:
                        match = apps.get_model('csgomatches.Match').objects.filter(
                            hltv_match_id=match_id
                        ).first()

                    else:
                        match = apps.get_model('csgomatches.Match').objects.filter(
                            tournament=tournament,
                            lineup_a=lineup_a,
                            lineup_b=lineup_b,
                            hltv_match_id=match_id
                        ).order_by('-first_map_at').first()

                    if not match:
                        match = apps.get_model('csgomatches.Match')(
                            tournament=tournament,
                            lineup_a=lineup_a,
                            lineup_b=lineup_b,
                            bestof=bestof,
                            hltv_match_id=match_id
                        )
                        match.save()

                    if match.enable_hltv:

                        # existing_matchmaps = apps.get_model('csgomatches.MatchMap').objects.filter(
                        #    match=match
                        # )

                        maps_data = match_data.get('maps', [])

                        # if existing_matchmaps.count() != len(maps_data):

                        # https://www.hltv.org/matches/2337711/match <- added match, strange hltv behaviour

                        hltv_livescore_data = None
                        if match_id:
                            hltv_url = 'https://www.hltv.org/matches/{}/match'.format(match_id)
                            apps.get_model('csgomatches.ExternalLink').objects.get_or_create(
                                url=hltv_url,
                                match=match,
                                link_type='hltv_match',
                                defaults={
                                    'title': str(match),
                                }
                            )

                            if not match.hltv_match_id:
                                match.hltv_match_id = match_id
                                match.save()

                            # if match.is_live():
                            hltv_livescore_data = asyncio.get_event_loop().run_until_complete(get_hlvt_score(int(match.hltv_match_id)))

                        vods_data = match_data.get('vods', {})
                        if isinstance(vods_data, dict):
                            for vod_lang, vod_url in vods_data.items():
                                link_type = 'twitch_vod'
                                vod_title = str(match)
                                mlang = ''
                                if '_m' in vod_lang and 'https://twitch.tv/videos/' in vod_url:
                                    link_type = 'twitch_vod'
                                    mlang, mnr = vod_lang.split('_')
                                    vod_title = 'VOD #{} ({})'.format(mnr, mlang)
                                    if '/videos/v' in vod_url:
                                        vod_url = vod_url.replace('/videos/v', '/videos/')
                                if '_m' in vod_lang and 'youtube' in vod_url:
                                    link_type = 'youtube_vod'
                                    mlang, mnr = vod_lang.split('_')
                                    vod_title = 'VOD #{} ({})'.format(mnr, mlang)
                                if vod_lang == 'demo':
                                    link_type = 'hltv_demo'
                                    mlang = 'eu'

                                apps.get_model('csgomatches.ExternalLink').objects.get_or_create(
                                    url=vod_url,
                                    match=match,
                                    link_type=link_type,
                                    defaults={
                                        'title': vod_title,
                                        'link_flag': mlang
                                    }
                                )

                        streams_data = match_data.get('streams', {})
                        if isinstance(vods_data, dict):
                            for steam_lang, stream_url in streams_data.items():
                                link_type = 'twitch_cast'

                                apps.get_model('csgomatches.ExternalLink').objects.get_or_create(
                                    url=stream_url,
                                    match=match,
                                    link_type=link_type,
                                    defaults={
                                        'title': str(match),
                                        'link_flag': steam_lang
                                    }
                                )

                        for i, map_data in enumerate(maps_data):
                            results = map_data.get('result')
                            livescore_results = None
                            map_pick_team_text = map_data.get('pick')
                            starting_at = aware_first_match_start + timezone.timedelta(hours=i)
                            if map_pick_team_text:
                                map_pick_lineup = apps.get_model('csgomatches.Lineup').objects.filter(id__in=[lineup_a.id, lineup_b.id]).search_lineups(name=map_pick_team_text).active_lineups(ref_dt=starting_at).first()
                            else:
                                map_pick_lineup = None

                            if i >= 2 and starting_at < timezone.now() and results == '-':
                                unplayed_matchmaps = apps.get_model('csgomatches.MatchMap').objects.filter(
                                    match=match,
                                    map_nr__gte=3,
                                    rounds_won_team_a=0,
                                    rounds_won_team_b=0,
                                    starting_at__lt=timezone.now()
                                )
                                if unplayed_matchmaps.exists():
                                    print("[crawl_y0fl0w_de] deleted unplayed Matchmap map_data=", map_data, "unplayed_matchmaps.pk=", unplayed_matchmaps.values_list('pk', flat=True))
                                    unplayed_matchmaps.delete()

                            else:
                                matchmap, matchmap_created = apps.get_model('csgomatches.MatchMap').objects.get_or_create(
                                    match=match,
                                    map_nr=i + 1,
                                    defaults={
                                        'starting_at': starting_at,
                                    }
                                )
                                name = map_data.get('name')

                                if matchmap_created:
                                    print("[crawl_y0fl0w_de] + created Matchmap map_data=", map_data, "matchmap.pk=", matchmap.pk, 'map_nr=', str(i + 1))

                                livescore = convert_to_score(hltv_livescore_data, map_nr=i + 1)
                                if livescore:
                                    livescore_by_team = {}

                                    for team_id, team_score in livescore.items():
                                        team = apps.get_model('csgomatches.Team').objects.filter(hltv_id=int(team_id)).first()
                                        if team:
                                            livescore_by_team[team] = team_score

                                    if len(livescore_by_team) == 2:
                                        print("[crawl_y0fl0w_de]  - livescore_by_team", livescore_by_team)
                                        t1_score = livescore_by_team[match.lineup_a.team]
                                        t2_score = livescore_by_team[match.lineup_b.team]
                                        if swap_team_and_score:
                                            # convert to 'incorrent' - will be later returned if swap_team_and_score is True
                                            t1_score, t2_score = t2_score, t1_score

                                        if results:
                                            print("[crawl_y0fl0w_de]  - Results by y0fl0w-API", results)

                                        # Overwriting results
                                        results = "{}:{}".format(t1_score, t2_score)
                                        print("[crawl_y0fl0w_de]  - Results by WebSocket livescore", results)


                                if results and ':' in results:
                                    t1_res, t2_res = results.split(":")
                                    try:
                                        t1_res, t2_res = int(t1_res), int(t2_res)
                                    except ValueError:
                                        t1_res, t2_res = 0, 0

                                    if swap_team_and_score:
                                        t1_res, t2_res = t2_res, t1_res

                                    if t1_res > matchmap.rounds_won_team_a or t2_res > matchmap.rounds_won_team_b:
                                        matchmap.rounds_won_team_a = t1_res
                                        matchmap.rounds_won_team_b = t2_res
                                        matchmap.save()

                                if name and 'TBA' not in name:
                                    # set map
                                    cs_name = HLTV_MAP_NAMES_TO_CS_NAME.get(name, 'de_' + name.lower())
                                    # not found in HLTV_MAP_NAMES_TO_CS_NAME
                                    played_map, played_map_created = apps.get_model('csgomatches.Map').objects.get_or_create(
                                        cs_name=cs_name,
                                        defaults={
                                            'name': name
                                        }
                                    )
                                    print("[crawl_y0fl0w_de]  - Setting Map name", name, match)
                                    matchmap.played_map = played_map
                                    matchmap.save()

                                if map_pick_lineup and matchmap.map_pick_of is None:
                                    matchmap.map_pick_of = map_pick_lineup
                                    matchmap.save()

    def crawl_99damage_de(self, include_archive_pages=False, fake=False):
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

                    lineup_a = apps.get_model('csgomatches.Lineup').objects.search_lineups(name=team_left).active_lineups(ref_dt=m_datetime).first()
                    lineup_b = apps.get_model('csgomatches.Lineup').objects.search_lineups(name=team_right).active_lineups(ref_dt=m_datetime).first()

                    if not lineup_b:
                        team_b = apps.get_model('csgomatches.Team').objects.search_team(name=team_right)
                        if not team_b:
                            print("[crawl_99damage_de] + Team created:", team_b)
                            team_b = apps.get_model('csgomatches.Team')(name=team_right)
                            team_b.save()
                        lineup_b = apps.get_model('csgomatches.Lineup')(team=team_b, active_from=timezone.now(), team_logo_url=team_logos[1])
                        lineup_b.save()
                        print('[crawl_99damage_de] + Lineup created: "{}"'.format(str(lineup_b)))

                    match = apps.get_model('csgomatches.Match').objects.filter(
                        tournament=tournament,
                        lineup_a=lineup_a,
                        lineup_b=lineup_b,
                    ).order_by('-first_map_at').first()

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
                        print("[crawl_99damage_de] + created new Match", match)

                    if match.enable_99dmg:

                        # Match Link
                        apps.get_model('csgomatches.ExternalLink').objects.get_or_create(
                            url=matches_url,
                            match=match,
                            link_type='99dmg_match',
                            defaults={
                                'title': str(match),
                                'link_flag': 'de'
                            }
                        )

                        print("[crawl_99damage_de] Match ", match, " map_cnt=", map_cnt, " map_indexes=", map_indexes, sep='')
                        existing_matchmaps = apps.get_model('csgomatches.MatchMap').objects.filter(
                            match=match,
                        )
                        print("[crawl_99damage_de]  - existing MatchMaps (before)", existing_matchmaps)

                        # Prepoulate Maps

                        for i in range(map_cnt):
                            map_nr = i + 1
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
                            print("[crawl_99damage_de]  - Matchmap data", m_tournament, team_left, team_right, score_left, score_right, date, "sub=", m_datetime, mapinfos)

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
                                map_nr=map_nr
                            ).first()
                            if matchmap:
                                print("[crawl_99damage_de]    - found Matchmap #", matchmap.map_nr, matchmap, sep='')

                            if matchmap:
                                if score_left > matchmap.rounds_won_team_a or score_right > matchmap.rounds_won_team_b or played_map != matchmap.played_map:
                                    matchmap.played_map = played_map
                                    matchmap.rounds_won_team_a = score_left
                                    matchmap.rounds_won_team_b = score_right
                                    matchmap.save()

                            if not matchmap:
                                matchmap = apps.get_model('csgomatches.MatchMap')(
                                    match=match,
                                    map_nr=map_nr,
                                    played_map=played_map,
                                    rounds_won_team_a=score_left,
                                    rounds_won_team_b=score_right,
                                    starting_at=m_datetime + timezone.timedelta(hours=map_nr),

                                )
                                matchmap.save()
                                print("[crawl_99damage_de]  + created Matchmap mapinfos=", mapinfos, " matchmap.pk=", matchmap.pk, ' map_nr=', str(map_nr), sep='')

                        existing_matchmaps = apps.get_model('csgomatches.MatchMap').objects.filter(
                            match=match,
                        )
                        print("[crawl_99damage_de]  - existing MatchMaps (after)", existing_matchmaps, existing_matchmaps.count(), map_cnt, "bo=", match.bestof)
                        if existing_matchmaps.count() > map_cnt >= 2 and match.bestof == 3:
                            if match.first_map_at < timezone.now():
                                unplayed_matchmaps = apps.get_model('csgomatches.MatchMap').objects.filter(
                                    match=match,
                                    map_nr__gte=3,
                                    # rounds_won_team_a=0,
                                    # rounds_won_team_b=0,
                                    starting_at__lt=timezone.now()
                                )
                                if unplayed_matchmaps.exists():
                                    for unplayed_mm in unplayed_matchmaps:
                                        print("[crawl_99damage_de]  - deleted unplayed Matchmap map_nr=", unplayed_mm.map_nr)
                                        unplayed_mm.delete()

    def crawl_esea(self):
        from csgomatches.utils.scrapers.esea import get_esea_team_schedule
        get_esea_team_schedule()
