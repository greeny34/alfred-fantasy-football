#!/usr/bin/env python3
"""
Debug script to show expert rankings, ranges, and detailed math calculations
"""
import sys
sys.path.append('/Users/jeffgreenfield/dev/ff_draft_vibe')

from complete_sleeper_assistant import CompleteDraftAssistant

def show_expert_rankings():
    """Display the expert rankings data with ranges"""
    print("🎯 EXPERT RANKINGS DATA")
    print("=" * 80)
    print("Format: Player Name | Consensus | Best Case | Worst Case | Std Dev | Range")
    print("-" * 80)
    
    # Create assistant instance to access methods
    assistant = CompleteDraftAssistant("dummy_id")
    
    # Sample of top players to show rankings
    sample_players = [
        {"name": "Ja'Marr Chase", "position": "WR", "team": "CIN"},
        {"name": "Bijan Robinson", "position": "RB", "team": "ATL"},
        {"name": "Justin Jefferson", "position": "WR", "team": "MIN"},
        {"name": "CeeDee Lamb", "position": "WR", "team": "DAL"},
        {"name": "Saquon Barkley", "position": "RB", "team": "PHI"},
        {"name": "Jahmyr Gibbs", "position": "RB", "team": "DET"},
        {"name": "Amon-Ra St. Brown", "position": "WR", "team": "DET"},
        {"name": "Puka Nacua", "position": "WR", "team": "LAR"},
        {"name": "Malik Nabers", "position": "WR", "team": "NYG"},
        {"name": "De'Von Achane", "position": "RB", "team": "MIA"},
        {"name": "Brian Thomas Jr.", "position": "WR", "team": "JAX"},
        {"name": "Ashton Jeanty", "position": "RB", "team": "LV"},
        {"name": "Brock Bowers", "position": "TE", "team": "LV"},
        {"name": "Christian McCaffrey", "position": "RB", "team": "SF"},
        {"name": "Josh Jacobs", "position": "RB", "team": "GB"},
        {"name": "A.J. Brown", "position": "WR", "team": "PHI"},
        {"name": "Josh Allen", "position": "QB", "team": "BUF"},
        {"name": "Lamar Jackson", "position": "QB", "team": "BAL"},
        {"name": "Aaron Jones", "position": "RB", "team": "MIN"},
        {"name": "Calvin Ridley", "position": "WR", "team": "TEN"},
        {"name": "Alvin Kamara", "position": "RB", "team": "NO"},
    ]
    
    for player in sample_players:
        consensus, high, low, std = assistant.get_player_expert_data(player)
        if consensus < 999:  # Has ranking data
            range_size = low - high
            print(f"{player['name']:<20} | #{consensus:>3} | #{high:>3} | #{low:>3} | {std:>4.1f} | {range_size:>3}")
    
    print("\n📊 INTERPRETATION:")
    print("• Consensus: Average ranking across all expert sources")
    print("• Best Case: Highest (best) ranking any expert gave")
    print("• Worst Case: Lowest (worst) ranking any expert gave") 
    print("• Std Dev: How much experts disagree (lower = more consensus)")
    print("• Range: Difference between best and worst case rankings")

