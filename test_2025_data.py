"""
Quick test to see what's in the database for 2025
"""

import sqlite3
import pandas as pd

conn = sqlite3.connect('DB/f1_database.db')

# Check races in 2025
print("=" * 60)
print("CHECKING 2025 DATA")
print("=" * 60)

cursor = conn.cursor()

# Check if we have any 2025 races
cursor.execute("SELECT COUNT(*) FROM Race WHERE season_year = 2025")
race_count = cursor.fetchone()[0]
print(f"\n2025 Races in database: {race_count}")

if race_count > 0:
    cursor.execute("SELECT race_id, race_name, race_date FROM Race WHERE season_year = 2025 LIMIT 5")
    races = cursor.fetchall()
    print("\nFirst 5 races in 2025:")
    for race in races:
        print(f"  - {race[1]} ({race[2]})")

# Check if we have results for 2025
cursor.execute("""
    SELECT COUNT(DISTINCT r.driver_id) 
    FROM Result r
    JOIN Race ra ON r.race_id = ra.race_id
    WHERE ra.season_year = 2025
""")
driver_count = cursor.fetchone()[0]
print(f"\nDrivers with 2025 results: {driver_count}")

# Check the actual query from app.py
print("\n" + "=" * 60)
print("TESTING APP QUERY FOR 2025")
print("=" * 60)

query = """
SELECT 
    d.driver_id as driverId,
    d.first_name || ' ' || d.last_name as driver_name,
    de.global_elo,
    (
        SELECT COUNT(DISTINCT r3.race_id)
        FROM Result res3
        JOIN Race r3 ON res3.race_id = r3.race_id
        WHERE res3.driver_id = d.driver_id 
        AND r3.season_year = 2025
    ) as total_races
FROM Driver d
INNER JOIN Driver_Elo de ON d.driver_id = de.driver_id
WHERE de.global_elo IS NOT NULL
ORDER BY de.global_elo DESC
LIMIT 10
"""

df = pd.read_sql_query(query, conn)
print(f"\nTop 10 drivers by ELO:")
print(df[['driver_name', 'global_elo', 'total_races']].to_string(index=False))

# Check how many have 2025 races
drivers_with_2025 = df[df['total_races'] > 0]
print(f"\nDrivers with 2025 races: {len(drivers_with_2025)}")

conn.close()
