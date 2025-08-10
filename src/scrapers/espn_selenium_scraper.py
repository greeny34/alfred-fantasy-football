#!/usr/bin/env python3
"""
ESPN Rankings Scraper using Selenium for JavaScript content
"""

import time
import re
import psycopg2
from datetime import datetime
import os
from typing import List, Dict, Optional, Tuple

# Since ESPN is blocking requests, let's create a manual input system
# where we can paste the rankings from the page

class ManualESPNRankings:
    def __init__(self):
        self.rankings_data = {}
        
    def get_db_connection(self):
        """Get database connection"""
        return psycopg2.connect(
            host='localhost',
            port='5432',
            user=os.environ.get('USER', 'jeffgreenfield'),
            password='',
            database='fantasy_draft_db'
        )
    
    def input_rankings_manually(self):
        """Manually input rankings since ESPN blocks scraping"""
        print("📝 ESPN blocks automated scraping. Let's input rankings manually.")
        print("🌐 Please visit: https://www.espn.com/fantasy/football/story/_/id/44786976/fantasy-football-rankings-2025-draft-ppr")
        print("\n📋 For each position, copy and paste the rankings text here.")
        print("   Format examples:")
        print("   1. Josh Allen, QB, BUF")
        print("   2. Lamar Jackson, QB, BAL") 
        print("   Or just: Josh Allen, Lamar Jackson, etc.")
        print("\n⏹️  Type 'done' when finished with a position")
        print("🚫 Type 'skip' to skip a position")
        print("🛑 Type 'quit' to exit\n")
        
        positions = ['QB', 'RB', 'WR', 'TE', 'K', 'DST']
        
        for position in positions:
            print(f"\n{'='*50}")
            print(f"📊 {position} RANKINGS")
            print(f"{'='*50}")
            print(f"Paste the {position} rankings from ESPN (one per line or comma-separated):")
            
            rankings_text = []
            line_count = 0
            
            while True:
                try:
                    line = input(f"{position} #{line_count + 1}: ").strip()
                    
                    if line.lower() == 'done':
                        break
                    elif line.lower() == 'skip':
                        print(f"⏭️  Skipping {position}")
                        break
                    elif line.lower() == 'quit':
                        print("🛑 Exiting manual input")
                        return self.rankings_data
                    elif line:
                        rankings_text.append(line)
                        line_count += 1
                        
                        # Show what we parsed so far
                        parsed = self._parse_input_line(line, position, line_count)
                        if parsed:
                            print(f"   ✅ Parsed: {parsed['name']} (Rank #{parsed['rank']})")
                        else:
                            print(f"   ⚠️  Could not parse - please check format")
                            
                except KeyboardInterrupt:
                    print(f"\n🛑 Interrupted. Saving {position} data...")
                    break
            
            if rankings_text:
                players = self._parse_position_rankings(rankings_text, position)
                if players:
                    self.rankings_data[position] = players
                    print(f"✅ Saved {len(players)} {position} players")
        
        return self.rankings_data
    
    def _parse_input_line(self, line: str, position: str, rank: int) -> Optional[Dict]:
        """Parse a single input line into player data"""
        # Handle comma-separated multiple players
        if ',' in line and not re.search(r'[A-Z]{2,4}', line):  # Multiple players, no team codes
            players = [name.strip() for name in line.split(',')]
            return {'multiple': players}
        
        # Clean up the line
        line = re.sub(r'^\d+[\.\-\s]*', '', line)  # Remove leading rank numbers
        
        # Extract player name
        name_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z\']*)*\s+[A-Z][a-z\']*)', line)
        if not name_match:
            return None
        
        name = name_match.group(1).strip()
        
        # Extract team code
        team_match = re.search(r'\b([A-Z]{2,4})\b', line)
        team = team_match.group(1) if team_match else ''
        
        # Validate team code is actually NFL team
        nfl_teams = {'ARI', 'ATL', 'BAL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE',\n                     'DAL', 'DEN', 'DET', 'GB', 'HOU', 'IND', 'JAX', 'KC',\n                     'LV', 'LAC', 'LAR', 'MIA', 'MIN', 'NE', 'NO', 'NYG',\n                     'NYJ', 'PHI', 'PIT', 'SF', 'SEA', 'TB', 'TEN', 'WAS'}\n        \n        if team not in nfl_teams:\n            team = ''\n        \n        return {\n            'name': name,\n            'position': position,\n            'team': team,\n            'rank': rank,\n            'source': 'ESPN',\n            'raw_text': line\n        }\n    \n    def _parse_position_rankings(self, rankings_text: List[str], position: str) -> List[Dict]:\n        \"\"\"Parse all rankings text for a position\"\"\"\n        players = []\n        current_rank = 1\n        \n        for line in rankings_text:\n            # Handle multiple players in one line\n            if ',' in line and not re.search(r'[A-Z]{2,4}', line):\n                names = [name.strip() for name in line.split(',')]\n                for name in names:\n                    if name and len(name.split()) >= 2:\n                        players.append({\n                            'name': name,\n                            'position': position,\n                            'team': '',\n                            'rank': current_rank,\n                            'source': 'ESPN',\n                            'raw_text': name\n                        })\n                        current_rank += 1\n            else:\n                parsed = self._parse_input_line(line, position, current_rank)\n                if parsed and 'multiple' not in parsed:\n                    players.append(parsed)\n                    current_rank += 1\n        \n        return players\n    \n    def match_with_database(self, espn_rankings: Dict[str, List[Dict]]) -> Tuple[List[Dict], List[Dict]]:\n        \"\"\"Match ESPN rankings with our player database\"\"\"\n        print(\"🔗 Matching manually entered ESPN rankings with database...\")\n        \n        conn = self.get_db_connection()\n        cur = conn.cursor()\n        \n        # Get all players from our database\n        cur.execute(\"\"\"\n            SELECT player_id, name, position, team \n            FROM players \n            ORDER BY position, name\n        \"\"\")\n        db_players = cur.fetchall()\n        \n        matched_players = []\n        unmatched_espn_players = []\n        \n        for position, espn_players in espn_rankings.items():\n            print(f\"📊 Matching {position} players...\")\n            \n            for espn_player in espn_players:\n                espn_name = espn_player['name'].lower().strip()\n                espn_position = espn_player['position']\n                espn_team = espn_player['team']\n                \n                # Try to find match in database\n                best_match = None\n                best_score = 0\n                \n                for db_player in db_players:\n                    db_id, db_name, db_position, db_team = db_player\n                    \n                    # Must match position\n                    if db_position != espn_position:\n                        continue\n                    \n                    # Calculate name match score\n                    db_name_clean = db_name.lower().strip()\n                    \n                    # Exact match\n                    if espn_name == db_name_clean:\n                        best_match = db_player\n                        best_score = 100\n                        break\n                    \n                    # Partial name matches\n                    espn_parts = espn_name.split()\n                    db_parts = db_name_clean.split()\n                    \n                    if len(espn_parts) >= 2 and len(db_parts) >= 2:\n                        # First and last name match\n                        if espn_parts[0] == db_parts[0] and espn_parts[-1] == db_parts[-1]:\n                            score = 95\n                            # Bonus for team match\n                            if espn_team and db_team == espn_team:\n                                score += 5\n                            if score > best_score:\n                                best_match = db_player\n                                best_score = score\n                        \n                        # Last name match\n                        elif espn_parts[-1] == db_parts[-1]:\n                            score = 80\n                            # Bonus for team match \n                            if espn_team and db_team == espn_team:\n                                score += 10\n                            if score > best_score:\n                                best_match = db_player\n                                best_score = score\n                \n                if best_match and best_score >= 80:\n                    matched_players.append({\n                        'db_player_id': best_match[0],\n                        'db_name': best_match[1],\n                        'db_position': best_match[2],\n                        'db_team': best_match[3],\n                        'espn_name': espn_player['name'],\n                        'espn_rank': espn_player['rank'],\n                        'espn_position': espn_player['position'],\n                        'espn_team': espn_player['team'],\n                        'match_score': best_score,\n                        'source': 'ESPN'\n                    })\n                else:\n                    unmatched_espn_players.append(espn_player)\n        \n        cur.close()\n        conn.close()\n        \n        print(f\"✅ Matched {len(matched_players)} players\")\n        print(f\"❓ {len(unmatched_espn_players)} ESPN players not found in database\")\n        \n        return matched_players, unmatched_espn_players\n    \n    def save_rankings_to_database(self, matched_players: List[Dict]):\n        \"\"\"Save matched rankings to database\"\"\"\n        print(\"💾 Saving manually entered ESPN rankings to database...\")\n        \n        conn = self.get_db_connection()\n        cur = conn.cursor()\n        \n        # Ensure ESPN source exists\n        cur.execute(\"\"\"\n            INSERT INTO ranking_sources (source_name, base_url)\n            VALUES (%s, %s)\n            ON CONFLICT (source_name) DO NOTHING\n        \"\"\", ('ESPN', 'https://www.espn.com/fantasy/football/'))\n        \n        # Get ESPN source ID\n        cur.execute(\"SELECT source_id FROM ranking_sources WHERE source_name = 'ESPN'\")\n        espn_source_id = cur.fetchone()[0]\n        \n        # Insert rankings\n        inserted_count = 0\n        for player in matched_players:\n            try:\n                cur.execute(\"\"\"\n                    INSERT INTO player_rankings (player_id, source_id, position_rank, ranking_date)\n                    VALUES (%s, %s, %s, %s)\n                    ON CONFLICT (player_id, source_id, ranking_date) DO UPDATE SET\n                        position_rank = EXCLUDED.position_rank\n                \"\"\", (\n                    player['db_player_id'],\n                    espn_source_id,\n                    player['espn_rank'],\n                    datetime.now().date()\n                ))\n                inserted_count += 1\n            except Exception as e:\n                print(f\"❌ Error inserting ranking for {player['db_name']}: {e}\")\n        \n        conn.commit()\n        cur.close()\n        conn.close()\n        \n        print(f\"✅ Saved {inserted_count} ESPN rankings to database\")\n    \n    def generate_report(self, matched_players: List[Dict], unmatched_espn_players: List[Dict], espn_rankings: Dict[str, List[Dict]]):\n        \"\"\"Generate detailed report\"\"\"\n        print(\"\\n\" + \"=\"*70)\n        print(\"📊 MANUALLY ENTERED ESPN 2025 RANKINGS REPORT\")\n        print(\"=\"*70)\n        \n        # Summary by position\n        position_stats = {}\n        for player in matched_players:\n            pos = player['db_position']\n            if pos not in position_stats:\n                position_stats[pos] = {'matched': 0, 'total_espn': 0}\n            position_stats[pos]['matched'] += 1\n        \n        # Count total ESPN rankings by position\n        for position, players in espn_rankings.items():\n            if position not in position_stats:\n                position_stats[position] = {'matched': 0, 'total_espn': len(players)}\n            else:\n                position_stats[position]['total_espn'] = len(players)\n        \n        print(f\"\\n📈 ESPN RANKING COVERAGE:\")\n        for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'DST']:\n            if pos in position_stats:\n                matched = position_stats[pos]['matched']\n                total_espn = position_stats[pos]['total_espn']\n                percentage = (matched / total_espn * 100) if total_espn > 0 else 0\n                print(f\"  {pos}: {matched}/{total_espn} ESPN rankings matched ({percentage:.1f}%)\")\n        \n        print(f\"\\n🎯 INPUT RESULTS:\")\n        total_entered = sum(len(players) for players in espn_rankings.values())\n        print(f\"  📊 Total rankings entered: {total_entered}\")\n        print(f\"  ✅ Successfully matched: {len(matched_players)} players\")\n        print(f\"  ❓ ESPN players not in DB: {len(unmatched_espn_players)} players\")\n        \n        if unmatched_espn_players:\n            print(f\"\\n❓ UNMATCHED ESPN PLAYERS:\")\n            by_position = {}\n            for player in unmatched_espn_players:\n                pos = player['position']\n                if pos not in by_position:\n                    by_position[pos] = []\n                by_position[pos].append(player)\n            \n            for pos, players in sorted(by_position.items()):\n                print(f\"\\n  {pos} ({len(players)} players):\")\n                for player in players:\n                    team_info = f\" ({player['team']})\" if player['team'] else \"\"\n                    print(f\"    #{player['rank']:2d} {player['name']}{team_info}\")\n        \n        print(\"\\n\" + \"=\"*70)\n\ndef main():\n    scraper = ManualESPNRankings()\n    \n    print(\"🚀 Manual ESPN 2025 Rankings Entry System\")\n    print(\"🌐 ESPN blocks automated scraping, so we'll enter rankings manually\")\n    \n    # Step 1: Manual input of rankings\n    espn_rankings = scraper.input_rankings_manually()\n    \n    if not espn_rankings:\n        print(\"❌ No rankings were entered.\")\n        return\n    \n    # Step 2: Match with database\n    matched_players, unmatched_espn_players = scraper.match_with_database(espn_rankings)\n    \n    # Step 3: Save to database\n    if matched_players:\n        scraper.save_rankings_to_database(matched_players)\n    \n    # Step 4: Generate report\n    scraper.generate_report(matched_players, unmatched_espn_players, espn_rankings)\n    \n    print(\"\\n🎉 Manual ESPN rankings entry completed!\")\n    print(\"💡 Your web app now has the real ESPN 2025 rankings!\")\n\nif __name__ == \"__main__\":\n    main()