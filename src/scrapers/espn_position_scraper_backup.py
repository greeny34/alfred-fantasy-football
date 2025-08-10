#!/usr/bin/env python3
"""
ESPN Position-Specific Rankings Scraper
Scrapes ESPN's position-specific ranking pages
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
import psycopg2
from datetime import datetime
import os
from typing import List, Dict, Optional, Tuple

class ESPNPositionScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none'
        })
        
        # ESPN position-specific URLs (exact URLs provided)
        self.position_urls = {
            'QB': 'https://www.espn.com/fantasy/football/story/_/page/FFPreseasonRank25QBPPR/nfl-fantasy-football-draft-rankings-2025-qb-quarterback',
            'RB': 'https://www.espn.com/fantasy/football/story/_/page/FFPreseasonRank25RBPPR/nfl-fantasy-football-draft-rankings-2025-rb-running-back-ppr',
            'WR': 'https://www.espn.com/fantasy/football/story/_/page/FFPreseasonRank25WRPPR/nfl-fantasy-football-draft-rankings-2025-wr-wide-receiver-ppr',
            'TE': 'https://www.espn.com/fantasy/football/story/_/page/FFPreseasonRank25TEPPR/nfl-fantasy-football-draft-rankings-2025-te-tight-end-ppr',
            'K': 'https://www.espn.com/fantasy/football/story/_/page/FFPreseasonRank25KPPR/nfl-fantasy-football-draft-rankings-2025-kicker-k',
            'DST': 'https://www.espn.com/fantasy/football/story/_/page/FFPreseasonRank25DSTPPR/nfl-fantasy-football-draft-rankings-2025-dst-defense'
        }
        
    def get_db_connection(self):
        """Get database connection"""
        return psycopg2.connect(
            host='localhost',
            port='5432',
            user=os.environ.get('USER', 'jeffgreenfield'),
            password='',
            database='fantasy_draft_db'
        )
    
    def scrape_all_positions(self) -> Dict[str, List[Dict]]:
        """Scrape all position-specific ESPN ranking pages"""
        print("🏈 Scraping ESPN 2025 Position-Specific Rankings...")
        
        all_rankings = {}
        
        for position, url in self.position_urls.items():
            print(f"\\n📊 Scraping {position} rankings...")
            print(f"🌐 URL: {url}")
            
            try:
                # Add delay between requests to be respectful
                time.sleep(1)
                
                response = self.session.get(url, timeout=30)
                print(f"📡 Response status: {response.status_code}")
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    print(f"✅ Successfully loaded {position} rankings page")
                    
                    # Parse rankings from this position page
                    position_rankings = self._parse_position_page(soup, position, url)
                    
                    if position_rankings:
                        all_rankings[position] = position_rankings
                        print(f"✅ Found {len(position_rankings)} {position} players")
                    else:
                        print(f"❌ No rankings found for {position}")
                        
                elif response.status_code == 403:
                    print(f"🚫 Access blocked for {position} (403 error)")
                elif response.status_code == 404:
                    print(f"📄 Page not found for {position} (404 error)")
                else:
                    print(f"❌ Failed to load {position}: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Error scraping {position}: {e}")
                continue
        
        total_players = sum(len(players) for players in all_rankings.values())
        print(f"\\n🎯 SCRAPING SUMMARY:")
        print(f"   ✅ Positions scraped: {len(all_rankings)} / {len(self.position_urls)}")
        print(f"   📊 Total players found: {total_players}")
        
        for pos, players in all_rankings.items():
            print(f"   {pos}: {len(players)} players")
            
        return all_rankings
    
    def _parse_position_page(self, soup: BeautifulSoup, position: str, url: str) -> List[Dict]:
        """Parse rankings from a position-specific page"""
        players = []
        
        # Debug page content
        page_text = soup.get_text()
        print(f"📄 Page length: {len(page_text)} characters")
        
        # Look for ranking patterns in the page text
        print(f"🔍 Looking for {position} ranking patterns...")
        
        # Method 1: Look for numbered lists with player names
        numbered_patterns = [
            r'(\d+)\s*[\.-]\s*([A-Z][a-z]+\s+[A-Z][a-z\']*(?:\s+[A-Z][a-z\']*)*?)(?:\s*[,\(]\s*([A-Z]{2,4}))?',
            r'(\d+)\s+([A-Z][a-z]+\s+[A-Z][a-z\']*(?:\s+[A-Z][a-z\']*)*?)(?:\s*[,\(]\s*([A-Z]{2,4}))?'
        ]
        
        for pattern in numbered_patterns:
            matches = re.finditer(pattern, page_text, re.MULTILINE)
            temp_players = []
            
            for match in matches:
                try:
                    rank = int(match.group(1))
                    name = match.group(2).strip()
                    team = match.group(3) if match.group(3) else ''
                    
                    # Validate this looks like a real player name
                    if (self._is_valid_player_name(name) and 
                        rank <= 50 and  # Reasonable rank limit
                        len(name.split()) >= 2):  # At least first and last name
                        
                        temp_players.append({
                            'name': name,
                            'position': position,
                            'team': team,
                            'rank': rank,
                            'source': 'ESPN',
                            'raw_text': match.group(0)
                        })
                        
                except (ValueError, IndexError):
                    continue
            
            if temp_players:
                print(f"✅ Pattern found {len(temp_players)} {position} players")
                players.extend(temp_players)
                break  # Use first successful pattern
        
        # Method 2: Look for structured HTML elements
        if not players:
            print(f"🔍 Trying structured HTML approach for {position}...")
            
            # Look for ordered lists
            ordered_lists = soup.find_all('ol')
            for ol in ordered_lists:
                list_items = ol.find_all('li')
                if len(list_items) > 5:  # Likely a ranking list
                    temp_players = []
                    for i, li in enumerate(list_items, 1):
                        text = li.get_text().strip()
                        player_info = self._extract_player_from_text(text, position, i)
                        if player_info:
                            temp_players.append(player_info)
                    
                    if temp_players:
                        print(f"✅ HTML list found {len(temp_players)} {position} players")
                        players.extend(temp_players)
                        break
        
        # Method 3: Look for specific ESPN ranking containers
        if not players:
            print(f"🔍 Trying ESPN-specific containers for {position}...")
            
            # Look for divs that might contain rankings
            ranking_containers = soup.find_all('div', class_=re.compile(r'rank|player|list', re.I))
            for container in ranking_containers:
                text = container.get_text()
                if len(text) > 50:  # Has substantial content
                    container_players = self._extract_players_from_container_text(text, position)
                    if container_players:
                        players.extend(container_players)
        
        # Clean up and deduplicate
        if players:
            # Remove duplicates based on name
            seen_names = set()
            unique_players = []
            for player in players:
                name_key = player['name'].lower().strip()
                if name_key not in seen_names:
                    seen_names.add(name_key)
                    unique_players.append(player)
            
            # Sort by rank and re-rank if needed
            unique_players.sort(key=lambda x: x['rank'])
            for i, player in enumerate(unique_players, 1):
                player['rank'] = i
            
            players = unique_players[:30]  # Limit to top 30
        
        return players
    
    def _extract_players_from_container_text(self, text: str, position: str) -> List[Dict]:
        """Extract players from container text"""
        players = []
        
        # Split by common delimiters and look for player names
        lines = re.split(r'[\n\r]+', text)
        rank = 1
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for player name patterns
            name_matches = re.finditer(r'\b([A-Z][a-z]+\s+[A-Z][a-z\']*(?:\s+[A-Z][a-z\']*)*)\b', line)
            for match in name_matches:
                name = match.group(1).strip()
                
                if (self._is_valid_player_name(name) and 
                    len(name.split()) >= 2 and
                    rank <= 30):
                    
                    # Look for team in the same line
                    team_match = re.search(r'\b([A-Z]{2,4})\b', line)
                    team = team_match.group(1) if team_match else ''
                    
                    players.append({
                        'name': name,
                        'position': position,
                        'team': team,
                        'rank': rank,
                        'source': 'ESPN',
                        'raw_text': line[:100]
                    })
                    rank += 1
                    break  # One player per line
        
        return players
    
    def _extract_player_from_text(self, text: str, position: str, rank: int) -> Optional[Dict]:
        """Extract player info from text"""
        # Remove leading numbers/bullets
        text = re.sub(r'^\d+[\.-]\s*', '', text)
        
        # Look for player name
        name_match = re.search(r'([A-Z][a-z]+\s+[A-Z][a-z\']*(?:\s+[A-Z][a-z\']*)*)', text)
        if not name_match:
            return None
        
        name = name_match.group(1).strip()
        
        # Look for team
        team_match = re.search(r'\b([A-Z]{2,4})\b', text)
        team = team_match.group(1) if team_match else ''
        
        # Validate team is NFL team
        nfl_teams = {'ARI', 'ATL', 'BAL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE',
                     'DAL', 'DEN', 'DET', 'GB', 'HOU', 'IND', 'JAX', 'KC',
                     'LV', 'LAC', 'LAR', 'MIA', 'MIN', 'NE', 'NO', 'NYG',
                     'NYJ', 'PHI', 'PIT', 'SF', 'SEA', 'TB', 'TEN', 'WAS'}
        
        if team not in nfl_teams:
            team = ''
        
        if self._is_valid_player_name(name):
            return {
                'name': name,
                'position': position,
                'team': team,
                'rank': rank,
                'source': 'ESPN',
                'raw_text': text[:100]
            }
        
        return None
    
    def _is_valid_player_name(self, name: str) -> bool:
        """Check if text looks like a valid player name"""
        if not name or len(name) < 4:
            return False
        
        # Should have at least first and last name
        words = name.split()
        if len(words) < 2:
            return False
        
        # Should not contain numbers (except for Jr., Sr., III, etc.)
        if re.search(r'\d', name) and not re.search(r'\b(Jr|Sr|III|IV|V)\b', name):
            return False
        
        # Should not contain too many special chars
        if re.search(r'[#$%^&*()+=\[\]{}|\:";?/><,]', name):
            return False
        
        # Each word should start with capital letter
        for word in words:
            if word and not word[0].isupper():
                return False
        
        # Exclude common non-names
        excluded_terms = ['quarterback', 'running', 'wide', 'tight', 'kicker', 'defense', 
                         'back', 'receiver', 'end', 'rankings', 'draft', 'fantasy',
                         'football', 'nfl', 'espn', 'ppr', 'standard', 'league']
        
        name_lower = name.lower()
        for term in excluded_terms:
            if term in name_lower:
                return False
        
        return True
    
    def match_with_database(self, espn_rankings: Dict[str, List[Dict]]) -> Tuple[List[Dict], List[Dict]]:
        """Match ESPN rankings with our player database"""
        print("🔗 Matching ESPN position rankings with database...")
        
        conn = self.get_db_connection()
        cur = conn.cursor()
        
        # Get all players from our database
        cur.execute("""
            SELECT player_id, name, position, team 
            FROM players 
            ORDER BY position, name
        """)
        db_players = cur.fetchall()
        
        matched_players = []
        unmatched_espn_players = []
        
        for position, espn_players in espn_rankings.items():
            print(f"📊 Matching {position} players...")
            
            for espn_player in espn_players:
                espn_name = espn_player['name'].lower().strip()
                espn_position = espn_player['position']
                espn_team = espn_player['team']
                
                # Try to find match in database
                best_match = None
                best_score = 0
                
                for db_player in db_players:
                    db_id, db_name, db_position, db_team = db_player
                    
                    # Must match position
                    if db_position != espn_position:
                        continue
                    
                    # Calculate name match score
                    db_name_clean = db_name.lower().strip()
                    
                    # Exact match
                    if espn_name == db_name_clean:
                        best_match = db_player
                        best_score = 100
                        break
                    
                    # Partial name matches
                    espn_parts = espn_name.split()
                    db_parts = db_name_clean.split()
                    
                    if len(espn_parts) >= 2 and len(db_parts) >= 2:
                        # First and last name match
                        if espn_parts[0] == db_parts[0] and espn_parts[-1] == db_parts[-1]:
                            score = 95
                            # Bonus for team match
                            if espn_team and db_team == espn_team:
                                score += 5
                            if score > best_score:
                                best_match = db_player
                                best_score = score
                        
                        # Last name match
                        elif espn_parts[-1] == db_parts[-1]:
                            score = 80
                            # Bonus for team match
                            if espn_team and db_team == espn_team:
                                score += 10
                            if score > best_score:
                                best_match = db_player
                                best_score = score
                
                if best_match and best_score >= 80:
                    matched_players.append({
                        'db_player_id': best_match[0],
                        'db_name': best_match[1],
                        'db_position': best_match[2],
                        'db_team': best_match[3],
                        'espn_name': espn_player['name'],
                        'espn_rank': espn_player['rank'],
                        'espn_position': espn_player['position'],
                        'espn_team': espn_player['team'],
                        'match_score': best_score,
                        'source': 'ESPN'
                    })
                else:
                    unmatched_espn_players.append(espn_player)
        
        cur.close()
        conn.close()
        
        print(f"✅ Matched {len(matched_players)} players")
        print(f"❓ {len(unmatched_espn_players)} ESPN players not found in database")
        
        return matched_players, unmatched_espn_players
    
    def save_rankings_to_database(self, matched_players: List[Dict]):
        """Save matched rankings to database"""
        print("💾 Saving ESPN position rankings to database...")
        
        conn = self.get_db_connection()
        cur = conn.cursor()
        
        # Ensure ESPN source exists
        cur.execute("""
            INSERT INTO ranking_sources (source_name, base_url)
            VALUES (%s, %s)
            ON CONFLICT (source_name) DO NOTHING
        """, ('ESPN', 'https://www.espn.com/fantasy/football/'))
        
        # Get ESPN source ID
        cur.execute("SELECT source_id FROM ranking_sources WHERE source_name = 'ESPN'")
        espn_source_id = cur.fetchone()[0]
        
        # Insert rankings
        inserted_count = 0
        for player in matched_players:
            try:
                cur.execute("""
                    INSERT INTO player_rankings (player_id, source_id, position_rank, ranking_date)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (player_id, source_id, ranking_date) DO UPDATE SET
                        position_rank = EXCLUDED.position_rank
                """, (
                    player['db_player_id'],
                    espn_source_id,
                    player['espn_rank'],
                    datetime.now().date()
                ))
                inserted_count += 1
            except Exception as e:
                print(f"❌ Error inserting ranking for {player['db_name']}: {e}")
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"✅ Saved {inserted_count} ESPN rankings to database")
    
    def generate_report(self, matched_players: List[Dict], unmatched_espn_players: List[Dict], espn_rankings: Dict[str, List[Dict]]):
        """Generate detailed report"""
        print("\n" + "="*70)
        print("📊 ESPN POSITION-SPECIFIC RANKINGS REPORT")
        print("="*70)
        
        # Summary by position
        position_stats = {}
        for player in matched_players:
            pos = player['db_position']
            if pos not in position_stats:
                position_stats[pos] = {'matched': 0, 'total_espn': 0}
            position_stats[pos]['matched'] += 1
        
        # Count total ESPN rankings by position
        for position, players in espn_rankings.items():
            if position not in position_stats:
                position_stats[position] = {'matched': 0, 'total_espn': len(players)}
            else:
                position_stats[position]['total_espn'] = len(players)
        
        print(f\"\\n📈 ESPN RANKING COVERAGE:\")
        for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'DST']:
            if pos in position_stats:
                matched = position_stats[pos]['matched']
                total_espn = position_stats[pos]['total_espn']
                percentage = (matched / total_espn * 100) if total_espn > 0 else 0
                print(f\"  {pos}: {matched}/{total_espn} ESPN rankings matched ({percentage:.1f}%)\")
        
        print(f\"\\n🎯 SCRAPING RESULTS:\")
        total_scraped = sum(len(players) for players in espn_rankings.values())
        print(f\"  📊 Total rankings scraped: {total_scraped}\")
        print(f\"  ✅ Successfully matched: {len(matched_players)} players\")
        print(f\"  ❓ ESPN players not in DB: {len(unmatched_espn_players)} players\")
        
        if unmatched_espn_players:
            print(f\"\\n❓ UNMATCHED ESPN PLAYERS:\")
            by_position = {}
            for player in unmatched_espn_players:
                pos = player['position']
                if pos not in by_position:
                    by_position[pos] = []
                by_position[pos].append(player)
            
            for pos, players in sorted(by_position.items()):
                print(f\"\\n  {pos} ({len(players)} players):\")
                for player in players[:10]:  # Show top 10
                    team_info = f\" ({player['team']})\" if player['team'] else \"\"
                    print(f\"    #{player['rank']:2d} {player['name']}{team_info}\")
                if len(players) > 10:
                    print(f\"    ... and {len(players) - 10} more\")
        
        print(\"\\n\" + \"=\"*70)

def main():
    scraper = ESPNPositionScraper()
    
    print(\"🚀 Starting ESPN Position-Specific Rankings Scrape...\")
    
    # Step 1: Scrape all position-specific pages
    espn_rankings = scraper.scrape_all_positions()
    
    if not espn_rankings:
        print(\"❌ No rankings found from ESPN position pages.\")
        return
    
    # Step 2: Match with database
    matched_players, unmatched_espn_players = scraper.match_with_database(espn_rankings)
    
    # Step 3: Save to database
    if matched_players:
        scraper.save_rankings_to_database(matched_players)
    
    # Step 4: Generate report
    scraper.generate_report(matched_players, unmatched_espn_players, espn_rankings)
    
    print(\"\\n🎉 ESPN position rankings scrape completed!\")

if __name__ == \"__main__\":
    main()