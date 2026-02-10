import requests
import json
import time
import logging
import sys
from socketio import SimpleClient, Client
import argparse
from random_user_agent.user_agent import UserAgent
from datetime import datetime


logging.basicConfig(
    stream=sys.stdout, 
    level=logging.INFO, 
    format='%(asctime)s | %(funcName)30s | %(levelname)s | %(message)s', 
    #log_colors={'DEBUG':    'cyan','INFO':     'green',	'WARNING':  'yellow','ERROR':    'red',	'CRITICAL': 'red,bg_white',	}
)
logger = logging.getLogger(__name__)

# Static variables
RANDOM_UA = UserAgent().get_random_user_agent()
DEBUG = False
#WSB_API_MATCHES_URL = "https://wannspieltbig.de/api/match_livescore/"
WSB_API_MATCHES_URL = "https://wannspieltbig.de/api/match_upcoming/?game=cs"
WSB_API_MATCHMAP_UPDATE_URL = "https://wannspieltbig.de/api/matchmap_update/"
HLTV_BIG_TEAMS_IDS = [
    7532, # BIG Main
    10254, # BIG Academy
    11718 # BIG Equipa
]

FACEIT_BIG_TEAMS_IDS = [
    'af894ef4-0b65-4e87-97d4-415967de35b3', # faction_id BIG Equipa @ ESEA
    'c40aceae-ecb7-47c1-9c6a-fa0efe3d6f36', # BIG Main @ Faceit
]


class HLTVClient(Client):    
    def _handle_eio_message(self, data):
        if DEBUG:
            logger.debug(f"HLTVSocketClient received data: {data}")
        try:
            return super()._handle_eio_message(data)
        except json.JSONDecodeError:
            if DEBUG:
                logger.warning("JSON-Error received in _handle_eio_message, ignoring...")
            else:
                pass


class HLTVSimpleClient(SimpleClient):
    """A simple Socket.IO client for HLTV scorebot server with custom client class."""
    client_class = HLTVClient


