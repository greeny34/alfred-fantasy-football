#!/usr/bin/env python3
"""
Export database data to CSV files for viewing
"""
import psycopg2
import pandas as pd
import os

def export_all_data():
    """Export all database tables to CSV"""
    
    conn = psycopg2.connect(
        host='localhost',
        port='5432',
        user=os.environ.get('USER', 'jeffgreenfield'),
        password='',
        database='fantasy_draft_db'
    )
    
    print("📤 EXPORTING DATABASE TO CSV FILES")
    print("=" * 40)
    
    # Export players
    players_df = pd.read_sql("""
        SELECT name, position, team, year, is_active, created_at
        FROM players 
        ORDER BY position, name;
    """, conn)
    
    players_df.to_csv('players_export.csv', index=False)
    print(f"✅ Exported {len(players_df)} players to players_export.csv")
    
    # Export rankings with player info
    rankings_df = pd.read_sql("""
        SELECT p.name, p.position, p.team, rs.source_name, 
               pr.position_rank, pr.ranking_date
        FROM players p
        JOIN player_rankings pr ON p.player_id = pr.player_id
        JOIN ranking_sources rs ON pr.source_id = rs.source_id
        ORDER BY rs.source_name, p.position, pr.position_rank;
    """, conn)
    
    rankings_df.to_csv('rankings_export.csv', index=False)
    print(f"✅ Exported {len(rankings_df)} rankings to rankings_export.csv")
    
    # Export by position for easier viewing
    positions = ['QB', 'RB', 'WR', 'TE']
    
    for pos in positions:
        pos_df = pd.read_sql(f"""
            SELECT p.name, p.team, rs.source_name, pr.position_rank
            FROM players p
            JOIN player_rankings pr ON p.player_id = pr.player_id
            JOIN ranking_sources rs ON pr.source_id = rs.source_id
            WHERE p.position = '{pos}'
            ORDER BY rs.source_name, pr.position_rank;
        """, conn)
        
        filename = f'{pos.lower()}_rankings.csv'
        pos_df.to_csv(filename, index=False)
        print(f"✅ Exported {len(pos_df)} {pos} rankings to {filename}")
    
    conn.close()
    
    print(f"\n📁 Files created in: {os.getcwd()}")
    print("   Open with Excel, Numbers, or any CSV viewer")

if __name__ == "__main__":
    export_all_data()