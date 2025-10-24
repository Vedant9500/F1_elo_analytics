"""
Direct SQL query test
"""

import sqlite3
import pandas as pd

conn = sqlite3.connect('DB/f1_database.db')

print("=" * 60)
print("TESTING SQL QUERY FROM APP.PY")
print("=" * 60)

# Test the exact query structure from app.py for 'century' filter
year_condition = "AND r.season_year >= 2000"

query = f"""
SELECT 
    d.driver_id as driverId,
    d.first_name || ' ' || d.last_name as driver_name,
    SUBSTR(d.last_name, 1, 3) as driver_code,
    d.nationality,
    COALESCE(de.qualifying_elo, 1500) as qualifying_elo,
    COALESCE(de.race_elo, 1500) as race_elo,
    COALESCE(de.global_elo, 1500) as global_elo,
    COALESCE(de.qualifying_races, 0) as qualifying_races,
    COALESCE(de.race_races, 0) as race_races,
    (
        SELECT t2.team_name 
        FROM Result res2
        JOIN Team t2 ON res2.team_id = t2.team_id
        JOIN Race r2 ON res2.race_id = r2.race_id
        WHERE res2.driver_id = d.driver_id
        ORDER BY r2.race_date DESC
        LIMIT 1
    ) as current_team,
    (
        SELECT COUNT(DISTINCT r3.race_id)
        FROM Result res3
        JOIN Race r3 ON res3.race_id = r3.race_id
        WHERE res3.driver_id = d.driver_id {year_condition.replace('r.season_year', 'r3.season_year')}
    ) as total_races,
    (
        SELECT COUNT(*)
        FROM Result res4
        JOIN Race r4 ON res4.race_id = r4.race_id
        WHERE res4.driver_id = d.driver_id 
        AND res4.finish_position = 1
        {year_condition.replace('r.season_year', 'r4.season_year')}
    ) as wins,
    (
        SELECT COUNT(*)
        FROM Result res5
        JOIN Race r5 ON res5.race_id = r5.race_id
        WHERE res5.driver_id = d.driver_id 
        AND res5.finish_position <= 3
        {year_condition.replace('r.season_year', 'r5.season_year')}
    ) as podiums
FROM Driver d
INNER JOIN Driver_Elo de ON d.driver_id = de.driver_id
WHERE de.global_elo IS NOT NULL
ORDER BY de.global_elo DESC
LIMIT 10
"""

print("\nExecuting query...")
try:
    df = pd.read_sql_query(query, conn)
    print(f"\nReturned {len(df)} rows")
    
    if len(df) > 0:
        print("\nTop 10 drivers:")
        print(df[['driver_name', 'global_elo', 'current_team', 'total_races']].to_string(index=False))
        
        # Check for drivers with races in 2000+
        drivers_with_races = df[df['total_races'] > 0]
        print(f"\n\nDrivers with races since 2000: {len(drivers_with_races)}")
        
        if len(drivers_with_races) == 0:
            print("\n⚠️  PROBLEM: Filter removes all drivers because they have 0 races in 2000-2024!")
            print("The app.py code filters out drivers with total_races = 0")
            
    else:
        print("ERROR: Query returned 0 rows!")
        
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()

conn.close()