def show_vorp_calculations():
    """Show detailed VORP calculation math"""
    print("\n\n⚡ VALUE OVER REPLACEMENT PLAYER (VORP) CALCULATIONS")
    print("=" * 80)
    
    assistant = CompleteDraftAssistant("dummy_id")
    
    # Create sample available players for calculations
    sample_available = [
        {"name": "Josh Jacobs", "position": "RB", "team": "GB", "player_id": "1"},
        {"name": "Aaron Jones", "position": "RB", "team": "MIN", "player_id": "2"},
        {"name": "Alvin Kamara", "position": "RB", "team": "NO", "player_id": "3"},
        {"name": "A.J. Brown", "position": "WR", "team": "PHI", "player_id": "4"},
        {"name": "Calvin Ridley", "position": "WR", "team": "TEN", "player_id": "5"},
        {"name": "Brock Bowers", "position": "TE", "team": "LV", "player_id": "6"},
        {"name": "Josh Allen", "position": "QB", "team": "BUF", "player_id": "7"},
    ]
    
    print("Showing VORP calculation breakdown for sample players:\n")
    
    for player in sample_available:
        print(f"🎯 {player['name']} ({player['position']}) - {player['team']}")
        print("-" * 50)
        
        # Get expert data
        consensus, high, low, std = assistant.get_player_expert_data(player)
        print(f"Expert Data: Consensus #{consensus}, Range #{high}-#{low}, Std Dev {std}")
        
        if consensus >= 999:
            print("❌ No ranking data available\n")
            continue
        
        # Calculate each component
        base_value = max(0, 200 - consensus)
        print(f"1. Base Value = max(0, 200 - {consensus}) = {base_value}")
        
        # Individual positional scarcity
        drop_off, uncertainty = assistant.calculate_individual_positional_scarcity(player, sample_available)
        scarcity_bonus = drop_off * 2
        print(f"2. Positional Scarcity = {drop_off} * 2 = {scarcity_bonus}")
        
        # Upside potential
        upside_potential = max(0, consensus - high) * 1.5
        print(f"3. Upside Potential = max(0, {consensus} - {high}) * 1.5 = {upside_potential}")
        
        # Stability bonus
        stability_bonus = max(0, 10 - std)
        print(f"4. Stability Bonus = max(0, 10 - {std}) = {stability_bonus}")
        
        # Ceiling-floor bonus
        range_factor = low - high
        ceiling_floor_bonus = range_factor * 0.3
        print(f"5. Ceiling-Floor Bonus = ({low} - {high}) * 0.3 = {ceiling_floor_bonus}")
        
        # Position multiplier
        position_multipliers = {
            'RB': 1.15, 'WR': 1.10, 'TE': 1.05, 'QB': 0.85, 'K': 0.1, 'D/ST': 0.2
        }
        multiplier = position_multipliers.get(player['position'], 1.0)
        
        # Total before multiplier
        subtotal = base_value + scarcity_bonus + upside_potential + stability_bonus + ceiling_floor_bonus
        print(f"6. Subtotal = {base_value} + {scarcity_bonus} + {upside_potential} + {stability_bonus} + {ceiling_floor_bonus} = {subtotal}")
        
        # Final VORP
        final_vorp = subtotal * multiplier
        print(f"7. Final VORP = {subtotal} * {multiplier} = {final_vorp:.1f}")
        
        print()

def show_positional_scarcity_math():
    """Show how positional scarcity is calculated"""
    print("\n\n📈 POSITIONAL SCARCITY CALCULATIONS")
    print("=" * 80)
    
    assistant = CompleteDraftAssistant("dummy_id")
    
    # Sample RBs for scarcity calculation
    sample_rbs = [
        {"name": "Josh Jacobs", "position": "RB", "team": "GB", "player_id": "1"},
        {"name": "Aaron Jones", "position": "RB", "team": "MIN", "player_id": "2"},
        {"name": "Alvin Kamara", "position": "RB", "team": "NO", "player_id": "3"},
        {"name": "Austin Ekeler", "position": "RB", "team": "WAS", "player_id": "4"},
    ]
    
    print("Example: RB Position Scarcity Analysis")
    print("-" * 40)
    
    print("Available RBs with rankings:")
    rb_data = []
    for rb in sample_rbs:
        consensus, high, low, std = assistant.get_player_expert_data(rb)
        if consensus < 999:
            rb_data.append({
                'name': rb['name'],
                'consensus': consensus,
                'high': high,
                'low': low,
                'std': std
            })
            print(f"  {rb['name']}: #{consensus} (range #{high}-#{low}, std {std})")
    
    if len(rb_data) >= 2:
        # Sort by consensus (best first)
        rb_data.sort(key=lambda x: x['consensus'])
        
        best = rb_data[0]
        second_best = rb_data[1]
        
        print(f"\nScarcity Calculation:")
        print(f"Best RB: {best['name']} at #{best['consensus']}")
        print(f"2nd Best RB: {second_best['name']} at #{second_best['consensus']}")
        
        consensus_drop = second_best['consensus'] - best['consensus']
        uncertainty_factor = (best['std'] + second_best['std']) / 2
        
        print(f"Drop-off = {second_best['consensus']} - {best['consensus']} = {consensus_drop}")
        print(f"Uncertainty = ({best['std']} + {second_best['std']}) / 2 = {uncertainty_factor:.1f}")
        print(f"Scarcity Bonus in VORP = {consensus_drop} * 2 = {consensus_drop * 2}")

def main():
    """Run all analyses"""
    print("🔍 FANTASY FOOTBALL RECOMMENDATION ALGORITHM ANALYSIS")
    print("=" * 80)
    
    show_expert_rankings()
    show_vorp_calculations()
    show_positional_scarcity_math()
    
    print("\n\n💡 SUMMARY:")
    print("The algorithm combines:")
    print("1. Expert consensus rankings (5 major sources)")
    print("2. Risk/reward analysis (upside vs reliability)")
    print("3. Positional scarcity (how big is the drop-off?)")
    print("4. Value over replacement calculations")
    print("5. Position-specific draft strategy adjustments")

if __name__ == "__main__":
    main()