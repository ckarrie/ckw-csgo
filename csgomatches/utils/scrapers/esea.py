import requests
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup
import cfscrape
import threading
import time
from django.apps import apps
from django.core.exceptions import AppRegistryNotReady
import dateutil.parser
from django.utils import timezone

DEBUG = False

"""
Run this local, not on a hosted server

Usage: 

/home/christian/workspace/venvs/wannbigspielt/bin/python /home/christian/workspace/src/github/ckw-csgo/csgomatches/utils/scrapers/esea.py
"""

run_thread = True


def get_bracket_match(bracket_id, match_id, update_id=None):
    MAP_LEFT_TEAMS = ['BIGCLAN']
    swap_score = False
    esea_bracket_url = 'https://play.esea.net/index.php?s=events&d=brackets&id={}'.format(bracket_id)
    scraper = cfscrape.CloudflareScraper()
    response = scraper.get(
        esea_bracket_url,
        headers={'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.70 Safari/537.36'}
    )
    print("Got page from", esea_bracket_url, response.status_code)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        match_div = soup.find('div', {'id': 'match-modal-{}'.format(match_id)})
        map_name = match_div.find("table", {'class': 'match-meta'}).select("td")[1].text
        print("Map", map_name)
        scores_table = match_div.find("table", {'class': 'scores'})
        try:
            team_a = scores_table.select("td")[0].text
            score_a = scores_table.select("td")[1].text
            team_b = scores_table.select("td")[2].text
            score_b = scores_table.select("td")[3].text
        except IndexError:
            return

        if team_b in MAP_LEFT_TEAMS:
            swap_score = True

        score_a = int(score_a)
        score_b = int(score_b)
        """
        if score_a == 16 or score_b == 16:
            if abs(score_a - score_b) >= 2:
                # match finished
                run_thread = False
        if score_a > 15 and score_b > 15:
            if abs(score_a - score_b) >= 2:
                run_thread = False
        """
        if swap_score:
            team_a, team_b = team_b, team_a
            score_a, score_b = score_b, score_a

        print(team_a, score_a, " - ", team_b, score_b)

        if update_id:
            publish_results(matchmap=update_id, a=score_a, b=score_b, map_name=map_name)
            """
            try:
                match = apps.get_model('csgomatches.Match').objects.filter(id=update_id).first()
            except AppRegistryNotReady:
                return
            if match:
                map_1 = match.matchmap_set.filter(map_nr=1).first()
                if map_1:
                    if reverse_score:
                        map_1.rounds_won_team_a = int(score_b)
                        map_1.rounds_won_team_b = int(score_a)
                    else:
                        map_1.rounds_won_team_a = int(score_a)
                        map_1.rounds_won_team_b = int(score_b)

                    map_1.save()
            else:
                print("Match not found")
            """


def publish_results(matchmap, a, b, map_nr=1, map_name=""):
    url = "https://wannspieltbig.de/api/matchmap_update/{}/".format(matchmap)
    username = None
    password = None
    with open('push_credentials.txt', 'r') as cred_file:
        s = cred_file.read()
        username, password = s.split(",")
    json = {
        'rounds_won_team_a': a,
        'rounds_won_team_b': b,
    }
    resp = requests.put(
        url,
        json=json,
        auth=HTTPBasicAuth(username, password)
    )
    if resp.status_code == 200:
        print(" - posted to", url, json)
    else:
        print("Error:", resp.content)


def as_thread(bracket_id, match_id, update_id=None):
    while run_thread:
        threading._start_new_thread(get_bracket_match, (bracket_id, match_id, update_id))
        time.sleep(120)   #120 = default


##get_bracket_match(bracket_id=532, match_id=33523)

#as_thread(
#    bracket_id=575,  # ESEA Bracket ID (siehe Link)
#    match_id=35760,  # ESEA Match ID (via Chrome DevTools)
#    update_id=6508,  # wsb.de pk of Matchmap (https://wannspieltbig.de/admin/csgomatches/matchmap/)
#)

# publish_results(2421,2,3)

