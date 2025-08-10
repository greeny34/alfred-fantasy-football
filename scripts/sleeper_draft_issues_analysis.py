"""
SLEEPER DRAFT ISSUES ANALYSIS AND FIXES
======================================

Based on the debug output, here are the critical issues found:

🔴 ISSUE #1: User Not in Draft Order
- Your user ID (352200144369963008) is NOT in the draft_order
- draft_order only contains: {'1256092194675113984': 4}
- This explains "Could not identify your team"

🔴 ISSUE #2: Empty Team IDs in Picks
- Most picks have picked_by='' (empty string)
- Only one user (1256092194675113984) has actual picks assigned
- This explains "Team " (empty team ID) in the display

🔴 ISSUE #3: Wrong User ID Being Used
- The draft only knows about user '1256092194675113984'
- You're using user ID '352200144369963008' but this user isn't in this draft
- This is likely a mock draft where you need the correct participant ID

🔴 ISSUE #4: roster_id is None
- All picks have roster_id=None instead of actual team numbers
- Should use slot_to_roster_id mapping instead

ROOT CAUSE:
This appears to be a mock draft where:
1. Most teams are CPU/auto-drafted (hence empty picked_by)
2. Only one human user is actually participating
3. You're using the wrong user ID for this specific draft

SOLUTIONS:
"""

import requests
import json

