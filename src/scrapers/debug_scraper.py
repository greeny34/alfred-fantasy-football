import os
import time
from datetime import datetime
from dotenv import load_dotenv
from espn_api.football import League
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

class DebugScraper:
    def __init__(self):
        load_dotenv()
        self.league = League(
            league_id=os.getenv('LEAGUE_ID'),
            year=int(os.getenv('YEAR')),
            espn_s2=os.getenv('ESPN_S2'),
            swid=os.getenv('SWID')
        )
        self.driver = None
        
    def setup_browser(self):
        """Set up Chrome browser"""
        print("🌐 Setting up browser...")
        
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            print("✅ Browser setup complete")
            return True
        except Exception as e:
            print(f"❌ Browser setup failed: {e}")
            return False
    
    def navigate_to_mock_draft(self):
        """Navigate to ESPN mock draft lobby"""
        print("🎯 Opening ESPN Mock Draft Lobby...")
        
        # Go directly to mock draft lobby
        self.driver.get("https://fantasy.espn.com/football/mockdraftlobby")
        
        print("📍 Join a mock draft in the browser window")
        print("Once you're IN the actual draft (not lobby), come back here and press Enter...")
        input("Press Enter when you're on the live draft page...")
        print("✅ Ready to debug the draft page")
    
    def debug_page_structure(self):
        """Debug the page structure to find draft picks"""
        print("\n🔍 Debugging page structure...")
        print("=" * 60)
        
        try:
            # Get page title
            print(f"Page title: {self.driver.title}")
            print(f"Current URL: {self.driver.current_url}")
            
            # Look for common ESPN draft elements
            selectors_to_try = [
                # Draft board selectors
                "[data-testid*='draft']",
                "[class*='draft']",
                "[class*='Draft']",
                "[id*='draft']",
                
                # Player/pick selectors  
                "[class*='player']",
                "[class*='Player']",
                "[data-testid*='player']",
                "[class*='pick']",
                "[class*='Pick']",
                
                # Team selectors
                "[class*='team']",
                "[class*='Team']",
                
                # Common ESPN class patterns
                "[class*='Table']",
                "[class*='Row']",
                "[class*='Cell']",
                ".jsx-",
                
                # Generic content
                "div",
                "span",
                "p"
            ]
            
            print(f"\n📊 Testing {len(selectors_to_try)} different selectors...")
            
            for i, selector in enumerate(selectors_to_try):
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        print(f"\n✅ {selector}: Found {len(elements)} elements")
                        
                        # Show sample content from first few elements
                        for j, element in enumerate(elements[:3]):
                            try:
                                text = element.text.strip()
                                if text and len(text) < 200:  # Only show reasonable length text
                                    print(f"   [{j+1}] {text[:100]}{'...' if len(text) > 100 else ''}")
                            except:
                                continue
                    
                    # Don't overwhelm with div/span results
                    if selector in ["div", "span", "p"] and len(elements) > 20:
                        print(f"❗ {selector}: {len(elements)} elements (too many to show)")
                        break
                        
                except Exception as e:
                    continue
            
            # Look for specific text patterns that indicate draft activity
            print(f"\n🎯 Looking for draft-related text patterns...")
            text_patterns = [
                "drafted", "selected", "pick", "round", "team", 
                "QB", "RB", "WR", "TE", "K", "D/ST", "DEF",
                "turn", "your pick", "available", "roster"
            ]
            
            page_text = self.driver.page_source.lower()
            found_patterns = []
            
            for pattern in text_patterns:
                if pattern in page_text:
                    count = page_text.count(pattern)
                    found_patterns.append(f"{pattern} ({count})")
            
            print(f"Found patterns: {', '.join(found_patterns) if found_patterns else 'None'}")
            
            # Save page source for manual inspection
            with open('debug_page_source.html', 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            print(f"\n💾 Saved page source to debug_page_source.html for manual inspection")
            
        except Exception as e:
            print(f"❌ Debug failed: {e}")
    
    def interactive_debug(self):
        """Interactive debugging session"""
        print(f"\n🛠 Interactive Debug Mode")
        print("Commands:")
        print("  - Enter CSS selector to test")
        print("  - Type 'text:pattern' to search for text")
        print("  - Type 'refresh' to reload debug info")
        print("  - Type 'quit' to exit")
        
        while True:
            try:
                command = input("\nDebug> ").strip()
                
                if command.lower() == 'quit':
                    break
                elif command.lower() == 'refresh':
                    self.debug_page_structure()
                elif command.startswith('text:'):
                    pattern = command[5:].lower()
                    page_text = self.driver.page_source.lower()
                    count = page_text.count(pattern)
                    print(f"Found '{pattern}' {count} times in page")
                else:
                    # Try as CSS selector
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, command)
                        print(f"Found {len(elements)} elements for '{command}'")
                        
                        for i, element in enumerate(elements[:5]):
                            try:
                                text = element.text.strip()
                                print(f"  [{i+1}] {text[:150]}{'...' if len(text) > 150 else ''}")
                            except:
                                print(f"  [{i+1}] (no text content)")
                                
                    except Exception as e:
                        print(f"Error with selector '{command}': {e}")
                        
            except KeyboardInterrupt:
                break
        
        print("🏁 Debug session ended")

def main():
    scraper = DebugScraper()
    
    if not scraper.setup_browser():
        return
    
    scraper.navigate_to_mock_draft()
    scraper.debug_page_structure()
    scraper.interactive_debug()
    
    if scraper.driver:
        scraper.driver.quit()

if __name__ == "__main__":
    main()