def get_esea_team_schedule(team_id=8749575):
    MAP_LEFT_TEAMS = ['BIGCLAN', 'BIG OMEN Academy']
    TEAM_ID_TOURNAMENT_MAPPING = {
        8749575: 487  # BIG OMEN Academy : ESEA CS:GO Open EU
    }
    TEAM_A_MAPPINGS = {
        # Academy:
        # ESEA Team ID, WSB _Team_ ID
        8749575: 3,

        # Main
        0000000: 1
    }

    api_url = 'https://play.esea.net/api/teams/{}/matches?page_size=50'.format(team_id)
    scraper = cfscrape.CloudflareScraper()
    print("ESEA", api_url)
    response = scraper.get(api_url)
    if response.status_code == 200:
        response_json = response.json()
        matches_data = response_json.get('data', [])
        for match_data in matches_data:
            swap_teams = False
            match_id = match_data.get('id')
            home_data = match_data.get('home', {})
            away_data = match_data.get('away', {})
            match_datetime = match_data.get('date', {})
            match_datetime = dateutil.parser.parse(match_datetime, dayfirst=False)
            score_text = match_data.get('score')
            map_name = match_data.get('map')
            if not score_text:
                score_text = "0-0"

            team_a_score, team_b_score = [int(x) for x in score_text.split('-')]

            if away_data.get('name') in MAP_LEFT_TEAMS:
                swap_teams = True

            if swap_teams:
                home_data, away_data = away_data, home_data
                team_a_score, team_b_score = team_b_score, team_a_score

            lineup_a = apps.get_model('csgomatches.Lineup').objects.filter(team__pk=TEAM_A_MAPPINGS.get(home_data.get('id')), is_active=True).first()

            print(match_id, home_data.get('name'), away_data.get('name'), team_a_score, team_b_score, match_datetime, match_data.get('date', {}))
            print(" - timezone.is_aware", timezone.is_aware(match_datetime))

            if not lineup_a:
                print("Could not find Team ID", TEAM_A_MAPPINGS.get(home_data.get('id')), home_data.get('name'))
                continue

            if match_id and match_datetime:
                match = apps.get_model('csgomatches.Match').objects.filter(esea_match_id=match_id).order_by('-first_map_at').first()
                if not match:

                    tournament = apps.get_model('csgomatches.Tournament').objects.filter(
                        pk=TEAM_ID_TOURNAMENT_MAPPING.get(home_data.get('id'))
                    ).first()

                    if not tournament:
                        t_name = 'Unknown ESEA Tournament'
                        tournament, tournament_created = apps.get_model('csgomatches.Tournament').objects.get_or_create(
                            name=t_name
                        )

                    lineup_b = apps.get_model('csgomatches.Lineup').objects.\
                        search_lineups(name=away_data.get('name')).\
                        active_lineups(ref_dt=match_datetime).\
                        first()
                    if not lineup_b:
                        team_b = apps.get_model('csgomatches.Team')(
                            name=away_data.get('name')
                        )
                        team_b.save()
                        lineup_b = apps.get_model('csgomatches.Lineup')(
                            team=team_b,
                            active_from=timezone.now() - timezone.timedelta(days=10)
                        )
                        lineup_b.save()
                    match = apps.get_model('csgomatches.Match')(
                        tournament=tournament,
                        lineup_a=lineup_a,
                        lineup_b=lineup_b,
                        bestof=1,
                        first_map_at=match_datetime,
                        esea_match_id=match_id,
                        enable_tweet=False
                    )
                    match.save()

                first_map_at_changed = False

                if match_datetime != match.first_map_at:
                    print(" - Different Match Datetime", match_datetime, match.first_map_at)
                    match.first_map_at = match_datetime
                    match.save()
                    first_map_at_changed = True

                map_pending_veto = map_name == 'Pending Veto'

                first_matchmap = match.get_first_matchmap()
                if not first_matchmap:
                    matchmap = apps.get_model('csgomatches.MatchMap')(
                        match=match,
                        starting_at=match.first_map_at,
                        map_nr=1
                    )
                    matchmap.save()
                    first_matchmap = matchmap

                if not map_pending_veto:
                    map_instance = apps.get_model('csgomatches.Map').objects.filter(
                        cs_name=map_name
                    ).first()
                    if team_a_score > first_matchmap.rounds_won_team_a or \
                        team_b_score > first_matchmap.rounds_won_team_b or \
                        first_map_at_changed or \
                        first_matchmap.played_map != map_instance:
                        first_matchmap.played_map = map_instance
                        first_matchmap.rounds_won_team_a = team_a_score
                        first_matchmap.rounds_won_team_b = team_b_score
                        first_matchmap.starting_at = match.first_map_at

                        first_matchmap.save()






def get_esea_match(match_id, update_id=None):
    MAP_LEFT_TEAMS = ['BIGCLAN', 'BIG OMEN Academy']
    swap_teams = False
    api_url = 'https://play.esea.net/api/match/{}'.format(match_id)
    scraper = cfscrape.CloudflareScraper()
    response = scraper.get(api_url)
    if response.status_code == 200:
        response_json = response.json()
        #print(response_json)
        data = response_json.get('data', {})
        started_at = data.get('started_at')
        map_name = data.get('map')
        team_1 = data.get('team_1', {})
        team_2 = data.get('team_2', {})
        if team_2.get('name') in MAP_LEFT_TEAMS:
            swap_teams = True

        if swap_teams:
            team_1, team_2 = team_2, team_1

        team_1_name = team_1.get('name')
        team_2_name = team_2.get('name')
        team_1_score = team_1.get('score')
        team_2_score = team_2.get('score')
        print("Match {} vs {}: {}:{} Map: {}".format(team_1_name, team_2_name, team_1_score, team_2_score, map_name))
