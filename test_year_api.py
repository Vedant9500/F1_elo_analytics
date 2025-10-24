import requests

# Test the year-specific endpoint
try:
    # Test /api/years endpoint
    response = requests.get('http://127.0.0.1:5000/api/years')
    data = response.json()
    
    if data['success']:
        print(f"✓ Available years loaded: {len(data['years'])} years")
        print(f"  Range: {min(data['years'])} to {max(data['years'])}")
    else:
        print("✗ Failed to load years")
    
    # Test year-specific rankings (2015)
    print("\nTesting 2015 rankings...")
    response = requests.get('http://127.0.0.1:5000/api/rankings?filter=year&year=2015')
    data = response.json()
    
    if data['success']:
        print(f"✓ 2015 rankings loaded: {data['count']} drivers")
        print("\nTop 5 drivers in 2015:")
        for i, driver in enumerate(data['rankings'][:5], 1):
            print(f"  {i}. {driver['driver_name']} ({driver.get('current_team', 'N/A')}) - ELO: {driver['global_elo']:.0f}")
    else:
        print("✗ Failed to load 2015 rankings")
    
    # Test 2020 rankings
    print("\nTesting 2020 rankings...")
    response = requests.get('http://127.0.0.1:5000/api/rankings?filter=year&year=2020')
    data = response.json()
    
    if data['success']:
        print(f"✓ 2020 rankings loaded: {data['count']} drivers")
        print("\nTop 5 drivers in 2020:")
        for i, driver in enumerate(data['rankings'][:5], 1):
            print(f"  {i}. {driver['driver_name']} ({driver.get('current_team', 'N/A')}) - ELO: {driver['global_elo']:.0f}")
    else:
        print("✗ Failed to load 2020 rankings")
        
except requests.exceptions.ConnectionError:
    print("✗ Could not connect to Flask server. Make sure it's running on http://127.0.0.1:5000")
except Exception as e:
    print(f"✗ Error: {e}")