class WSBProxy:
    def __init__(self, auth_user=None, auth_pass=None, faceit_api_key=None, test_hltv_match_id=None):
        self.auth_user = auth_user
        self.auth_pass = auth_pass
        self.faceit_api_key = faceit_api_key
        self.test_hltv_match_id = test_hltv_match_id

    def fetch_wannspieltbig_matches(self):
        try:
            response = requests.get(WSB_API_MATCHES_URL, timeout=10)
            response.raise_for_status()
            matches_data = response.json().get('results', [])
            logger.info(f"Fetched {len(matches_data)} matches from WSB.")
            return matches_data
        except requests.RequestException as e:
            logger.error(f"Error fetching matches: {e}")
            return None
        
    def filter_wsb_matches(self, matches):
        #print(" [filter_wsb_matches] === Scores @ Wannspieltbig.de ===")
        hltv_matches = []
        faceit_matches = []
        skipped_ended_matches = []
        skipped_missing_enemy_team_matches = []
        not_today_matches = []
        for match in matches:
            has_ended = match.get('has_ended', False)
            lineup_a = match.get('lineup_a', {})
            lineup_b = match.get('lineup_b', {})
            if has_ended:
                skipped_ended_matches.append(match)
                logger.debug(f"Skipping ended match: Match Slug {match.get('slug')}")
                continue
            
            if lineup_a:
                team_a_id = lineup_a.get('team', {}).get('hltv_id')
            else:
                team_a_id = None
            if lineup_b:
                team_b_id = lineup_b.get('team', {}).get('hltv_id')
            else:
                team_b_id = None
                skipped_missing_enemy_team_matches.append(match)   
                logger.debug(f"Skipping match with missing enemy team: Match Slug {match.get('slug')}")
                continue

            # Filter matches not scheduled for today based on 'first_map_at' field
            first_map_at_str = match.get('first_map_at')
            if first_map_at_str:
                first_map_at = datetime.fromisoformat(first_map_at_str)
                now = datetime.now()
                if first_map_at.date() != now.date():
                    not_today_matches.append(match)
                    logger.debug(f"Skipping match not scheduled for today: Match Slug {match.get('slug')}, Scheduled Date: {first_map_at.date()}")
                    continue

            # HLTV Match ID filter
            hltv_match_id = match.get('hltv_match_id')
            if hltv_match_id is not None and (team_a_id in HLTV_BIG_TEAMS_IDS or team_b_id in HLTV_BIG_TEAMS_IDS):
                hltv_matches.append(match)

            # ESEA/Faceit Match ID filter
            esea_match_id = match.get('esea_match_id')
            if self.faceit_api_key and esea_match_id:
                faceit_matches.append(match)
            if self.faceit_api_key is None and esea_match_id:
                logger.warning("Faceit API Key not provided, skipping Faceit matches processing.")
        
        logger.info(f"Skipped {len(skipped_ended_matches)} ended matches.")
        logger.info(f"Skipped {len(skipped_missing_enemy_team_matches)} matches with missing enemy team.") 
        logger.info(f"Skipped {len(not_today_matches)} matches not scheduled for today.")
        logger.info(f"Filtered {len(hltv_matches)} HLTV matches and {len(faceit_matches)} FACEIT matches involving BIG teams.")
        for match in hltv_matches:
            logger.info(f" - HLTV Match ID: {match.get('hltv_match_id')}, Teams: {match.get('lineup_a', {}).get('team', {}).get('name')} vs {match.get('lineup_b', {}).get('team', {}).get('name')}")
            for matchmap in match.get('matchmaps', []):
                played_map = matchmap.get('played_map', {})
                map_name = '?'
                if played_map:
                    map_name = played_map.get('cs_name', '?')
                logger.info(f"   - Map {matchmap.get('map_nr')} ({map_name}): Score: {matchmap.get('rounds_won_team_a')} - {matchmap.get('rounds_won_team_b')}")
        return hltv_matches, faceit_matches
    
    def fetch_hltv_livescore(self, hltv_match_id):
        logger.info("=== Scores @ HLTV.org ===")
        score_by_map_and_teamid = {}
        with HLTVSimpleClient() as sio:
            #ua = 'Mozilla/5.0 (Windows; U; Windows NT 6.0; pl; rv:1.9.2) Gecko/20100115 Firefox/3.6'
            
            headers = {
                #'User-Agent': UserAgent().get_random_user_agent(),
                'User-Agent': RANDOM_UA,
            }
            sio.connect('https://scorebot-lb.hltv.org', headers=headers, transports="websocket")
            logger.debug(f"HLTV connection infos: sid={sio.sid}, transport={sio.transport}, user_agent={headers['User-Agent']}")
            sio.emit("readyForScores", data=json.dumps({"token": "", "listIds": [hltv_match_id]}))
            event_name, event_data = sio.receive(timeout=15)
            if event_name == 'score':
                mapscore_data = event_data.get('mapScores', {})
                if hltv_match_id == self.test_hltv_match_id:
                    logger.info(f"Test HLTV Match ID {hltv_match_id}: Data from HLTV: {event_data}")
                map_ids = mapscore_data.keys()
                logger.debug(f" [fetch_hltv_livescore]  HLTV map_ids={map_ids}")
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

                    logger.info(f"Map Half Scores: {map_half_scores}")

                    score_by_map_and_teamid[int(map_id)] = {
                        fh_ct_teamid: map_score_by_teamid[fh_ct_teamid],
                        fh_t_teamid: map_score_by_teamid[fh_t_teamid],
                        'unplayed': mapscore_data.get(map_id, {}).get('defaultWin', False),
                        'map_name': map_name
                    }
                    logger.info(f"Match {hltv_match_id} - Map: {map_id} ({map_name}), Score: CT-Team {fh_ct_teamid} {map_score_by_teamid[fh_ct_teamid]} - T-Team {fh_t_teamid} {map_score_by_teamid[fh_t_teamid]}")
            sio.disconnect()
        return score_by_map_and_teamid
    
    def fetch_faceit_livescore(self, esea_match_id):
        logger.info("=== Scores @ Faceit.com / ESEA.net ===")
        headers = {"Authorization": f"Bearer {self.faceit_api_key}"}
        try:
            resp = requests.get(f"https://open.faceit.com/data/v4/matches/{esea_match_id}", timeout=10, headers=headers)
        except requests.ReadTimeout:
            logger.error(f"Timeout fetching Faceit match stats for Match ID {esea_match_id}")
            return None
        if resp.status_code == 200:
            match_data = resp.json()
            if match_data.get('best_of') == 1:
                logger.debug(f"Match {esea_match_id} is a BO1, match_data: {match_data}")
                match_status = match_data.get('status')
                logger.info(f" - Fetching Faceit match status: {match_status}")
                #print(f" - Teams: {match_data.get('teams', {})}")
                if match_data.get('teams', {}):
                    team_a = match_data.get('teams', {}).get('faction1', {})
                    team_b = match_data.get('teams', {}).get('faction2', {})
                    logger.info(f" - Teams: {team_a.get('name')} vs {team_b.get('name')}")
                    logger.debug(f"   - Team A: {team_a.get('name')} (ID: {team_a.get('faction_id')})")
                    logger.debug(f"   - Team B: {team_b.get('name')} (ID: {team_b.get('faction_id')})")

                    if team_a.get('faction_id') in FACEIT_BIG_TEAMS_IDS or team_b.get('faction_id') in FACEIT_BIG_TEAMS_IDS:
                        logger.info(f" - BIG Team involved in Match ID {esea_match_id}. Fetching stats...")
                        big_faction = 'faction1' if team_a.get('faction_id') in FACEIT_BIG_TEAMS_IDS else 'faction2'
                        other_faction = 'faction2' if big_faction == 'faction1' else 'faction1'
                        score = match_data.get('results', {}).get('score', {})
                        logger.debug(f"   - Results : {match_data.get('results', {})}")
                        voted_maps = match_data.get('voting', {}).get('map', {}).get('pick', [])
                        logger.info(f"   - Voted Maps : {voted_maps}")
                        played_map = None
                        if voted_maps:
                            played_map = voted_maps[0]
                        if len(voted_maps) > 1:
                            logger.error(f"   - More than one map voted ({voted_maps}), need implementation for multi-map matches!")

                        return {
                            'rounds_won_team_a': score.get(big_faction, 0),
                            'rounds_won_team_b': score.get(other_faction, 0),
                            'map_name': played_map
                        }
                    else:
                        logger.error(f" - No BIG Team involved in Match ID {esea_match_id}. Skipping stats fetch. Missing Team ID in FACEIT_BIG_TEAMS_IDS.")
                        logger.error(f"   - Team A: {team_a.get('name')} (ID: {team_a.get('faction_id')})")
                        logger.error(f"   - Team B: {team_b.get('name')} (ID: {team_b.get('faction_id')})")
                        return None
                    
        else:
            logger.error(f"Error fetching Faceit match stats for Match ID {esea_match_id}: Status Code {resp.status_code}")

            # Further processing can be done here as needed

    
    def update_wannspieltbig_matchmap(self, matchmap_id, rounds_won_team_a, rounds_won_team_b, unplayed=False, played_map_name=None):
        payload = {
            'rounds_won_team_a': rounds_won_team_a,
            'rounds_won_team_b': rounds_won_team_b,
            'unplayed': unplayed
        }
        if played_map_name:
            payload['played_map_name'] = played_map_name
        logger.info(f"Updating WSB MatchMap ID {matchmap_id} with payload: {payload}")
        
        try:            
            response = requests.put(
                f"{WSB_API_MATCHMAP_UPDATE_URL}{matchmap_id}/",
                auth=(self.auth_user, self.auth_pass),
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            updated_data = response.json()
            logger.info(f"Updated WSB MatchMap ID {matchmap_id} with scores {rounds_won_team_a}-{rounds_won_team_b}.")
            return updated_data
        except requests.RequestException as e:
            logger.error(f"Error updating matchmap {matchmap_id}: {e}")
            return None
        
    def compare_and_update_scores(self, scores_from_hltv_by_matchid, hltv_matches):
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

            logger.info(f"Hltv Scores for Match ID {hltv_match_id}: {hltv_scores}, BIG Team ID: {big_team_id}, Other Team ID: {other_team_id} ")
            for wsb_map in wsb_matchmaps:
                map_nr = wsb_map.get('map_nr')
                wsb_rounds_a = wsb_map.get('rounds_won_team_a', 0)
                wsb_rounds_b = wsb_map.get('rounds_won_team_b', 0)
                hltv_map_score = hltv_scores.get(map_nr, {})
                matchmap_id = wsb_map.get('id')
                if hltv_map_score:
                    hltv_rounds_a = hltv_map_score.get(big_team_id, 0)
                    hltv_rounds_b = hltv_map_score.get(other_team_id, 0)
                    if (wsb_rounds_a != hltv_rounds_a) or (wsb_rounds_b != hltv_rounds_b):
                        logger.warning(f"Score Update for Map {map_nr}: WSB {wsb_rounds_a}-{wsb_rounds_b} vs HLTV {hltv_rounds_a}-{hltv_rounds_b}. Updating WSB...")
                        self.update_wannspieltbig_matchmap(
                            matchmap_id=matchmap_id,
                            rounds_won_team_a=hltv_rounds_a,
                            rounds_won_team_b=hltv_rounds_b,
                            unplayed=hltv_map_score.get('unplayed', False),
                            played_map_name=hltv_map_score.get('map_name', None)
                        )
                    else:
                        logger.info(f"Scores for Map {map_nr}: {wsb_rounds_a}-{wsb_rounds_b}. No update needed.")
                else:
                    logger.info(f"No HLTV score for Map {map_nr}.")
            

    def loop(self, interval=60):
        while True:
            start_time = time.time()
            logger.info("=== WSB Proxy Loop ===")
            # Step 1: Fetch matches from Wannspieltbig.de
            wsb_matches = self.fetch_wannspieltbig_matches()            
            
            # Step 2: Filter matches to those with HLTV IDs involving BIG teams
            hltv_matches, faceit_matches = self.filter_wsb_matches(wsb_matches) if wsb_matches else []
            if self.test_hltv_match_id:
                if self.test_hltv_match_id not in [m['hltv_match_id'] for m in hltv_matches]:
                    logger.info(f"Adding test HLTV Match ID {self.test_hltv_match_id} to processing list.")
                    hltv_matches.append({
                        'hltv_match_id': self.test_hltv_match_id,
                        'matchmaps': []
                    })

            logger.debug(f"Filtered HLTV Matches: {hltv_matches}")
            
            # Step 3: For each HLTV match, fetch live score data
            scores_from_hltv_by_matchid = {}
            for match in hltv_matches:
                hltv_match_id=match['hltv_match_id']
                score_from_hltv = self.fetch_hltv_livescore(hltv_match_id)
                scores_from_hltv_by_matchid[hltv_match_id] = score_from_hltv
            logger.info(f"Collected scores from HLTV for {len(scores_from_hltv_by_matchid)} matches.")

            for match in faceit_matches:
                esea_match_id=match['esea_match_id']
                score_from_faceit = self.fetch_faceit_livescore(esea_match_id)
                if score_from_faceit:
                    matchmaps = match.get('matchmaps', [])
                    if matchmaps:
                        matchmap_id = matchmaps[0].get('id')
                        self.update_wannspieltbig_matchmap(
                            matchmap_id=matchmap_id,
                            rounds_won_team_a=score_from_faceit['rounds_won_team_a'],
                            rounds_won_team_b=score_from_faceit['rounds_won_team_b'],
                            unplayed=False,
                            played_map_name=score_from_faceit['map_name']
                        )
            
            # Step 4: Compare scores and log differences
            self.compare_and_update_scores(scores_from_hltv_by_matchid, hltv_matches)
            end_time = time.time()
            elapsed_time = end_time - start_time
            logger.info(f"Loop iteration took {elapsed_time:.2f} seconds. Sleeping for {interval} seconds before next fetch. Stop with Ctrl+C.")
            time.sleep(interval)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='WSB Proxy to fetch HLTV live scores for BIG matches.')
    parser.add_argument('--interval', type=int, default=60, help='Interval in seconds between fetches (default: 60)')
    parser.add_argument('--auth_user', type=str, required=True, help='Username for WSB API authentication')
    parser.add_argument('--auth_pass', type=str, required=True, help='Password for WSB API authentication')
    parser.add_argument('--test_hltv_match_id', type=int, required=False, help='HLTV Match ID for testing purposes')
    parser.add_argument('--faceit_api_key', type=str, required=False, help='API Key for Faceit API, see https://developers.faceit.com/apps')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')

    args = parser.parse_args()
    auth_user = args.auth_user
    auth_pass = args.auth_pass
    if args.debug:
        DEBUG = True
        logger.setLevel(logging.DEBUG)
    
    proxy = WSBProxy(auth_user, auth_pass, faceit_api_key=args.faceit_api_key, test_hltv_match_id=args.test_hltv_match_id)
    try:
        logger.info("Starting WSB Proxy...")
        proxy.loop(interval=args.interval)  # Fetch every 1 minutes
    except KeyboardInterrupt:
        print("Stopping WSB Proxy...")
    