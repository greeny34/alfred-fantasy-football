import os
from dotenv import load_dotenv
from espn_api.football import League

def test_current_league_draft_status():
    """Check if current league has draft capabilities"""
    load_dotenv()
    
    try:
        league = League(
            league_id=os.getenv('LEAGUE_ID'),
            year=int(os.getenv('YEAR')),
            espn_s2=os.getenv('ESPN_S2'),
            swid=os.getenv('SWID')
        )
        
        print("🔍 Current League Draft Status")
        print("=" * 40)
        print(f"League ID: {os.getenv('LEAGUE_ID')}")
        print(f"League Name: {getattr(league, 'name', 'Unknown')}")
        print(f"Teams: {len(league.teams)}")
        print(f"Current Week: {getattr(league, 'current_week', 'Unknown')}")
        
        # Check draft status
        print(f"\n📊 Draft Information:")
        try:
            draft_complete = getattr(league, 'draft_complete', None)
            print(f"Draft Complete: {draft_complete}")
            
            if hasattr(league, 'draft') and league.draft:
                print(f"Draft Object: ✅ Available ({len(league.draft)} picks)")
                
                # Show some draft picks
                print(f"\nSample draft picks:")
                for i, pick in enumerate(league.draft[:10]):
                    print(f"  {i+1}. {pick}")
            else:
                print(f"Draft Object: ❌ Not available")
                
        except Exception as e:
            print(f"Error accessing draft: {e}")
        
        # Check if we can trigger a new draft
        print(f"\n🎯 Draft Testing Options:")
        print("1. Current league status - see above")
        print("2. If draft_complete=False, we might be able to test with this league")
        print("3. If draft_complete=True, we'd need a new league")
        
        # Check team rosters for draft picks
        print(f"\n👥 Team Roster Analysis:")
        total_draft_picks = 0
        
        for i, team in enumerate(league.teams):
            draft_picks = []
            for player in team.roster:
                if hasattr(player, 'acquisition_type') and player.acquisition_type == 'DRAFT':
                    draft_picks.append(f"{player.name} ({player.position})")
                    total_draft_picks += 1
            
            print(f"  {i+1}. {team.team_name}: {len(draft_picks)} draft picks")
            if draft_picks and len(draft_picks) <= 3:
                print(f"     {', '.join(draft_picks)}")
        
        print(f"\nTotal draft picks found: {total_draft_picks}")
        
        if total_draft_picks == 0:
            print("🎯 This league might be ready for a fresh draft test!")
        else:
            print("📋 This league has existing draft data")
            
        return league
        
    except Exception as e:
        print(f"❌ Error connecting to league: {e}")
        return None

def create_draft_simulation():
    """Create a realistic draft simulation for testing"""
    print("\n🎲 Draft Simulation Option")
    print("=" * 30)
    print("Since ESPN API limitations exist, we can create a realistic")
    print("draft simulation using ESPN player rankings to test our system.")
    print()
    print("This would involve:")
    print("1. Get ESPN player rankings/projections")
    print("2. Simulate 10 teams with different draft strategies")
    print("3. Generate realistic pick sequences")
    print("4. Test recommendation engine against this data")
    print()
    
    create_sim = input("Would you like me to create a draft simulation? (y/n): ")
    return create_sim.lower().startswith('y')

def main():
    print("🏈 FF Draft Vibe - Testing Setup")
    print("=" * 40)
    
    # Test current league
    league = test_current_league_draft_status()
    
    if league:
        print(f"\n🤔 Next Steps:")
        print("1. If your current league is pre-draft, we can test with it")
        print("2. Create a new private league for dedicated testing")
        print("3. Build a draft simulation for controlled testing")
        
        # Ask user preference
        choice = input(f"\nWhich option do you prefer? (1/2/3): ").strip()
        
        if choice == "1":
            print("✅ We can use your current league for testing")
            print("The ESPN API should work well with real league drafts")
        elif choice == "2":
            print("✅ Create a new private ESPN league:")
            print("- Go to ESPN Fantasy Football")
            print("- Create new league for 2025")
            print("- Set it up with 10 teams (you can control multiple)")
            print("- Get the new league ID and update your .env file")
        elif choice == "3":
            if create_draft_simulation():
                print("✅ I'll create a draft simulation system")
    else:
        print("❌ Could not connect to current league")
        print("Consider creating a new league or using simulation")

if __name__ == "__main__":
    main()