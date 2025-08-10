import requests
import time
from datetime import datetime

class FixedSleeperDraftAssistant:
    def __init__(self, draft_id, user_id=None):
        self.draft_id = draft_id
        self.user_id = user_id  # Will be auto-detected if None
        self.seen_picks = set()
        self.players_db = {}
        self.team_rosters = {}
        self.my_team_id = None
        self.my_draft_slot = None
        self.draft_order = {}
        self.slot_to_roster = {}
        self.current_pick = 0
        self.total_teams = 0
        self.rounds = 0
        self.snake_draft = True
        
        # Load player database
        self.load_players()
        
    def load_players(self):
        """Load NFL player database"""
        print("📥 Loading NFL player database...")
        try:
            url = "https://api.sleeper.app/v1/players/nfl"
            response = requests.get(url)
            
            if response.status_code == 200:
                self.players_db = response.json()
                print(f"✅ Loaded {len(self.players_db)} players")
            else:
                print(f"❌ Error loading players: {response.status_code}")
        except Exception as e:
            print(f"❌ Error loading players: {e}")
    
    def get_player_name(self, player_id):
        """Get player name from ID"""
        if not player_id or player_id not in self.players_db:
            return f"Unknown_{player_id}"
        
        player = self.players_db[player_id]
        name = player.get('full_name', 'Unknown')
        position = player.get('position', 'UNK')
        team = player.get('team', 'FA')
        
        return f"{name} ({position}) - {team}"
    
    def get_draft_info(self):
        """Get draft information"""
        try:
            url = f"https://api.sleeper.app/v1/draft/{self.draft_id}"
            response = requests.get(url)
            
            if response.status_code == 200:
                draft_data = response.json()
                
                # Store draft settings
                settings = draft_data.get('settings', {})
                self.total_teams = settings.get('teams', 10)
                self.rounds = settings.get('rounds', 16)
                self.snake_draft = draft_data.get('type') == 'snake'
                
                # Store mappings
                self.draft_order = draft_data.get('draft_order', {})
                self.slot_to_roster = draft_data.get('slot_to_roster_id', {})
                
                # Auto-detect user ID if not provided
                if not self.user_id and self.draft_order:
                    available_users = list(self.draft_order.keys())
                    if len(available_users) == 1:
                        self.user_id = available_users[0]
                        print(f"🎯 Auto-detected user ID: {self.user_id}")
                
                # Find your team using FIXED logic
                if self.user_id and self.user_id in self.draft_order:
                    self.my_draft_slot = self.draft_order[self.user_id]
                    self.my_team_id = self.slot_to_roster.get(str(self.my_draft_slot), self.my_draft_slot)
                
                return draft_data
            else:
                print(f"❌ Error getting draft info: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Error getting draft info: {e}")
            return None
    
    def get_current_picks(self):
        """Get all current draft picks with FIXED team assignment"""
        try:
            url = f"https://api.sleeper.app/v1/draft/{self.draft_id}/picks"
            response = requests.get(url)
            
            if response.status_code == 200:
                picks = response.json()
                
                # FIXED: Assign proper team IDs using draft_slot
                for pick in picks:
                    draft_slot = pick.get('draft_slot')
                    if draft_slot:
                        pick['team_id'] = self.slot_to_roster.get(str(draft_slot), draft_slot)
                    else:
                        pick['team_id'] = 'Unknown'
                
                # Find new picks
                new_picks = []
                for pick in picks:
                    pick_key = f"{pick.get('round')}-{pick.get('pick_no')}"
                    if pick_key not in self.seen_picks:
                        self.seen_picks.add(pick_key)
                        new_picks.append(pick)
                
                # Update team rosters with fixed team IDs
                self.update_team_rosters(picks)
                
                return new_picks, len(picks)
            else:
                print(f"❌ Error getting picks: {response.status_code}")
                return [], 0
        except Exception as e:
            print(f"❌ Error getting picks: {e}")
            return [], 0
    
    def update_team_rosters(self, all_picks):
        """Update team rosters based on picks with FIXED team IDs"""
        self.team_rosters = {}
        
        for pick in all_picks:
            # Use the fixed team_id we assigned
            team_id = pick.get('team_id', 'Unknown')
            player_id = pick.get('player_id')
            
            if team_id not in self.team_rosters:
                self.team_rosters[team_id] = []
            
            if player_id and player_id in self.players_db:
                player_info = self.players_db[player_id]
                self.team_rosters[team_id].append({
                    'player_id': player_id,
                    'name': player_info.get('full_name', 'Unknown'),
                    'position': player_info.get('position', 'UNK'),
                    'team': player_info.get('team', 'FA'),
                    'round': pick.get('round'),
                    'pick_no': pick.get('pick_no')
                })
    
    def get_whose_turn_fixed(self, total_picks):
        """FIXED version of whose turn calculation"""
        if total_picks >= self.total_teams * self.rounds:
            return None  # Draft complete
        
        current_round = (total_picks // self.total_teams) + 1
        pick_in_round = total_picks % self.total_teams
        
        if self.snake_draft and current_round % 2 == 0:
            # Even rounds reverse for snake
            next_draft_slot = self.total_teams - pick_in_round
        else:
            # Odd rounds normal order
            next_draft_slot = pick_in_round + 1
        
        # Map draft slot to roster ID
        team_id = self.slot_to_roster.get(str(next_draft_slot), next_draft_slot)
        
        return {
            'team_id': team_id,
            'draft_slot': next_draft_slot,
            'round': current_round,
            'pick_in_round': pick_in_round + 1,
            'pick_number': total_picks + 1
        }
    
    def is_my_turn(self, total_picks):
        """Check if it's your turn to pick using FIXED logic"""
        if not self.my_team_id:
            return False
        
        turn_info = self.get_whose_turn_fixed(total_picks)
        if not turn_info:
            return False
        
        return turn_info['team_id'] == self.my_team_id
    
    def analyze_team_needs(self, team_id):
        """Analyze what positions a team needs"""
        roster = self.team_rosters.get(team_id, [])
        
        # Count positions
        position_counts = {}
        for player in roster:
            pos = player.get('position', 'UNK')
            position_counts[pos] = position_counts.get(pos, 0) + 1
        
        # Standard needs
        needs = []
        
        # Early draft strategy (first 8 picks)
        if len(roster) < 8:
            if position_counts.get('RB', 0) < 2:
                needs.extend(['RB'] * (2 - position_counts.get('RB', 0)))
            if position_counts.get('WR', 0) < 2:
                needs.extend(['WR'] * (2 - position_counts.get('WR', 0)))
            if position_counts.get('QB', 0) < 1:
                needs.append('QB')
            if position_counts.get('TE', 0) < 1:
                needs.append('TE')
        else:
            # Later rounds - depth and specials
            if position_counts.get('RB', 0) < 3:
                needs.append('RB')
            if position_counts.get('WR', 0) < 3:
                needs.append('WR')
            if position_counts.get('QB', 0) < 2:
                needs.append('QB')
            if position_counts.get('K', 0) < 1:
                needs.append('K')
            if position_counts.get('D/ST', 0) < 1:
                needs.append('D/ST')
        
        return needs[:3]  # Top 3 needs
    
    def get_available_players(self):
        """Get available players (not yet drafted)"""
        drafted_player_ids = set()
        
        # Collect all drafted player IDs
        for roster in self.team_rosters.values():
            for player in roster:
                drafted_player_ids.add(player['player_id'])
        
        # Filter available players
        available = []
        for player_id, player_data in self.players_db.items():
            if player_id not in drafted_player_ids:
                # Only include skill position players and relevant positions
                position = player_data.get('position', '')
                if position in ['QB', 'RB', 'WR', 'TE', 'K', 'D/ST']:
                    available.append({
                        'player_id': player_id,
                        'name': player_data.get('full_name', 'Unknown'),
                        'position': position,
                        'team': player_data.get('team', 'FA'),
                        'fantasy_positions': player_data.get('fantasy_positions', [])
                    })
        
        return available
    
    def get_recommendations(self, for_team_id):
        """Get smart recommendations for a team"""
        if not for_team_id:
            return []
        
        available_players = self.get_available_players()
        team_needs = self.analyze_team_needs(for_team_id)
        
        if not available_players:
            return []
        
        recommendations = []
        
        # Recommend best available at each needed position
        for need in team_needs:
            position_players = [p for p in available_players if p['position'] == need]
            if position_players:
                best_at_position = position_players[0]
                recommendations.append({
                    'player': best_at_position,
                    'reason': f"Best {need} available (team need)",
                    'priority': 'high'
                })
        
        # Add some best overall regardless of position
        skill_positions = ['QB', 'RB', 'WR', 'TE']
        best_overall = [p for p in available_players if p['position'] in skill_positions][:3]
        
        for player in best_overall:
            if not any(rec['player']['player_id'] == player['player_id'] for rec in recommendations):
                recommendations.append({
                    'player': player,
                    'reason': "Best available player",
                    'priority': 'medium'
                })
        
        return recommendations[:5]
    
    def display_draft_status(self, new_picks, total_picks):
        """Display focused status with FIXED team identification"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        if new_picks:
            # Show new picks with FIXED team IDs
            for pick in new_picks:
                player_name = self.get_player_name(pick.get('player_id'))
                round_num = pick.get('round', '?')
                pick_num = pick.get('pick_no', '?')
                team_id = pick.get('team_id', 'Unknown')
                print(f"✅ Pick {pick_num}: Team {team_id} - {player_name}")
        
        # Check if it's your turn using FIXED logic
        if self.is_my_turn(total_picks):
            turn_info = self.get_whose_turn_fixed(total_picks)
            
            print(f"\n🎯 YOUR TURN! (Round {turn_info['round']}, Pick {turn_info['pick_number']})")
            print("=" * 50)
            
            if self.my_team_id:
                recommendations = self.get_recommendations(self.my_team_id)
                
                if recommendations:
                    print(f"💡 TOP RECOMMENDATIONS:")
                    for i, rec in enumerate(recommendations[:5], 1):
                        player = rec['player']
                        priority = "🔥" if rec['priority'] == 'high' else "💎"
                        print(f"   {priority} {i}. {player['name']} ({player['position']}) - {rec['reason']}")
                
                # Show your current roster
                if self.my_team_id in self.team_rosters:
                    roster = self.team_rosters[self.my_team_id]
                    if roster:
                        print(f"\n📋 Your current roster (Team {self.my_team_id}):")
                        for player in roster:
                            print(f"   Round {player['round']}: {player['name']} ({player['position']})")
                
                print("\n" + "=" * 50)
            else:
                print("❓ Could not identify your team")
        
        # Show waiting status with FIXED team display
        elif total_picks % 5 == 0 or not hasattr(self, '_last_status_time') or time.time() - self._last_status_time > 30:
            turn_info = self.get_whose_turn_fixed(total_picks)
            if turn_info:
                team_id = turn_info['team_id']
                pick_num = turn_info['pick_number']
                round_num = turn_info['round']
                
                # Check if it's a human or CPU
                is_human = any(user_id for user_id, slot in self.draft_order.items() if self.slot_to_roster.get(str(slot)) == team_id)
                human_indicator = "👤" if is_human else "🤖"
                
                print(f"⏳ Waiting... {human_indicator} Team {team_id}'s turn (Round {round_num}, Pick {pick_num})")
            self._last_status_time = time.time()
    
    def monitor_draft(self):
        """Main monitoring loop with FIXED logic"""
        print(f"🎯 FIXED SLEEPER DRAFT ASSISTANT")
        print("=" * 50)
        print(f"Draft ID: {self.draft_id}")
        
        # Get draft info
        draft_info = self.get_draft_info()
        if draft_info:
            print(f"Status: {draft_info.get('status', 'Unknown')}")
            print(f"Teams: {self.total_teams}")
            print(f"Rounds: {self.rounds}")
            print(f"Type: {'Snake' if self.snake_draft else 'Linear'}")
            
            if self.user_id:
                print(f"Your User ID: {self.user_id}")
                if self.my_team_id:
                    print(f"Your Team: #{self.my_team_id} (Draft Slot {self.my_draft_slot})")
                else:
                    print("⚠️  Could not identify your team")
            else:
                print("⚠️  No user ID provided or detected")
        
        print(f"\nMonitoring draft... You'll see recommendations when it's your turn.")
        print(f"Press Ctrl+C to stop\n")
        
        try:
            while True:
                new_picks, total_picks = self.get_current_picks()
                self.display_draft_status(new_picks, total_picks)
                
                time.sleep(2)  # Check every 2 seconds
                
        except KeyboardInterrupt:
            print(f"\n👋 Draft monitoring stopped")
            
            # Final summary with FIXED team IDs
            if self.team_rosters:
                print(f"\n📊 FINAL DRAFT SUMMARY:")
                for team_id, roster in self.team_rosters.items():
                    # Show if it's your team
                    is_you = team_id == self.my_team_id
                    team_label = f"Team {team_id}" + (" (YOU)" if is_you else "")
                    
                    print(f"\n{team_label} ({len(roster)} picks):")
                    for player in roster:
                        print(f"   Round {player['round']}: {player['name']} ({player['position']})")

def main():
    print("🏈 FF Draft Vibe - FIXED Sleeper Draft Assistant")
    print("=" * 55)
    print("Enter your Sleeper draft URL or just the draft ID")
    print("Example: https://sleeper.com/draft/nfl/1256093340819001344")
    print("Or just: 1256093340819001344")
    print()
    
    try:
        user_input = input("Draft URL or ID: ").strip()
        
        # Extract draft ID from URL if full URL provided
        if "sleeper.com/draft" in user_input:
            parts = user_input.split("/")
            draft_id = parts[-1].split("?")[0]
        else:
            draft_id = user_input
        
        if not draft_id:
            print("❌ No draft ID provided")
            return
        
        print(f"🎯 Using Draft ID: {draft_id}")
        
        # Ask for user ID (optional - will auto-detect if possible)
        user_id_input = input("Your User ID (optional, will auto-detect if possible): ").strip()
        user_id = user_id_input if user_id_input else None
        
        print()
        
        assistant = FixedSleeperDraftAssistant(draft_id, user_id)
        assistant.monitor_draft()
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except EOFError:
        print("❌ No input provided")
        return

if __name__ == "__main__":
    main()