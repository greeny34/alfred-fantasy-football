import requests
import json
from datetime import datetime

class SleeperDraftDebugger:
    def __init__(self, draft_id, user_id="352200144369963008"):
        self.draft_id = draft_id
        self.user_id = user_id
        
    def debug_draft_structure(self):
        """Comprehensive debug of Sleeper draft structure"""
        print("🔍 SLEEPER DRAFT STRUCTURE DEBUG")
        print("=" * 60)
        print(f"Draft ID: {self.draft_id}")
        print(f"User ID: {self.user_id}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 1. Get draft info
        print("1️⃣ DRAFT INFO ANALYSIS")
        print("-" * 30)
        draft_info = self.get_draft_info()
        
        if not draft_info:
            print("❌ Failed to get draft info - stopping debug")
            return
        
        # 2. Analyze draft order structure
        print("\n2️⃣ DRAFT ORDER ANALYSIS")
        print("-" * 30)
        self.analyze_draft_order(draft_info)
        
        # 3. Get and analyze picks
        print("\n3️⃣ PICKS ANALYSIS")
        print("-" * 30)
        picks = self.get_picks()
        if picks:
            self.analyze_picks(picks, draft_info)
        
        # 4. Team identification debug
        print("\n4️⃣ TEAM IDENTIFICATION DEBUG")
        print("-" * 35)
        self.debug_team_identification(draft_info, picks)
        
        # 5. Turn calculation debug
        print("\n5️⃣ TURN CALCULATION DEBUG")
        print("-" * 30)
        if picks:
            self.debug_turn_calculation(draft_info, picks)
    
    def get_draft_info(self):
        """Get draft information with detailed structure analysis"""
        try:
            url = f"https://api.sleeper.app/v1/draft/{self.draft_id}"
            response = requests.get(url)
            
            print(f"📡 API Call: {url}")
            print(f"🌐 Status Code: {response.status_code}")
            
            if response.status_code != 200:
                print(f"❌ Error: {response.status_code}")
                if response.status_code == 404:
                    print("   Draft not found - check the draft ID")
                return None
            
            draft_data = response.json()
            
            # Show overall structure
            print(f"✅ Draft data received")
            print(f"📊 Top-level keys: {list(draft_data.keys())}")
            
            # Analyze each key
            for key, value in draft_data.items():
                if isinstance(value, dict):
                    print(f"   📁 {key}: dict with {len(value)} keys {list(value.keys())[:5]}")
                elif isinstance(value, list):
                    print(f"   📋 {key}: list with {len(value)} items")
                    if value and isinstance(value[0], dict):
                        print(f"      Sample item keys: {list(value[0].keys())[:5]}")
                else:
                    print(f"   📄 {key}: {type(value).__name__} = {value}")
            
            return draft_data
            
        except Exception as e:
            print(f"❌ Exception getting draft info: {e}")
            return None
    
    def analyze_draft_order(self, draft_info):
        """Analyze the draft_order field structure"""
        draft_order = draft_info.get('draft_order')
        
        print(f"🎯 draft_order type: {type(draft_order)}")
        print(f"🎯 draft_order value: {draft_order}")
        
        if draft_order is None:
            print("❌ draft_order is None!")
            return
        
        if isinstance(draft_order, dict):
            print(f"📊 draft_order is a dict with {len(draft_order)} entries:")
            for user_id, team_id in draft_order.items():
                is_you = "👤 (YOU!)" if user_id == self.user_id else ""
                print(f"   User {user_id} -> Team {team_id} {is_you}")
        
        elif isinstance(draft_order, list):
            print(f"📋 draft_order is a list with {len(draft_order)} items:")
            for i, item in enumerate(draft_order):
                print(f"   Position {i+1}: {item} (type: {type(item)})")
                if item == self.user_id:
                    print(f"      👤 This is you! Your draft position is {i+1}")
        
        else:
            print(f"❓ Unexpected draft_order type: {type(draft_order)}")
        
        # Check other order-related fields
        print(f"\n🔍 Other order-related fields:")
        for key in ['slot_to_roster_id', 'roster_positions', 'settings']:
            if key in draft_info:
                value = draft_info[key]
                print(f"   {key}: {type(value)} = {value}")
    
    def get_picks(self):
        """Get draft picks with analysis"""
        try:
            url = f"https://api.sleeper.app/v1/draft/{self.draft_id}/picks"
            response = requests.get(url)
            
            print(f"📡 API Call: {url}")
            print(f"🌐 Status Code: {response.status_code}")
            
            if response.status_code != 200:
                print(f"❌ Error getting picks: {response.status_code}")
                return None
            
            picks = response.json()
            print(f"✅ Got {len(picks)} picks")
            
            return picks
            
        except Exception as e:
            print(f"❌ Exception getting picks: {e}")
            return None
    
    def analyze_picks(self, picks, draft_info):
        """Analyze pick structure and team assignments"""
        if not picks:
            print("❌ No picks to analyze")
            return
        
        print(f"📋 Analyzing {len(picks)} picks")
        
        # Show sample pick structure
        sample_pick = picks[0]
        print(f"📄 Sample pick structure:")
        for key, value in sample_pick.items():
            print(f"   {key}: {type(value).__name__} = {value}")
        
        # Analyze team assignments
        print(f"\n🏈 Team assignments in picks:")
        team_pick_counts = {}
        
        for pick in picks[:10]:  # Show first 10 picks
            picked_by = pick.get('picked_by', 'MISSING')
            roster_id = pick.get('roster_id', 'MISSING')
            round_num = pick.get('round', '?')
            pick_no = pick.get('pick_no', '?')
            player_id = pick.get('player_id', 'No player')
            
            # Count picks by team
            team_pick_counts[picked_by] = team_pick_counts.get(picked_by, 0) + 1
            
            print(f"   Pick {pick_no} (R{round_num}): picked_by='{picked_by}', roster_id='{roster_id}', player='{player_id}'")
        
        print(f"\n📊 Pick counts by team:")
        for team_id, count in team_pick_counts.items():
            print(f"   Team '{team_id}': {count} picks")
        
        # Check if picked_by matches roster_id
        mismatches = []
        for pick in picks:
            picked_by = pick.get('picked_by')
            roster_id = pick.get('roster_id')
            if picked_by != roster_id:
                mismatches.append({
                    'pick_no': pick.get('pick_no'),
                    'picked_by': picked_by,
                    'roster_id': roster_id
                })
        
        if mismatches:
            print(f"\n⚠️  picked_by vs roster_id mismatches:")
            for mismatch in mismatches[:5]:
                print(f"   Pick {mismatch['pick_no']}: picked_by='{mismatch['picked_by']}' vs roster_id='{mismatch['roster_id']}'")
        else:
            print(f"✅ picked_by and roster_id match for all picks")
    
    def debug_team_identification(self, draft_info, picks):
        """Debug team identification for the user"""
        print(f"🔍 Looking for user {self.user_id} in draft...")
        
        # Method 1: Check draft_order
        draft_order = draft_info.get('draft_order', {})
        print(f"\n📋 Method 1 - draft_order lookup:")
        print(f"   draft_order type: {type(draft_order)}")
        
        if isinstance(draft_order, dict):
            if self.user_id in draft_order:
                team_id = draft_order[self.user_id]
                print(f"   ✅ Found in draft_order: User {self.user_id} -> Team {team_id}")
            else:
                print(f"   ❌ User {self.user_id} NOT found in draft_order")
                print(f"   Available user IDs: {list(draft_order.keys())}")
        
        elif isinstance(draft_order, list):
            try:
                position = draft_order.index(self.user_id)
                print(f"   ✅ Found in draft_order list at position {position + 1}")
                print(f"   This means you are team #{position + 1}")
            except ValueError:
                print(f"   ❌ User {self.user_id} NOT found in draft_order list")
                print(f"   Draft order: {draft_order}")
        
        # Method 2: Check slot_to_roster_id if available
        slot_to_roster = draft_info.get('slot_to_roster_id', {})
        if slot_to_roster:
            print(f"\n📋 Method 2 - slot_to_roster_id:")
            print(f"   slot_to_roster_id: {slot_to_roster}")
            
            # Try to find user through reverse lookup
            for slot, roster_id in slot_to_roster.items():
                print(f"   Slot {slot} -> Roster {roster_id}")
        
        # Method 3: Check other user-related fields
        print(f"\n📋 Method 3 - Other user fields:")
        user_fields = ['owners', 'users', 'league_id', 'creator']
        for field in user_fields:
            if field in draft_info:
                value = draft_info[field]
                print(f"   {field}: {type(value)} = {value}")
                if isinstance(value, list) and self.user_id in value:
                    print(f"      👤 Found user {self.user_id} in {field}")
        
        # Method 4: Check if user made any picks
        if picks:
            print(f"\n📋 Method 4 - User's picks analysis:")
            user_picks = [p for p in picks if p.get('picked_by') == self.user_id]
            print(f"   Picks made by user {self.user_id}: {len(user_picks)}")
            
            if user_picks:
                sample_pick = user_picks[0]
                team_id = sample_pick.get('picked_by')
                roster_id = sample_pick.get('roster_id')
                print(f"   ✅ User is team '{team_id}' (roster_id: '{roster_id}')")
            else:
                print(f"   ❌ No picks found for user {self.user_id}")
                
                # Show who did make picks
                pickers = set(p.get('picked_by') for p in picks)
                print(f"   Teams that made picks: {sorted(list(pickers))}")
    
    def debug_turn_calculation(self, draft_info, picks):
        """Debug turn calculation logic"""
        print(f"🎯 Turn calculation debug")
        
        # Get draft settings
        settings = draft_info.get('settings', {})
        total_teams = settings.get('teams', 10)
        total_rounds = settings.get('rounds', 16)
        draft_type = draft_info.get('type', 'unknown')
        is_snake = draft_type == 'snake'
        
        print(f"   Teams: {total_teams}")
        print(f"   Rounds: {total_rounds}")
        print(f"   Type: {draft_type} (snake: {is_snake})")
        
        total_picks = len(picks)
        print(f"   Total picks made: {total_picks}")
        
        # Calculate current turn
        if total_picks >= total_teams * total_rounds:
            print(f"   ✅ Draft complete!")
            return
        
        # Current round and position
        current_round = (total_picks // total_teams) + 1
        pick_in_round = total_picks % total_teams
        
        print(f"   Current round: {current_round}")
        print(f"   Pick in round: {pick_in_round}")
        
        # Calculate who should pick next
        if is_snake and current_round % 2 == 0:
            # Even rounds reverse for snake
            next_team_slot = total_teams - pick_in_round
        else:
            # Odd rounds or linear draft
            next_team_slot = pick_in_round + 1
        
        print(f"   Next team slot: {next_team_slot}")
        
        # Try to map slot to actual team
        draft_order = draft_info.get('draft_order', {})
        if isinstance(draft_order, dict):
            # Find team by slot (reverse lookup)
            slot_to_user = {v: k for k, v in draft_order.items()}
            if next_team_slot in slot_to_user:
                next_user = slot_to_user[next_team_slot]
                is_you = next_user == self.user_id
                print(f"   Next picker: User {next_user} (Team {next_team_slot}) {'👤 YOU!' if is_you else ''}")
            else:
                print(f"   ❌ Could not find user for team slot {next_team_slot}")
        
        elif isinstance(draft_order, list):
            if 0 <= next_team_slot - 1 < len(draft_order):
                next_user = draft_order[next_team_slot - 1]
                is_you = next_user == self.user_id
                print(f"   Next picker: User {next_user} (Position {next_team_slot}) {'👤 YOU!' if is_you else ''}")
        
        # Show recent picks to verify
        print(f"\n📋 Last 5 picks for verification:")
        for pick in picks[-5:]:
            round_num = pick.get('round', '?')
            pick_no = pick.get('pick_no', '?')
            picked_by = pick.get('picked_by', 'Unknown')
            player_id = pick.get('player_id', 'No player')
            print(f"   Pick {pick_no} (R{round_num}): Team '{picked_by}' -> Player {player_id}")

def main():
    """Main debug function"""
    print("🏈 SLEEPER DRAFT STRUCTURE DEBUGGER")
    print("=" * 50)
    
    # Use the problematic draft ID from the user's issue
    draft_id = "1256139365948604416"
    user_id = "352200144369963008"
    
    print(f"🎯 Debugging Draft ID: {draft_id}")
    print(f"👤 User ID: {user_id}")
    print()
    
    debugger = SleeperDraftDebugger(draft_id, user_id)
    debugger.debug_draft_structure()
    
    print(f"\n" + "=" * 50)
    print(f"🔧 DEBUGGING COMPLETE")
    print(f"=" * 50)
    
    print(f"\n💡 Key things to check from this output:")
    print(f"   1. Does draft_order contain your user ID?")
    print(f"   2. What format is draft_order (dict vs list)?")
    print(f"   3. Are team IDs in picks empty or wrong?")
    print(f"   4. Does turn calculation match who actually picked?")
    print(f"   5. Can we find your team through any method?")

if __name__ == "__main__":
    main()