#!/usr/bin/env python3
"""
Test the real VORP calculation with current function
"""
import sys
sys.path.append('/Users/jeffgreenfield/dev/ff_draft_vibe')

from complete_sleeper_assistant import CompleteDraftAssistant

def test_real_vorp():
    assistant = CompleteDraftAssistant("dummy_id")
    
    # Sample RBs
    sample_rbs = [
        {"name": "Josh Jacobs", "position": "RB", "team": "GB", "player_id": "1"},
        {"name": "Aaron Jones", "position": "RB", "team": "MIN", "player_id": "2"},
        {"name": "Alvin Kamara", "position": "RB", "team": "NO", "player_id": "3"},
        {"name": "Austin Ekeler", "position": "RB", "team": "WAS", "player_id": "4"},
    ]
    
    print("🔍 REAL VORP CALCULATIONS")
    print("=" * 50)
    
    for rb in sample_rbs:
        print(f"\n🎯 {rb['name']} ({rb['position']}) - {rb['team']}")
        print("-" * 40)
        
        # Get VORP
        vorp = assistant.calculate_value_over_replacement(rb, sample_rbs)
        print(f"Final VORP: {vorp:.1f}")
        
        # Break down components
        consensus, high, low, std = assistant.get_player_expert_data(rb)
        base_value = max(0, 200 - consensus)
        
        drop_off, uncertainty = assistant.calculate_individual_positional_scarcity(rb, sample_rbs)
        scarcity_bonus = drop_off * 2
        
        upside_potential = max(0, consensus - high) * 1.5
        stability_bonus = max(0, 10 - std)
        range_factor = low - high
        ceiling_floor_bonus = range_factor * 0.3
        
        subtotal = base_value + scarcity_bonus + upside_potential + stability_bonus + ceiling_floor_bonus
        multiplier = 1.15  # RB multiplier
        final_vorp = subtotal * multiplier
        
        print(f"  Base: {base_value}")
        print(f"  Scarcity: {drop_off} * 2 = {scarcity_bonus}")
        print(f"  Upside: {upside_potential:.1f}")
        print(f"  Stability: {stability_bonus:.1f}")
        print(f"  Ceiling-Floor: {ceiling_floor_bonus:.1f}")
        print(f"  Subtotal: {subtotal:.1f}")
        print(f"  Final: {subtotal:.1f} * {multiplier} = {final_vorp:.1f}")
        
        # Check if matches function result
        if abs(vorp - final_vorp) > 0.1:
            print(f"❌ MISMATCH! Function returned {vorp:.1f}, manual calc {final_vorp:.1f}")
        else:
            print(f"✅ Matches function result")

if __name__ == "__main__":
    test_real_vorp()