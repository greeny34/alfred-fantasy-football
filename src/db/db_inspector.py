#!/usr/bin/env python3
"""
Database Inspector - Tool to evaluate and fix fantasy football data
"""
import psycopg2
import pandas as pd
import os

class DatabaseInspector:
    def __init__(self):
        self.db_config = {
            'host': 'localhost', 
            'port': '5432',
            'user': os.environ.get('USER', 'jeffgreenfield'),
            'password': '',
            'database': 'fantasy_draft_db'
        }
    
    def show_all_players(self):
        """Show all players in database for inspection"""
        print("👥 ALL PLAYERS IN DATABASE:")
        print("=" * 60)
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            cur.execute("""
                SELECT name, position, team, year, is_active
                FROM players 
                ORDER BY position, name;
            """)
            
            players = cur.fetchall()
            
            current_position = None
            for name, position, team, year, is_active in players:
                if position != current_position:
                    print(f"\n{position}:")
                    current_position = position
                
                status = "✅" if is_active else "❌"
                print(f"  {status} {name} ({team}) - {year}")
            
            print(f"\nTotal players: {len(players)}")
            
            cur.close()
            conn.close()
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def show_player_rankings(self, player_name: str):
        """Show all rankings for a specific player"""
        print(f"📊 RANKINGS FOR: {player_name}")
        print("=" * 40)
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            cur.execute("""
                SELECT p.name, p.position, p.team, rs.source_name, pr.position_rank, pr.ranking_date
                FROM players p
                JOIN player_rankings pr ON p.player_id = pr.player_id
                JOIN ranking_sources rs ON pr.source_id = rs.source_id
                WHERE p.name ILIKE %s
                ORDER BY rs.source_name, pr.ranking_date DESC;
            """, (f"%{player_name}%",))
            
            rankings = cur.fetchall()
            
            if not rankings:
                print(f"No rankings found for '{player_name}'")
            else:
                for name, position, team, source, rank, date in rankings:
                    print(f"  {source}: {position}{rank} ({team}) - {date}")
            
            cur.close()
            conn.close()
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def update_player_team(self, player_name: str, new_team: str):
        """Update a player's team"""
        print(f"✏️ UPDATING {player_name} to {new_team}")
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            # Find the player
            cur.execute("""
                SELECT player_id, name, team FROM players 
                WHERE name ILIKE %s;
            """, (f"%{player_name}%",))
            
            players = cur.fetchall()
            
            if not players:
                print(f"❌ Player '{player_name}' not found")
                return False
            
            if len(players) > 1:
                print(f"⚠️ Multiple players found:")
                for pid, name, team in players:
                    print(f"  {pid}: {name} ({team})")
                print("Please be more specific")
                return False
            
            player_id, name, old_team = players[0]
            
            # Update the team
            cur.execute("""
                UPDATE players 
                SET team = %s, updated_at = CURRENT_TIMESTAMP
                WHERE player_id = %s;
            """, (new_team, player_id))
            
            conn.commit()
            
            print(f"✅ Updated {name}: {old_team} → {new_team}")
            
            cur.close()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def find_suspicious_teams(self):
        """Find players that might have wrong team assignments"""
        print("🔍 CHECKING FOR SUSPICIOUS TEAM ASSIGNMENTS:")
        print("=" * 50)
        
        # Known 2025 team changes to check
        known_moves = {
            "DK Metcalf": "PIT",
            "Russell Wilson": "PIT", 
            "Calvin Ridley": "TEN",
            "Saquon Barkley": "PHI",
            "Tony Pollard": "TEN",
            "Josh Jacobs": "GB",
            "Aaron Jones": "MIN",
            "Joe Mixon": "HOU",
            "Stefon Diggs": "HOU",
            "DeAndre Hopkins": "KC",
            "Amari Cooper": "BUF",
            "Jerry Jeudy": "CLE",
            "Geno Smith": "LV",
            "Kirk Cousins": "ATL",
            "Aaron Rodgers": "PIT"
        }
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            issues_found = 0
            
            for player_name, expected_team in known_moves.items():
                cur.execute("""
                    SELECT name, team FROM players 
                    WHERE name ILIKE %s;
                """, (f"%{player_name}%",))
                
                result = cur.fetchone()
                if result:
                    name, current_team = result
                    if current_team != expected_team:
                        print(f"❌ {name}: DB shows {current_team}, should be {expected_team}")
                        issues_found += 1
                    else:
                        print(f"✅ {name}: Correctly shows {current_team}")
                else:
                    print(f"⚠️ {player_name}: Not found in database")
            
            print(f"\nIssues found: {issues_found}")
            
            cur.close()
            conn.close()
            
            return issues_found
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return -1
    
    def export_for_review(self):
        """Export all data to CSV for manual review"""
        print("📤 EXPORTING DATA FOR REVIEW...")
        
        try:
            conn = psycopg2.connect(**self.db_config)
            
            # Export players
            players_df = pd.read_sql("""
                SELECT name, position, team, year, is_active, created_at
                FROM players 
                ORDER BY position, name;
            """, conn)
            
            players_df.to_csv('/Users/jeffgreenfield/dev/ff_draft_vibe/players_review.csv', index=False)
            
            # Export rankings with player info
            rankings_df = pd.read_sql("""
                SELECT p.name, p.position, p.team, rs.source_name, 
                       pr.position_rank, pr.ranking_date
                FROM players p
                JOIN player_rankings pr ON p.player_id = pr.player_id
                JOIN ranking_sources rs ON pr.source_id = rs.source_id
                ORDER BY rs.source_name, p.position, pr.position_rank;
            """, conn)
            
            rankings_df.to_csv('/Users/jeffgreenfield/dev/ff_draft_vibe/rankings_review.csv', index=False)
            
            conn.close()
            
            print("✅ Data exported:")
            print("  📄 players_review.csv")
            print("  📄 rankings_review.csv")
            
            return True
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def interactive_mode(self):
        """Interactive mode for database inspection and fixes"""
        print("🔧 DATABASE INSPECTOR - INTERACTIVE MODE")
        print("=" * 45)
        print("Commands:")
        print("  'players' - Show all players")
        print("  'search <name>' - Show player rankings")
        print("  'update <name> <team>' - Update player team")
        print("  'check' - Check for suspicious team assignments")
        print("  'export' - Export data for review")
        print("  'quit' - Exit")
        print()
        
        while True:
            try:
                cmd = input("🔍 > ").strip().lower()
                
                if cmd == 'quit':
                    break
                elif cmd == 'players':
                    self.show_all_players()
                elif cmd == 'check':
                    self.find_suspicious_teams()
                elif cmd == 'export':
                    self.export_for_review()
                elif cmd.startswith('search '):
                    player_name = cmd[7:]
                    self.show_player_rankings(player_name)
                elif cmd.startswith('update '):
                    parts = cmd[7:].split()
                    if len(parts) >= 2:
                        player_name = ' '.join(parts[:-1])
                        team = parts[-1].upper()
                        self.update_player_team(player_name, team)
                    else:
                        print("Usage: update <player name> <team>")
                else:
                    print("Unknown command. Type 'quit' to exit.")
                    
                print()
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
        
        print("👋 Goodbye!")

if __name__ == "__main__":
    inspector = DatabaseInspector()
    
    # Run automatic checks first
    print("🏈 DATABASE INSPECTION REPORT")
    print("=" * 40)
    
    inspector.find_suspicious_teams()
    print()
    
    inspector.export_for_review()
    print()
    
    # Enter interactive mode
    inspector.interactive_mode()