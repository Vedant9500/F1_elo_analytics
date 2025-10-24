import sqlite3

conn = sqlite3.connect('DB/f1_database.db')
cursor = conn.cursor()

# Check NULL values
cursor.execute('SELECT COUNT(*) FROM Driver_Elo WHERE era_adjusted_elo IS NULL')
print(f'NULL era_adjusted_elo: {cursor.fetchone()[0]}')

# Check top 5 modern era
cursor.execute('''
SELECT d.first_name || ' ' || d.last_name, de.era_adjusted_elo, de.global_elo 
FROM Driver_Elo de
JOIN Driver d ON de.driver_id = d.driver_id
WHERE de.debut_year >= 2000 
ORDER BY de.era_adjusted_elo DESC 
LIMIT 5
''')
print('\nTop 5 Modern Era (2000+):')
for row in cursor.fetchall():
    print(f'{row[0]}: Era={row[1]:.0f}, Global={row[2]:.0f}')

# Check 2024 season drivers
cursor.execute('''
SELECT DISTINCT d.first_name || ' ' || d.last_name, de.era_adjusted_elo 
FROM Driver d
JOIN Driver_Elo de ON d.driver_id = de.driver_id
WHERE EXISTS (
    SELECT 1 FROM Result r 
    JOIN Race ra ON r.race_id = ra.race_id 
    WHERE r.driver_id = d.driver_id AND ra.season_year = 2024
)
ORDER BY de.era_adjusted_elo DESC 
LIMIT 5
''')
print('\nTop 5 2024 Season:')
for row in cursor.fetchall():
    print(f'{row[0]}: Era={row[1]:.0f}')

# Check all-time top 5
cursor.execute('''
SELECT d.first_name || ' ' || d.last_name, de.global_elo 
FROM Driver_Elo de
JOIN Driver d ON de.driver_id = d.driver_id
ORDER BY de.global_elo DESC 
LIMIT 5
''')
print('\nTop 5 All-Time:')
for row in cursor.fetchall():
    print(f'{row[0]}: Global={row[1]:.0f}')

conn.close()
