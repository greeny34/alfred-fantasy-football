#!/usr/bin/env python3
"""
ESPN Fantasy Football Rankings Scraper
Scrapes ESPN's position rankings and matches with our player database
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

class ESPNRankingsScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # ESPN fantasy position mapping
        self.espn_positions = {
            'QB': 1,
            'RB': 2, 
            'WR': 3,
            'TE': 4,
            'K': 17,
            'DST': 16
        }
        
        # Base ESPN fantasy URL
        self.base_url = "https://www.espn.com/fantasy/football/story/_/id/33896370/fantasy-football-rankings-2024-best-players-qb-rb-wr-te-k-dst"
        
        self.rankings = {}
        
    def get_db_connection(self):
        """Get database connection"""
        return psycopg2.connect(
            host='localhost',
            port='5432',
            user=os.environ.get('USER', 'jeffgreenfield'),
            password='',
            database='fantasy_draft_db'
        )
    
    def scrape_espn_rankings(self) -> Dict[str, List[Dict]]:
        """
        Scrape ESPN's fantasy football rankings
        Returns rankings by position
        """
        print("🏈 Starting ESPN Fantasy Rankings Scrape...")
        
        try:
            # Try multiple ESPN fantasy ranking URLs for 2025 season
            rankings_urls = [
                "https://www.espn.com/fantasy/football/story/_/page/2025rankings/fantasy-football-rankings-2025-best-players-qb-rb-wr-te-k-dst",
                "https://www.espn.com/fantasy/football/story/_/id/33896370/fantasy-football-rankings-2024-best-players-qb-rb-wr-te-k-dst",
                "https://www.espn.com/fantasy/football/tools/rankings",
                "https://fantasy.espn.com/football/players/projections",
                "https://www.espn.com/fantasy/football/players/projections/_/scoringPeriodId/17",
                "https://www.espn.com/fantasy/football/freeagency",
                "https://www.espn.com/fantasy/football/players/add",
                "https://fantasy.espn.com/football/players/projections/_/view/projections_",
                "https://www.espn.com/fantasy/football/story/_/page/rankings/fantasy-football-week-1-rankings"
            ]
            
            for url in rankings_urls:
                print(f"📡 Trying URL: {url}")
                try:
                    response = self.session.get(url, timeout=30)
                    if response.status_code == 200:
                        print(f"✅ Successfully accessed {url}")
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Look for various ESPN ranking formats
                        rankings = self._parse_espn_rankings_page(soup, url)
                        if rankings:
                            print(f"✅ Found {sum(len(players) for players in rankings.values())} total rankings")
                            return rankings
                        else:
                            print(f"⚠️  No rankings found on {url}, trying next...")
                        
                except Exception as e:
                    print(f"❌ Failed to access {url}: {e}")
                    continue
            
            # If main pages don't work, try API approach
            print("📡 Trying ESPN API approach...")
            return self._scrape_via_espn_api()
            
        except Exception as e:
            print(f"❌ Error scraping ESPN rankings: {e}")
            return {}
    
    def _parse_espn_rankings_page(self, soup: BeautifulSoup, url: str) -> Dict[str, List[Dict]]:
        """Parse ESPN rankings from HTML page"""
        rankings = {}
        
        print(f"🔍 Parsing page: {url[:80]}...")
        
        # Debug: Show page structure
        page_text = soup.get_text()[:500]
        print(f"📄 Page sample: {page_text[:200]}...")
        
        # Format 1: Look for ESPN's player tables/cards
        # Modern ESPN uses various div structures
        player_containers = soup.find_all(['div', 'tr', 'li'], class_=re.compile(r'player|rank|name|position', re.I))
        print(f"🔍 Found {len(player_containers)} potential player containers")
        
        # Try to parse player containers
        temp_players = []
        for container in player_containers[:100]:  # Limit to avoid noise
            text = container.get_text().strip()
            if len(text) > 10 and any(name in text for name in ['QB', 'RB', 'WR', 'TE', 'K', 'DST']):
                player_info = self._extract_player_from_text(text)
                if player_info:
                    temp_players.append(player_info)
        
        if temp_players:
            print(f"✅ Extracted {len(temp_players)} players from containers")
            # Group by position
            for player in temp_players:
                pos = player['position']
                if pos not in rankings:
                    rankings[pos] = []
                rankings[pos].append(player)
        
        # Format 2: Traditional tables
        tables = soup.find_all('table')
        print(f"🔍 Found {len(tables)} tables")
        for i, table in enumerate(tables):
            position_rankings = self._extract_rankings_from_table(table)
            if position_rankings:
                print(f"✅ Table {i+1} yielded rankings for: {list(position_rankings.keys())}")
                for pos, players in position_rankings.items():
                    if pos not in rankings:
                        rankings[pos] = []
                    rankings[pos].extend(players)
        
        # Format 3: Look for structured lists
        lists = soup.find_all(['ol', 'ul'])
        print(f"🔍 Found {len(lists)} lists")
        for i, list_elem in enumerate(lists):
            list_items = list_elem.find_all('li')
            if len(list_items) > 5:  # Likely a rankings list
                position_rankings = self._extract_rankings_from_list(list_elem)
                if position_rankings:
                    print(f"✅ List {i+1} yielded rankings for: {list(position_rankings.keys())}")
                    for pos, players in position_rankings.items():
                        if pos not in rankings:
                            rankings[pos] = []
                        rankings[pos].extend(players)
        
        # Format 4: JSON data embedded in page
        scripts = soup.find_all('script')
        print(f"🔍 Found {len(scripts)} script tags")
        for script in scripts:
            if script.string and len(script.string) > 100:
                # Look for player data patterns
                if any(pattern in script.string.lower() for pattern in ['player', 'athlete', 'fantasy', 'rank']):
                    json_rankings = self._extract_json_from_script(script.string)
                    if json_rankings:
                        print(f"✅ Script yielded rankings for: {list(json_rankings.keys())}")
                        for pos, players in json_rankings.items():
                            if pos not in rankings:
                                rankings[pos] = []
                            rankings[pos].extend(players)
        
        # Clean up and deduplicate
        for pos in rankings:
            # Remove duplicates based on name
            seen_names = set()
            unique_players = []
            for player in rankings[pos]:
                name_key = player['name'].lower().strip()
                if name_key not in seen_names:
                    seen_names.add(name_key)
                    unique_players.append(player)
            rankings[pos] = unique_players
            
            # Re-rank players
            for i, player in enumerate(rankings[pos], 1):
                player['rank'] = i
        
        if rankings:
            total_players = sum(len(players) for players in rankings.values())
            print(f"✅ Final rankings - {total_players} players across positions: {list(rankings.keys())}")
            for pos, players in rankings.items():
                print(f"   {pos}: {len(players)} players")
        else:
            print("❌ No rankings extracted from this page")
        
        return rankings
    
    def _extract_rankings_from_table(self, table) -> Dict[str, List[Dict]]:
        """Extract rankings from HTML table"""
        rankings = {}
        
        rows = table.find_all('tr')
        if len(rows) < 2:
            return rankings
        
        # Try to identify position from table headers or context
        headers = [th.get_text().strip() for th in rows[0].find_all(['th', 'td'])]
        
        # Look for position indicators
        position = None
        for header in headers:
            for pos in self.espn_positions.keys():
                if pos.lower() in header.lower():
                    position = pos
                    break
            if position:
                break
        
        if not position:
            # Try to infer from player names in rows
            for row in rows[1:6]:  # Check first few rows
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    player_text = cells[1].get_text().strip()
                    # Look for position indicators in player text
                    for pos in self.espn_positions.keys():
                        if pos in player_text or f"({pos})" in player_text:
                            position = pos
                            break
                if position:
                    break
        
        if not position:
            return rankings
        
        # Extract player data from rows
        players = []
        for i, row in enumerate(rows[1:], 1):
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                rank = i
                player_text = cells[1].get_text().strip()
                
                # Parse player name (remove position, team info)
                player_name = self._clean_player_name(player_text)
                team = self._extract_team_from_text(player_text)
                
                if player_name:
                    players.append({
                        'name': player_name,
                        'position': position,
                        'team': team,
                        'rank': rank,
                        'source': 'ESPN',
                        'raw_text': player_text
                    })
        
        if players:
            rankings[position] = players
        
        return rankings
    
    def _extract_rankings_from_section(self, section) -> Dict[str, List[Dict]]:
        """Extract rankings from HTML section/list"""
        rankings = {}
        
        # Look for position headers
        position = None
        position_header = section.find_previous(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if position_header:
            header_text = position_header.get_text().strip()
            for pos in self.espn_positions.keys():
                if pos.lower() in header_text.lower():
                    position = pos
                    break
        
        if not position:
            # Try to find position in section classes or attributes
            section_text = str(section)
            for pos in self.espn_positions.keys():
                if pos.lower() in section_text.lower():
                    position = pos
                    break
        
        if not position:
            return rankings
        
        # Extract player items
        player_items = section.find_all(['li', 'div'], recursive=True)
        players = []
        
        for i, item in enumerate(player_items[:50], 1):  # Limit to top 50
            item_text = item.get_text().strip()
            
            # Skip if too short or doesn't look like player info
            if len(item_text) < 5 or not any(c.isalpha() for c in item_text):
                continue
            
            player_name = self._clean_player_name(item_text)
            team = self._extract_team_from_text(item_text)
            
            if player_name:
                players.append({
                    'name': player_name,
                    'position': position,
                    'team': team,
                    'rank': i,
                    'source': 'ESPN',
                    'raw_text': item_text
                })
        
        if players:
            rankings[position] = players
        
        return rankings
    
    def _extract_rankings_from_json(self, data: Dict) -> Dict[str, List[Dict]]:
        """Extract rankings from JSON data"""
        rankings = {}
        
        # Try different JSON structures ESPN might use
        if 'players' in data:
            players_data = data['players']
            if isinstance(players_data, list):
                for i, player in enumerate(players_data, 1):
                    if isinstance(player, dict):
                        name = player.get('name', player.get('fullName', ''))
                        position = player.get('position', player.get('eligibleSlots', [''])[0])
                        team = player.get('team', player.get('proTeam', ''))
                        
                        # Map ESPN position codes to our format
                        if isinstance(position, int):
                            position = self._map_espn_position_code(position)
                        
                        if name and position in self.espn_positions:
                            if position not in rankings:
                                rankings[position] = []
                            
                            rankings[position].append({
                                'name': name,
                                'position': position,
                                'team': team,
                                'rank': i,
                                'source': 'ESPN',
                                'raw_text': str(player)
                            })
        
        return rankings
    
    def _scrape_via_espn_api(self) -> Dict[str, List[Dict]]:
        """Try to scrape via ESPN's fantasy API endpoints"""
        rankings = {}
        
        # ESPN Fantasy API endpoints for 2025 season
        api_urls = [
            "https://fantasy.espn.com/apis/v3/games/ffl/seasons/2025/segments/0/leaguedefaults/3?view=kona_player_info",
            "https://fantasy.espn.com/apis/v3/games/ffl/seasons/2024/segments/0/leaguedefaults/3?view=kona_player_info",
            "https://site.api.espn.com/apis/fantasy/v2/games/ffl/players",
            "https://fantasy.espn.com/apis/v3/games/ffl/players",
            "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/athletes"
        ]
        
        for url in api_urls:
            try:
                print(f"📡 Trying API: {url}")
                response = self.session.get(url, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    api_rankings = self._extract_rankings_from_json(data)
                    if api_rankings:
                        for pos, players in api_rankings.items():
                            if pos not in rankings:
                                rankings[pos] = []
                            rankings[pos].extend(players)
                        
                        print(f"✅ Found API rankings for positions: {list(api_rankings.keys())}")
                
            except Exception as e:
                print(f"❌ API failed {url}: {e}")
                continue
        
        return rankings
    
    def _extract_player_from_text(self, text: str) -> Optional[Dict]:
        """Extract player info from text string"""
        # Look for patterns like "1. Patrick Mahomes QB KC" or "Josh Allen, QB, BUF"
        
        # Remove rank numbers at start
        text = re.sub(r'^\d+\.?\s*', '', text)
        
        # Look for position patterns
        position = None
        for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'DST']:
            if pos in text:
                position = pos
                break
        
        if not position:
            return None
        
        # Extract name (usually before position)
        parts = text.split()
        name_parts = []
        for part in parts:
            if part in ['QB', 'RB', 'WR', 'TE', 'K', 'DST']:
                break
            if part.isalpha() and len(part) > 1:
                name_parts.append(part)
        
        if len(name_parts) >= 2:
            name = f"{name_parts[0]} {name_parts[1]}"
        elif len(name_parts) == 1:
            name = name_parts[0]
        else:
            return None
        
        # Extract team
        team = self._extract_team_from_text(text)
        
        return {
            'name': name,
            'position': position,
            'team': team,
            'rank': 1,  # Will be set later
            'source': 'ESPN',
            'raw_text': text[:100]
        }
    
    def _extract_rankings_from_list(self, list_elem) -> Dict[str, List[Dict]]:
        """Extract rankings from HTML list element"""
        rankings = {}
        
        items = list_elem.find_all('li')
        position = None
        
        # Try to determine position from context
        list_text = list_elem.get_text().lower()
        for pos in ['quarterback', 'running back', 'wide receiver', 'tight end', 'kicker', 'defense']:
            if pos in list_text:
                position_map = {
                    'quarterback': 'QB',
                    'running back': 'RB', 
                    'wide receiver': 'WR',
                    'tight end': 'TE',
                    'kicker': 'K',
                    'defense': 'DST'
                }
                position = position_map[pos]
                break
        
        # If no position found, try to infer from items
        if not position and items:
            for item in items[:5]:
                item_text = item.get_text()
                for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'DST']:
                    if pos in item_text:
                        position = pos
                        break
                if position:
                    break
        
        if not position:
            return rankings
        
        players = []
        for i, item in enumerate(items, 1):
            item_text = item.get_text().strip()
            player_info = self._extract_player_from_text(item_text)
            if player_info:
                player_info['rank'] = i
                players.append(player_info)
        
        if players:
            rankings[position] = players
        
        return rankings
    
    def _extract_json_from_script(self, script_text: str) -> Dict[str, List[Dict]]:
        """Extract rankings from JavaScript/JSON in script tags"""
        rankings = {}
        
        try:
            # Look for various JSON patterns
            patterns = [
                r'"players"\s*:\s*\[(.*?)\]',
                r'"athletes"\s*:\s*\[(.*?)\]',
                r'playerData\s*=\s*({.*?});',
                r'rankings\s*=\s*({.*?});'
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, script_text, re.DOTALL)
                for match in matches:
                    try:
                        # Try to parse the matched JSON
                        json_str = '{' + match.group(1) + '}'
                        data = json.loads(json_str)
                        
                        json_rankings = self._extract_rankings_from_json(data)
                        if json_rankings:
                            for pos, players in json_rankings.items():
                                if pos not in rankings:
                                    rankings[pos] = []
                                rankings[pos].extend(players)
                    except:
                        continue
        
        except Exception as e:
            pass
        
        return rankings
    
    def _clean_player_name(self, text: str) -> str:
        """Clean and extract player name from text"""
        # Remove common suffixes and team info
        text = re.sub(r'\s*\([^)]*\)', '', text)  # Remove parentheses content
        text = re.sub(r'\s*,.*$', '', text)       # Remove comma and everything after
        text = re.sub(r'\s*-.*$', '', text)       # Remove dash and everything after
        text = re.sub(r'\s+', ' ', text).strip()  # Normalize whitespace
        
        # Extract just the name part (first two words typically)
        words = text.split()
        if len(words) >= 2:
            return f"{words[0]} {words[1]}"
        elif len(words) == 1:
            return words[0]
        
        return text.strip()
    
    def _extract_team_from_text(self, text: str) -> str:
        """Extract team abbreviation from text"""
        # Look for team patterns
        team_match = re.search(r'\b([A-Z]{2,4})\b', text)
        if team_match:
            team = team_match.group(1)
            # Validate it's a real NFL team
            nfl_teams = ['ARI', 'ATL', 'BAL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE',
                        'DAL', 'DEN', 'DET', 'GB', 'HOU', 'IND', 'JAX', 'KC',
                        'LV', 'LAC', 'LAR', 'MIA', 'MIN', 'NE', 'NO', 'NYG',
                        'NYJ', 'PHI', 'PIT', 'SF', 'SEA', 'TB', 'TEN', 'WAS']
            if team in nfl_teams:
                return team
        
        return ""
    
    def _map_espn_position_code(self, code: int) -> str:
        """Map ESPN position codes to our position strings"""
        code_map = {
            1: 'QB',
            2: 'RB',
            3: 'WR', 
            4: 'TE',
            16: 'DST',
            17: 'K'
        }
        return code_map.get(code, '')
    
    def match_with_database(self, espn_rankings: Dict[str, List[Dict]]) -> Tuple[List[Dict], List[Dict]]:
        """
        Match ESPN rankings with our player database
        Returns (matched_players, unmatched_espn_players)
        """
        print("🔗 Matching ESPN rankings with database...")
        
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
                            score = 90
                            # Bonus for team match
                            if espn_team and db_team == espn_team:
                                score += 5
                            
                            if score > best_score:
                                best_match = db_player
                                best_score = score
                        
                        # Last name match (common for fantasy)
                        elif espn_parts[-1] == db_parts[-1]:
                            score = 70
                            # Bonus for team match
                            if espn_team and db_team == espn_team:
                                score += 10
                            
                            if score > best_score:
                                best_match = db_player
                                best_score = score
                
                if best_match and best_score >= 75:  # Minimum confidence threshold
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
        print("💾 Saving ESPN rankings to database...")
        
        conn = self.get_db_connection()
        cur = conn.cursor()
        
        # Ensure ESPN source exists
        cur.execute("""
            INSERT INTO ranking_sources (source_name, source_url, last_updated)
            VALUES (%s, %s, %s)
            ON CONFLICT (source_name) DO UPDATE SET
                last_updated = EXCLUDED.last_updated
        """, ('ESPN', 'https://www.espn.com/fantasy/football/', datetime.now()))
        
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
                    ON CONFLICT (player_id, source_id) DO UPDATE SET
                        position_rank = EXCLUDED.position_rank,
                        ranking_date = EXCLUDED.ranking_date
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
    
    def generate_report(self, matched_players: List[Dict], unmatched_espn_players: List[Dict]):
        """Generate a detailed report of the scraping results"""
        print("\n" + "="*60)
        print("📊 ESPN RANKINGS SCRAPING REPORT")
        print("="*60)
        
        # Summary by position
        position_stats = {}
        for player in matched_players:
            pos = player['db_position']
            if pos not in position_stats:
                position_stats[pos] = {'matched': 0, 'total_db': 0}
            position_stats[pos]['matched'] += 1
        
        # Get total players by position from database
        conn = self.get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT position, COUNT(*) 
            FROM players 
            GROUP BY position 
            ORDER BY position
        """)
        
        for position, count in cur.fetchall():
            if position not in position_stats:
                position_stats[position] = {'matched': 0, 'total_db': count}
            else:
                position_stats[position]['total_db'] = count
        
        cur.close()
        conn.close()
        
        print(f"\n📈 POSITION COVERAGE:")
        for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'DST']:
            if pos in position_stats:
                matched = position_stats[pos]['matched']
                total = position_stats[pos]['total_db']
                percentage = (matched / total * 100) if total > 0 else 0
                print(f"  {pos}: {matched}/{total} players ({percentage:.1f}% coverage)")
        
        print(f"\n🎯 MATCHING RESULTS:")
        print(f"  ✅ Successfully matched: {len(matched_players)} players")
        print(f"  ❓ ESPN players not in DB: {len(unmatched_espn_players)} players")
        
        if unmatched_espn_players:
            print(f"\n❓ UNMATCHED ESPN PLAYERS:")
            by_position = {}
            for player in unmatched_espn_players:
                pos = player['position']
                if pos not in by_position:
                    by_position[pos] = []
                by_position[pos].append(player)
            
            for pos, players in sorted(by_position.items()):
                print(f"\n  {pos} ({len(players)} players):")
                for player in players[:10]:  # Show top 10
                    print(f"    #{player['rank']:2d} {player['name']} ({player['team']})")
                if len(players) > 10:
                    print(f"    ... and {len(players) - 10} more")
        
        print("\n" + "="*60)

def main():
    scraper = ESPNRankingsScraper()
    
    print("🚀 Starting ESPN Rankings Import Process...")
    
    # Step 1: Scrape ESPN rankings
    espn_rankings = scraper.scrape_espn_rankings()
    
    if not espn_rankings:
        print("❌ No rankings found from ESPN. Check the scraper logic.")
        return
    
    print(f"✅ Scraped rankings for {len(espn_rankings)} positions")
    for pos, players in espn_rankings.items():
        print(f"  📊 {pos}: {len(players)} players")
    
    # Step 2: Match with database
    matched_players, unmatched_espn_players = scraper.match_with_database(espn_rankings)
    
    # Step 3: Save to database
    if matched_players:
        scraper.save_rankings_to_database(matched_players)
    
    # Step 4: Generate report
    scraper.generate_report(matched_players, unmatched_espn_players)
    
    print("\n🎉 ESPN rankings import completed!")

if __name__ == "__main__":
    main()