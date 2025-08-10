#!/usr/bin/env python3
"""
Debug the scarcity calculation issue
"""
import sys
sys.path.append('/Users/jeffgreenfield/dev/ff_draft_vibe')

from complete_sleeper_assistant import CompleteDraftAssistant

def debug_scarcity():
    assistant = CompleteDraftAssistant("dummy_id")
    
    # Sample RBs
    sample_rbs = [
        {"name": "Josh Jacobs", "position": "RB", "team": "GB", "player_id": "1"},
        {"name": "Aaron Jones", "position": "RB", "team": "MIN", "player_id": "2"},
        {"name": "Alvin Kamara", "position": "RB", "team": "NO", "player_id": "3"},
        {"name": "Austin Ekeler", "position": "RB", "team": "WAS", "player_id": "4"},
    ]
    
    print("🔍 DEBUGGING POSITIONAL SCARCITY CALCULATION")
    print("=" * 60)
    
    for rb in sample_rbs:
        print(f"\n🎯 {rb['name']} ({rb['position']}) - {rb['team']}")
        print("-" * 40)
        
        # Get his ranking
        consensus, high, low, std = assistant.get_player_expert_data(rb)
        print(f"His rank: #{consensus}")
        
        # Get all RB rankings
        print("All RBs available:")
        all_rb_data = []
        for other_rb in sample_rbs:
            other_consensus, _, _, _ = assistant.get_player_expert_data(other_rb)
            if other_consensus < 999:
                all_rb_data.append({
                    'name': other_rb['name'],
                    'consensus': other_consensus
                })
                print(f"  {other_rb['name']}: #{other_consensus}")
        
        # Sort by ranking
        all_rb_data.sort(key=lambda x: x['consensus'])
        sorted_names = [f"{rb['name']} (#{rb['consensus']})" for rb in all_rb_data]
        print(f"Sorted order: {sorted_names}")
        
        # Find next player manually
        next_player = None
        for other_data in all_rb_data:
            if other_data['consensus'] > consensus:
                next_player = other_data
                break
        
        if next_player:
            drop_off = next_player['consensus'] - consensus
            print(f"Next worse RB: {next_player['name']} at #{next_player['consensus']}")
            print(f"Drop-off: {next_player['consensus']} - {consensus} = {drop_off}")
        else:
            print("❌ No next player found (this is the worst RB)")
        
        # Compare with function result
        calculated_drop, uncertainty = assistant.calculate_individual_positional_scarcity(rb, sample_rbs)
        print(f"Function returned: drop_off={calculated_drop}, uncertainty={uncertainty}")
        
        if next_player:
            expected_drop = next_player['consensus'] - consensus
            if calculated_drop != expected_drop:
                print(f"❌ MISMATCH! Expected {expected_drop}, got {calculated_drop}")
            else:
                print(f"✅ Correct calculation")

if __name__ == "__main__":
    debug_scarcity()