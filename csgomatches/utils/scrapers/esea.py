import requests
from bs4 import BeautifulSoup
import cfscrape
import threading
import time
from django.apps import apps

def get_bracket_match(bracket_id, match_id, update_id=None, reverse_score=False):
    esea_bracket_url = 'https://play.esea.net/index.php?s=events&d=brackets&id={}'.format(bracket_id)
    scraper = cfscrape.CloudflareScraper()
    response = scraper.get(esea_bracket_url)
    print("Got page from", esea_bracket_url, response.status_code)
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

        print(team_a, score_a, " - ",team_b, score_b)
    except IndexError:
        return


    if update_id:
        match = apps.get_model('csgomatches.Match').objects.filter(id=update_id).first()
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


def as_thread(bracket_id, match_id, update_id=None, reverse_score=False):
    while True:
        threading._start_new_thread(get_bracket_match, (bracket_id, match_id, update_id, reverse_score))
        time.sleep(20)


##get_bracket_match(bracket_id=532, match_id=33523)

#as_thread(532, 33579, 1177, True)