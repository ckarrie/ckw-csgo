import asyncio
import pprint
import time

from csgomatches.utils.scrapers.hltv import get_hlvt_score, convert_to_score


def test_get_hlvt_score(matchid):
    while True:
        r = asyncio.get_event_loop().run_until_complete(get_hlvt_score(matchid))
        pprint.pprint(r)
        for mapnr, map_data in r[1]['mapScores'].items():
            print(" ---------- MAP", mapnr, "SCORE", convert_to_score(r, mapnr))


        time.sleep(2)


"""
from csgomatches.utils.scrapers import ws_test
ws_test.test_get_hlvt_score(2339162)
"""