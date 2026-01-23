import socketio
import json
import time
from json.decoder import JSONDecodeError
from random_user_agent.user_agent import UserAgent


def get_match_score(hltv_match_id):
    with socketio.SimpleClient() as sio:
        ua = 'Mozilla/5.0 (Windows; U; Windows NT 6.0; pl; rv:1.9.2) Gecko/20100115 Firefox/3.6'
        headers = {
            #'User-Agent': UserAgent().get_random_user_agent(),
            'User-Agent': ua,
        }
        sio.connect('https://scorebot-lb.hltv.org', headers=headers, transports="websocket")
        print(f"Connection infos: sid={sio.sid}, transport={sio.transport}, user_agent={ua}")

        sio.emit("readyForScores", data=json.dumps({"token": "", "listIds": [m]}))

        while True:
            event = sio.receive(timeout=20)
            event_name, event_data = event
            print(f"event_name={event_name}")
            #print(f'received event: "{event[0]}" with arguments {event[1:]}')
            time.sleep(30)

        """
        try:
            sio.emit("readyForScores", data=json.dumps({"token": "", "listIds": [m]}))
        except JSONDecodeError:
            print("JSON-Error received in readyForScores")

        try:
            event = sio.receive(timeout=20)
            print(f'received event: "{event[0]}" with arguments {event[1:]}')
        except JSONDecodeError:
            print("JSON-Error received in event")
        """
    



django_matches = [2389587]
for m in django_matches:
    get_match_score(hltv_match_id=m)