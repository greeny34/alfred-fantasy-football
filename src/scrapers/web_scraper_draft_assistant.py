import os
import time
from datetime import datetime
from dotenv import load_dotenv
from espn_api.football import League
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class WebScraperDraftAssistant:
    def __init__(self):
        load_dotenv()
        self.league = League(
            league_id=os.getenv('LEAGUE_ID'),
            year=int(os.getenv('YEAR')),
            espn_s2=os.getenv('ESPN_S2'),
            swid=os.getenv('SWID')
        )
        self.drafted_players = set()
        self.draft_picks = []
        self.driver = None
        self.my_team_name = ""
        
    def setup_browser(self):
        """Set up Chrome browser for web scraping"""
        print("🌐 Setting up browser...")
        
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        # Don't run headless so you can see what's happening
        # chrome_options.add_argument("--headless")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            print("✅ Browser setup complete")
            return True
        except Exception as e:
            print(f"❌ Browser setup failed: {e}")
            print("Make sure you have Chrome and chromedriver installed")
            return False
    
    def navigate_to_mock_draft(self):
        """Navigate to ESPN mock draft page"""
        print("🎯 Opening ESPN Mock Draft Lobby...")
        
        # Go directly to mock draft lobby
        self.driver.get("https://fantasy.espn.com/football/mockdraftlobby")
        
        print("📍 Join a mock draft in the browser window")
        print("Once you're IN the actual draft (not lobby), come back here and press Enter...")
        input("Press Enter when you're on the live draft page...")
        print("✅ Ready to monitor mock draft")
        
        # Ask for team identification
        self.my_team_name = input("What's your team name in the mock draft? ").strip()
        print(f"✅ Watching for your team: {self.my_team_name}")
    
    def scrape_draft_picks(self):
        """Scrape current draft picks from the page"""
        try:
            current_picks = []
            
            # Try multiple selector strategies for ESPN mock draft
            selectors_to_try = [
                # Common ESPN patterns
                "[class*='Table'] [class*='Row']",
                "[class*='draft'] *",
                "[class*='pick'] *",
                "[data-testid*='draft']",
                "[data-testid*='pick']",
                
                # Look for player names and positions
                "*:contains('QB')", "*:contains('RB')", "*:contains('WR')",
                "*:contains('TE')", "*:contains('K')", "*:contains('D/ST')",
                
                # Generic table/list structures
                "table tr", "tbody tr", 
                "ul li", "ol li",
                ".jsx-* *",
                
                # Any element with player-like text
                "*"
            ]
            
            # Look for elements containing player positions or draft terms
            all_elements = self.driver.find_elements(By.CSS_SELECTOR, "*")
            
            for element in all_elements:
                try:
                    text = element.text.strip()
                    if not text or len(text) > 200:  # Skip empty or very long text
                        continue
                    
                    text_lower = text.lower()
                    
                    # Look for draft-related patterns
                    draft_indicators = [
                        # Position indicators
                        any(pos in text for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'D/ST', 'DEF']),
                        # Draft terms
                        any(term in text_lower for term in ['drafted', 'selected', 'pick', 'round']),
                        # Team indicators
                        any(term in text_lower for term in ['team', 'owner']),
                        # Names (contains both first and last name pattern)
                        len(text.split()) >= 2 and text.replace(' ', '').replace('.', '').isalpha()
                    ]
                    
                    if any(draft_indicators) and text not in current_picks:
                        current_picks.append(text)
                        
                except:
                    continue
            
            # Filter and clean picks
            filtered_picks = []
            for pick in current_picks:
                # Skip very short text or common UI elements
                if len(pick) < 3 or pick.lower() in ['pick', 'team', 'player', 'position', 'round']:
                    continue
                filtered_picks.append(pick)
            
            return filtered_picks[:20]  # Limit to reasonable number
            
        except Exception as e:
            print(f"Error scraping picks: {e}")
            return []
    
    def get_available_players(self):
        """Get available players from ESPN API"""
        try:
            available = self.league.free_agents(size=200)
            return [{
                'name': player.name,
                'position': player.position,
                'projected_points': getattr(player, 'projected_total_points', 0),
                'percent_owned': getattr(player, 'percent_owned', 0)
            } for player in available if player.name not in self.drafted_players]
        except Exception as e:
            print(f"Error getting available players: {e}")
            return []
    
    def analyze_team_needs(self):
        """Simple team needs analysis"""
        my_picks = [pick for pick in self.draft_picks if self.my_team_name.lower() in pick.lower()]
        
        # Count positions drafted
        positions = {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'K': 0, 'D/ST': 0}
        
        for pick in my_picks:
            for pos in positions.keys():
                if pos in pick:
                    positions[pos] += 1
                    break
        
        # Determine needs
        needs = []
        if positions['QB'] < 1: needs.append('QB')
        if positions['RB'] < 2: needs.extend(['RB'] * (2 - positions['RB']))
        if positions['WR'] < 2: needs.extend(['WR'] * (2 - positions['WR']))
        if positions['TE'] < 1: needs.append('TE')
        if positions['K'] < 1: needs.append('K')
        if positions['D/ST'] < 1: needs.append('D/ST')
        
        return needs
    
    def get_recommendations(self):
        """Get player recommendations"""
        available_players = self.get_available_players()
        team_needs = self.analyze_team_needs()
        
        if not available_players:
            return []
        
        recommendations = []
        
        # Recommend by position need
        for need in team_needs[:3]:
            position_players = [p for p in available_players if p['position'] == need]
            if position_players:
                position_players.sort(key=lambda x: x['projected_points'], reverse=True)
                recommendations.append({
                    'player': position_players[0],
                    'reason': f"Fills {need} need"
                })
        
        # Add best available
        all_sorted = sorted(available_players, key=lambda x: x['projected_points'], reverse=True)
        for player in all_sorted[:2]:
            if not any(rec['player']['name'] == player['name'] for rec in recommendations):
                recommendations.append({
                    'player': player,
                    'reason': "Best available"
                })
        
        return recommendations[:5]
    
    def check_for_my_turn(self):
        """Check if it's your turn by looking for turn indicators"""
        try:
            # Look for "Your Turn" or similar indicators
            turn_indicators = self.driver.find_elements(By.XPATH, 
                "//*[contains(text(), 'Your Turn') or contains(text(), 'YOUR TURN') or contains(text(), 'Make Pick')]")
            
            return len(turn_indicators) > 0
        except:
            return False
    
    def monitor_draft(self):
        """Main monitoring loop"""
        print("\n🎯 Starting mock draft monitoring...")
        print("Press Ctrl+C to stop\n")
        
        last_pick_count = 0
        iteration = 0
        
        try:
            while True:
                iteration += 1
                print(f"📊 Check #{iteration} ({datetime.now().strftime('%H:%M:%S')})")
                
                try:
                    # Scrape current picks
                    current_picks = self.scrape_draft_picks()
                    
                    # Show what we found (for debugging)
                    if iteration <= 3:  # Only show first few iterations to avoid spam
                        print(f"   Found {len(current_picks)} potential draft elements")
                        if current_picks:
                            print("   Sample elements:")
                            for i, pick in enumerate(current_picks[:5]):
                                print(f"     {i+1}. {pick}")
                    
                    # Check for new draft-related content
                    new_content = []
                    for pick in current_picks:
                        if pick not in self.draft_picks:
                            # Filter for likely actual picks (player names with positions)
                            if any(pos in pick for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'D/ST']) and len(pick.split()) >= 2:
                                self.draft_picks.append(pick)
                                new_content.append(pick)
                                self.drafted_players.add(pick.split()[0] + " " + pick.split()[1])  # Add player name
                    
                    # Show new picks
                    if new_content:
                        print("🔄 New draft content detected:")
                        for pick in new_content:
                            print(f"   ✅ {pick}")
                    elif iteration > 3:  # Don't spam "no changes" for first few checks
                        print("   No new draft content")
                    
                    # Check if it's your turn
                    is_my_turn = self.check_for_my_turn()
                    if is_my_turn:
                        print("🚨 IT'S YOUR TURN!")
                    
                    # Show recommendations
                    print(f"💡 {'🚨 YOUR TURN! ' if is_my_turn else ''}Recommendations:")
                    recommendations = self.get_recommendations()
                    
                    for i, rec in enumerate(recommendations, 1):
                        player = rec['player']
                        print(f"   {i}. {player['name']} ({player['position']}) - {rec['reason']}")
                        print(f"      Projected: {player['projected_points']:.1f} pts")
                    
                    if not recommendations:
                        print("   No recommendations available")
                    
                    # Show current draft status
                    if len(self.draft_picks) > last_pick_count:
                        print(f"📋 Draft status: {len(self.draft_picks)} picks tracked")
                        last_pick_count = len(self.draft_picks)
                        
                except Exception as e:
                    print(f"Error during monitoring: {e}")
                
                print("   Waiting 3 seconds...\n")
                time.sleep(3)
                
        except KeyboardInterrupt:
            print("\n👋 Draft monitoring stopped")
        finally:
            if self.driver:
                self.driver.quit()
                print("🔧 Browser closed")

def main():
    assistant = WebScraperDraftAssistant()
    
    if not assistant.setup_browser():
        return
    
    assistant.navigate_to_mock_draft()
    assistant.monitor_draft()

if __name__ == "__main__":
    main()