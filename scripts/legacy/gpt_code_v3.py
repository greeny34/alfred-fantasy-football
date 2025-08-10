class DraftState:
    def __init__(self, available_players):
        self.available_players = available_players
        self.drafted_players = []
        self.current_round = 1
        self.current_position = 1

    def add_pick(self, player_name, team_name):
        if player_name in self.available_players:
            self.drafted_players.append((player_name, team_name))
            self.available_players.remove(player_name)
            self.current_position += 1
            if self.current_position > len(self.available_players) + len(self.drafted_players):
                self.current_round += 1
                self.current_position = 1

    def get_available_players_by_position(self, position):
        return [player for player in self.available_players if player['position'] == position]

    def suggest_best_pick(self, team_needs):
        for need in team_needs:
            available_by_need = self.get_available_players_by_position(need)
            if available_by_need:
                return available_by_need[0]
        return None

# Example usage
available_players = [
    {'name': 'Player1', 'position': 'QB'},
    {'name': 'Player2', 'position': 'RB'},
    {'name': 'Player3', 'position': 'WR'},
    {'name': 'Player4', 'position': 'TE'}
]

draft = DraftState(available_players)
draft.add_pick('Player1', 'TeamA')
print(draft.get_available_players_by_position('RB'))
print(draft.suggest_best_pick(['RB', 'WR']))