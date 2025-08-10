import os
from dotenv import load_dotenv
from espn_api.football import League

def debug_league_data():
    """Debug what data we can actually see from the ESPN API"""
    load_dotenv()
    
    league = League(
        league_id=os.getenv('LEAGUE_ID'),
        year=int(os.getenv('YEAR')),
        espn_s2=os.getenv('ESPN_S2'),
        swid=os.getenv('SWID')
    )
    
    print("🔍 ESPN League Debug Info")
    print("=" * 40)
    
    # Basic league info
    print(f"League Name: {getattr(league, 'name', 'Unknown')}")
    print(f"Number of teams: {len(league.teams)}")
    print(f"Current week: {getattr(league, 'current_week', 'Unknown')}")
    
    # Check draft status
    print(f"\n📋 Draft Status:")
    print(f"Draft complete: {getattr(league, 'draft_complete', 'Unknown')}")
    
    # Check if there's draft data
    try:
        draft = getattr(league, 'draft', None)
        if draft:
            print(f"Draft object exists: {type(draft)}")
            print(f"Draft picks available: {len(draft) if hasattr(draft, '__len__') else 'Not iterable'}")
        else:
            print("No draft object found")
    except Exception as e:
        print(f"Error accessing draft: {e}")
    
    # Check team rosters
    print(f"\n👥 Team Roster Info:")
    for i, team in enumerate(league.teams):
        print(f"{i+1}. {team.team_name}")
        print(f"   Roster size: {len(team.roster)}")
        if team.roster:
            print(f"   Sample players: {[p.name for p in team.roster[:3]]}")
            # Check acquisition types
            acq_types = [getattr(p, 'acquisition_type', 'Unknown') for p in team.roster[:5]]
            print(f"   Acquisition types: {set(acq_types)}")
        print()
    
    # Try to access draft picks directly
    print(f"📊 Attempting to access draft picks...")
    try:
        # Method 1: league.draft
        if hasattr(league, 'draft') and league.draft:
            print(f"Draft method 1 - league.draft: {len(league.draft)} picks")
            for i, pick in enumerate(league.draft[:5]):
                print(f"   Pick {i+1}: {pick}")
    except Exception as e:
        print(f"Method 1 failed: {e}")
    
    try:
        # Method 2: Check for draft_recap or similar
        if hasattr(league, 'draft_recap'):
            print(f"Draft method 2 - draft_recap available")
    except Exception as e:
        print(f"Method 2 failed: {e}")
    
    # Check available league attributes
    print(f"\n🔧 Available league attributes:")
    attrs = [attr for attr in dir(league) if not attr.startswith('_')]
    draft_related = [attr for attr in attrs if 'draft' in attr.lower()]
    print(f"Draft-related attributes: {draft_related}")
    
    return league

if __name__ == "__main__":
    debug_league_data()