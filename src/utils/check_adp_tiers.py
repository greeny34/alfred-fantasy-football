#!/usr/bin/env python3
"""
Check ADP data to verify draft position tiers
"""

import psycopg2
import os

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(
        host='localhost',
        port='5432',
        user=os.environ.get('USER', 'jeffgreenfield'),
        password='',
        database='fantasy_draft_db'
    )

def check_adp_tiers():
    """Check top ADP players for tier planning"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get top 25 by consensus ADP
    cur.execute("""
        SELECT 
            p.name, 
            p.position, 
            p.team,
            ca.consensus_rank as adp,
            ca.mean_adp
        FROM players p
        JOIN consensus_adp ca ON p.player_id = ca.player_id
        WHERE ca.consensus_rank <= 25
        ORDER BY ca.consensus_rank
    """)
    
    players = cur.fetchall()
    
    print("TOP 25 PLAYERS BY ADP:\n")
    print(f"{'Rank':<5} {'Name':<25} {'Pos':<4} {'Team':<4} {'ADP':<6}")
    print("-" * 50)
    
    for name, pos, team, rank, mean_adp in players:
        print(f"{rank:<5} {name:<25} {pos:<4} {team:<4} {mean_adp:>6.1f}")
    
    # Group by tiers based on user's suggestions
    print("\n\nDRAFT POSITION TIERS:\n")
    
    print("TIER 1 (Pick 1) - Top 3:")
    for i, (name, pos, team, rank, mean_adp) in enumerate(players[:3]):
        print(f"  {name} ({pos}) - ADP: {mean_adp:.1f}")
    
    print("\nTIER 2 (Picks 2-5) - Top 9:")
    for i, (name, pos, team, rank, mean_adp) in enumerate(players[:9]):
        print(f"  {name} ({pos}) - ADP: {mean_adp:.1f}")
    
    print("\nTIER 3 (Picks 6-9) - Players 6-15:")
    for i, (name, pos, team, rank, mean_adp) in enumerate(players[5:15]):
        print(f"  {name} ({pos}) - ADP: {mean_adp:.1f}")
    
    print("\nTIER 4 (Pick 10) - Players 10-20:")
    for i, (name, pos, team, rank, mean_adp) in enumerate(players[9:20]):
        print(f"  {name} ({pos}) - ADP: {mean_adp:.1f}")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_adp_tiers()