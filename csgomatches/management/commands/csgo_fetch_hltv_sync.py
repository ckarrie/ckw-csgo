import socketio
from socketio import SimpleClient, Client
import json
import time
from json.decoder import JSONDecodeError
from random_user_agent.user_agent import UserAgent


DEBUG = False
RUN_ONCE = False
django_matches = [2389194]


class HLTVClient(Client):    
    def _handle_eio_message(self, data):
        if DEBUG:
            print(f"HLTVSocketClient received data: {data}")
        try:
            return super()._handle_eio_message(data)
        except JSONDecodeError:
            if DEBUG:
                print("JSON-Error received in _handle_eio_message")
            else:
                pass


class HLTVSimpleClient(SimpleClient):
    """A simple Socket.IO client for HLTV scorebot server with custom client class."""
    client_class = HLTVClient
    


def get_match_score(hltv_match_id):
    with HLTVSimpleClient() as sio:
        ua = 'Mozilla/5.0 (Windows; U; Windows NT 6.0; pl; rv:1.9.2) Gecko/20100115 Firefox/3.6'
        headers = {
            #'User-Agent': UserAgent().get_random_user_agent(),
            'User-Agent': ua,
        }
        sio.connect('https://scorebot-lb.hltv.org', headers=headers, transports="websocket")
        print(f"Connection infos: sid={sio.sid}, transport={sio.transport}, user_agent={ua}")

        #sio.emit("readyForMatch", data=json.dumps({"listIds": [hltv_match_id]}))
        sio.emit("readyForScores", data=json.dumps({"token": "", "listIds": [hltv_match_id]}))

        run_counter = 0
        
        while True:
            print(f"--- Listening for events for match {hltv_match_id}, run #{run_counter} ---")
            run_counter += 1
            try:
                event_name, event_data = sio.receive(timeout=5)    
                if DEBUG:
                    print(f"event_name={event_name}")
                    print(f'received event: "{event_name}" with arguments {event_data}')
                if event_name == 'score':
                    mapscore_data = event_data.get('mapScores', {})
                    map_ids = mapscore_data.keys()
                    for map_id in map_ids:
                        score_team_a = mapscore_data.get(map_id, {}).get('firstHalf', {}).get('ctScore', 0) + mapscore_data.get(map_id, {}).get('secondHalf', {}).get('tScore', 0)
                        score_team_b = mapscore_data.get(map_id, {}).get('firstHalf', {}).get('tScore', 0) + mapscore_data.get(map_id, {}).get('secondHalf', {}).get('ctScore', 0)
                        map_name = mapscore_data.get(map_id, {}).get('map', 'unknown')
                        print(f"Match {hltv_match_id} - Map: {map_id} ({map_name}), Score: Team A {score_team_a} - Team B {score_team_b}")
                if RUN_ONCE:
                    break  # exit after processing one event for demo purposes

            except socketio.exceptions.TimeoutError:
                time.sleep(10)  # avoid busy loop
            except KeyboardInterrupt:
                print("Interrupted by user")
                break
            except socketio.exceptions.DisconnectedError:
                print("Disconnected, exiting")
                break



for m in django_matches:
    get_match_score(hltv_match_id=m)