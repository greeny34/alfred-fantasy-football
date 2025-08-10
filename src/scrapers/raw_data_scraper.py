#!/usr/bin/env python3
"""
Raw Data Scraper for Fantasy Football Rankings
Brute force approach - scrape actual data from each site and build data repository
"""
import requests
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import time
import json
import re
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

class RawDataScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        }
        
        # Raw data storage
        self.raw_data = {
            'FantasyPros': {},
            'ESPN': {},
            'Yahoo': {},
            'CBS': {},
            'NFL': {},
            'DraftSharks': {}
        }
        
        # Site URLs
        self.sites = {
            'FantasyPros': {
                'QB': 'https://www.fantasypros.com/nfl/rankings/qb.php',
                'RB': 'https://www.fantasypros.com/nfl/rankings/ppr-rb.php',
                'WR': 'https://www.fantasypros.com/nfl/rankings/ppr-wr.php', 
                'TE': 'https://www.fantasypros.com/nfl/rankings/ppr-te.php',
                'K': 'https://www.fantasypros.com/nfl/rankings/k.php',
                'D/ST': 'https://www.fantasypros.com/nfl/rankings/dst.php'
            },
            'ESPN': {
                'base': 'https://www.espn.com/fantasy/football/story/_/page/'
            },
            'Yahoo': {
                'base': 'https://football.fantasysports.yahoo.com/f1/public_prerank'
            },
            'CBS': {
                'QB': 'https://www.cbssports.com/fantasy/football/rankings/ppr/qb/',
                'RB': 'https://www.cbssports.com/fantasy/football/rankings/ppr/rb/',
                'WR': 'https://www.cbssports.com/fantasy/football/rankings/ppr/wr/',
                'TE': 'https://www.cbssports.com/fantasy/football/rankings/ppr/te/'
            }
        }
    
    def scrape_fantasypros(self):
        """Scrape FantasyPros rankings for all positions"""
        print("🔍 Scraping FantasyPros 2025 PPR Rankings...")
        
        for position, url in self.sites['FantasyPros'].items():
            print(f"   📊 Scraping FantasyPros {position}...")
            
            try:
                response = requests.get(url, headers=self.headers)
                time.sleep(2)  # Be respectful
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                players = []
                
                # Look for player ranking tables
                tables = soup.find_all('table')
                
                for table in tables:
                    tbody = table.find('tbody')
                    if tbody:
                        rows = tbody.find_all('tr')
                        
                        for row in rows:
                            cells = row.find_all('td')
                            if len(cells) >= 2:
                                try:
                                    # First cell should be rank
                                    rank_cell = cells[0]
                                    rank_text = rank_cell.get_text(strip=True)
                                    
                                    if rank_text.isdigit():
                                        rank = int(rank_text)
                                        
                                        # Second cell should be player info
                                        player_cell = cells[1]
                                        player_link = player_cell.find('a')
                                        
                                        if player_link:
                                            player_name = player_link.get_text(strip=True)
                                            
                                            # Look for team info
                                            team_elem = player_cell.find('small')
                                            team = 'UNK'
                                            if team_elem:
                                                team_text = team_elem.get_text(strip=True)
                                                # Extract team (usually format like "LAR" or "LAR - WR")
                                                team_match = re.search(r'([A-Z]{2,3})', team_text)
                                                if team_match:
                                                    team = team_match.group(1)
                                            
                                            players.append({
                                                'rank': rank,
                                                'player': player_name,
                                                'team': team,
                                                'position': position
                                            })
                                except Exception as e:
                                    continue
                
                self.raw_data['FantasyPros'][position] = players
                print(f"   ✅ FantasyPros {position}: {len(players)} players")
                
            except Exception as e:
                print(f"   ❌ FantasyPros {position} error: {e}")
                self.raw_data['FantasyPros'][position] = []
    
    def scrape_espn(self):
        """Scrape ESPN rankings for all positions"""
        print("🔍 Scraping ESPN 2025 PPR Rankings...")
        
        # ESPN position URLs
        espn_urls = {
            'QB': 'https://www.espn.com/fantasy/football/story/_/page/FFPreseasonRank25QBPPR/nfl-fantasy-football-draft-rankings-2025-qb-quarterback',
            'RB': 'https://www.espn.com/fantasy/football/story/_/page/FFPreseasonRank25RBPPR/nfl-fantasy-football-draft-rankings-2025-rb-running-back-ppr',
            'WR': 'https://www.espn.com/fantasy/football/story/_/page/FFPreseasonRank25WRPPR/nfl-fantasy-football-draft-rankings-2025-wr-wide-receiver-ppr',
            'TE': 'https://www.espn.com/fantasy/football/story/_/page/FFPreseasonRank25TEPPR/nfl-fantasy-football-draft-rankings-2025-te-tight-end-ppr'
        }
        
        for position, url in espn_urls.items():
            print(f"   📊 Scraping ESPN {position}...")
            
            try:
                response = requests.get(url, headers=self.headers)
                time.sleep(2)
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                players = []
                
                # Look for ESPN ranking content
                # ESPN often uses different structures, try multiple approaches
                
                # Method 1: Look for ordered lists with player info
                ol_elements = soup.find_all('ol')
                for ol in ol_elements:
                    li_elements = ol.find_all('li')
                    for i, li in enumerate(li_elements):
                        text = li.get_text(strip=True)
                        # Look for pattern like "Player Name, Team"
                        if ',' in text and len(text) > 5:
                            parts = text.split(',')
                            if len(parts) >= 2:
                                player_name = parts[0].strip()
                                team_part = parts[1].strip()
                                
                                # Extract team
                                team_match = re.search(r'([A-Z]{2,3})', team_part)
                                team = team_match.group(1) if team_match else 'UNK'
                                
                                players.append({
                                    'rank': i + 1,
                                    'player': player_name,
                                    'team': team,
                                    'position': position
                                })
                
                # Method 2: Look for div elements with player rankings
                if not players:
                    divs = soup.find_all('div', class_=re.compile(r'player|rank'))
                    rank_counter = 1
                    for div in divs:
                        text = div.get_text(strip=True)
                        if re.search(r'[A-Za-z\s]+,\s+[A-Z]{2,3}', text):
                            parts = text.split(',')
                            if len(parts) >= 2:
                                player_name = parts[0].strip()
                                team = parts[1].strip()[:3]
                                
                                players.append({
                                    'rank': rank_counter,
                                    'player': player_name,
                                    'team': team,
                                    'position': position
                                })
                                rank_counter += 1
                
                # Method 3: Look for paragraph text with rankings
                if not players:
                    paragraphs = soup.find_all('p')
                    for p in paragraphs:
                        text = p.get_text()
                        # Look for numbered lists in paragraph text
                        lines = text.split('\n')
                        for line in lines:
                            # Match patterns like "1. Player Name, TEAM"
                            match = re.match(r'(\d+)\.\s+([^,]+),\s*([A-Z]{2,3})', line.strip())
                            if match:
                                rank = int(match.group(1))
                                player_name = match.group(2).strip()
                                team = match.group(3).strip()
                                
                                players.append({
                                    'rank': rank,
                                    'player': player_name,
                                    'team': team,
                                    'position': position
                                })
                
                self.raw_data['ESPN'][position] = players
                print(f"   ✅ ESPN {position}: {len(players)} players")
                
            except Exception as e:
                print(f"   ❌ ESPN {position} error: {e}")
                self.raw_data['ESPN'][position] = []
    
    def scrape_cbs(self):
        """Scrape CBS Sports rankings for all positions"""
        print("🔍 Scraping CBS Sports 2025 PPR Rankings...")
        
        for position, url in self.sites['CBS'].items():
            print(f"   📊 Scraping CBS {position}...")
            
            try:
                response = requests.get(url, headers=self.headers)
                time.sleep(2)
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                players = []
                
                # Look for CBS ranking tables
                tables = soup.find_all('table')
                
                for table in tables:
                    rows = table.find_all('tr')
                    
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 3:
                            try:
                                # Look for rank in first cell
                                rank_cell = cells[0]
                                rank_text = rank_cell.get_text(strip=True)
                                
                                if rank_text.isdigit():
                                    rank = int(rank_text)
                                    
                                    # Player info usually in second cell
                                    player_cell = cells[1]
                                    player_text = player_cell.get_text(strip=True)
                                    
                                    # Parse player name and team
                                    if ',' in player_text:
                                        parts = player_text.split(',')
                                        player_name = parts[0].strip()
                                        
                                        # Look for team in remaining parts or in next cell
                                        team = 'UNK'
                                        for part in parts[1:]:
                                            team_match = re.search(r'([A-Z]{2,3})', part)
                                            if team_match:
                                                team = team_match.group(1)
                                                break
                                        
                                        # If no team found in player cell, check next cell
                                        if team == 'UNK' and len(cells) > 2:
                                            team_cell = cells[2]
                                            team_text = team_cell.get_text(strip=True)
                                            team_match = re.search(r'([A-Z]{2,3})', team_text)
                                            if team_match:
                                                team = team_match.group(1)
                                        
                                        players.append({
                                            'rank': rank,
                                            'player': player_name,
                                            'team': team,
                                            'position': position
                                        })
                            except Exception as e:
                                continue
                
                self.raw_data['CBS'][position] = players
                print(f"   ✅ CBS {position}: {len(players)} players")
                
            except Exception as e:
                print(f"   ❌ CBS {position} error: {e}")
                self.raw_data['CBS'][position] = []
    
    def scrape_yahoo(self):
        """Scrape Yahoo Sports rankings"""
        print("🔍 Scraping Yahoo Sports 2025 PPR Rankings...")
        
        try:
            # Yahoo's main prerank page
            url = "https://football.fantasysports.yahoo.com/f1/public_prerank"
            response = requests.get(url, headers=self.headers)
            time.sleep(2)
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Yahoo has complex dynamic content, look for player data
            # Method 1: Look for JSON data in script tags
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and 'prerank' in script.string.lower():
                    try:
                        # Try to extract JSON data
                        script_content = script.string
                        # Look for player data patterns
                        json_match = re.search(r'\{.*"players".*\}', script_content)
                        if json_match:
                            # Parse JSON if found
                            pass
                    except:
                        continue
            
            # Method 2: Look for table structures
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    # Process table data similar to other sites
            
            # For now, set empty data since Yahoo requires complex handling
            for position in ['QB', 'RB', 'WR', 'TE', 'K', 'D/ST']:
                self.raw_data['Yahoo'][position] = []
                print(f"   ⚠️  Yahoo {position}: Complex dynamic content - 0 players")
                
        except Exception as e:
            print(f"   ❌ Yahoo error: {e}")
            for position in ['QB', 'RB', 'WR', 'TE', 'K', 'D/ST']:
                self.raw_data['Yahoo'][position] = []
    
    def export_raw_data(self):
        """Export all raw scraped data to files"""
        print("💾 Exporting raw data repository...")
        
        # Create comprehensive data export
        all_data = []
        
        for site_name, site_data in self.raw_data.items():
            for position, players in site_data.items():
                for player_data in players:
                    all_data.append({
                        'Site': site_name,
                        'Position': position,
                        'Rank': player_data['rank'],
                        'Player': player_data['player'],
                        'Team': player_data['team']
                    })
        
        # Export to CSV for easy inspection
        df = pd.DataFrame(all_data)
        csv_filename = '/Users/jeffgreenfield/dev/ff_draft_vibe/FF_2025_RAW_SCRAPED_DATA.csv'
        df.to_csv(csv_filename, index=False)
        
        # Export to Excel with separate sheets per site
        excel_filename = '/Users/jeffgreenfield/dev/ff_draft_vibe/FF_2025_RAW_DATA_REPOSITORY.xlsx'
        
        with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
            
            # Summary sheet
            summary_data = []
            for site_name, site_data in self.raw_data.items():
                for position, players in site_data.items():
                    summary_data.append({
                        'Site': site_name,
                        'Position': position,
                        'Player_Count': len(players),
                        'Top_Player': players[0]['player'] if players else 'None',
                        'Status': 'Success' if players else 'Failed'
                    })
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Scraping_Summary', index=False)
            
            # Individual site sheets
            for site_name, site_data in self.raw_data.items():
                site_rows = []
                for position, players in site_data.items():
                    for player_data in players:
                        site_rows.append({
                            'Position': position,
                            'Rank': player_data['rank'],
                            'Player': player_data['player'],
                            'Team': player_data['team']
                        })
                
                if site_rows:
                    site_df = pd.DataFrame(site_rows)
                    site_df.to_excel(writer, sheet_name=f'{site_name}_Raw', index=False)
        
        print(f"✅ Raw data exported:")
        print(f"   📄 CSV: FF_2025_RAW_SCRAPED_DATA.csv")
        print(f"   📊 Excel: FF_2025_RAW_DATA_REPOSITORY.xlsx")
        
        # Print summary
        total_players = len(all_data)
        print(f"\n📊 SCRAPING SUMMARY:")
        print(f"   Total records: {total_players}")
        
        for site_name, site_data in self.raw_data.items():
            site_total = sum(len(players) for players in site_data.values())
            print(f"   {site_name}: {site_total} players")
            for position, players in site_data.items():
                if players:
                    print(f"      {position}: {len(players)} players")
        
        return df
    
    def run_raw_data_collection(self):
        """Run complete raw data collection from all sites"""
        print("🏈 RAW FANTASY FOOTBALL DATA SCRAPER")
        print("🎯 Building Data Repository from Live Sites")
        print("=" * 60)
        
        # Scrape each site
        self.scrape_fantasypros()
        print()
        
        self.scrape_espn()
        print()
        
        self.scrape_cbs()
        print()
        
        self.scrape_yahoo()
        print()
        
        # Export all raw data
        df = self.export_raw_data()
        
        return self.raw_data, df

if __name__ == "__main__":
    scraper = RawDataScraper()
    raw_data, df = scraper.run_raw_data_collection()