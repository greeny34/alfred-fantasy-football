import requests

def get_espn_players(league_id, season_id, espn_s2, swid):
    url = f"https://fantasy.espn.com/apis/v3/games/ffl/seasons/{season_id}/segments/0/leagues/{league_id}?view=kona_player_info"
    cookies = {
        'espn_s2': espn_s2,
        'SWID': swid
    }
    response = requests.get(url, cookies=cookies)
    data = response.json()
    players = data.get('players', [])
    available_players = [player for player in players if player['status'] == 'FREEAGENT']
    return available_players

league_id = 'your_league_id'
season_id = 'your_season_id'
espn_s2 = 'your_espn_s2_cookie'
swid = 'your_swid_cookie'

available_players = get_espn_players(league_id, season_id, espn_s2, swid)
for player in available_players:
    print(player['player']['fullName'])