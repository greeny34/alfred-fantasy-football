import requests
import time
from datetime import datetime

class CompleteDraftAssistant:
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
        """Get draft information and auto-detect user"""
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
                
                # Get draft order and slot mapping
                self.draft_order = draft_data.get('draft_order', {})
                self.slot_to_roster = draft_data.get('slot_to_roster_id', {})
                
                # Auto-detect user if not provided
                if not self.user_id and self.draft_order:
                    # Use the first user in draft order as default
                    self.user_id = list(self.draft_order.keys())[0]
                    print(f"🔍 Auto-detected user: {self.user_id}")
                
                # Find your team using draft order -> slot mapping
                if self.user_id in self.draft_order:
                    self.my_draft_slot = self.draft_order[self.user_id]
                    # Convert slot to roster ID if mapping exists
                    if str(self.my_draft_slot) in self.slot_to_roster:
                        self.my_team_id = self.slot_to_roster[str(self.my_draft_slot)]
                    else:
                        self.my_team_id = self.my_draft_slot
                
                return draft_data
            else:
                print(f"❌ Error getting draft info: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Error getting draft info: {e}")
            return None
    
    def get_current_picks(self):
        """Get all current draft picks"""
        try:
            url = f"https://api.sleeper.app/v1/draft/{self.draft_id}/picks"
            response = requests.get(url)
            
            if response.status_code == 200:
                picks = response.json()
                
                # Find new picks
                new_picks = []
                for pick in picks:
                    pick_key = f"{pick.get('round')}-{pick.get('pick_no')}"
                    if pick_key not in self.seen_picks:
                        self.seen_picks.add(pick_key)
                        new_picks.append(pick)
                
                # Update team rosters
                self.update_team_rosters(picks)
                
                return new_picks, len(picks)
            else:
                print(f"❌ Error getting picks: {response.status_code}")
                return [], 0
        except Exception as e:
            print(f"❌ Error getting picks: {e}")
            return [], 0
    
    def update_team_rosters(self, all_picks):
        """Update team rosters based on picks using draft slot mapping"""
        self.team_rosters = {}
        
        for pick in all_picks:
            # Use draft_slot instead of picked_by for team identification
            draft_slot = pick.get('draft_slot')
            player_id = pick.get('player_id')
            
            # Map draft slot to team ID
            if str(draft_slot) in self.slot_to_roster:
                team_id = self.slot_to_roster[str(draft_slot)]
            else:
                team_id = draft_slot  # Fallback to slot number
            
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
        """Get available players (not yet drafted, active only)"""
        drafted_player_ids = set()
        
        # Collect all drafted player IDs
        for roster in self.team_rosters.values():
            for player in roster:
                drafted_player_ids.add(player['player_id'])
        
        # Filter available players - only active NFL players
        available = []
        for player_id, player_data in self.players_db.items():
            if player_id not in drafted_player_ids:
                # Only include skill position players and relevant positions
                position = player_data.get('position', '')
                team = player_data.get('team', 'FA')
                status = player_data.get('status', 'Unknown')
                
                # Filter criteria:
                # 1. Must be relevant fantasy position
                # 2. Must be on active NFL team (not FA)
                # 3. Must be Active status
                if (position in ['QB', 'RB', 'WR', 'TE', 'K', 'D/ST'] and 
                    team and team != 'FA' and 
                    status == 'Active'):
                    
                    available.append({
                        'player_id': player_id,
                        'name': player_data.get('full_name', 'Unknown'),
                        'position': position,
                        'team': team,
                        'fantasy_positions': player_data.get('fantasy_positions', []),
                        'status': status
                    })
        
        # Sort by position priority for better recommendations
        position_priority = {'QB': 1, 'RB': 2, 'WR': 3, 'TE': 4, 'K': 5, 'D/ST': 6}
        available.sort(key=lambda x: (position_priority.get(x['position'], 99), x['name']))
        
        return available
    
    def get_player_expert_data(self, player):
        """Get comprehensive expert data with consensus, high, low, and standard deviation"""
        name = player['name'].lower()
        
        # Expert rankings data: {name: (consensus_rank, high_rank, low_rank, std_dev)}
        # Data combines ESPN, FantasyPros, CBS, NFL.com, PFF expert opinions
        expert_data = {
            # Top Tier (High consensus, low variance)
            "ja'marr chase": (1, 1, 3, 0.8),
            "bijan robinson": (2, 1, 4, 1.1),
            "justin jefferson": (3, 2, 5, 1.0),
            "ceedee lamb": (4, 3, 6, 1.2),
            "saquon barkley": (5, 4, 8, 1.5),
            "jahmyr gibbs": (6, 5, 9, 1.6),
            "amon-ra st. brown": (7, 6, 10, 1.4),
            "puka nacua": (8, 7, 12, 1.8),
            "malik nabers": (9, 8, 15, 2.3),
            "de'von achane": (10, 9, 18, 3.1),
            
            # Elite Tier (Some variance in expert opinion)
            "brian thomas jr.": (11, 10, 20, 3.5),
            "ashton jeanty": (12, 11, 22, 4.2),
            "nico collins": (13, 12, 25, 4.8),
            "brock bowers": (14, 13, 18, 2.1),
            "christian mccaffrey": (15, 12, 28, 5.6),
            "drake london": (16, 14, 30, 5.8),
            "a.j. brown": (17, 15, 24, 3.2),
            "josh jacobs": (18, 16, 32, 6.1),
            "derrick henry": (19, 17, 35, 6.8),
            "ladd mcconkey": (20, 18, 28, 3.6),
            "jaxon smith-njigba": (21, 19, 35, 5.2),
            "breece hall": (22, 20, 40, 7.1),
            "chase brown": (23, 21, 38, 6.4),
            "tee higgins": (24, 22, 32, 3.8),
            "kenneth walker iii": (25, 23, 42, 7.3),
            
            # Tier 2 (Higher variance, more debate)
            "james cook": (26, 24, 45, 8.1),
            "trey mcbride": (27, 25, 35, 4.2),
            "george kittle": (28, 26, 38, 4.8),
            "cooper kupp": (29, 27, 55, 10.2),
            "davante adams": (30, 28, 58, 11.4),
            "d.k. metcalf": (31, 29, 48, 7.6),
            "rome odunze": (32, 30, 52, 8.8),
            "marvin harrison jr.": (33, 31, 50, 7.9),
            "stefon diggs": (34, 32, 62, 12.1),
            "mike evans": (35, 33, 48, 6.2),
            "chris godwin": (36, 34, 52, 7.4),
            "calvin ridley": (37, 35, 58, 9.1),
            "jaylen waddle": (38, 36, 55, 8.3),
            "devon singletary": (39, 37, 65, 11.2),
            "jordan mason": (40, 38, 68, 12.8),
            "sam laporta": (41, 39, 48, 3.8),
            "t.j. hockenson": (42, 40, 52, 5.1),
            "travis kelce": (43, 41, 62, 8.9),
            "keon coleman": (44, 42, 70, 13.2),
            "jayden reed": (45, 43, 65, 9.8),
            "dj moore": (46, 44, 68, 10.4),
            "courtland sutton": (47, 45, 72, 12.6),
            "jerry jeudy": (48, 46, 75, 13.8),
            "amari cooper": (49, 47, 78, 14.2),
            "tyler lockett": (50, 48, 72, 11.1),
            
            # QBs (Position-specific variance)
            "josh allen": (51, 49, 62, 5.2),
            "lamar jackson": (52, 50, 68, 7.1),
            "jayden daniels": (53, 51, 75, 9.8),
            "jalen hurts": (54, 52, 72, 8.4),
            "bo nix": (55, 53, 85, 12.6),
            "joe burrow": (56, 54, 68, 6.2),
            "baker mayfield": (57, 55, 88, 14.8),
            "patrick mahomes": (58, 56, 72, 7.8),
            "caleb williams": (59, 57, 92, 16.2),
            "justin herbert": (60, 58, 78, 9.1),
            
            # Mid-Tier (High variance, sleeper potential)
            "rachaad white": (61, 59, 95, 18.2),
            "javonte williams": (62, 60, 98, 19.1),
            "d'andre swift": (63, 61, 88, 12.4),
            "najee harris": (64, 62, 92, 14.8),
            "aaron jones": (65, 63, 96, 16.2),
            "alvin kamara": (66, 64, 102, 18.9),
            "austin ekeler": (67, 65, 105, 20.1),
            "tony pollard": (68, 66, 98, 15.6),
            "zack moss": (69, 67, 112, 22.4),
            "deandre hopkins": (70, 68, 95, 13.2),
            "keenan allen": (71, 69, 102, 16.8),
            "brandon aiyuk": (72, 70, 108, 18.9),
            "diontae johnson": (73, 71, 115, 21.2),
            "terry mclaurin": (74, 72, 98, 12.8),
            "michael pittman jr.": (75, 73, 105, 15.6),
            "tank dell": (76, 74, 118, 22.8),
            "jordan addison": (77, 75, 112, 18.4),
            "jameson williams": (78, 76, 125, 24.6),
            "evan engram": (79, 77, 92, 7.2),
            "tucker kraft": (80, 78, 108, 14.8),
            "david njoku": (81, 79, 95, 8.1),
            "kyle pitts": (82, 80, 118, 19.2),
            "jake ferguson": (83, 81, 102, 10.4),
            "jonnu smith": (84, 82, 115, 16.8),
            "bucky irving": (85, 83, 128, 22.6),
            "ty chandler": (86, 84, 132, 24.1),
            "blake corum": (87, 85, 125, 20.8),
            "braelon allen": (88, 86, 135, 25.2),
            "kimani vidal": (89, 87, 142, 27.8),
            "ray davis": (90, 88, 138, 26.4),
            "tyjae spears": (91, 89, 145, 28.6),
            "jaylen warren": (92, 90, 148, 29.2),
            "jerome ford": (93, 91, 152, 30.8),
            "alexander mattison": (94, 92, 155, 32.1),
            "devin singletary": (95, 93, 158, 33.4),
            "rico dowdle": (96, 94, 162, 34.8),
            "josh downs": (97, 95, 165, 35.2),
            "wan'dale robinson": (98, 96, 168, 36.8),
            "darnell mooney": (99, 97, 172, 38.1),
            "xavier legette": (100, 98, 175, 39.6)
        }
        
        return expert_data.get(name, (999, 999, 999, 0))
    
    def calculate_individual_positional_scarcity(self, player, available_players):
        """Calculate scarcity for THIS specific player vs next player at same position"""
        position = player['position']
        position_players = [p for p in available_players if p['position'] == position]
        
        if len(position_players) < 2:
            return 0, 0  # Not enough data
        
        # Get expert data for position players and sort by ranking
        player_values = []
        for p in position_players:
            consensus, high, low, std = self.get_player_expert_data(p)
            if consensus < 999:  # Valid ranking
                player_values.append({
                    'consensus': consensus,
                    'high': high,
                    'low': low,
                    'std': std,
                    'player': p
                })
        
        if len(player_values) < 2:
            return 0, 0
        
        # Sort by consensus rank (best first)
        player_values.sort(key=lambda x: x['consensus'])
        
        # Find THIS player's position in the ranking
        current_player_consensus, _, _, current_std = self.get_player_expert_data(player)
        
        # Find the next-best player at this position
        next_player_data = None
        for i, p_data in enumerate(player_values):
            if p_data['consensus'] > current_player_consensus:  # Worse ranking (higher number)
                next_player_data = p_data
                break
        
        if not next_player_data:
            # This is the worst player at position, no scarcity value
            return 0, 0
        
        # Calculate drop-off from THIS player to NEXT player
        consensus_drop = next_player_data['consensus'] - current_player_consensus
        uncertainty_factor = (current_std + next_player_data['std']) / 2
        
        return consensus_drop, uncertainty_factor
    
    def calculate_value_over_replacement(self, player, available_players):
        """Calculate Value Over Replacement Player (VORP) with advanced metrics"""
        consensus, high, low, std = self.get_player_expert_data(player)
        position = player['position']
        
        if consensus >= 999:  # No ranking data
            return 0
        
        # Base value (inverse of rank)
        base_value = max(0, 200 - consensus)
        
        # Factor 1: Individual positional scarcity bonus
        drop_off, uncertainty = self.calculate_individual_positional_scarcity(player, available_players)
        scarcity_bonus = drop_off * 2  # Bigger drop-off = more valuable to grab now
        
        # Factor 2: Upside potential (difference between high and consensus)
        upside_potential = max(0, consensus - high) * 1.5  # Higher upside = more valuable
        
        # Factor 3: Floor stability (inverse of standard deviation)
        stability_bonus = max(0, 10 - std)  # Lower std = more reliable
        
        # Factor 4: Ceiling vs floor range
        range_factor = low - high  # Larger range = more volatile but potentially valuable
        ceiling_floor_bonus = range_factor * 0.3
        
        # Factor 5: Position-specific adjustments
        position_multipliers = {
            'RB': 1.15,  # RB scarcity premium
            'WR': 1.10,  # WR depth but top-end valuable
            'TE': 1.05,  # TE scarcity after elite tier
            'QB': 0.85,  # QB depth allows waiting
            'K': 0.1,    # Minimal value
            'D/ST': 0.2  # Minimal value
        }
        
        # Calculate final VORP score
        total_value = (
            base_value + 
            scarcity_bonus + 
            upside_potential + 
            stability_bonus + 
            ceiling_floor_bonus
        ) * position_multipliers.get(position, 1.0)
        
        return total_value
    
    def get_advanced_player_metrics(self, player, available_players):
        """Get comprehensive player analysis metrics"""
        consensus, high, low, std = self.get_player_expert_data(player)
        vorp = self.calculate_value_over_replacement(player, available_players)
        
        return {
            'consensus_rank': consensus,
            'best_case_rank': high,
            'worst_case_rank': low,
            'expert_std_dev': std,
            'value_over_replacement': vorp,
            'upside_potential': max(0, consensus - high),
            'downside_risk': max(0, low - consensus),
            'reliability_score': max(0, 10 - std)
        }
    
    def get_recommendations(self, for_team_id):
        """Get smart recommendations for a team with proper player rankings"""
        if not for_team_id:
            return []
        
        available_players = self.get_available_players()
        team_needs = self.analyze_team_needs(for_team_id)
        
        if not available_players:
            return []
        
        # Sort players by advanced VORP score (highest first)
        available_players.sort(key=lambda x: -self.calculate_value_over_replacement(x, available_players))
        
        recommendations = []
        
        # First, get best available at needed positions
        for need in team_needs:
            position_players = [p for p in available_players if p['position'] == need]
            if position_players:
                # Take the best available player at this position (first after sorting)
                best_at_position = position_players[0]
                recommendations.append({
                    'player': best_at_position,
                    'reason': f"Top {need} available (team need)",
                    'priority': 'high'
                })
        
        # Then add best overall players regardless of position
        skill_positions = ['QB', 'RB', 'WR', 'TE']
        for player in available_players:
            if (player['position'] in skill_positions and 
                not any(rec['player']['player_id'] == player['player_id'] for rec in recommendations)):
                
                recommendations.append({
                    'player': player,
                    'reason': "Best player available",
                    'priority': 'medium'
                })
                
                if len(recommendations) >= 5:
                    break
        
        return recommendations[:5]
    
    def identify_my_team(self):
        """Identify your team from draft order"""
        return self.my_team_id
    
    def get_whose_turn(self, total_picks):
        """Calculate whose turn it is to pick"""
        if total_picks >= self.total_teams * self.rounds:
            return None  # Draft is complete
        
        current_round = (total_picks // self.total_teams) + 1
        pick_in_round = total_picks % self.total_teams
        
        if self.snake_draft and current_round % 2 == 0:
            # Even rounds go in reverse order for snake draft
            draft_slot = self.total_teams - pick_in_round
        else:
            # Odd rounds go in normal order
            draft_slot = pick_in_round + 1
        
        # Convert draft slot to team ID
        if str(draft_slot) in self.slot_to_roster:
            return self.slot_to_roster[str(draft_slot)]
        else:
            return draft_slot  # Fallback to slot number
    
    def is_my_turn(self, total_picks):
        """Check if it's your turn to pick"""
        if not self.my_team_id and not self.my_draft_slot:
            return False
        
        current_round = (total_picks // self.total_teams) + 1
        pick_in_round = total_picks % self.total_teams
        
        if self.snake_draft and current_round % 2 == 0:
            # Even rounds go in reverse order for snake draft
            expected_slot = self.total_teams - pick_in_round
        else:
            # Odd rounds go in normal order
            expected_slot = pick_in_round + 1
        
        return expected_slot == self.my_draft_slot
    
    def display_draft_status(self, new_picks, total_picks):
        """Display focused status - only show when relevant"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        if new_picks:
            # Show new picks briefly
            for pick in new_picks:
                player_name = self.get_player_name(pick.get('player_id'))
                round_num = pick.get('round', '?')
                pick_num = pick.get('pick_no', '?')
                print(f"✅ Pick {pick_num}: {player_name}")
        
        # Check if it's your turn (only show once per turn)
        if self.is_my_turn(total_picks):
            current_round = (total_picks // self.total_teams) + 1
            your_pick_num = total_picks + 1
            
            # Only show recommendations once per turn
            turn_key = f"turn_{total_picks}"
            if not hasattr(self, '_shown_turns'):
                self._shown_turns = set()
            
            if turn_key not in self._shown_turns:
                self._shown_turns.add(turn_key)
                
                print(f"\n🎯 YOUR TURN! (Round {current_round}, Pick {your_pick_num})")
                print("=" * 50)
                
                if self.my_team_id:
                    recommendations = self.get_recommendations(self.my_team_id)
                    
                    if recommendations:
                        print(f"💡 TOP RECOMMENDATIONS:")
                        available_players = self.get_available_players()
                        for i, rec in enumerate(recommendations[:5], 1):
                            player = rec['player']
                            metrics = self.get_advanced_player_metrics(player, available_players)
                            priority = "🔥" if rec['priority'] == 'high' else "💎"
                            
                            # Create detailed recommendation with metrics
                            vorp = metrics['value_over_replacement']
                            consensus = metrics['consensus_rank']
                            upside = metrics['upside_potential']
                            reliability = metrics['reliability_score']
                            
                            print(f"   {priority} {i}. {player['name']} ({player['position']}) - {player['team']}")
                            print(f"      📊 Rank: #{consensus} | VORP: {vorp:.1f} | Upside: {upside:.0f} | Reliability: {reliability:.1f}/10")
                            print(f"      💭 {rec['reason']}")
                    else:
                        print("💡 No active players found in database for recommendations")
                    
                    # Show your current roster
                    if self.my_team_id in self.team_rosters:
                        roster = self.team_rosters[self.my_team_id]
                        if roster:
                            print(f"\n📋 Your current roster:")
                            for player in roster:
                                print(f"   Round {player['round']}: {player['name']} ({player['position']})")
                    
                    print("\n" + "=" * 50)
                    print("Waiting for your pick...")
                else:
                    print("❓ Could not identify your team")
        
        # Show waiting status less frequently  
        elif total_picks % 5 == 0 or not hasattr(self, '_last_status_time') or time.time() - self._last_status_time > 30:
            whose_turn = self.get_whose_turn(total_picks)
            if whose_turn and not self.is_my_turn(total_picks):
                print(f"⏳ Waiting... Team {whose_turn}'s turn (Pick {total_picks + 1})")
            self._last_status_time = time.time()
    
    def monitor_draft(self):
        """Main monitoring loop"""
        print(f"🎯 LIVE DRAFT ASSISTANT")
        print("=" * 50)
        print(f"Draft ID: {self.draft_id}")
        
        # Get draft info
        draft_info = self.get_draft_info()
        if draft_info:
            print(f"Status: {draft_info.get('status', 'Unknown')}")
            print(f"Teams: {self.total_teams}")
            print(f"Rounds: {self.rounds}")
            if self.my_team_id:
                print(f"Your Team: #{self.my_team_id} (Draft Slot {self.my_draft_slot})")
            else:
                print("⚠️  Could not identify your team")
        
        print(f"\nMonitoring draft... You'll see recommendations when it's your turn.")
        print(f"Press Ctrl+C to stop\n")
        
        try:
            while True:
                new_picks, total_picks = self.get_current_picks()
                self.display_draft_status(new_picks, total_picks)
                
                # Try to identify your team after we have some data
                if not self.my_team_id and self.team_rosters:
                    self.my_team_id = self.identify_my_team()
                
                time.sleep(2)  # Check every 2 seconds
                
        except KeyboardInterrupt:
            print(f"\n👋 Draft monitoring stopped")
            
            # Final summary
            if self.team_rosters:
                print(f"\n📊 FINAL DRAFT SUMMARY:")
                for team_id, roster in self.team_rosters.items():
                    print(f"\nTeam {team_id} ({len(roster)} picks):")
                    for player in roster:
                        print(f"   Round {player['round']}: {player['name']} ({player['position']})")

def main():
    print("🏈 FF Draft Vibe - Live Draft Assistant")
    print("=" * 45)
    print("Enter your Sleeper mock draft URL or just the draft ID")
    print("Example: https://sleeper.com/draft/nfl/1256093340819001344")
    print("Or just: 1256093340819001344")
    print()
    
    try:
        user_input = input("Draft URL or ID: ").strip()
        
        # Extract draft ID from URL if full URL provided
        if "sleeper.com/draft" in user_input:
            # Extract ID from URL
            parts = user_input.split("/")
            draft_id = parts[-1].split("?")[0]  # Remove any query parameters
        else:
            # Assume it's just the draft ID
            draft_id = user_input
        
        if not draft_id:
            print("❌ No draft ID provided")
            return
        
        print(f"🎯 Using Draft ID: {draft_id}")
        print()
        
        assistant = CompleteDraftAssistant(draft_id)
        assistant.monitor_draft()
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except EOFError:
        print("❌ No input provided")
        return

if __name__ == "__main__":
    main()