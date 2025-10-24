"""
Direct test of the get_driver_rankings function
"""

import sys
sys.path.insert(0, 'd:/f1-elo')

from app import get_driver_rankings

print("Testing get_driver_rankings function...")
print("=" * 60)

# Test century filter
print("\nTesting 'century' filter:")
rankings = get_driver_rankings('century')
print(f"Returned {len(rankings)} drivers")

if rankings:
    print("\nFirst 5 drivers:")
    for i, driver in enumerate(rankings[:5], 1):
        print(f"{i}. {driver.get('driver_name', 'Unknown')} - ELO: {driver.get('global_elo', 0):.1f}")
else:
    print("ERROR: No rankings returned!")
    print("\nLet me check the query directly...")
    
    import sqlite3
    import pandas as pd
    
    conn = sqlite3.connect('DB/f1_database.db')
    
    # Simple test query
    query = """
    SELECT 
        d.driver_id,
        d.first_name || ' ' || d.last_name as driver_name,
        de.global_elo
    FROM Driver d
    INNER JOIN Driver_Elo de ON d.driver_id = de.driver_id
    WHERE de.global_elo IS NOT NULL
    ORDER BY de.global_elo DESC
    LIMIT 5
    """
    
    df = pd.read_sql_query(query, conn)
    print("\nDirect query results:")
    print(df.to_string(index=False))
    
    conn.close()
