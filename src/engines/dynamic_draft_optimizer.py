#!/usr/bin/env python3
"""
Dynamic Fantasy Football Draft Optimizer
Three-layer dynamic programming system for optimal roster construction
"""

import psycopg2
import os
import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from itertools import permutations, combinations_with_replacement
import hashlib

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(
        host='localhost',
        port='5432',
        user=os.environ.get('USER', 'jeffgreenfield'),
        password='',
        database='fantasy_draft_db'
    )

@dataclass
class RosterState:
    """Current roster composition"""
    QB: int = 0
    RB: int = 0
    WR: int = 0
    TE: int = 0
    K: int = 0
    DST: int = 0
    
    def to_dict(self):
        return {'QB': self.QB, 'RB': self.RB, 'WR': self.WR, 'TE': self.TE, 'K': self.K, 'DST': self.DST}
    
    def signature(self):
        """Create unique hash for caching"""
        return hashlib.md5(str(self.to_dict()).encode()).hexdigest()[:12]
    
    def total_players(self):
        return self.QB + self.RB + self.WR + self.TE + self.K + self.DST
    
    def needs_position(self, position: str) -> bool:
        """Check if we need more of this position"""
        targets = {'QB': 2, 'RB': 4, 'WR': 5, 'TE': 2, 'K': 1, 'DST': 1}
        current = getattr(self, position)
        return current < targets.get(position, 0)
    
    def add_player(self, position: str):
        """Return new RosterState with added position"""
        new_state = RosterState(self.QB, self.RB, self.WR, self.TE, self.K, self.DST)
        current = getattr(new_state, position)
        setattr(new_state, position, current + 1)
        return new_state

@dataclass 
class PlayerTier:
    """Player tier information"""
    position: str
    tier_number: int
    tier_name: str
    min_rank: int
    max_rank: int
    base_value: float
    scarcity_multiplier: float
    current_available: int = 0  # How many players left in this tier

@dataclass
class OptimalPath:
    """Optimal roster completion path"""
    sequence: List[str]  # Positions to draft in order
    expected_points: float
    confidence: float
    reasoning: str
    player_targets: Dict[str, List[str]] = None  # Position -> list of target player names

