import asyncio
import websockets
import json
import requests
from bs4 import BeautifulSoup

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


DEBUGGING = False
if DEBUGGING:
    import logging
    logger = logging.getLogger('websockets')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())

async def get_hlvt_score(match_id: int = 2338003):
    uri = "wss://scorebot-secure.hltv.org/socket.io/?EIO=3&transport=websocket"
    #ws_data = ["readyForMatch", {'token': "", 'listID': "2338003"}]
    #ws_data2 = ["readyForMatch", {'token': "", 'listIds': [2338003]}]
    #ws_str = '61:42["readyForMatch","{\"token\":\"\",\"listId\":\"2338003\"}"]'
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