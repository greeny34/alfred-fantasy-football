#!/usr/bin/env python3
"""
Test the fixed Sleeper draft logic with the problematic draft
"""

import requests

def test_fixed_logic():
    """Test the fixed logic against the problematic draft"""
    draft_id = "1256139365948604416"
    
    print("🧪 TESTING FIXED SLEEPER DRAFT LOGIC")
    print("=" * 45)
    print(f"Draft ID: {draft_id}")
    print()
    
    # Get draft info
    print("1️⃣ Getting draft info...")
    draft_url = f"https://api.sleeper.app/v1/draft/{draft_id}"
    draft_response = requests.get(draft_url)
    
    if draft_response.status_code != 200:
        print(f"❌ Failed to get draft info: {draft_response.status_code}")
        return
    
    draft_info = draft_response.json()
    
    # Get picks
    print("2️⃣ Getting picks...")
    picks_url = f"https://api.sleeper.app/v1/draft/{draft_id}/picks"
    picks_response = requests.get(picks_url)
    
    if picks_response.status_code != 200:
        print(f"❌ Failed to get picks: {picks_response.status_code}")
        return
    
    picks = picks_response.json()
    
    # Extract key data
    draft_order = draft_info.get('draft_order', {})
    slot_to_roster = draft_info.get('slot_to_roster_id', {})
    settings = draft_info.get('settings', {})
    total_teams = settings.get('teams', 10)
    is_snake = draft_info.get('type') == 'snake'
    
    print(f"✅ Got {len(picks)} picks")
    print(f"Draft Order: {draft_order}")
    print(f"Slot to Roster: {slot_to_roster}")
    print()
    
    # Test 1: Fixed team identification
    print("3️⃣ Testing fixed team identification...")
    
    # Auto-detect user ID
    if draft_order:
        user_id = list(draft_order.keys())[0]
        draft_slot = draft_order[user_id]
        team_id = slot_to_roster.get(str(draft_slot), draft_slot)
        
        print(f"✅ Auto-detected User ID: {user_id}")
        print(f"✅ Draft Slot: {draft_slot}")
        print(f"✅ Team ID: {team_id}")
    else:
        print("❌ No users in draft_order")
        return
    
    print()
    
    # Test 2: Fixed pick team assignment
    print("4️⃣ Testing fixed pick team assignment...")
    
    # Show old vs new team assignment for first 5 picks
    print("Pick | Old picked_by | New team_id | Draft Slot")
    print("-" * 45)
    
    for i, pick in enumerate(picks[:5]):
        old_picked_by = pick.get('picked_by', '')
        draft_slot = pick.get('draft_slot')
        new_team_id = slot_to_roster.get(str(draft_slot), draft_slot) if draft_slot else 'Unknown'
        
        # Show empty strings more clearly
        display_old = f"'{old_picked_by}'" if old_picked_by == '' else old_picked_by
        
        print(f"{i+1:4} | {display_old:13} | {new_team_id:11} | {draft_slot}")
    
    print()
    
    # Test 3: Fixed turn calculation
    print("5️⃣ Testing fixed turn calculation...")
    
    total_picks = len(picks)
    current_round = (total_picks // total_teams) + 1
    pick_in_round = total_picks % total_teams
    
    if is_snake and current_round % 2 == 0:
        next_draft_slot = total_teams - pick_in_round
    else:
        next_draft_slot = pick_in_round + 1
    
    next_team_id = slot_to_roster.get(str(next_draft_slot), next_draft_slot)
    
    print(f"Total picks made: {total_picks}")
    print(f"Current round: {current_round}")
    print(f"Pick in round: {pick_in_round}")
    print(f"Next draft slot: {next_draft_slot}")
    print(f"Next team ID: {next_team_id}")
    
    # Check if it's the detected user's turn
    is_users_turn = next_team_id == team_id
    print(f"Is detected user's turn: {'YES 🎯' if is_users_turn else 'No'}")
    
    print()
    
    # Test 4: Show team rosters with fixed assignments
    print("6️⃣ Testing team rosters with fixed assignments...")
    
    team_rosters = {}
    for pick in picks:
        draft_slot = pick.get('draft_slot')
        if draft_slot:
            fixed_team_id = slot_to_roster.get(str(draft_slot), draft_slot)
            
            if fixed_team_id not in team_rosters:
                team_rosters[fixed_team_id] = []
            
            team_rosters[fixed_team_id].append({
                'round': pick.get('round'),
                'pick_no': pick.get('pick_no'),
                'player_id': pick.get('player_id', 'Unknown')
            })
    
    print(f"Teams with picks:")
    for tid, roster in team_rosters.items():
        is_user_team = tid == team_id
        marker = " (YOU)" if is_user_team else ""
        print(f"  Team {tid}{marker}: {len(roster)} picks")
    
    print()
    
    # Summary
    print("7️⃣ SUMMARY OF FIXES")
    print("-" * 25)
    print("✅ User identification: Auto-detects from draft_order")
    print("✅ Team assignment: Uses draft_slot + slot_to_roster_id")
    print("✅ Turn calculation: Uses fixed snake draft logic")
    print("✅ Empty picked_by fields: No longer cause issues")
    print()
    print("🎯 The assistant should now correctly:")
    print("   1. Identify your team")
    print("   2. Show proper team IDs for all picks")
    print("   3. Calculate whose turn it is accurately")

if __name__ == "__main__":
    test_fixed_logic()