#!/usr/bin/env python3
"""
Real ESPN Fantasy Football Rankings Scraper
Scrapes ESPN's actual 2025 fantasy football rankings from the specific URL
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

class RealESPNScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        self.target_url = "https://www.espn.com/fantasy/football/story/_/id/44786976/fantasy-football-rankings-2025-draft-ppr"
        
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
        Scrape ESPN's real 2025 fantasy football rankings
        """
        print(f"🏈 Scraping ESPN 2025 Fantasy Rankings from:")
        print(f"   {self.target_url}")
        
        try:
            response = self.session.get(self.target_url, timeout=30)
            print(f"📡 Response status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"❌ Failed to access ESPN rankings: HTTP {response.status_code}")
                return {}
            
            soup = BeautifulSoup(response.content, 'html.parser')
            print(f"✅ Successfully loaded ESPN rankings page")
            
            # Debug: Show page content sample
            page_text = soup.get_text()
            print(f"📄 Page length: {len(page_text)} characters")
            if "fantasy" in page_text.lower() and "ranking" in page_text.lower():
                print("✅ Page contains fantasy ranking content")
            else:
                print("⚠️  Page may not contain expected ranking content")
                
            # Look for different ESPN ranking formats in the article
            rankings = self._parse_espn_article_rankings(soup)
            
            if rankings:
                total_players = sum(len(players) for players in rankings.values())
                print(f"✅ Successfully extracted {total_players} rankings across {len(rankings)} positions")
                for pos, players in rankings.items():
                    print(f"   {pos}: {len(players)} players")
            else:
                print("❌ No rankings found in the article")
                
            return rankings
            
        except Exception as e:
            print(f"❌ Error scraping ESPN rankings: {e}")
            return {}
    
    def _parse_espn_article_rankings(self, soup: BeautifulSoup) -> Dict[str, List[Dict]]:
        """Parse rankings from ESPN article format"""
        rankings = {}
        
        print("🔍 Parsing ESPN article for ranking lists...")
        
        # Method 1: Look for structured ranking lists in the article
        # ESPN often uses ordered lists or structured divs for rankings
        
        # Find all text that might contain rankings
        article_content = soup.find('div', class_=re.compile(r'article|story|content', re.I))
        if not article_content:
            article_content = soup.find('main') or soup
            
        print(f"📄 Found article content container")
        
        # Look for position headers and associated rankings
        position_sections = self._find_position_sections(article_content)
        
        for position, section_text in position_sections.items():
            print(f"🎯 Processing {position} section...")
            players = self._extract_players_from_text(section_text, position)
            if players:
                rankings[position] = players
                print(f"   ✅ Found {len(players)} {position} players")
        
        # Method 2: Look for structured lists
        if not rankings:
            print("🔍 Trying structured list approach...")
            lists = article_content.find_all(['ol', 'ul'])
            for i, list_elem in enumerate(lists):
                items = list_elem.find_all('li')
                if len(items) > 5:  # Likely a ranking list
                    print(f"📋 Analyzing list {i+1} with {len(items)} items")
                    list_rankings = self._parse_ranking_list(list_elem)
                    for pos, players in list_rankings.items():
                        if pos not in rankings:
                            rankings[pos] = []
                        rankings[pos].extend(players)
        
        # Method 3: Look for table structures
        if not rankings:
            print("🔍 Trying table approach...")
            tables = article_content.find_all('table')
            for i, table in enumerate(tables):
                print(f"📊 Analyzing table {i+1}")
                table_rankings = self._parse_ranking_table(table)
                for pos, players in table_rankings.items():
                    if pos not in rankings:
                        rankings[pos] = []
                    rankings[pos].extend(players)
        
        # Method 4: Look for embedded JSON or structured data
        if not rankings:
            print("🔍 Trying JSON/script data approach...")
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and len(script.string) > 100:
                    if any(term in script.string.lower() for term in ['ranking', 'player', 'fantasy']):
                        json_rankings = self._extract_json_rankings(script.string)
                        for pos, players in json_rankings.items():
                            if pos not in rankings:
                                rankings[pos] = []
                            rankings[pos].extend(players)
        
        # Clean and validate rankings
        cleaned_rankings = {}
        for pos, players in rankings.items():
            if pos in ['QB', 'RB', 'WR', 'TE', 'K', 'DST'] and players:
                # Remove duplicates and re-rank
                seen_names = set()
                unique_players = []
                for player in players:
                    name_key = player['name'].lower().strip()
                    if name_key not in seen_names:
                        seen_names.add(name_key)
                        unique_players.append(player)
                
                # Re-rank
                for i, player in enumerate(unique_players, 1):
                    player['rank'] = i
                
                cleaned_rankings[pos] = unique_players
        
        return cleaned_rankings
    
    def _find_position_sections(self, content) -> Dict[str, str]:
        """Find sections for each fantasy position"""
        sections = {}
        
        # Look for position headers
        position_patterns = {
            'QB': [r'quarterback', r'\bqb\b', r'qb rankings', r'qb\s+rankings'],
            'RB': [r'running back', r'\brb\b', r'rb rankings', r'rb\s+rankings'], 
            'WR': [r'wide receiver', r'\bwr\b', r'wr rankings', r'wr\s+rankings'],
            'TE': [r'tight end', r'\bte\b', r'te rankings', r'te\s+rankings'],
            'K': [r'kicker', r'\bk\b', r'k rankings', r'kicker rankings'],
            'DST': [r'defense', r'dst', r'd/st', r'defense rankings', r'team defense']
        }
        
        text_content = content.get_text()
        
        for position, patterns in position_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    # Extract text around the match (next 2000 chars)
                    start = match.start()
                    section_text = text_content[start:start + 2000]
                    
                    if position not in sections or len(section_text) > len(sections[position]):
                        sections[position] = section_text
                    break
        
        return sections
    
    def _extract_players_from_text(self, text: str, position: str) -> List[Dict]:
        """Extract ranked players from text section"""
        players = []
        
        # Look for numbered lists or ranking patterns
        patterns = [
            r'(\d+)\.\s*([A-Z][a-z]+\s+[A-Z][a-z]+)(?:\s*[,\(\-]\s*([A-Z]{2,4}))?',  # "1. Josh Allen, BUF"
            r'(\d+)\s*[-\.]\s*([A-Z][a-z]+\s+[A-Z][a-z]+)(?:\s*[,\(\-]\s*([A-Z]{2,4}))?',  # "1 - Josh Allen (BUF)"
            r'(\d+)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)(?:\s*[,\(\-]\s*([A-Z]{2,4}))?'  # "1 Josh Allen BUF"
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.MULTILINE)
            for match in matches:
                rank = int(match.group(1))
                name = match.group(2).strip()
                team = match.group(3) if match.group(3) else ''
                
                # Validate this looks like a real NFL player
                if self._is_valid_player_name(name) and rank <= 50:  # Reasonable rank limit
                    players.append({
                        'name': name,
                        'position': position,
                        'team': team,
                        'rank': rank,
                        'source': 'ESPN',
                        'raw_text': match.group(0)
                    })
        
        # Sort by rank and remove duplicates
        players.sort(key=lambda x: x['rank'])
        seen_names = set()
        unique_players = []
        for player in players:
            name_key = player['name'].lower()
            if name_key not in seen_names:
                seen_names.add(name_key)
                unique_players.append(player)
        
        return unique_players[:30]  # Limit to top 30 per position
    
    def _parse_ranking_list(self, list_elem) -> Dict[str, List[Dict]]:
        """Parse rankings from HTML list element"""
        rankings = {}
        
        # Try to determine position from context
        position = self._determine_position_from_context(list_elem)
        if not position:
            return rankings
        
        items = list_elem.find_all('li')
        players = []
        
        for i, item in enumerate(items, 1):
            text = item.get_text().strip()
            player_info = self._extract_player_from_list_item(text, position, i)
            if player_info:
                players.append(player_info)
        
        if players:
            rankings[position] = players
        
        return rankings
    
    def _parse_ranking_table(self, table) -> Dict[str, List[Dict]]:
        """Parse rankings from HTML table"""
        rankings = {}
        
        rows = table.find_all('tr')
        if len(rows) < 2:
            return rankings
        
        # Try to determine position and structure
        headers = [th.get_text().strip().lower() for th in rows[0].find_all(['th', 'td'])]
        
        # Look for position indicators
        position = None
        for header in headers:
            for pos in ['qb', 'rb', 'wr', 'te', 'k', 'dst', 'defense']:
                if pos in header:
                    position = {'qb': 'QB', 'rb': 'RB', 'wr': 'WR', 'te': 'TE', 'k': 'K', 'dst': 'DST', 'defense': 'DST'}[pos]
                    break
            if position:
                break
        
        if not position:
            return rankings
        
        players = []
        for i, row in enumerate(rows[1:], 1):
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                # Try to extract player info from cells
                for cell in cells:
                    text = cell.get_text().strip()
                    if self._is_valid_player_name(text):
                        players.append({
                            'name': text,
                            'position': position,
                            'team': '',
                            'rank': i,
                            'source': 'ESPN',
                            'raw_text': text
                        })
                        break
        
        if players:
            rankings[position] = players
        
        return rankings
    
    def _extract_json_rankings(self, script_text: str) -> Dict[str, List[Dict]]:
        """Extract rankings from JSON in script tags"""
        rankings = {}
        
        try:
            # Look for JSON patterns that might contain player rankings
            json_patterns = [
                r'"players"\s*:\s*\[(.*?)\]',
                r'"rankings"\s*:\s*\[(.*?)\]',
                r'"athletes"\s*:\s*\[(.*?)\]'
            ]
            
            for pattern in json_patterns:
                matches = re.finditer(pattern, script_text, re.DOTALL)
                for match in matches:
                    try:
                        json_str = '[' + match.group(1) + ']'
                        data = json.loads(json_str)
                        
                        for item in data:
                            if isinstance(item, dict) and 'name' in item:
                                name = item.get('name', item.get('fullName', ''))
                                position = item.get('position', '')
                                team = item.get('team', '')
                                
                                if name and position in ['QB', 'RB', 'WR', 'TE', 'K', 'DST']:
                                    if position not in rankings:
                                        rankings[position] = []
                                    
                                    rankings[position].append({
                                        'name': name,
                                        'position': position,
                                        'team': team,
                                        'rank': len(rankings[position]) + 1,
                                        'source': 'ESPN',
                                        'raw_text': str(item)
                                    })
                    except:
                        continue
        
        except Exception as e:
            pass
        
        return rankings
    
    def _determine_position_from_context(self, element) -> Optional[str]:
        """Determine fantasy position from element context"""
        # Check element and parent text for position indicators
        context_text = ""
        current = element
        for _ in range(3):  # Check 3 levels up
            if current:
                context_text += current.get_text().lower()
                current = current.parent
            else:
                break
        
        position_keywords = {
            'QB': ['quarterback', 'qb'],
            'RB': ['running back', 'rb', 'runningback'],
            'WR': ['wide receiver', 'wr', 'receiver'],
            'TE': ['tight end', 'te'],
            'K': ['kicker', 'k'],
            'DST': ['defense', 'dst', 'd/st', 'team defense']
        }
        
        for position, keywords in position_keywords.items():
            if any(keyword in context_text for keyword in keywords):
                return position
        
        return None
    
    def _extract_player_from_list_item(self, text: str, position: str, rank: int) -> Optional[Dict]:
        """Extract player info from list item text"""
        # Clean up text
        text = re.sub(r'^\d+[\.\-\s]*', '', text)  # Remove leading numbers
        
        # Look for player name patterns
        name_match = re.search(r'([A-Z][a-z]+\s+[A-Z][a-z]+)', text)
        if not name_match:
            return None
        
        name = name_match.group(1).strip()
        
        # Look for team
        team_match = re.search(r'\b([A-Z]{2,4})\b', text)
        team = team_match.group(1) if team_match else ''
        
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
        
        # Should not contain numbers or special chars (except apostrophes, hyphens)
        if re.search(r'[0-9@#$%^&*()+=\[\]{}|\\:";?/>.<,]', name):
            return False
        
        # Each word should start with capital letter
        for word in words:
            if not word[0].isupper():
                return False
        
        return True
    
    def match_with_database(self, espn_rankings: Dict[str, List[Dict]]) -> Tuple[List[Dict], List[Dict]]:
        """Match ESPN rankings with our player database"""
        print("🔗 Matching real ESPN rankings with database...")
        
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
                    
                    # For DST, match team names
                    if espn_position == 'DST':
                        if (espn_team and db_team == espn_team) or \
                           (espn_name in db_name_clean or db_name_clean in espn_name):
                            best_match = db_player
                            best_score = 95
                            break
                    
                    # Partial name matches for players
                    else:
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
                
                if best_match and best_score >= 80:  # Confidence threshold
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
        print("💾 Saving real ESPN rankings to database...")
        
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
        
        print(f"✅ Saved {inserted_count} real ESPN rankings to database")
    
    def generate_report(self, matched_players: List[Dict], unmatched_espn_players: List[Dict], espn_rankings: Dict[str, List[Dict]]):
        """Generate detailed report"""
        print("\n" + "="*70)
        print("📊 REAL ESPN 2025 FANTASY RANKINGS REPORT")
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
        
        print(f"\n📈 ESPN RANKING COVERAGE:")
        for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'DST']:
            if pos in position_stats:
                matched = position_stats[pos]['matched']
                total_espn = position_stats[pos]['total_espn']
                percentage = (matched / total_espn * 100) if total_espn > 0 else 0
                print(f"  {pos}: {matched}/{total_espn} ESPN rankings matched ({percentage:.1f}%)")
        
        print(f"\n🎯 SCRAPING RESULTS:")
        total_scraped = sum(len(players) for players in espn_rankings.values())
        print(f"  📊 Total rankings scraped: {total_scraped}")
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
                    team_info = f" ({player['team']})" if player['team'] else ""
                    print(f"    #{player['rank']:2d} {player['name']}{team_info}")
                if len(players) > 10:
                    print(f"    ... and {len(players) - 10} more")
        
        print(f"\n💡 DATA QUALITY:")
        if total_scraped > 50:
            print(f"  ✅ Good scraping coverage ({total_scraped} total rankings)")
        else:
            print(f"  ⚠️  Limited scraping coverage ({total_scraped} total rankings)")
            print(f"      Consider reviewing scraping logic or ESPN page structure")
        
        print("\n" + "="*70)

def main():
    scraper = RealESPNScraper()
    
    print("🚀 Starting Real ESPN 2025 Rankings Scrape...")
    
    # Step 1: Scrape real ESPN rankings
    espn_rankings = scraper.scrape_espn_rankings()
    
    if not espn_rankings:
        print("❌ No rankings found from ESPN. The page structure may have changed.")
        print("💡 You may need to inspect the page manually and update the scraping logic.")
        return
    
    # Step 2: Match with database
    matched_players, unmatched_espn_players = scraper.match_with_database(espn_rankings)
    
    # Step 3: Save to database
    if matched_players:
        scraper.save_rankings_to_database(matched_players)
    
    # Step 4: Generate report
    scraper.generate_report(matched_players, unmatched_espn_players, espn_rankings)
    
    print("\n🎉 Real ESPN rankings scrape completed!")

if __name__ == "__main__":
    main()