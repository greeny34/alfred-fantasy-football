from espn_api.football import League
from dotenv import load_dotenv
import os

load_dotenv()
league = League(
    league_id=os.getenv('LEAGUE_ID'),
    year=int(os.getenv('YEAR')),
    espn_s2=os.getenv('ESPN_S2'),
    swid=os.getenv('SWID')
)

for team in league.teams:
    print(f"Team: {team.team_name}")