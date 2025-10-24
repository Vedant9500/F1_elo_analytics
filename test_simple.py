"""
Simple working query
"""

import sqlite3
import pandas as pd

conn = sqlite3.connect('DB/f1_database.db')

print("=" * 60)
print("SIMPLIFIED WORKING QUERY")
print("=" * 60)

# Simple query that should work
query = """
SELECT 
    d.driver_id,
    d.first_name || ' ' || d.last_name as driver_name,
    d.nationality,
    de.qualifying_elo,
    de.race_elo,
    de.global_elo,
    de.qualifying_races,
    de.race_races
FROM Driver d
INNER JOIN Driver_Elo de ON d.driver_id = de.driver_id
WHERE de.global_elo IS NOT NULL
ORDER BY de.global_elo DESC
LIMIT 20
"""

print("\nExecuting simple query...")
df = pd.read_sql_query(query, conn)
print(f"Returned {len(df)} rows\n")
print(df[['driver_name', 'global_elo', 'nationality']].to_string(index=False))

conn.close()

print("\n" + "=" * 60)
print("✅ SUCCESS! Basic query works!")
print("=" * 60)
