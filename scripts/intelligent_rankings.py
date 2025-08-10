#!/usr/bin/env python3
"""
Intelligent Expert Ranking Extension - Properly extend expert rankings to all players
"""
import sys
sys.path.append('/Users/jeffgreenfield/dev/ff_draft_vibe')

import pandas as pd
import requests
from complete_sleeper_assistant import CompleteDraftAssistant

def create_intelligent_rankings():
    """Create intelligent rankings by properly extending expert methodology"""
    
    print("🏈 CREATING INTELLIGENT EXPERT RANKING EXTENSION")
    print("🎯 Properly ranking ALL players with football knowledge")
    print("=" * 60)
    
    # Get all fantasy players
    url = "https://api.sleeper.app/v1/players/nfl"
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"❌ Error loading players: {response.status_code}")
        return None
    
    all_sleeper_players = response.json()
    print(f"✅ Loaded {len(all_sleeper_players)} total players from Sleeper")
    
    # Filter fantasy players
    fantasy_players = []
    for player_id, player_data in all_sleeper_players.items():
        position = player_data.get('position', '')
        team = player_data.get('team', '')
        name = player_data.get('full_name', '')
        status = player_data.get('status', 'Unknown')
        
        if position in ['QB', 'RB', 'WR', 'TE', 'K']:
            if team and team != 'FA' and name:
                fantasy_players.append({
                    'player_id': player_id,
                    'name': name,
                    'position': position,
                    'team': team,
                    'status': status,
                    'age': player_data.get('age'),
                    'years_exp': player_data.get('years_exp'),
                    'injury_status': player_data.get('injury_status', ''),
                    'sleeper_data': player_data
                })
        elif position == 'DEF':
            if team:
                fantasy_players.append({
                    'player_id': player_id,
                    'name': f"{team} Defense",
                    'position': 'D/ST',
                    'team': team,
                    'status': 'Active',
                    'age': None,
                    'years_exp': None,
                    'injury_status': '',
                    'sleeper_data': player_data
                })
    
    print(f"🎯 Total fantasy players: {len(fantasy_players)}")
    
    # Get expert rankings for top players
    assistant = CompleteDraftAssistant("dummy_id")
    
    # Separate expert and non-expert players
    expert_players = []
    non_expert_players = []
    
    for player in fantasy_players:
        player_obj = {
            "name": player['name'],
            "position": player['position'],
            "team": player['team'],
            "player_id": player['player_id']
        }
        
        consensus, high, low, std = assistant.get_player_expert_data(player_obj)
        
        if consensus < 999:
            player['expert_rank'] = consensus
            player['expert_high'] = high
            player['expert_low'] = low
            player['expert_std'] = std
            player['has_expert'] = True
            expert_players.append(player)
        else:
            player['has_expert'] = False
            non_expert_players.append(player)
    
    print(f"✅ Found {len(expert_players)} players with expert rankings")
    print(f"🎯 Need to intelligently rank {len(non_expert_players)} additional players")
    
    # Now intelligently rank the non-expert players by position
    intelligently_ranked = []
    
    # Process each position separately with football knowledge
    intelligently_ranked.extend(rank_qbs_intelligently(non_expert_players))
    intelligently_ranked.extend(rank_rbs_intelligently(non_expert_players))
    intelligently_ranked.extend(rank_wrs_intelligently(non_expert_players))
    intelligently_ranked.extend(rank_tes_intelligently(non_expert_players))
    intelligently_ranked.extend(rank_kickers_intelligently(non_expert_players))
    intelligently_ranked.extend(rank_defenses_intelligently(non_expert_players))
    
    # Combine expert and intelligently ranked players
    all_ranked = expert_players + intelligently_ranked
    
    # Sort by ranking and apply final rankings
    all_ranked.sort(key=lambda x: x.get('expert_rank', x.get('intelligent_rank', 999)))
    
    # Apply final integer rankings
    for i, player in enumerate(all_ranked, 1):
        player['final_rank'] = i
        
        # Create proper high/low ranges
        if player['has_expert']:
            player['high_rank'] = player['expert_high']
            player['low_rank'] = player['expert_low']
            player['std_deviation'] = player['expert_std']
        else:
            # Create reasonable ranges for intelligently ranked players
            range_size = get_intelligent_range(i, player['position'])
            player['high_rank'] = max(1, i - range_size//2)
            player['low_rank'] = min(len(all_ranked), i + range_size//2)
            player['std_deviation'] = round(range_size / 6, 2)
        
        player['rank_range'] = player['low_rank'] - player['high_rank']
    
    # Add position ranks
    position_counters = {}
    for player in all_ranked:
        pos = player['position']
        if pos not in position_counters:
            position_counters[pos] = 0
        position_counters[pos] += 1
        player['position_rank'] = position_counters[pos]
    
    # Calculate VORP
    print("🧮 Calculating VORP scores...")
    for player in all_ranked:
        base_vorp = max(0, 250 - player['final_rank'])
        range_bonus = player['rank_range'] * 0.3
        
        pos_multipliers = {
            'RB': 1.15, 'WR': 1.10, 'TE': 1.05, 'QB': 0.85, 'K': 0.3, 'D/ST': 0.5
        }
        
        multiplier = pos_multipliers.get(player['position'], 1.0)
        player['vorp_score'] = round((base_vorp + range_bonus) * multiplier, 1)
    
    print(f"✅ Created intelligent rankings for all {len(all_ranked)} players")
    return all_ranked

def rank_qbs_intelligently(all_players):
    """Rank QBs with actual football knowledge"""
    qbs = [p for p in all_players if p['position'] == 'QB']
    
    # Tier 1: Established starters missing from expert rankings
    tier1_qbs = []
    for qb in qbs:
        name = qb['name'].lower()
        if any(starter in name for starter in ['tua tagovailoa', 'jordan love', 'dak prescott', 'kirk cousins', 'aaron rodgers']):
            qb['intelligent_rank'] = 101  # Right after expert rankings
            tier1_qbs.append(qb)
    
    # Tier 2: Young/developing starters
    tier2_qbs = []
    for qb in qbs:
        if qb in tier1_qbs:
            continue
        name = qb['name'].lower()
        if any(starter in name for starter in ['anthony richardson', 'drake maye', 'bryce young', 'c.j. stroud', 'geno smith']):
            qb['intelligent_rank'] = 110
            tier2_qbs.append(qb)
    
    # Tier 3: Backup QBs on good teams / Former starters
    tier3_qbs = []
    for qb in qbs:
        if qb in tier1_qbs or qb in tier2_qbs:
            continue
        name = qb['name'].lower()
        team = qb['team']
        # Good team backups or former starters
        if (team in ['KC', 'BUF', 'SF', 'PHI', 'DET'] or 
            any(backup in name for backup in ['gardner minshew', 'jacoby brissett', 'ryan tannehill', 'jimmy garoppolo'])):
            qb['intelligent_rank'] = 200
            tier3_qbs.append(qb)
    
    # Remaining QBs get lower rankings
    remaining_qbs = []
    current_rank = 400
    for qb in qbs:
        if qb not in tier1_qbs and qb not in tier2_qbs and qb not in tier3_qbs:
            qb['intelligent_rank'] = current_rank
            current_rank += 10
            remaining_qbs.append(qb)
    
    # Sort each tier and assign specific ranks
    for tier, base_rank in [(tier1_qbs, 101), (tier2_qbs, 110), (tier3_qbs, 200)]:
        tier.sort(key=lambda x: get_qb_tier_score(x))
        for i, qb in enumerate(tier):
            qb['intelligent_rank'] = base_rank + i
    
    return tier1_qbs + tier2_qbs + tier3_qbs + remaining_qbs

def get_qb_tier_score(qb):
    """Score QBs within their tier"""
    name = qb['name'].lower()
    team = qb['team']
    age = qb.get('age') or 30
    years_exp = qb.get('years_exp') or 5
    
    score = 0
    
    # Age preference (prime years)
    if 24 <= age <= 30:
        score += 10
    elif age <= 35:
        score += 5
    
    # Team quality
    elite_teams = ['KC', 'BUF', 'SF', 'PHI', 'DET', 'MIA', 'DAL', 'CIN']
    if team in elite_teams:
        score += 15
    
    # Experience sweet spot
    if 3 <= years_exp <= 8:
        score += 8
    
    return -score  # Negative because we want higher scores first

def rank_rbs_intelligently(all_players):
    """Rank RBs with actual football knowledge"""
    rbs = [p for p in all_players if p['position'] == 'RB']
    
    # Separate by likely fantasy relevance
    starter_rbs = []
    backup_rbs = []
    deep_rbs = []
    
    for rb in rbs:
        name = rb['name'].lower()
        team = rb['team']
        age = rb.get('age', 25)
        years_exp = rb.get('years_exp', 2)
        
        # Likely starters/significant contributors
        if (any(starter in name for starter in [
            'ezekiel elliott', 'miles sanders', 'dameon pierce', 'antonio gibson', 'clyde edwards-helaire',
            'jamaal williams', 'd\'andre swift', 'cam akers', 'elijah mitchell', 'david montgomery',
            'kareem hunt', 'melvin gordon', 'leonard fournette'
        ]) or 
        (team in ['SF', 'KC', 'BUF', 'PHI', 'DET'] and (years_exp or 0) >= 2 and (age or 30) <= 28)):
            rb['intelligent_rank'] = 102
            starter_rbs.append(rb)
        
        # Backup RBs with upside
        elif ((years_exp or 0) <= 3 and (age or 30) <= 26) or team in ['KC', 'SF', 'BUF', 'PHI', 'DET']:
            rb['intelligent_rank'] = 250
            backup_rbs.append(rb)
        
        # Deep/irrelevant RBs
        else:
            rb['intelligent_rank'] = 500
            deep_rbs.append(rb)
    
    # Sort and rank each group
    starter_rbs.sort(key=lambda x: get_rb_score(x))
    backup_rbs.sort(key=lambda x: get_rb_score(x))
    deep_rbs.sort(key=lambda x: get_rb_score(x))
    
    # Apply rankings
    current_rank = 102
    for rb in starter_rbs:
        rb['intelligent_rank'] = current_rank
        current_rank += 1
    
    current_rank = 250
    for rb in backup_rbs:
        rb['intelligent_rank'] = current_rank
        current_rank += 1
    
    current_rank = 500
    for rb in deep_rbs:
        rb['intelligent_rank'] = current_rank
        current_rank += 1
    
    return starter_rbs + backup_rbs + deep_rbs

def get_rb_score(rb):
    """Score RBs for ranking within tier"""
    team = rb['team']
    age = rb.get('age') or 25
    years_exp = rb.get('years_exp') or 2
    
    score = 0
    
    # Age is critical for RBs
    if age <= 25:
        score += 15
    elif age <= 28:
        score += 10
    elif age <= 30:
        score += 5
    else:
        score -= 10
    
    # Team offensive quality
    elite_offenses = ['SF', 'KC', 'BUF', 'PHI', 'DET', 'MIA', 'DAL']
    if team in elite_offenses:
        score += 12
    
    # Experience (not too much, not too little)
    if 2 <= years_exp <= 5:
        score += 8
    elif years_exp <= 7:
        score += 5
    
    return -score

def rank_wrs_intelligently(all_players):
    """Rank WRs with football knowledge"""
    wrs = [p for p in all_players if p['position'] == 'WR']
    
    relevant_wrs = []
    deep_wrs = []
    
    for wr in wrs:
        name = wr['name'].lower()
        team = wr['team']
        age = wr.get('age', 25)
        years_exp = wr.get('years_exp', 2)
        
        # Check if likely fantasy relevant
        if (any(relevant in name for relevant in [
            'marquise goodwin', 'nelson agholor', 'allen robinson', 'jarvis landry', 'kenny golladay',
            'tyler boyd', 'adam thielen', 'robert woods', 'cole beasley', 'golden tate'
        ]) or 
        (team in ['KC', 'BUF', 'SF', 'PHI', 'DET', 'MIA', 'CIN', 'LAR'] and (years_exp or 0) >= 2) or
        ((age or 30) <= 26 and (years_exp or 0) <= 3)):
            wr['intelligent_rank'] = 103
            relevant_wrs.append(wr)
        else:
            wr['intelligent_rank'] = 600
            deep_wrs.append(wr)
    
    # Sort and rank
    relevant_wrs.sort(key=lambda x: get_wr_score(x))
    deep_wrs.sort(key=lambda x: get_wr_score(x))
    
    current_rank = 103
    for wr in relevant_wrs:
        wr['intelligent_rank'] = current_rank
        current_rank += 1
    
    current_rank = 600
    for wr in deep_wrs:
        wr['intelligent_rank'] = current_rank
        current_rank += 1
    
    return relevant_wrs + deep_wrs

def get_wr_score(wr):
    """Score WRs for ranking"""
    team = wr['team']
    age = wr.get('age') or 25
    years_exp = wr.get('years_exp') or 2
    
    score = 0
    
    # Age curve for WRs
    if 24 <= age <= 30:
        score += 12
    elif age <= 32:
        score += 8
    
    # Team passing volume
    pass_heavy = ['KC', 'BUF', 'MIA', 'CIN', 'LAC', 'LAR', 'TB', 'GB']
    if team in pass_heavy:
        score += 15
    
    # Experience
    if 3 <= years_exp <= 8:
        score += 10
    
    return -score

def rank_tes_intelligently(all_players):
    """Rank TEs with football knowledge"""
    tes = [p for p in all_players if p['position'] == 'TE']
    
    starter_tes = []
    backup_tes = []
    
    for te in tes:
        name = te['name'].lower()
        team = te['team']
        years_exp = te.get('years_exp', 2)
        
        # Likely starters or relevant TEs
        if (any(starter in name for starter in [
            'zach ertz', 'austin hooper', 'noah fant', 'hayden hurst', 'gerald everett',
            'tyler higbee', 'robert tonyan', 'cole kmet', 'pat freiermuth'
        ]) or (years_exp or 0) >= 3):
            te['intelligent_rank'] = 104
            starter_tes.append(te)
        else:
            te['intelligent_rank'] = 700
            backup_tes.append(te)
    
    # Sort and rank
    starter_tes.sort(key=lambda x: get_te_score(x))
    backup_tes.sort(key=lambda x: get_te_score(x))
    
    current_rank = 104
    for te in starter_tes:
        te['intelligent_rank'] = current_rank
        current_rank += 1
    
    current_rank = 700
    for te in backup_tes:
        te['intelligent_rank'] = current_rank
        current_rank += 1
    
    return starter_tes + backup_tes

def get_te_score(te):
    """Score TEs for ranking"""
    team = te['team']
    age = te.get('age') or 26
    years_exp = te.get('years_exp') or 3
    
    score = 0
    
    # TEs peak later
    if 25 <= age <= 32:
        score += 12
    
    # TE-friendly offenses
    te_friendly = ['KC', 'SF', 'LV', 'ATL', 'TB', 'PHI']
    if team in te_friendly:
        score += 10
    
    # Experience important for TEs
    if 4 <= years_exp <= 10:
        score += 12
    
    return -score

def rank_kickers_intelligently(all_players):
    """Rank kickers by team quality and accuracy"""
    kickers = [p for p in all_players if p['position'] == 'K']
    
    for i, kicker in enumerate(kickers):
        team = kicker['team']
        
        # Elite offenses = more FG opportunities
        if team in ['KC', 'BUF', 'SF', 'PHI', 'DET']:
            kicker['intelligent_rank'] = 900 + i
        elif team in ['MIA', 'CIN', 'DAL', 'LAR', 'BAL']:
            kicker['intelligent_rank'] = 920 + i
        else:
            kicker['intelligent_rank'] = 950 + i
    
    kickers.sort(key=lambda x: x['intelligent_rank'])
    return kickers

def rank_defenses_intelligently(all_players):
    """Rank defenses by actual defensive quality"""
    defenses = [p for p in all_players if p['position'] == 'D/ST']
    
    # Elite defenses
    elite_d = ['BUF', 'SF', 'DAL', 'PIT', 'BAL', 'NE']
    good_d = ['DEN', 'MIA', 'PHI', 'NYJ', 'CLE', 'IND']
    
    for defense in defenses:
        team = defense['team']
        
        if team in elite_d:
            defense['intelligent_rank'] = 800 + elite_d.index(team)
        elif team in good_d:
            defense['intelligent_rank'] = 810 + good_d.index(team)
        else:
            defense['intelligent_rank'] = 820 + hash(team) % 20
    
    defenses.sort(key=lambda x: x['intelligent_rank'])
    return defenses

def get_intelligent_range(rank, position):
    """Get appropriate range sizes for intelligently ranked players"""
    if rank <= 150:
        base_range = 20
    elif rank <= 300:
        base_range = 35
    elif rank <= 500:
        base_range = 50
    else:
        base_range = 80
    
    # Position adjustments
    if position in ['K', 'D/ST']:
        base_range = int(base_range * 1.5)
    elif position == 'QB':
        base_range = int(base_range * 0.8)
    
    return base_range

def export_intelligent_rankings():
    """Export intelligently ranked system"""
    
    all_players = create_intelligent_rankings()
    
    if not all_players:
        print("❌ Failed to create intelligent rankings")
        return
    
    # Create DataFrame
    df_data = []
    for player in all_players:
        df_data.append({
            'Final_Rank': player['final_rank'],
            'Position_Rank': player['position_rank'],
            'Player_Name': player['name'],
            'Position': player['position'],
            'Team': player['team'],
            'High_Rank': player['high_rank'],
            'Low_Rank': player['low_rank'],
            'Std_Deviation': player['std_deviation'],
            'Rank_Range': player['rank_range'],
            'VORP_Score': player['vorp_score'],
            'Has_Expert_Data': player['has_expert'],
            'Age': player['age'],
            'Years_Exp': player['years_exp'],
            'Status': player['status'],
            'Injury_Status': player['injury_status'],
            'Sleeper_ID': player['player_id']
        })
    
    df = pd.DataFrame(df_data)
    
    # Export to Excel
    filename = '/Users/jeffgreenfield/dev/ff_draft_vibe/FF_2025_INTELLIGENT_Rankings.xlsx'
    
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        
        # Main sheet
        main_cols = ['Final_Rank', 'Player_Name', 'Position', 'Team', 'Position_Rank',
                    'High_Rank', 'Low_Rank', 'Std_Deviation', 'Rank_Range', 'VORP_Score',
                    'Has_Expert_Data', 'Age', 'Years_Exp', 'Status']
        df[main_cols].to_excel(writer, sheet_name='Intelligent_Rankings', index=False)
        
        # Position sheets
        for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'D/ST']:
            pos_df = df[df['Position'] == pos]
            if not pos_df.empty:
                pos_cols = ['Position_Rank', 'Player_Name', 'Team', 'Final_Rank',
                           'High_Rank', 'Low_Rank', 'Std_Deviation', 'VORP_Score', 'Has_Expert_Data']
                pos_summary = pos_df[pos_cols]
                sheet_name = pos.replace('/', '_') + '_Intelligent'
                pos_summary.to_excel(writer, sheet_name=sheet_name, index=False)
    
    print(f"🎉 INTELLIGENT RANKINGS EXPORTED!")
    print(f"📁 File: FF_2025_INTELLIGENT_Rankings.xlsx")
    print(f"📊 Total players: {len(df)}")
    
    # Show QB verification
    print(f"\n🏈 QB RANKING VERIFICATION:")
    qb_df = df[df['Position'] == 'QB'].head(20)
    for _, row in qb_df.iterrows():
        expert_status = 'Expert' if row['Has_Expert_Data'] else 'Intelligent'
        print(f"QB{int(row['Position_Rank']):2d}. {row['Player_Name']:<25} (Overall: {int(row['Final_Rank']):3d}) - {expert_status}")

if __name__ == "__main__":
    export_intelligent_rankings()