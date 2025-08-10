import os
from dotenv import load_dotenv
from espn_api.football import League

load_dotenv()

league_id = os.getenv('LEAGUE_ID')
year = int(os.getenv('YEAR'))
espn_s2 = os.getenv('ESPN_S2')
swid = os.getenv('SWID')

league = League(league_id=league_id, year=year, espn_s2=espn_s2, swid=swid)

available_players = league.free_agents()

for player in available_players:
    print(f"Name: {player.name}, Position: {player.position}")