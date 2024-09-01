import asyncio
import json

import requests
import websockets
from bs4 import BeautifulSoup

from ... import models


def get_hltv_team_name_from_id(hltv_id: int):
    """
    Parsing title-tag

        <title>pro100 team overview | HLTV.org</title>

    :param hltv_id:
    :return:
    """
    url = 'https://www.hltv.org/team/{}/team'.format(hltv_id)
    response = requests.get(url=url)
    soup = BeautifulSoup(response.text, "html.parser")
    title_tag = soup.select('title')[0]
    team_name = title_tag.text.split('team overview')[0].strip()
    return team_name


def get_hltv_id_from_team_name(team_mdl: models.Team, return_team_json=False):
    db_names = []
    if team_mdl:
        db_names.append(team_mdl.name)
        if team_mdl.name_long:
            db_names.append(team_mdl.name_long)
        if team_mdl.name_alt:
            db_names.append(team_mdl.name_alt)
    db_names_lower = [n.lower() for n in db_names]
    for name in db_names:
        url = 'https://www.hltv.org/search?term={}'.format(name)
        response = requests.get(url=url)
        response_json = response.json()
        teams = response_json[0].get("teams")
        for team in teams:
            hltv_name = team['name']
            print("[get_hltv_id_from_team_name] checking if hltv_name={} in db_names={}".format(hltv_name, db_names))
            if hltv_name in db_names:
                if return_team_json:
                    return team
                return team['id']
            if hltv_name.lower() in db_names_lower:
                if return_team_json:
                    return team
                return team['id']


def build_players(team_mdl: models.Team):
    """
    Player-Dict:
    {
        'firstName': 'Semyon',
        'nickName': 'kinqie',
        'lastName': 'Lisitsyn',
        'flagUrl': 'https://static.hltv.org/images/bigflags/30x20/RU.gif',
        'location': '/player/3459/kinqie'
    }
    :param team_mdl:
    :return:
    """
    current_lineup = team_mdl.lineup_set.active_lineups().first()
    if team_mdl.hltv_id:
        team_dict = get_hltv_id_from_team_name(team_mdl=team_mdl, return_team_json=True)
        if not team_dict:
            return
        players = team_dict.get('players', [])

        if len(players) == 5:
            player_instances = []
            players_created = []
            for player_data in players:
                first_name = player_data.get('firstName')
                last_name = player_data.get('lastName')
                ingame_name = player_data.get('nickName')
                hltv_id_url = player_data.get('location')
                hltv_id = int(hltv_id_url.split("/")[2])
                player, player_created = models.Player.objects.get_or_create(
                    ingame_name=ingame_name,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'hltv_id': hltv_id
                    }
                )
                player_instances.append(player)
                if player_created:
                    players_created.append(player)

            print("player_instances", player_instances)
            print("players_created", players_created)

            player_instances_ids = [o.pk for o in player_instances]

            existing_lineup_players = current_lineup.lineupplayer_set.filter(
                player__id__in=player_instances_ids
            )
            print("existing_lineup_players", existing_lineup_players)
            if existing_lineup_players.count() == 0:
                for player in player_instances:
                    lu_player = models.LineupPlayer(
                        player=player,
                        lineup=current_lineup
                    )
                    lu_player.save()
            elif 0 < existing_lineup_players.count() < 5:
                print("Maybe create new Lineup now!!!")
                moved_out_lps = current_lineup.lineupplayer_set.exclude(
                    player__id__in=player_instances_ids
                )
                for mo_lp in moved_out_lps:
                    print(" - Player {} left the Lineup".format(mo_lp.player))
        else:
            print("Found {} Players for Team {}, ignoring".format(len(players), team))


DEBUGGING = True
if DEBUGGING:
    import logging

    logger = logging.getLogger('websockets')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())


async def get_hlvt_score(match_id: int = 2338003):
    uri = "wss://scorebot-secure.hltv.org/socket.io/?EIO=3&transport=websocket"
    # ws_data = ["readyForMatch", {'token': "", 'listID': "2338003"}]
    # ws_data2 = ["readyForMatch", {'token': "", 'listIds': [2338003]}]
    # ws_str = '61:42["readyForMatch","{\"token\":\"\",\"listId\":\"2338003\"}"]'
    ws_str2 = '61:42["readyForMatch","{\\"token\\":\\"\\",\\"listID\\":\\"' + str(match_id) + '"\\}"]'
    ws_str2 = '61:42["readyForScores","{\\"token\\":\\"\\",\\"listIds\\":[' + str(match_id) + ']}"]'
    results = {}
    async with websockets.connect(uri) as websocket:

        ret = await websocket.recv()
        if DEBUGGING:
            print(1, ret)
        ret = await websocket.recv()
        if DEBUGGING:
            print(2, ret)
        if DEBUGGING:
            print(4, "Sending ", ws_str2)
        s = await websocket.send(ws_str2)
        if DEBUGGING:
            print(5, "Send", s)
            print("Waiting for data")
        ret = await asyncio.wait_for(websocket.recv(), timeout=1)
        if ret.startswith("42["):
            ret = ret.replace("42[", "[")
            results = json.loads(ret)

    return results


def convert_to_score(json_result_list: list = [], map_nr: int = 1):
    try:
        return json_result_list[1]['mapScores'][str(map_nr)]['scores']
    except (IndexError, KeyError) as e:
        return None


def get_map_name(json_result_list: list = [], map_nr: int = 1):
    try:
        return json_result_list[1]['mapScores'][str(map_nr)]['map']
    except (IndexError, KeyError) as e:
        return None


if __name__ == '__main__':
    r = asyncio.get_event_loop().run_until_complete(get_hlvt_score(2337996))
    if not DEBUGGING:
        print("Map #1", convert_to_score(r, map_nr=1))
        print("Map #2", convert_to_score(r, map_nr=2))
        print("Map #3", convert_to_score(r, map_nr=3))
    else:
        print("HLTV-Score", r)