class DynamicDraftOptimizer:
    def __init__(self):
        self.conn = get_db_connection()
        self.position_tiers = self._load_position_tiers()
        self.strategy_params = self._load_strategy_parameters()
        self.roster_targets = {'QB': 2, 'RB': 4, 'WR': 5, 'TE': 2, 'K': 1, 'DST': 1}
        self.total_picks = 15  # 16 rounds - 1 for total roster size
        
        # Memoization cache
        self.path_cache = {}
    
    def _load_position_tiers(self) -> Dict[str, List[PlayerTier]]:
        """Load position tier definitions"""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT position, tier_number, tier_name, min_rank, max_rank, 
                   base_value, scarcity_multiplier
            FROM position_tier_values 
            ORDER BY position, tier_number
        """)
        
        tiers = {}
        for pos, tier_num, tier_name, min_rank, max_rank, base_val, scarcity in cur.fetchall():
            if pos not in tiers:
                tiers[pos] = []
            tiers[pos].append(PlayerTier(
                position=pos,
                tier_number=tier_num,
                tier_name=tier_name,
                min_rank=min_rank,
                max_rank=max_rank,
                base_value=float(base_val),
                scarcity_multiplier=float(scarcity),
            ))
        
        cur.close()
        return tiers
    
    def _load_strategy_parameters(self) -> Dict:
        """Load strategy parameters by draft position"""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT draft_position, round_number, parameter_name, parameter_value
            FROM strategy_parameters
        """)
        
        params = {}
        for draft_pos, round_num, param_name, param_val in cur.fetchall():
            key = (draft_pos, round_num)
            if key not in params:
                params[key] = {}
            params[key][param_name] = float(param_val)
        
        cur.close()
        return params
    
    def generate_roster_paths(self, current_roster: RosterState, remaining_picks: int) -> List[List[str]]:
        """
        Layer 1: Generate realistic roster completion paths
        Returns list of position sequences that complete the roster
        """
        if remaining_picks <= 0:
            return [[]]
        
        # Calculate remaining needs
        remaining_needs = {}
        for pos, target in self.roster_targets.items():
            current = getattr(current_roster, pos)
            remaining_needs[pos] = max(0, target - current)
        
        total_needs = sum(remaining_needs.values())
        
        # Generate strategic paths based on common draft approaches
        paths = []
        
        # Strategy 1: Fill needs first, then depth
        if total_needs <= remaining_picks:
            base_path = self._get_needs_first_path(remaining_needs, remaining_picks)
            paths.append(base_path)
        
        # Strategy 2: RB-heavy approach (if RB needs exist)
        if remaining_needs.get('RB', 0) > 0:
            rb_heavy = self._get_rb_heavy_path(current_roster, remaining_needs, remaining_picks)
            if rb_heavy and rb_heavy not in paths:
                paths.append(rb_heavy)
        
        # Strategy 3: WR-heavy approach (if WR needs exist)  
        if remaining_needs.get('WR', 0) > 0:
            wr_heavy = self._get_wr_heavy_path(current_roster, remaining_needs, remaining_picks)
            if wr_heavy and wr_heavy not in paths:
                paths.append(wr_heavy)
        
        # Strategy 4: Balanced approach
        balanced = self._get_balanced_path(current_roster, remaining_needs, remaining_picks)
        if balanced and balanced not in paths:
            paths.append(balanced)
        
        # Strategy 5: Zero-RB approach (if early in draft)
        if current_roster.total_players() < 4 and remaining_needs.get('WR', 0) > 0:
            zero_rb = self._get_zero_rb_path(current_roster, remaining_needs, remaining_picks)
            if zero_rb and zero_rb not in paths:
                paths.append(zero_rb)
        
        return paths[:10] if paths else [self._get_fallback_path(remaining_needs, remaining_picks)]
    
    def _get_needs_first_path(self, remaining_needs: Dict[str, int], remaining_picks: int) -> List[str]:
        """Generate path that fills needs first, then adds depth"""
        path = []
        
        # Add all required positions
        for pos, count in remaining_needs.items():
            path.extend([pos] * count)
        
        # Add depth with remaining picks (favor RB/WR)
        extra_picks = remaining_picks - len(path)
        depth_priority = ['RB', 'WR', 'QB', 'TE']
        
        for i in range(extra_picks):
            pos = depth_priority[i % len(depth_priority)]
            path.append(pos)
        
        return path
    
    def _get_rb_heavy_path(self, current_roster: RosterState, remaining_needs: Dict[str, int], remaining_picks: int) -> List[str]:
        """Generate RB-heavy path"""
        path = []
        rb_needs = remaining_needs.get('RB', 0)
        
        if rb_needs == 0:
            return None
        
        # Front-load RBs
        path.extend(['RB'] * min(rb_needs + 1, 3))  # Take extra RB if possible
        
        # Fill other needs
        for pos, count in remaining_needs.items():
            if pos != 'RB':
                path.extend([pos] * count)
        
        # Add remaining picks as depth
        while len(path) < remaining_picks:
            if len([p for p in path if p == 'RB']) < 5:  # Max 5 RBs
                path.append('RB')
            else:
                path.append('WR')
        
        return path[:remaining_picks]
    
    def _get_wr_heavy_path(self, current_roster: RosterState, remaining_needs: Dict[str, int], remaining_picks: int) -> List[str]:
        """Generate WR-heavy path"""
        path = []
        wr_needs = remaining_needs.get('WR', 0)
        
        if wr_needs == 0:
            return None
        
        # Front-load WRs
        path.extend(['WR'] * min(wr_needs + 1, 4))  # Take extra WR if possible
        
        # Fill other needs
        for pos, count in remaining_needs.items():
            if pos != 'WR':
                path.extend([pos] * count)
        
        # Add remaining picks as depth
        while len(path) < remaining_picks:
            if len([p for p in path if p == 'WR']) < 6:  # Max 6 WRs
                path.append('WR')
            else:
                path.append('RB')
        
        return path[:remaining_picks]
    
    def _get_balanced_path(self, current_roster: RosterState, remaining_needs: Dict[str, int], remaining_picks: int) -> List[str]:
        """Generate balanced approach path"""
        path = []
        
        # Alternate between RB and WR for first few picks
        rb_needs = remaining_needs.get('RB', 0)
        wr_needs = remaining_needs.get('WR', 0)
        
        # Add RB/WR in alternating fashion
        for i in range(min(4, remaining_picks)):
            if i % 2 == 0 and rb_needs > 0:
                path.append('RB')
                rb_needs -= 1
            elif wr_needs > 0:
                path.append('WR')
                wr_needs -= 1
            elif rb_needs > 0:
                path.append('RB')
                rb_needs -= 1
            else:
                break
        
        # Fill remaining needs
        for pos, count in remaining_needs.items():
            if pos not in ['RB', 'WR']:
                path.extend([pos] * count)
        
        # Add any remaining RB/WR needs
        path.extend(['RB'] * rb_needs)
        path.extend(['WR'] * wr_needs)
        
        # Fill to remaining picks
        while len(path) < remaining_picks:
            path.append('RB' if len(path) % 2 == 0 else 'WR')
        
        return path[:remaining_picks]
    
    def _get_zero_rb_path(self, current_roster: RosterState, remaining_needs: Dict[str, int], remaining_picks: int) -> List[str]:
        """Generate Zero-RB approach path"""
        if current_roster.RB > 0:  # Already have RB, not zero-RB anymore
            return None
        
        path = []
        
        # Start with WRs if early in draft
        wr_needs = remaining_needs.get('WR', 0)
        path.extend(['WR'] * min(wr_needs, 3))  # Take 3 WRs first
        
        # Add TE if needed
        if remaining_needs.get('TE', 0) > 0:
            path.append('TE')
        
        # Add QB if needed
        if remaining_needs.get('QB', 0) > 0:
            path.append('QB')
        
        # Finally add RBs
        rb_needs = remaining_needs.get('RB', 0)
        path.extend(['RB'] * rb_needs)
        
        # Fill remaining with WR depth
        while len(path) < remaining_picks:
            path.append('WR')
            
        return path[:remaining_picks]
    
    def _get_fallback_path(self, remaining_needs: Dict[str, int], remaining_picks: int) -> List[str]:
        """Fallback path when other strategies fail"""
        path = []
        
        # Simple priority order
        priority = ['RB', 'WR', 'QB', 'TE', 'K', 'DST']
        
        for pos in priority:
            count = remaining_needs.get(pos, 0)
            path.extend([pos] * count)
        
        # Fill remaining with RB/WR
        while len(path) < remaining_picks:
            path.append('RB' if len(path) % 2 == 0 else 'WR')
            
        return path[:remaining_picks]
    
    def _is_valid_depth_combination(self, current_roster: RosterState, base_needs: List[str], depth_picks: List[str]) -> bool:
        """Check if depth combination makes sense"""
        # Don't exceed reasonable roster limits
        max_limits = {'QB': 3, 'RB': 6, 'WR': 7, 'TE': 3, 'K': 1, 'DST': 1}
        
        for pos in set(base_needs + depth_picks):
            current = getattr(current_roster, pos)
            drafted_count = base_needs.count(pos) + depth_picks.count(pos)
            if current + drafted_count > max_limits.get(pos, 5):
                return False
        
        return True
    
    def _generate_priority_paths(self, remaining_needs: Dict[str, int], remaining_picks: int) -> List[List[str]]:
        """Generate priority-based paths when we can't fill all needs"""
        priority_order = ['RB', 'WR', 'QB', 'TE', 'K', 'DST']
        
        paths = []
        available_picks = remaining_picks
        path = []
        
        for pos in priority_order:
            needed = remaining_needs.get(pos, 0)
            can_take = min(needed, available_picks)
            path.extend([pos] * can_take)
            available_picks -= can_take
            
            if available_picks <= 0:
                break
        
        return [path]
    
    def calculate_path_value(self, path: List[str], current_roster: RosterState, 
                           draft_position: int, start_pick: int) -> Tuple[float, float, List[str]]:
        """
        Layer 2: Calculate expected value for a specific roster path
        Returns (expected_points, confidence, player_targets)
        """
        total_value = 0.0
        confidence = 1.0
        target_players = []
        
        temp_roster = current_roster
        current_pick = start_pick
        
        for i, position in enumerate(path):
            # Get best available tier for this position at this pick
            tier_info = self._get_best_available_tier(position, current_pick)
            if not tier_info:
                confidence *= 0.5  # Heavily penalize if no players available
                continue
            
            # Calculate position value with strategy multipliers
            position_value = self._calculate_position_value(
                tier_info, position, temp_roster, draft_position, 
                round_num=((current_pick - 1) // 10) + 1
            )
            
            total_value += position_value
            
            # Update confidence based on tier availability and pick timing
            tier_confidence = self._calculate_tier_confidence(tier_info, current_pick)
            confidence *= tier_confidence
            
            # Add to target players (simplified - would use actual player names)
            target_players.append(f"{position}_{tier_info.tier_name}")
            
            # Update state for next iteration
            temp_roster = temp_roster.add_player(position)
            current_pick += 1
        
        return total_value, confidence, target_players
    
    def _get_best_available_tier(self, position: str, pick_number: int) -> Optional[PlayerTier]:
        """Get the best tier likely available at this pick for this position"""
        if position not in self.position_tiers:
            return None
        
        # Simplified tier availability based on pick number
        # In reality, this would query actual available players
        tiers = self.position_tiers[position]
        
        for tier in tiers:
            # Rough approximation: elite tiers go early, lower tiers later
            if position in ['RB', 'WR']:
                if tier.tier_number == 1 and pick_number <= 20:
                    return tier
                elif tier.tier_number == 2 and pick_number <= 50:
                    return tier
                elif tier.tier_number == 3 and pick_number <= 100:
                    return tier
                elif tier.tier_number >= 4:
                    return tier
            else:
                # QB/TE/K/DST are less pick-sensitive
                return tier
        
        return tiers[-1] if tiers else None
    
    def _calculate_position_value(self, tier: PlayerTier, position: str, 
                                current_roster: RosterState, draft_position: int, round_num: int) -> float:
        """Calculate value for drafting this position/tier"""
        base_value = tier.base_value * tier.scarcity_multiplier
        
        # Apply strategy parameters
        multiplier = 1.0
        
        # Draft position specific bonuses
        if (draft_position, None) in self.strategy_params:
            params = self.strategy_params[(draft_position, None)]
            if position == 'RB' and 'rb_bonus_early' in params:
                multiplier *= params['rb_bonus_early']
            elif position == 'WR' and 'wr_bonus_late' in params:
                multiplier *= params['wr_bonus_late']
            elif 'upside_bonus' in params and position in ['RB', 'WR']:
                multiplier *= params['upside_bonus']
        
        # Round specific penalties/bonuses
        if (0, round_num) in self.strategy_params:  # 0 = all positions
            params = self.strategy_params[(0, round_num)]
            if position == 'QB' and 'no_qb_penalty' in params:
                multiplier *= params['no_qb_penalty']
            elif position == 'TE' and 'no_te_penalty' in params:
                multiplier *= params['no_te_penalty']
            elif position == 'DST' and 'dst_bonus' in params:
                multiplier *= params['dst_bonus']
            elif position == 'K' and 'k_bonus' in params:
                multiplier *= params['k_bonus']
        
        # Need multiplier - higher value if we need this position
        if current_roster.needs_position(position):
            need_multiplier = 1.3
        else:
            need_multiplier = 0.8  # Depth pick
        
        return base_value * multiplier * need_multiplier
    
    def _calculate_tier_confidence(self, tier: PlayerTier, pick_number: int) -> float:
        """Calculate confidence that we can get a player from this tier at this pick"""
        # Simplified confidence calculation
        # Elite tiers become less likely as picks progress
        if tier.tier_number == 1:
            return max(0.3, 1.0 - (pick_number / 50.0))
        elif tier.tier_number == 2:
            return max(0.5, 1.0 - (pick_number / 80.0))
        else:
            return max(0.7, 1.0 - (pick_number / 120.0))
    
    def find_optimal_strategy(self, session_id: int) -> OptimalPath:
        """
        Layer 3: Find the optimal draft strategy
        Main entry point for optimization
        """
        # Get current draft state
        current_roster, next_pick = self._get_draft_state(session_id)
        draft_position = self._get_draft_position(session_id)
        
        remaining_picks = self.total_picks - current_roster.total_players()
        
        if remaining_picks <= 0:
            return OptimalPath([], 0.0, 1.0, "Draft complete")
        
        # Check cache first
        cache_key = f"{current_roster.signature()}_{remaining_picks}_{draft_position}"
        if cache_key in self.path_cache:
            return self.path_cache[cache_key]
        
        # Generate all possible roster completion paths
        print(f"🔍 Generating paths for {remaining_picks} remaining picks...")
        possible_paths = self.generate_roster_paths(current_roster, remaining_picks)
        print(f"📊 Evaluating {len(possible_paths)} possible strategies...")
        
        # Evaluate each path
        best_path = None
        best_value = -float('inf')
        
        for path in possible_paths[:20]:  # Limit evaluation for performance
            expected_points, confidence, targets = self.calculate_path_value(
                path, current_roster, draft_position, next_pick
            )
            
            # Weighted score: value * confidence
            weighted_score = expected_points * confidence
            
            if weighted_score > best_value:
                best_value = weighted_score
                best_path = OptimalPath(
                    sequence=path,
                    expected_points=expected_points,
                    confidence=confidence,
                    reasoning=self._generate_reasoning(path, current_roster, draft_position),
                    player_targets=targets
                )
        
        # Cache result
        if best_path:
            self.path_cache[cache_key] = best_path
        
        return best_path or OptimalPath([], 0.0, 0.0, "No valid paths found")
    
    def _get_draft_state(self, session_id: int) -> Tuple[RosterState, int]:
        """Get current roster state and next pick number"""
        cur = self.conn.cursor()
        
        # Get current roster
        cur.execute("""
            SELECT p.position, COUNT(*) as count
            FROM draft_picks dp
            JOIN players p ON dp.player_id = p.player_id
            WHERE dp.session_id = %s AND dp.is_user_pick = TRUE
            GROUP BY p.position
        """, (session_id,))
        
        roster = RosterState()
        for position, count in cur.fetchall():
            setattr(roster, position, count)
        
        # Get next pick number
        cur.execute("""
            SELECT COALESCE(MAX(pick_number), 0) + 1 as next_pick
            FROM draft_picks 
            WHERE session_id = %s
        """, (session_id,))
        
        next_pick = cur.fetchone()[0]
        cur.close()
        return roster, next_pick
    
    def _get_draft_position(self, session_id: int) -> int:
        """Get user's draft position"""
        cur = self.conn.cursor()
        cur.execute("SELECT user_draft_position FROM draft_sessions WHERE session_id = %s", (session_id,))
        result = cur.fetchone()
        cur.close()
        return result[0] if result else 6  # Default to middle position
    
    def _generate_reasoning(self, path: List[str], current_roster: RosterState, draft_position: int) -> str:
        """Generate human-readable reasoning for the strategy"""
        next_3 = path[:3]
        reasoning_parts = []
        
        # Analyze immediate needs
        urgent_needs = []
        for pos, target in self.roster_targets.items():
            current = getattr(current_roster, pos)
            if current < target:
                needed = target - current
                if needed >= 2:
                    urgent_needs.append(f"{pos}({needed} needed)")
        
        if urgent_needs:
            reasoning_parts.append(f"Urgent needs: {', '.join(urgent_needs)}")
        
        # Analyze next few picks
        if len(next_3) >= 2:
            if next_3[0] == next_3[1]:
                reasoning_parts.append(f"Double-tap {next_3[0]} strategy")
            elif set(next_3[:2]) == {'RB', 'WR'}:
                reasoning_parts.append("Balanced RB/WR approach")
        
        # Draft position strategy
        if draft_position == 1:
            reasoning_parts.append("Pick 1: Lock elite talent early")
        elif draft_position == 10:
            reasoning_parts.append("Pick 10: Leverage turn advantage")
        elif 6 <= draft_position <= 9:
            reasoning_parts.append("Mid-round: Target upside plays")
        
        return "; ".join(reasoning_parts) if reasoning_parts else "Optimal value-based approach"
    
    def save_strategy_state(self, session_id: int, optimal_path: OptimalPath, pick_number: int):
        """Save current optimal strategy to database"""
        cur = self.conn.cursor()
        
        try:
            cur.execute("""
                INSERT INTO draft_strategy_states 
                (session_id, pick_number, roster_state, optimal_path, confidence_score, 
                 expected_points, reasoning)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (session_id, pick_number) 
                DO UPDATE SET 
                    optimal_path = EXCLUDED.optimal_path,
                    confidence_score = EXCLUDED.confidence_score,
                    expected_points = EXCLUDED.expected_points,
                    reasoning = EXCLUDED.reasoning
            """, (
                session_id,
                pick_number,
                json.dumps(optimal_path.sequence[:5]),  # Next 5 picks
                json.dumps(optimal_path.sequence),
                optimal_path.confidence * 100,  # Convert to percentage
                optimal_path.expected_points,
                optimal_path.reasoning
            ))
            
            self.conn.commit()
            print(f"✅ Saved strategy state for pick {pick_number}")
            
        except Exception as e:
            print(f"❌ Error saving strategy state: {e}")
            self.conn.rollback()
        finally:
            cur.close()
    
    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()


def test_optimizer():
    """Test the dynamic draft optimizer"""
    print("🧪 Testing Dynamic Draft Optimizer...\n")
    
    optimizer = DynamicDraftOptimizer()
    
    # Create test session
    cur = optimizer.conn.cursor()
    cur.execute("""
        INSERT INTO draft_sessions (session_name, team_count, user_draft_position)
        VALUES ('Optimization Test', 10, 6)
        RETURNING session_id
    """)
    session_id = cur.fetchone()[0]
    optimizer.conn.commit()
    
    print(f"📊 Created test session: {session_id}")
    
    # Test with empty roster (start of draft)
    print("\n🚀 Testing start-of-draft optimization...")
    optimal_strategy = optimizer.find_optimal_strategy(session_id)
    
    print(f"📈 Optimal Strategy:")
    print(f"   Next 5 picks: {optimal_strategy.sequence[:5]}")
    print(f"   Expected points: {optimal_strategy.expected_points:.1f}")
    print(f"   Confidence: {optimal_strategy.confidence*100:.1f}%")
    print(f"   Reasoning: {optimal_strategy.reasoning}")
    
    # Save the strategy
    optimizer.save_strategy_state(session_id, optimal_strategy, 1)
    
    # Test with partial roster
    print("\n🔄 Testing mid-draft optimization (after drafting RB, WR)...")
    
    # Add some test picks using real player IDs
    cur.execute("SELECT player_id FROM players LIMIT 2")
    player_ids = [row[0] for row in cur.fetchall()]
    
    if len(player_ids) >= 2:
        cur.execute("""
            INSERT INTO draft_picks (session_id, player_id, pick_number, round_number, 
                                   pick_in_round, team_number, is_user_pick)
            VALUES (%s, %s, 6, 1, 6, 6, TRUE), (%s, %s, 15, 2, 5, 6, TRUE)
        """, (session_id, player_ids[0], session_id, player_ids[1]))
    optimizer.conn.commit()
    
    optimal_strategy2 = optimizer.find_optimal_strategy(session_id)
    
    print(f"📈 Updated Optimal Strategy:")
    print(f"   Next 5 picks: {optimal_strategy2.sequence[:5]}")
    print(f"   Expected points: {optimal_strategy2.expected_points:.1f}")
    print(f"   Confidence: {optimal_strategy2.confidence*100:.1f}%")
    print(f"   Reasoning: {optimal_strategy2.reasoning}")
    
    # Clean up - delete all related records first
    cur.execute("DELETE FROM draft_strategy_states WHERE session_id = %s", (session_id,))
    cur.execute("DELETE FROM draft_picks WHERE session_id = %s", (session_id,))
    cur.execute("DELETE FROM draft_sessions WHERE session_id = %s", (session_id,))
    optimizer.conn.commit()
    cur.close()
    
    print("\n✅ Optimization test complete!")


if __name__ == "__main__":
    test_optimizer()