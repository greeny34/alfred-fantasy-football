#!/usr/bin/env python3
"""
ESPN Mike Clay 2025 Fantasy Football Rankings Scraper
Scrapes the specific ESPN article with actual rankings
"""

import requests
from bs4 import BeautifulSoup
import re
import psycopg2
from datetime import datetime
import os
from typing import List, Dict, Optional, Tuple

class ESPNMikeClayRankings:
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
        
        self.url = "https://www.espn.com/fantasy/football/story/_/id/43261183/2025-fantasy-football-rankings-ppr-mike-clay"
        
    def get_db_connection(self):
        """Get database connection"""
        return psycopg2.connect(
            host='localhost',
            port='5432',
            user=os.environ.get('USER', 'jeffgreenfield'),
            password='',
            database='fantasy_draft_db'
        )
    
    def scrape_rankings(self) -> Dict[str, List[Dict]]:
        """Scrape Mike Clay's ESPN rankings"""
        print("🏈 Scraping ESPN Mike Clay 2025 Fantasy Rankings...")
        print(f"🌐 URL: {self.url}")
        
        try:
            response = self.session.get(self.url, timeout=30)
            print(f"📡 Response status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"❌ Failed to access page: HTTP {response.status_code}")
                return {}
            
            soup = BeautifulSoup(response.content, 'html.parser')
            print("✅ Successfully loaded page")
            
            # Extract rankings using multiple strategies
            rankings = self._extract_rankings_from_page(soup)
            
            if rankings:
                total_players = sum(len(players) for players in rankings.values())
                print(f"✅ Found {total_players} total player rankings")
                for pos, players in rankings.items():
                    print(f"   {pos}: {len(players)} players")
            else:
                print("❌ No rankings found")
                
            return rankings
            
        except Exception as e:
            print(f"❌ Error scraping rankings: {e}")
            return {}
    
    def _extract_rankings_from_page(self, soup: BeautifulSoup) -> Dict[str, List[Dict]]:
        """Extract rankings from the Mike Clay article"""
        rankings = {
            'QB': [],
            'RB': [],
            'WR': [],
            'TE': [],
            'K': [],
            'DST': []
        }
        
        # Get all text content to parse
        page_text = soup.get_text()
        
        # Look for ranking sections with patterns like:
        # "Top 5 Quarterbacks:" followed by numbered list
        # "1. Josh Allen (Bills)" etc.
        
        print("🔍 Searching for ranking sections...")
        
        # Find QB rankings
        qb_section = self._find_position_section(page_text, ['quarterbacks', 'qb'])
        if qb_section:
            rankings['QB'] = self._parse_ranking_section(qb_section, 'QB')
            print(f"📊 Found {len(rankings['QB'])} QB rankings")
        
        # Find RB rankings  
        rb_section = self._find_position_section(page_text, ['running backs', 'rb'])
        if rb_section:
            rankings['RB'] = self._parse_ranking_section(rb_section, 'RB')
            print(f"📊 Found {len(rankings['RB'])} RB rankings")
        
        # Find WR rankings
        wr_section = self._find_position_section(page_text, ['wide receivers', 'wr'])
        if wr_section:
            rankings['WR'] = self._parse_ranking_section(wr_section, 'WR')
            print(f"📊 Found {len(rankings['WR'])} WR rankings")
        
        # Find TE rankings
        te_section = self._find_position_section(page_text, ['tight ends', 'te'])
        if te_section:
            rankings['TE'] = self._parse_ranking_section(te_section, 'TE')
            print(f"📊 Found {len(rankings['TE'])} TE rankings")
        
        # Find K rankings
        k_section = self._find_position_section(page_text, ['kickers', 'kicker', 'k'])
        if k_section:
            rankings['K'] = self._parse_ranking_section(k_section, 'K')
            print(f"📊 Found {len(rankings['K'])} K rankings")
        
        # Find DST rankings
        dst_section = self._find_position_section(page_text, ['defense', 'dst', 'd/st'])
        if dst_section:
            rankings['DST'] = self._parse_ranking_section(dst_section, 'DST')
            print(f"📊 Found {len(rankings['DST'])} DST rankings")
        
        # Also look for "Top Overall" rankings and assign positions
        overall_section = self._find_position_section(page_text, ['top 5 overall', 'overall players'])
        if overall_section:
            overall_players = self._parse_ranking_section(overall_section, None)
            # Distribute overall players to position-specific rankings
            for player in overall_players:
                pos = player['position']
                if pos in rankings:
                    # Only add if not already in position rankings
                    existing_names = [p['name'].lower() for p in rankings[pos]]
                    if player['name'].lower() not in existing_names:
                        rankings[pos].append(player)
            
            print(f"📊 Found {len(overall_players)} overall rankings")
        
        # Remove empty positions
        rankings = {pos: players for pos, players in rankings.items() if players}
        
        return rankings
    
    def _find_position_section(self, text: str, keywords: List[str]) -> Optional[str]:
        """Find a section of text containing position rankings"""
        text_lower = text.lower()
        
        for keyword in keywords:
            # Look for patterns like "Top 5 Quarterbacks:" or "Quarterbacks"
            pattern = rf"(?:top \d+ )?{keyword}[:\s]*\n?(.*?)(?=(?:top \d+ |[a-z]+ \d+|\n\n|\Z))"
            match = re.search(pattern, text_lower, re.DOTALL | re.IGNORECASE)
            
            if match:
                # Get the original case text from the same position
                start = match.start()
                end = match.end()
                return text[start:end]
        
        return None
    
    def _parse_ranking_section(self, section_text: str, position: Optional[str]) -> List[Dict]:
        """Parse a ranking section to extract player data"""
        players = []
        
        # Look for numbered list patterns like:
        # "1. Josh Allen (Bills)"
        # "2. Lamar Jackson (Ravens)"
        
        patterns = [
            r'(\d+)\.\s*([A-Z][a-z\'\-]+(?:\s+[A-Z][a-z\'\-]+)*)\s*\(([A-Z][a-z\'\-]+(?:\s+[A-Z][a-z\'\-]+)*)\)',  # "1. Player Name (Team)"
            r'(\d+)\.\s*([A-Z][a-z\'\-]+(?:\s+[A-Z][a-z\'\-]+)*)\s*\(([A-Z]{2,4})\)',  # "1. Player Name (TEX)"
            r'(\d+)\.\s*([A-Z][a-z\'\-]+(?:\s+[A-Z][a-z\'\-]+)*),?\s*([A-Z]{2,4})?',  # "1. Player Name, TEX"
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, section_text)
            for match in matches:
                rank = int(match.group(1))
                name = match.group(2).strip()
                team_or_city = match.group(3) if match.group(3) else ''
                
                # Clean up team names
                team = self._normalize_team_name(team_or_city)
                
                # Infer position if not provided
                if not position:
                    inferred_pos = self._infer_position_from_context(section_text, name)
                    position = inferred_pos if inferred_pos else 'UNKNOWN'
                
                if self._is_valid_player_name(name):
                    players.append({
                        'name': name,
                        'position': position,
                        'team': team,
                        'rank': rank,
                        'source': 'ESPN_Mike_Clay',
                        'raw_text': match.group(0)
                    })
            
            if players:
                break  # Use first successful pattern
        
        # Sort by rank and remove duplicates
        players.sort(key=lambda x: x['rank'])
        seen_names = set()
        unique_players = []
        for player in players:
            name_key = player['name'].lower()
            if name_key not in seen_names:
                seen_names.add(name_key)
                unique_players.append(player)
        
        return unique_players
    
    def _normalize_team_name(self, team_text: str) -> str:
        """Convert team names to standard abbreviations"""
        if not team_text:
            return ''
        
        team_mappings = {
            # Full team names to abbreviations
            'bills': 'BUF', 'ravens': 'BAL', 'commanders': 'WAS', 'eagles': 'PHI',
            'bengals': 'CIN', 'falcons': 'ATL', 'lions': 'DET', '49ers': 'SF',
            'raiders': 'LV', 'cowboys': 'DAL', 'rams': 'LAR', 'giants': 'NYG',
            'cardinals': 'ARI', 'vikings': 'MIN', 'bears': 'CHI', 'packers': 'GB',
            'saints': 'NO', 'buccaneers': 'TB', 'panthers': 'CAR', 'seahawks': 'SEA',
            'broncos': 'DEN', 'chiefs': 'KC', 'chargers': 'LAC', 'titans': 'TEN',
            'colts': 'IND', 'texans': 'HOU', 'jaguars': 'JAX', 'steelers': 'PIT',
            'browns': 'CLE', 'dolphins': 'MIA', 'jets': 'NYJ', 'patriots': 'NE'
        }
        
        team_lower = team_text.lower().strip()
        
        # If it's already an abbreviation, return it
        if len(team_text) <= 4 and team_text.isupper():
            return team_text
        
        # Look up full name
        return team_mappings.get(team_lower, team_text)
    
    def _infer_position_from_context(self, section_text: str, player_name: str) -> Optional[str]:
        """Infer player position from section context"""
        section_lower = section_text.lower()
        
        if any(word in section_lower for word in ['quarterback', 'qb']):
            return 'QB'
        elif any(word in section_lower for word in ['running back', 'rb']):
            return 'RB'
        elif any(word in section_lower for word in ['wide receiver', 'wr']):
            return 'WR'
        elif any(word in section_lower for word in ['tight end', 'te']):
            return 'TE'
        elif any(word in section_lower for word in ['kicker', 'k']):
            return 'K'
        elif any(word in section_lower for word in ['defense', 'dst', 'd/st']):
            return 'DST'
        
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
        print("🔗 Matching ESPN Mike Clay rankings with database...")
        
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
                        'source': 'ESPN_Mike_Clay'
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
        print("💾 Saving ESPN Mike Clay rankings to database...")
        
        conn = self.get_db_connection()
        cur = conn.cursor()
        
        # Ensure ESPN source exists
        cur.execute("""
            INSERT INTO ranking_sources (source_name, base_url)
            VALUES (%s, %s)
            ON CONFLICT (source_name) DO NOTHING
        """, ('ESPN_Mike_Clay', self.url))
        
        # Get ESPN source ID
        cur.execute("SELECT source_id FROM ranking_sources WHERE source_name = 'ESPN_Mike_Clay'")
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
        
        print(f"✅ Saved {inserted_count} ESPN Mike Clay rankings to database")
    
    def generate_report(self, matched_players: List[Dict], unmatched_espn_players: List[Dict], espn_rankings: Dict[str, List[Dict]]):
        """Generate detailed report"""
        print("\n" + "="*70)
        print("📊 ESPN MIKE CLAY 2025 RANKINGS REPORT")
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
        
        print("\n" + "="*70)

def main():
    scraper = ESPNMikeClayRankings()
    
    print("🚀 Starting ESPN Mike Clay 2025 Rankings Scrape...")
    
    # Step 1: Scrape rankings
    espn_rankings = scraper.scrape_rankings()
    
    if not espn_rankings:
        print("❌ No rankings found from ESPN Mike Clay article.")
        return
    
    # Step 2: Match with database
    matched_players, unmatched_espn_players = scraper.match_with_database(espn_rankings)
    
    # Step 3: Save to database
    if matched_players:
        scraper.save_rankings_to_database(matched_players)
    
    # Step 4: Generate report
    scraper.generate_report(matched_players, unmatched_espn_players, espn_rankings)
    
    print("\n🎉 ESPN Mike Clay rankings scrape completed!")

if __name__ == "__main__":
    main()