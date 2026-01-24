import requests
import json
import time
import socketio
from socketio import SimpleClient, Client
import argparse

# Static variables
DEBUG = False
WSB_API_MATCHES_URL = "https://wannspieltbig.de/api/match_livescore/"
WSB_API_MATCHMAP_UPDATE_URL = "https://wannspieltbig.de/api/matchmap_update/"
HLTV_BIG_TEAMS_IDS = [
    7532, # BIG Main
    10254, # BIG Academy
    11718 # BIG Equipa
]

class HLTVClient(Client):    
    def _handle_eio_message(self, data):
        if DEBUG:
            print(f"HLTVSocketClient received data: {data}")
        try:
            return super()._handle_eio_message(data)
        except json.JSONDecodeError:
            if DEBUG:
                print("JSON-Error received in _handle_eio_message")
            else:
                pass


class HLTVSimpleClient(SimpleClient):
    """A simple Socket.IO client for HLTV scorebot server with custom client class."""
    client_class = HLTVClient


class WSBProxy:
    def __init__(self, auth_user=None, auth_pass=None):
        self.auth_user = auth_user
        self.auth_pass = auth_pass

    def fetch_wannspieltbig_matches(self):
        try:
            response = requests.get(WSB_API_MATCHES_URL, timeout=10)
            response.raise_for_status()
            matches_data = response.json().get('results', [])
            return matches_data
        except requests.RequestException as e:
            print(f"Error fetching matches: {e}")
            return None
        
    def filter_hltv_matches(self, matches):
        print("=== Scores @ Wannspieltbig.de ===")
        hltv_matches = []
        for match in matches:
            lineup_a = match.get('lineup_a', {})
            lineup_b = match.get('lineup_b', {})
            if lineup_a:
                team_a_id = lineup_a.get('team', {}).get('hltv_id')
            else:
                team_a_id = None
            if lineup_b:
                team_b_id = lineup_b.get('team', {}).get('hltv_id')
            else:
                team_b_id = None

            hltv_match_id = match.get('hltv_match_id')
            if hltv_match_id is not None and (team_a_id in HLTV_BIG_TEAMS_IDS or team_b_id in HLTV_BIG_TEAMS_IDS):
                hltv_matches.append(match)
        
        print(f"Filtered {len(hltv_matches)} HLTV matches involving BIG teams.")
        for match in hltv_matches:
            print(f" - HLTV Match ID: {match.get('hltv_match_id')}, Teams: {match.get('lineup_a', {}).get('team', {}).get('name')} vs {match.get('lineup_b', {}).get('team', {}).get('name')}")
            for matchmap in match.get('matchmaps', []):
                print(f"   - Map {matchmap.get('map_nr')}: {matchmap.get('map_name')}, Score: {matchmap.get('rounds_won_team_a')} - {matchmap.get('rounds_won_team_b')}")
        return hltv_matches
    
    def fetch_hltv_livescore(self, hltv_match_id):
        print("=== Scores @ HLTV.org ===")
        score_by_map_and_teamid = {}
        with HLTVSimpleClient() as sio:
            ua = 'Mozilla/5.0 (Windows; U; Windows NT 6.0; pl; rv:1.9.2) Gecko/20100115 Firefox/3.6'
            headers = {
                #'User-Agent': UserAgent().get_random_user_agent(),
                'User-Agent': ua,
            }
            sio.connect('https://scorebot-lb.hltv.org', headers=headers, transports="websocket")
            if DEBUG:
                print(f" [fetch_hltv_livescore] HLTV connection infos: sid={sio.sid}, transport={sio.transport}, user_agent={ua}")
            sio.emit("readyForScores", data=json.dumps({"token": "", "listIds": [hltv_match_id]}))
            event_name, event_data = sio.receive(timeout=15)
            if event_name == 'score':
                mapscore_data = event_data.get('mapScores', {})
                map_ids = mapscore_data.keys()
                if DEBUG:
                    print(f" [fetch_hltv_livescore]  HLTV map_ids={map_ids}")
                for map_id in map_ids:                        
                    fh_ct = mapscore_data.get(map_id, {}).get('firstHalf', {}).get('ctScore', 0)
                    fh_ct_teamid = mapscore_data.get(map_id, {}).get('firstHalf', {}).get('ctTeamDbId', 'unknown')
                    fh_t = mapscore_data.get(map_id, {}).get('firstHalf', {}).get('tScore', 0)
                    fh_t_teamid = mapscore_data.get(map_id, {}).get('firstHalf', {}).get('tTeamDbId', 'unknown')
                    sh_ct = mapscore_data.get(map_id, {}).get('secondHalf', {}).get('ctScore', 0)
                    sh_t = mapscore_data.get(map_id, {}).get('secondHalf', {}).get('tScore', 0)
                    ot_ct = mapscore_data.get(map_id, {}).get('overtime', {}).get('ctScore', 0)
                    #ot_ct_teamid = mapscore_data.get(map_id, {}).get('overtime', {}).get('ctTeamDbId', 'unknown')
                    ot_t = mapscore_data.get(map_id, {}).get('overtime', {}).get('tScore', 0)
                    #ot_t_teamid = mapscore_data.get(map_id, {}).get('overtime', {}).get('tTeamDbId', 'unknown')
                    map_name = mapscore_data.get(map_id, {}).get('map', 'unknown')
                    map_score_by_teamid = {
                        fh_ct_teamid: fh_ct + sh_t + ot_t,
                        fh_t_teamid: fh_t + sh_ct + ot_ct
                    }
                    map_half_scores = {
                        fh_ct_teamid: (fh_ct, sh_t, ot_t),
                        fh_t_teamid: (fh_t, sh_ct, ot_ct)
                    }

                    print(f" [fetch_hltv_livescore] Map Half Scores: {map_half_scores}")

                    score_by_map_and_teamid[int(map_id)] = {
                        fh_ct_teamid: map_score_by_teamid[fh_ct_teamid],
                        fh_t_teamid: map_score_by_teamid[fh_t_teamid],
                        'map_name': map_name
                    }
                    print(f" [fetch_hltv_livescore] Match {hltv_match_id} - Map: {map_id} ({map_name}), Score: CT-Team {fh_ct_teamid} {map_score_by_teamid[fh_ct_teamid]} - T-Team {fh_t_teamid} {map_score_by_teamid[fh_t_teamid]}")
            sio.disconnect()
        return score_by_map_and_teamid
    
    def update_wannspieltbig_matchmap(self, matchmap_id, rounds_won_team_a, rounds_won_team_b):
        payload = {
            'rounds_won_team_a': rounds_won_team_a,
            'rounds_won_team_b': rounds_won_team_b
        }
        print(f" [update_wannspieltbig_matchmap] Updating WSB MatchMap ID {matchmap_id} with payload: {payload}")
        
        try:
            
            response = requests.put(
                f"{WSB_API_MATCHMAP_UPDATE_URL}{matchmap_id}/",
                auth=(self.auth_user, self.auth_pass),
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            updated_data = response.json()
            print(f" [update_wannspieltbig_matchmap] Updated WSB MatchMap ID {matchmap_id} with scores {rounds_won_team_a}-{rounds_won_team_b}.")
            return updated_data
        except requests.RequestException as e:
            print(f" [update_wannspieltbig_matchmap] Error updating matchmap {matchmap_id}: {e}")
            return None

    def loop(self, interval=60):
        while True:
            # Step 1: Fetch matches from Wannspieltbig.de
            wsb_matches = self.fetch_wannspieltbig_matches()
            if wsb_matches is not None:
                print(f"Fetched {len(wsb_matches)} matches from WSB.")
            else:
                print("Failed to fetch matches.")
            
            # Step 2: Filter matches to those with HLTV IDs involving BIG teams
            hltv_matches = self.filter_hltv_matches(wsb_matches) if wsb_matches else []
            
            # Step 3: For each HLTV match, fetch live score data
            scores_from_hltv_by_matchid = {}
            for match in hltv_matches:
                hltv_match_id=match['hltv_match_id']
                score_from_hltv = self.fetch_hltv_livescore(hltv_match_id)
                scores_from_hltv_by_matchid[hltv_match_id] = score_from_hltv
            print(f"Collected scores from HLTV for {len(scores_from_hltv_by_matchid)} matches.")
            
            # Step 4: Compare scores and log differences
            for match in hltv_matches:
                hltv_match_id = match['hltv_match_id']
                wsb_matchmaps = match.get('matchmaps', [])
                hltv_scores = scores_from_hltv_by_matchid.get(hltv_match_id, {})
                big_team_id = None
                other_team_id = None
                for team_id in HLTV_BIG_TEAMS_IDS:
                    if team_id in [match.get('lineup_a', {}).get('team', {}).get('hltv_id'),
                                   match.get('lineup_b', {}).get('team', {}).get('hltv_id')]:
                        big_team_id = team_id
                        break

                for map_nr in hltv_scores.keys():
                    for team_id in hltv_scores[map_nr].keys():
                        if team_id != big_team_id:
                            other_team_id = team_id
                            break

                print(f"Hltv Scores for Match ID {hltv_match_id}: {hltv_scores}, BIG Team ID: {big_team_id}, Other Team ID: {other_team_id} ")
                for wsb_map in wsb_matchmaps:
                    map_nr = wsb_map.get('map_nr')
                    wsb_rounds_a = wsb_map.get('rounds_won_team_a', 0)
                    wsb_rounds_b = wsb_map.get('rounds_won_team_b', 0)
                    hltv_map_score = hltv_scores.get(map_nr, {})
                    if hltv_map_score:
                        hltv_rounds_a = hltv_map_score.get(big_team_id, 0)
                        hltv_rounds_b = hltv_map_score.get(other_team_id, 0)
                        if (wsb_rounds_a != hltv_rounds_a) or (wsb_rounds_b != hltv_rounds_b):
                            print(f"Score mismatch for Match HLTV ID {hltv_match_id} Map {map_nr}: WSB {wsb_rounds_a}-{wsb_rounds_b} vs HLTV {hltv_rounds_a}-{hltv_rounds_b}. Updating WSB...")
                            self.update_wannspieltbig_matchmap(
                                matchmap_id=wsb_map['id'],
                                rounds_won_team_a=hltv_rounds_a,
                                rounds_won_team_b=hltv_rounds_b
                            )
                        else:
                            print(f"Scores match for Match HLTV ID {hltv_match_id} Map {map_nr}: {wsb_rounds_a}-{wsb_rounds_b}. No update needed.")
                    else:
                        print(f"No HLTV score data for Match HLTV ID {hltv_match_id} Map {map_nr}.")
            
            time.sleep(interval)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='WSB Proxy to fetch HLTV live scores for BIG matches.')
    parser.add_argument('--interval', type=int, default=60, help='Interval in seconds between fetches (default: 60)')
    parser.add_argument('--auth_user', type=str, required=True, help='Username for WSB API authentication')
    parser.add_argument('--auth_pass', type=str, required=True, help='Password for WSB API authentication')
    args = parser.parse_args()
    auth_user = args.auth_user
    auth_pass = args.auth_pass
    proxy = WSBProxy(auth_user, auth_pass)
    proxy.loop(interval=args.interval)  # Fetch every 1 minutes