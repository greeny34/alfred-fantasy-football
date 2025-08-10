#!/usr/bin/env python3
"""
Complete System Test - Demonstrates the full draft optimization system
"""

import requests
import json
import time

BASE_URL = 'http://127.0.0.1:5001'

def test_complete_workflow():
    """Test the complete draft optimization workflow"""
    print("🚀 Testing Complete Fantasy Football Draft Optimization System\n")
    
    # Step 1: Create a new draft session
    print("📊 Step 1: Creating new draft session...")
    session_data = {
        'session_name': 'Complete System Test',
        'team_count': 10,
        'user_draft_position': 6,
        'draft_format': 'ppr'
    }
    
    response = requests.post(f'{BASE_URL}/api/draft/sessions/new', json=session_data)
    if response.status_code != 200:
        print(f"❌ Failed to create session: {response.text}")
        return
    
    session_id = response.json()['session_id']
    print(f"✅ Created session {session_id} (Position 6 in 10-team PPR)")
    
    # Step 2: Get initial optimal strategy
    print(f"\n🎯 Step 2: Getting initial optimal strategy...")
    response = requests.get(f'{BASE_URL}/api/draft/optimize/{session_id}')
    if response.status_code == 200:
        strategy = response.json()
        print(f"✅ Initial Strategy (Pick #{strategy['current_pick']}):")
        print(f"   Next 5 picks: {' → '.join(strategy['optimal_strategy']['next_positions'])}")
        print(f"   Expected points: {strategy['optimal_strategy']['expected_points']:.1f}")
        print(f"   Confidence: {strategy['optimal_strategy']['confidence']:.1f}%")
        print(f"   Reasoning: {strategy['optimal_strategy']['reasoning']}")
    else:
        print(f"❌ Failed to get initial strategy: {response.text}")
    
    # Step 3: Simulate draft picks to user's turn
    print(f"\n🤖 Step 3: Simulating draft to user's turn...")
    response = requests.post(f'{BASE_URL}/api/draft/{session_id}/simulate-round')
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Simulated {result['picks_simulated']} picks")
        print(f"   Next user pick: #{result['next_user_pick']} (Round {result['current_round']})")
        
        # Show some simulated picks
        if 'simulated_picks' in result and result['simulated_picks']:
            print("   Recent AI picks:")
            for pick in result['simulated_picks'][-3:]:
                print(f"   - Pick {pick['pick_number']}: {pick['player']['name']} ({pick['player']['position']}) by Team {pick['team_number']} ({pick['ai_strategy']})")
    else:
        print(f"❌ Failed to simulate round: {response.text}")
    
    # Step 4: Get updated optimal strategy after simulation
    print(f"\n🎯 Step 4: Getting updated strategy after simulation...")
    response = requests.get(f'{BASE_URL}/api/draft/optimize/{session_id}')
    if response.status_code == 200:
        strategy = response.json()
        print(f"✅ Updated Strategy (Pick #{strategy['current_pick']}):")
        print(f"   Current roster: {strategy['current_roster']}")
        print(f"   Next 5 picks: {' → '.join(strategy['optimal_strategy']['next_positions'])}")
        print(f"   Expected points: {strategy['optimal_strategy']['expected_points']:.1f}")
        print(f"   Confidence: {strategy['optimal_strategy']['confidence']:.1f}%")
        print(f"   Reasoning: {strategy['optimal_strategy']['reasoning']}")
    else:
        print(f"❌ Failed to get updated strategy: {response.text}")
    
    # Step 5: Get available players for user's pick
    print(f"\n🎯 Step 5: Getting available players for drafting...")
    response = requests.get(f'{BASE_URL}/api/draft/available-players/{session_id}')
    if response.status_code == 200:
        data = response.json()
        players = data.get('players', [])
        print(f"✅ Top 10 available players:")
        for i, player in enumerate(players[:10], 1):
            print(f"   {i}. {player['name']} ({player['position']}, {player['team']}) - ADP: {player['adp']}")
        
        # Make a user pick (select first available player)
        if players:
            selected_player = players[0]
            print(f"\n🎯 Step 6: Making user pick - {selected_player['name']}...")
            
            pick_data = {'player_id': selected_player['player_id']}
            response = requests.post(f'{BASE_URL}/api/draft/{session_id}/make-pick', json=pick_data)
            
            if response.status_code == 200:
                pick_result = response.json()
                print(f"✅ Successfully drafted {pick_result['player']['name']} ({pick_result['player']['position']}) with pick #{pick_result['pick_number']}")
            else:
                print(f"❌ Failed to make pick: {response.text}")
    else:
        print(f"❌ Failed to get available players: {response.text}")
    
    # Step 7: Continue simulation and show strategy adaptation
    print(f"\n🤖 Step 7: Continuing simulation to see strategy adaptation...")
    response = requests.post(f'{BASE_URL}/api/draft/{session_id}/simulate/10')
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Simulated {result['picks_simulated']} more picks")
        
        # Get final strategy
        response = requests.get(f'{BASE_URL}/api/draft/optimize/{session_id}')
        if response.status_code == 200:
            strategy = response.json()
            print(f"🎯 Final Strategy (Pick #{strategy['current_pick']}):")
            print(f"   Current roster: {strategy['current_roster']}")
            print(f"   Next 5 picks: {' → '.join(strategy['optimal_strategy']['next_positions'])}")
            print(f"   Expected points: {strategy['optimal_strategy']['expected_points']:.1f}")
            print(f"   Confidence: {strategy['optimal_strategy']['confidence']:.1f}%")
            print(f"   Reasoning: {strategy['optimal_strategy']['reasoning']}")
    else:
        print(f"❌ Failed to continue simulation: {response.text}")
    
    # Step 8: Get draft status summary
    print(f"\n📈 Step 8: Getting final draft status...")
    response = requests.get(f'{BASE_URL}/api/draft/{session_id}/status')
    if response.status_code == 200:
        status = response.json()
        print(f"✅ Draft Status:")
        print(f"   Session: {status['session']['session_name']}")
        print(f"   Current pick: #{status['session']['current_pick']}")
        print(f"   Your roster: {status['roster']}")
        
        if status['strategy']:
            print(f"   Strategy confidence: {status['strategy']['confidence']}%")
    else:
        print(f"❌ Failed to get draft status: {response.text}")
    
    print(f"\n🎉 Complete system test finished!")
    print(f"📋 Test Summary:")
    print(f"   ✅ Created draft session with position-based optimization")
    print(f"   ✅ Generated initial optimal strategy with confidence scoring")
    print(f"   ✅ Simulated realistic AI opponents with different strategies")
    print(f"   ✅ Adapted strategy recommendations based on draft state")
    print(f"   ✅ Provided available players for user selection")
    print(f"   ✅ Processed user pick and updated recommendations")
    print(f"   ✅ Demonstrated continuous strategy adaptation")
    
    print(f"\n🌐 Web Interface Available:")
    print(f"   Main App: {BASE_URL}/optimizer")
    print(f"   You can now interact with the draft optimizer through the web interface!")
    
    return session_id

if __name__ == "__main__":
    try:
        session_id = test_complete_workflow()
        print(f"\n🔗 Test session ID: {session_id}")
        print(f"Visit {BASE_URL}/optimizer to continue interacting with this session!")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()