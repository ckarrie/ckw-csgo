import requests
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup
import cfscrape
import threading
import time
from django.apps import apps
from django.core.exceptions import AppRegistryNotReady

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
    url = "http://0.0.0.0:8002/api/matchmap_update/{}/".format(matchmap)
    username = None
    password = None
    with open('push_credentials.txt', 'r') as cred_file:
        s = cred_file.read()
        username, password = s.split(",")
    resp = requests.put(
        url,
        json={
            'rounds_won_team_a': a,
            'rounds_won_team_b': b,
        },
        auth=HTTPBasicAuth(username, password)
    )
    if resp.status_code == 200:
        print(" - posted to", url)
    else:
        print("Error:", resp.content)


def as_thread(bracket_id, match_id, update_id=None):
    while run_thread:
        threading._start_new_thread(get_bracket_match, (bracket_id, match_id, update_id))
        time.sleep(600)


##get_bracket_match(bracket_id=532, match_id=33523)

#as_thread(
#    bracket_id=533,     # ESEA Bracket ID (siehe Link)
#    match_id=None,          # ESEA Match ID (via Chrome DevTools)
#    update_id=None,  # wsb.de pk of Matchmap (https://wannspieltbig.de/admin/csgomatches/matchmap/)
#)

publish_results(2421,2,3)