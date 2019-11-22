import asyncio
from collections import OrderedDict
from csgomatches.utils.scrapers.hltv import get_hlvt_score, get_hltv_team_name_from_id

from django.apps import apps


class MapLiveScore(object):
    def __init__(self, hltv_match_id, map_nr):
        self.hltv_match_id = hltv_match_id
        self.team_a_id = 0
        self.team_a_name = "Team A"
        self.team_b_id = 0
        self.team_b_name = "Team B"
        self.map_nr = map_nr
        self.score_team_a = 16
        self.score_team_b = 7


class HLTVMap(object):
    def __init__(self, hltv_match_id, team_a_id, team_b_id, score_a, score_b, map_name, map_nr):
        self.hltv_match_id = hltv_match_id
        self.team_a_id = team_a_id
        self.team_b_id = team_b_id
        self.score_a = score_a
        self.score_b = score_b
        self.map_name = map_name
        self.map_nr = map_nr

    def __str__(self):
        return "{} {} {}:{} {}".format(self.map_name, self.team_a_id, self.score_a, self.score_b, self.team_b_id)

    def __repr__(self):
        return "<Map #{} - {}>".format(self.map_nr, self.map_name)


class HLTVMatch(object):
    def __init__(self, hltv_match_id):
        self.hltv_match_id = hltv_match_id
        self.team_a_id = 0
        self.team_a_name = None
        self.team_b_id = 0
        self.team_b_name = None
        self.maps = []

        team_id_to_name = OrderedDict()  # Team A first, Team B second
        name_to_team_id = OrderedDict()  # Team A first, Team B second

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        r = asyncio.get_event_loop().run_until_complete(get_hlvt_score(self.hltv_match_id))
        if r:
            for map_nr, map_data in r[1]['mapScores'].items():
                map_nr = int(map_nr)
                scores = OrderedDict(map_data['scores'])
                map_name = map_data['map']
                score_keys = list(scores.keys())
                team_a_id = int(score_keys[0])
                team_b_id = int(score_keys[1])
                if map_nr == 1:
                    team_a_name = get_hltv_team_name_from_id(team_a_id)
                    team_b_name = get_hltv_team_name_from_id(team_b_id)
                    team_id_to_name[int(team_a_id)] = team_a_name
                    team_id_to_name[int(team_b_id)] = team_b_name
                    name_to_team_id[team_a_name] = team_a_id
                    name_to_team_id[team_b_name] = team_b_id
                map_obj = HLTVMap(
                    hltv_match_id=self.hltv_match_id,
                    team_a_id=team_a_id,
                    team_b_id=team_b_id,
                    score_a=scores[str(team_a_id)],
                    score_b=scores[str(team_b_id)],
                    map_name=map_name,
                    map_nr=map_nr
                )
                self.maps.append(map_obj)

        if len(team_id_to_name) == 2:
            team_id_to_name_keys = list(team_id_to_name.keys())
            self.team_a_id = team_id_to_name_keys[0]
            self.team_b_id = team_id_to_name_keys[1]
            self.team_a_name = team_id_to_name[self.team_a_id]
            self.team_b_name = team_id_to_name[self.team_b_id]

        self.team_id_to_name = team_id_to_name
        self.name_to_team_id = name_to_team_id
