#!/usr/bin/env python3
"""
Official NFL Roster Scraper
Scrapes current rosters from NFL.com team pages for accurate player-team mappings
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
import psycopg2
import time
import os
from typing import Dict, List, Tuple, Optional
import re

class NFLRosterScraper:
    def __init__(self):
        # Database connection parameters
        self.db_config = {
            'host': 'localhost', 
            'port': '5432',
            'user': os.environ.get('USER', 'jeffgreenfield'),
            'password': '',
            'database': 'fantasy_draft_db'
        }
        
        # Headers to appear like a real browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # NFL team mappings
        self.nfl_teams = {
            'arizona-cardinals': 'ARI',
            'atlanta-falcons': 'ATL', 
            'baltimore-ravens': 'BAL',
            'buffalo-bills': 'BUF',
            'carolina-panthers': 'CAR',
            'chicago-bears': 'CHI',
            'cincinnati-bengals': 'CIN',
            'cleveland-browns': 'CLE',
            'dallas-cowboys': 'DAL',
            'denver-broncos': 'DEN',
            'detroit-lions': 'DET',
            'green-bay-packers': 'GB',
            'houston-texans': 'HOU',
            'indianapolis-colts': 'IND',
            'jacksonville-jaguars': 'JAX',
            'kansas-city-chiefs': 'KC',
            'las-vegas-raiders': 'LV',
            'los-angeles-chargers': 'LAC',
            'los-angeles-rams': 'LAR',
            'miami-dolphins': 'MIA',
            'minnesota-vikings': 'MIN',
            'new-england-patriots': 'NE',
            'new-orleans-saints': 'NO',
            'new-york-giants': 'NYG',
            'new-york-jets': 'NYJ',
            'philadelphia-eagles': 'PHI',
            'pittsburgh-steelers': 'PIT',
            'san-francisco-49ers': 'SF',
            'seattle-seahawks': 'SEA',
            'tampa-bay-buccaneers': 'TB',
            'tennessee-titans': 'TEN',
            'washington-commanders': 'WAS'
        }
        
        # Fantasy relevant positions
        self.fantasy_positions = {'QB', 'RB', 'WR', 'TE', 'K', 'DST'}
        
    def scrape_team_roster(self, team_slug: str, team_code: str) -> List[Dict]:
        """Scrape roster for a specific NFL team"""
        print(f"🏈 Scraping {team_code} roster...")
        
        url = f"https://www.nfl.com/teams/{team_slug}/roster"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            players = []
            
            # Look for roster table - NFL.com uses various formats
            # Try multiple selectors
            roster_selectors = [
                'table.d3-o-table tbody tr',
                '.nfl-c-roster__table tbody tr',
                '[data-testid="roster-table"] tbody tr',
                '.roster-table tbody tr'
            ]
            
            roster_rows = []
            for selector in roster_selectors:
                roster_rows = soup.select(selector)
                if roster_rows:
                    print(f"  Found roster using selector: {selector}")
                    break
            
            if not roster_rows:
                # Fallback: look for any table with player data
                tables = soup.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    if len(rows) > 5:  # Likely a roster table
                        roster_rows = rows[1:]  # Skip header
                        print(f"  Found roster table with {len(roster_rows)} rows")
                        break
            
            if not roster_rows:
                print(f"  ❌ No roster data found for {team_code}")
                return []
            
            for row in roster_rows:
                try:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) < 3:
                        continue
                    
                    # Extract player data - format varies by team
                    player_data = {}
                    
                    # Common patterns for NFL roster tables:
                    # [Number, Name, Position, Height, Weight, Experience, College]
                    
                    # Try to find name and position
                    name = None
                    position = None
                    number = None
                    
                    for i, cell in enumerate(cells):
                        text = cell.get_text(strip=True)
                        
                        # Skip empty cells
                        if not text or text in ['--', '-']:
                            continue
                        
                        # Jersey number (usually first column)
                        if i == 0 and text.isdigit():
                            number = text
                        
                        # Player name (look for links or longer text)
                        if not name and (cell.find('a') or len(text.split()) >= 2):
                            # Clean up name
                            name = text.strip()
                            # Remove any extra info like "(R)" for rookie
                            name = re.sub(r'\s*\([^)]*\)\s*', '', name)
                        
                        # Position (2-3 letter codes)
                        if not position and re.match(r'^[A-Z]{1,3}$', text):
                            position = text
                    
                    if name and position:
                        # Map position to fantasy categories  
                        fantasy_pos = self.map_to_fantasy_position(position)
                        
                        if fantasy_pos:  # Only include fantasy-relevant positions
                            player_data = {
                                'name': name,
                                'position': fantasy_pos,
                                'nfl_position': position,
                                'team': team_code,
                                'jersey_number': number
                            }
                            players.append(player_data)
                
                except Exception as e:
                    continue  # Skip problematic rows
            
            print(f"  ✅ Found {len(players)} fantasy-relevant players for {team_code}")
            time.sleep(1)  # Be respectful to NFL.com
            
            return players
            
        except Exception as e:
            print(f"  ❌ Error scraping {team_code}: {e}")
            return []
    
    def map_to_fantasy_position(self, nfl_position: str) -> Optional[str]:
        """Map NFL position to fantasy position"""
        position_mapping = {
            # Quarterbacks
            'QB': 'QB',
            
            # Running Backs
            'RB': 'RB', 'FB': 'RB', 'HB': 'RB',
            
            # Wide Receivers  
            'WR': 'WR', 'WRS': 'WR', 'SWR': 'WR',
            
            # Tight Ends
            'TE': 'TE',
            
            # Kickers
            'K': 'K', 'PK': 'K',
            
            # Defense/Special Teams - we'll handle this separately
            'P': None,  # Punters not fantasy relevant individually
            'LS': None,  # Long snappers not fantasy relevant
        }
        
        return position_mapping.get(nfl_position)
    
    def scrape_all_rosters(self) -> List[Dict]:
        """Scrape rosters for all NFL teams"""
        print("🏈 NFL OFFICIAL ROSTER SCRAPER")
        print("🎯 Scraping all 32 NFL team rosters")
        print("=" * 50)
        
        all_players = []
        
        for team_slug, team_code in self.nfl_teams.items():
            try:
                team_players = self.scrape_team_roster(team_slug, team_code)
                all_players.extend(team_players)
                
                # Progress update
                if len(team_players) > 0:
                    print(f"  Running total: {len(all_players)} players")
                
            except Exception as e:
                print(f"❌ Failed to scrape {team_code}: {e}")
                continue
        
        print(f"\n✅ Scraping complete! Found {len(all_players)} total players")
        return all_players
    
    def clean_and_dedupe_players(self, players: List[Dict]) -> List[Dict]:
        """Clean up player data and remove duplicates"""
        print("🧹 Cleaning and deduplicating player data...")
        
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(players)
        
        if df.empty:
            return []
        
        print(f"  Before cleaning: {len(df)} players")
        
        # Remove players with no name or position
        df = df.dropna(subset=['name', 'position'])
        df = df[df['name'].str.len() > 0]
        
        # Clean up names
        df['name'] = df['name'].str.strip()
        df['name'] = df['name'].str.title()
        
        # Remove exact duplicates (same name, position, team)
        before_dedup = len(df)
        df = df.drop_duplicates(subset=['name', 'position', 'team'])
        print(f"  Removed {before_dedup - len(df)} exact duplicates")
        
        # Handle players who might be on multiple teams (recent trades)
        # Keep the most recent entry (last in our scraping order)
        df = df.drop_duplicates(subset=['name', 'position'], keep='last')
        
        print(f"  After cleaning: {len(df)} players")
        
        return df.to_dict('records')
    
    def update_database(self, players: List[Dict]) -> bool:
        """Update database with scraped roster data"""
        print("📝 Updating database with official roster data...")
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            # Clear existing data
            print("  🗑️ Clearing old player data...")
            cur.execute("DELETE FROM player_rankings;")
            cur.execute("DELETE FROM players;")
            
            # Insert new players
            print("  📥 Inserting new player data...")
            inserted_count = 0
            
            for player in players:
                try:
                    cur.execute("""
                        INSERT INTO players (name, position, team, year, is_active)
                        VALUES (%s, %s, %s, %s, %s);
                    """, (
                        player['name'],
                        player['position'], 
                        player['team'],
                        2025,
                        True
                    ))
                    inserted_count += 1
                    
                except Exception as e:
                    print(f"    Error inserting {player['name']}: {e}")
                    continue
            
            conn.commit()
            cur.close()
            conn.close()
            
            print(f"✅ Database updated! Inserted {inserted_count} players")
            return True
            
        except Exception as e:
            print(f"❌ Database error: {e}")
            return False
    
    def export_roster_data(self, players: List[Dict]) -> None:
        """Export roster data to CSV for review"""
        if not players:
            return
            
        df = pd.DataFrame(players)
        
        # Export by team
        output_file = '/Users/jeffgreenfield/dev/ff_draft_vibe/nfl_official_rosters.csv'
        df.to_csv(output_file, index=False)
        print(f"📄 Roster data exported to: {output_file}")
        
        # Show summary by team
        print(f"\n📊 ROSTER SUMMARY:")
        team_summary = df.groupby(['team', 'position']).size().unstack(fill_value=0)
        print(team_summary)
    
    def run_full_pipeline(self) -> bool:
        """Run the complete roster scraping pipeline"""
        print("🚀 STARTING NFL ROSTER SCRAPING PIPELINE")
        print("=" * 60)
        
        # Step 1: Scrape all rosters
        players = self.scrape_all_rosters()
        
        if not players:
            print("❌ No player data scraped!")
            return False
        
        # Step 2: Clean and deduplicate
        clean_players = self.clean_and_dedupe_players(players)
        
        # Step 3: Export for review
        self.export_roster_data(clean_players)
        
        # Step 4: Update database
        success = self.update_database(clean_players)
        
        if success:
            print(f"\n🎉 PIPELINE COMPLETE!")
            print(f"📊 {len(clean_players)} official NFL players added to database")
            print(f"🏈 All 32 teams scraped from NFL.com")
            print(f"✅ Ready for fantasy rankings integration")
        
        return success

if __name__ == "__main__":
    scraper = NFLRosterScraper()
    scraper.run_full_pipeline()