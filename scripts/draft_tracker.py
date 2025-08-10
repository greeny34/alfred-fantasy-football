from espn_api.football import League
from dotenv import load_dotenv
import os

class Player:
    def __init__(self, player_id, name, position, team):
        self.player_id = player_id
        self.name = name
        self.position = position
        self.team = team

class DraftState:
    def __init__(self):
        self.drafted_players = []

    def draft_player(self, player):
        if player not in self.drafted_players:
            self.drafted_players.append(player)

    def is_player_drafted(self, player):
        return player in self.drafted_players

class DraftTracker:
    def __init__(self):
        self.players = []
        self.draft_state = DraftState()
        self.load_players()

    def load_players(self):
        load_dotenv()
        league = League(
            league_id=os.getenv('LEAGUE_ID'),
            year=int(os.getenv('YEAR')),
            espn_s2=os.getenv('ESPN_S2'),
            swid=os.getenv('SWID')
        )
        for espn_player in league.free_agents():
            player = Player(
                player_id=espn_player.playerId,
                name=espn_player.name,
                position=espn_player.position,
                team=espn_player.proTeam
            )
            self.players.append(player)

    def suggest_pick(self, position_needs):
        available_players = [p for p in self.players if not self.draft_state.is_player_drafted(p)]
        for position in position_needs:
            for player in available_players:
                if player.position == position:
                    return player
        return None

# Example usage
draft_tracker = DraftTracker()
position_needs = ['QB', 'RB', 'WR']  # Position names instead of numbers
suggested_player = draft_tracker.suggest_pick(position_needs)
if suggested_player:
    print(f"Suggested pick: {suggested_player.name} - {suggested_player.position}")