class SleeperDraftFixer:
    def __init__(self, draft_id):
        self.draft_id = draft_id
        
    def get_draft_info(self):
        """Get draft info"""
        url = f"https://api.sleeper.app/v1/draft/{self.draft_id}"
        response = requests.get(url)
        return response.json() if response.status_code == 200 else None
    
    def get_picks(self):
        """Get draft picks"""
        url = f"https://api.sleeper.app/v1/draft/{self.draft_id}/picks"
        response = requests.get(url)
        return response.json() if response.status_code == 200 else None
    
    def solution_1_find_correct_user_id(self):
        """Solution 1: Find the correct user ID for this draft"""
        print("🔧 SOLUTION 1: Find Correct User ID")
        print("-" * 40)
        
        draft_info = self.get_draft_info()
        if not draft_info:
            print("❌ Could not get draft info")
            return None
        
        draft_order = draft_info.get('draft_order', {})
        print(f"Available user IDs in this draft:")
        
        for user_id, team_slot in draft_order.items():
            print(f"   User ID: {user_id} -> Team Slot: {team_slot}")
        
        if len(draft_order) == 1:
            correct_user_id = list(draft_order.keys())[0]
            print(f"\n✅ Use this user ID instead: {correct_user_id}")
            return correct_user_id
        else:
            print(f"❌ Multiple or no users found")
            return None
    
    def solution_2_handle_empty_team_ids(self):
        """Solution 2: Show how to handle empty team IDs"""
        print("\n🔧 SOLUTION 2: Handle Empty Team IDs")
        print("-" * 40)
        
        draft_info = self.get_draft_info()
        picks = self.get_picks()
        
        if not draft_info or not picks:
            print("❌ Could not get draft data")
            return
        
        slot_to_roster = draft_info.get('slot_to_roster_id', {})
        print(f"slot_to_roster_id mapping: {slot_to_roster}")
        
        # Show how to map draft_slot to team
        print(f"\nFixed team assignment logic:")
        print(f"for pick in picks:")
        print(f"    draft_slot = pick.get('draft_slot')")
        print(f"    team_id = slot_to_roster.get(str(draft_slot), draft_slot)")
        print(f"    # This gives proper team numbers instead of empty strings")
        
        # Demonstrate with actual data
        print(f"\nExample fixes for first 5 picks:")
        for i, pick in enumerate(picks[:5]):
            draft_slot = pick.get('draft_slot')
            picked_by = pick.get('picked_by', 'EMPTY')
            team_id = slot_to_roster.get(str(draft_slot), draft_slot)
            
            print(f"   Pick {i+1}: draft_slot={draft_slot}, picked_by='{picked_by}' -> Fixed team_id={team_id}")
    
    def solution_3_fix_turn_calculation(self):
        """Solution 3: Fix turn calculation using draft_slot"""
        print("\n🔧 SOLUTION 3: Fix Turn Calculation")
        print("-" * 40)
        
        draft_info = self.get_draft_info()
        picks = self.get_picks()
        
        if not draft_info or not picks:
            return
        
        settings = draft_info.get('settings', {})
        total_teams = settings.get('teams', 10)
        is_snake = draft_info.get('type') == 'snake'
        
        total_picks = len(picks)
        current_round = (total_picks // total_teams) + 1
        pick_in_round = total_picks % total_teams
        
        if is_snake and current_round % 2 == 0:
            next_draft_slot = total_teams - pick_in_round
        else:
            next_draft_slot = pick_in_round + 1
        
        print(f"Current calculation:")
        print(f"   Total picks: {total_picks}")
        print(f"   Current round: {current_round}")
        print(f"   Pick in round: {pick_in_round}")
        print(f"   Next draft slot: {next_draft_slot}")
        
        # Map to roster ID
        slot_to_roster = draft_info.get('slot_to_roster_id', {})
        next_team_id = slot_to_roster.get(str(next_draft_slot), next_draft_slot)
        
        print(f"   Next team ID: {next_team_id}")
        
        # Check if this matches draft_order
        draft_order = draft_info.get('draft_order', {})
        user_for_team = None
        for user_id, team_slot in draft_order.items():
            if team_slot == next_draft_slot:
                user_for_team = user_id
                break
        
        if user_for_team:
            print(f"   Next picker: User {user_for_team}")
        else:
            print(f"   Next picker: CPU/Auto (Team {next_team_id})")
    
    def solution_4_create_fixed_assistant(self):
        """Solution 4: Create code for fixed draft assistant"""
        print("\n🔧 SOLUTION 4: Fixed Draft Assistant Code")
        print("-" * 45)
        
        fixed_code = '''
def get_whose_turn_fixed(draft_info, picks):
    """Fixed version of whose turn calculation"""
    settings = draft_info.get('settings', {})
    total_teams = settings.get('teams', 10)
    total_rounds = settings.get('rounds', 16)
    is_snake = draft_info.get('type') == 'snake'
    
    total_picks = len(picks)
    
    if total_picks >= total_teams * total_rounds:
        return None  # Draft complete
    
    current_round = (total_picks // total_teams) + 1
    pick_in_round = total_picks % total_teams
    
    if is_snake and current_round % 2 == 0:
        next_draft_slot = total_teams - pick_in_round
    else:
        next_draft_slot = pick_in_round + 1
    
    # Map draft slot to roster ID
    slot_to_roster = draft_info.get('slot_to_roster_id', {})
    team_id = slot_to_roster.get(str(next_draft_slot), next_draft_slot)
    
    return {
        'team_id': team_id,
        'draft_slot': next_draft_slot,
        'round': current_round,
        'pick_in_round': pick_in_round + 1
    }

def identify_user_team_fixed(draft_info, user_id):
    """Fixed version of team identification"""
    draft_order = draft_info.get('draft_order', {})
    
    if user_id in draft_order:
        draft_slot = draft_order[user_id]
        
        # Map to roster ID
        slot_to_roster = draft_info.get('slot_to_roster_id', {})
        team_id = slot_to_roster.get(str(draft_slot), draft_slot)
        
        return {
            'team_id': team_id,
            'draft_slot': draft_slot,
            'found': True
        }
    
    return {'found': False}

def assign_picks_to_teams_fixed(picks, draft_info):
    """Fixed version of pick team assignment"""
    slot_to_roster = draft_info.get('slot_to_roster_id', {})
    
    for pick in picks:
        # Use draft_slot to determine team instead of picked_by
        draft_slot = pick.get('draft_slot')
        if draft_slot:
            pick['team_id'] = slot_to_roster.get(str(draft_slot), draft_slot)
        else:
            pick['team_id'] = 'Unknown'
    
    return picks
        '''
        
        print(fixed_code)

def main():
    """Run all solutions"""
    print("🏈 SLEEPER DRAFT ISSUES - SOLUTIONS")
    print("=" * 50)
    
    draft_id = "1256139365948604416"
    fixer = SleeperDraftFixer(draft_id)
    
    # Run all solutions
    correct_user_id = fixer.solution_1_find_correct_user_id()
    fixer.solution_2_handle_empty_team_ids()
    fixer.solution_3_fix_turn_calculation()
    fixer.solution_4_create_fixed_assistant()
    
    print("\n" + "=" * 50)
    print("📋 SUMMARY OF FIXES NEEDED")
    print("=" * 50)
    
    print(f"1. ✅ Use correct user ID: {correct_user_id if correct_user_id else 'Find your actual user ID'}")
    print(f"2. ✅ Use draft_slot + slot_to_roster_id for team mapping")
    print(f"3. ✅ Don't rely on picked_by field (often empty in mock drafts)")
    print(f"4. ✅ Use fixed turn calculation logic")
    
    print(f"\n💡 Next Steps:")
    print(f"   1. Update your assistant to use the fixed code above")
    print(f"   2. Use the correct user ID for this draft")
    print(f"   3. Test with the corrected logic")

if __name__ == "__main__":
    main()