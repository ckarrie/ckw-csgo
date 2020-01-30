import requests
from django.core.cache import cache

FACEIT_NICK_TO_TWITCH_ID_CACHE = {}

def get_hubs():
    # Faceit Hubs
    hub_ids = {
        '74caad23-077b-4ef3-8b1d-c6a2254dfa75': 'FPL CSGO Europe',
        '748cf78c-be73-4eb9-b131-21552f2f8b75': 'FPL CSGO North America',
        'ea898dde-51e9-4631-a630-a994f9cb4825': 'UK Invite Gathers',
        'ac41cb6c-df11-4597-8391-9b79a0cdfff6': 'UKPL',
        '86108299-a413-4d45-95dd-20a638e91c03': 'GPL Ersatz Div 1',
        '7167749f-a7de-4db6-828c-839b339c000e': 'German Championship Series Pro',
        'fd5780d5-dd2f-4479-906c-57b8e41ae9d7': 'FPL CSGO Challenger Europe',
        'e655b953-4ef1-4993-965b-b9e9e83df6e7': 'German Pro League',
        '6f63b115-f45e-42b7-88ef-2a96714cd5e1': 'LEGENDS - 2700 ELO TO ENTER',
    }
    return hub_ids

def get_nicknames():
    # Faceit Player Nicknames
    nicknames_main = ['tabseN', 'k1to', 'syrsoN', 'XANTARES', 'tiziaN', ]
    nicknames_academy = ['PANIX_', 'Anhuin', 'HadeZ_', 'prosus', 'krimb0b', ]

    nicknames_other = [
        'y00000000',  # zonixx
        'gobb',
        'nex---',
        'LEGIJA',
        'keev',
        'nooky',
        'headshinsky',
        'smooya',
        'roxi'
    ]
    nicknames = nicknames_main + nicknames_academy + nicknames_other
    return nicknames


def check_hubs_for_matches():
    hub_ids = get_hubs()
    nicknames = get_nicknames()

    match_nr = 0
    infos_by_match = {}

    for hid, hub_name in hub_ids.items():
        params = {
            'entityId': hid,
            'entityType': 'hub',
            'limit': 20,
            'offset': 0,
            'state': ['SUBSTITUTION', 'CAPTAIN_PICK', 'VOTING', 'CONFIGURING', 'READY', 'ONGOING', 'MANUAL_RESULT', 'ABORTED']
        }
        api_url = 'https://api.faceit.com/match/v1/match'
        resp = requests.get(api_url, params=params)
        resp_json = resp.json()
        match_payloads = resp_json.get('payload', [])
        #print(api_url, params['entityId'])
        if match_payloads:
            for match in match_payloads:
                infos_by_match[match_nr] = {
                    'players': [],
                    'streams': [],
                    'map': None,
                    'roster1': [],
                    'roster2': [],
                    'faceit_room_id': match.get('id'),
                    'first_avatar': None,
                    'hub_name': hub_name,
                    'hub_id': hid
                }

                roster1 = match.get('teams', {}).get('faction1', {}).get('roster', [])
                roster2 = match.get('teams', {}).get('faction2', {}).get('roster', [])
                #infos_by_match[match_nr]['roster1'] = roster1
                #infos_by_match[match_nr]['roster2'] = roster2

                map_pick = match.get('voting', {}).get('map', {}).get('pick', [])
                if map_pick:
                    map_pick = map_pick[0]
                    infos_by_match[match_nr]['map'] = map_pick

                twitch_ids = []

                for r in roster1 + roster2:
                    nickname = r.get('nickname')
                    if nickname in nicknames:
                        infos_by_match[match_nr]['players'].append(nickname)
                        infos_by_match[match_nr]['first_avatar'] = r.get('avatar')

                        print("Found", nickname)

                if infos_by_match[match_nr]['players']:
                    for r in roster1 + roster2:
                        twitch_id = faceit2twitch_id(nickname=r.get('nickname'))
                        if twitch_id:
                            twitch_ids.append(twitch_id)
                    online_streams = get_twitch_stream_status(twitch_ids)
                    infos_by_match[match_nr]['streams'] = online_streams

                match_nr += 1

    matches_dict = {
        'looked_up_nicknames': nicknames,
        'matches': infos_by_match
    }

    return matches_dict



def faceit2twitch_id(nickname):
    bypasses = {
        # old twitch name: new twitch name
        's1mple': 's1mple'
    }

    if nickname in bypasses:
        return bypasses[nickname]

    #if nickname in FACEIT_NICK_TO_TWITCH_ID_CACHE:
        #return FACEIT_NICK_TO_TWITCH_ID_CACHE[nickname]

    cache_key = 'faceit_twitch_id_' + nickname
    cached_twitch_id = cache.get(cache_key)
    if cached_twitch_id:
        cache.touch(cache_key)
        return cached_twitch_id


    api_url = 'https://api.faceit.com/core/v1/nicknames/{}'.format(nickname)
    resp = requests.get(api_url)
    resp_json = resp.json()
    twitch_id = resp_json.get('payload', {}).get('streaming', {}).get('twitch_id', None)
    #is_streaming = resp_json.get('payload', {}).get('streaming', {}).get('is_streaming', None)
    cache.set(cache_key, twitch_id, timeout=None)

    return twitch_id

def get_twitch_stream_status(nicknames=[]):
    online_streams = []
    params = {
        'user_login': [nn.lower() for nn in nicknames],
        #'client_id': 'w7skd7sc9mop0p60bnqe0ukc2qj8ht'
    }
    headers = {'Client-ID': 'w7skd7sc9mop0p60bnqe0ukc2qj8ht', 'Accept': 'application/vnd.twitchtv.v5+json'}
    api_url = 'https://api.twitch.tv/helix/streams'

    resp = requests.get(api_url, params=params, headers=headers)
    resp_json = resp.json()
    results = resp_json.get('data', [])
    for r in results:
        is_live = r.get('type', '') == 'live'
        lang = r.get('language', '')
        user_name = r.get('user_name', '')
        viewer_cnt = r.get('viewer_count', 0)
        if is_live:
            #print("  - LIVE: https://twitch.tv/{}".format(user_name), viewer_cnt)
            online_streams.append(user_name)

    return online_streams

def loop_check_hubs_for_matches():
    import time
    import sys
    while True:
        check_hubs_for_matches()
        #sys.
        print("=======================================================================" * 2)
        time.sleep(60)


#loop_check_hubs_for_matches()

