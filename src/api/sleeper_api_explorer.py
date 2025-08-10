import requests
import json

def explore_sleeper_api():
    """Comprehensive exploration of Sleeper API"""
    print("🔍 Sleeper API Explorer")
    print("=" * 40)
    
    base_url = "https://api.sleeper.app"
    
    # Test different endpoints
    endpoints_to_test = [
        # User endpoints
        ("/v1/user/jeffgreenfield", "Find user by username"),
        
        # Draft endpoints  
        ("/v1/state/nfl", "Get NFL state info"),
        ("/v1/players/nfl", "Get all NFL players (large file)"),
        
        # Mock draft related
        ("/mockdraft", "Mock draft main page"),
        ("/v1/mockdraft", "Mock draft API v1"),
        
        # Try some other common patterns
        ("/v1/drafts", "All drafts"),
        ("/v1/leagues", "All leagues"),
        ("/v1/mock", "Mock endpoint"),
    ]
    
    for endpoint, description in endpoints_to_test:
        try:
            url = f"{base_url}{endpoint}"
            print(f"\n📍 Testing: {description}")
            print(f"   URL: {url}")
            
            # Make request with timeout
            response = requests.get(url, timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                # Check content type
                content_type = response.headers.get('content-type', '')
                print(f"   Content-Type: {content_type}")
                
                if 'application/json' in content_type:
                    try:
                        data = response.json()
                        print(f"   ✅ JSON Response")
                        
                        if isinstance(data, dict):
                            keys = list(data.keys())[:5]
                            print(f"   🔑 Keys: {keys}")
                            if 'user_id' in data:
                                print(f"   👤 User ID: {data.get('user_id')}")
                            if 'display_name' in data:
                                print(f"   📝 Display Name: {data.get('display_name')}")
                                
                        elif isinstance(data, list):
                            print(f"   📋 List with {len(data)} items")
                            if data and isinstance(data[0], dict):
                                sample_keys = list(data[0].keys())[:3]
                                print(f"   🔑 Sample keys: {sample_keys}")
                        else:
                            print(f"   📊 Data type: {type(data)}")
                            
                    except json.JSONDecodeError:
                        print(f"   ❌ Invalid JSON")
                        # Show first 100 chars of response
                        preview = response.text[:100]
                        print(f"   📄 Preview: {preview}...")
                        
                elif 'text/html' in content_type:
                    print(f"   🌐 HTML Response (probably web page)")
                    # Check if it mentions mock draft
                    if 'mock' in response.text.lower() or 'draft' in response.text.lower():
                        print(f"   🎯 Contains draft-related content")
                    
                else:
                    print(f"   📄 Other content type")
                    
            elif response.status_code == 404:
                print(f"   ❌ Not Found")
            elif response.status_code == 403:
                print(f"   🔒 Forbidden (might need auth)")
            else:
                print(f"   ❓ Other status: {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ Request timed out")
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request error: {e}")
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")

def test_user_lookup():
    """Test looking up a specific user"""
    print("\n🔍 Testing User Lookup")
    print("=" * 30)
    
    # Test with some common usernames
    test_usernames = ["jeffgreenfield", "test", "admin", "user"]
    
    for username in test_usernames:
        try:
            url = f"https://api.sleeper.app/v1/user/{username}"
            response = requests.get(url, timeout=5)
            
            print(f"Username: {username}")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"✅ Found user: {data.get('display_name', 'Unknown')}")
                    print(f"   User ID: {data.get('user_id', 'Unknown')}")
                    return data.get('user_id')  # Return first valid user ID
                except:
                    print(f"❌ Invalid JSON response")
            else:
                print(f"❌ User not found")
                
            print()
            
        except Exception as e:
            print(f"❌ Error: {e}\n")
    
    return None

def test_nfl_state():
    """Test getting NFL state information"""
    print("\n🏈 Testing NFL State")
    print("=" * 25)
    
    try:
        url = "https://api.sleeper.app/v1/state/nfl"
        response = requests.get(url, timeout=5)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ NFL State Data:")
            
            for key, value in data.items():
                print(f"   {key}: {value}")
                
            # Check if it's the 2025 season
            season = data.get('season', 'Unknown')
            week = data.get('week', 'Unknown')
            season_type = data.get('season_type', 'Unknown')
            
            print(f"\n🎯 Current: {season} Season, Week {week}, Type: {season_type}")
            
        else:
            print(f"❌ Failed to get NFL state")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print("🏈 Comprehensive Sleeper API Test")
    print("=" * 50)
    
    # Test 1: General API exploration
    explore_sleeper_api()
    
    # Test 2: User lookup
    user_id = test_user_lookup()
    
    # Test 3: NFL state
    test_nfl_state()
    
    print(f"\n🎯 Next Steps:")
    if user_id:
        print(f"✅ Found valid user ID: {user_id}")
        print(f"   You can now test league/draft endpoints")
    else:
        print(f"❌ No valid user found")
        print(f"   Try with your actual Sleeper username")
    
    print(f"\n💡 To test with your account:")
    print(f"   1. Create/join a league or mock draft on Sleeper")
    print(f"   2. Use your username in the API")
    print(f"   3. Access your leagues and drafts")

if __name__ == "__main__":
    main()