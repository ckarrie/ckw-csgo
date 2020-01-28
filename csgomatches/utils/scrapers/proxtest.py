import cfscrape

import json
with open('proxies.json', 'r') as pfile:
    proxies = json.loads(pfile.readlines()[0])


scraper = cfscrape.CloudflareScraper()

resp = scraper.get('http://play.esea.net/api/teams/8749575/matches?page_size=50', proxies=proxies )

print(resp.json())