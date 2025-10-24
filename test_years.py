import sqlite3

conn = sqlite3.connect('DB/f1_database.db')
cursor = conn.cursor()

# Get available years
cursor.execute('SELECT DISTINCT season_year FROM Race ORDER BY season_year')
years = [row[0] for row in cursor.fetchall()]
print(f'Available years: {min(years)} to {max(years)}')
print(f'Total years: {len(years)}')

# Test query for a specific year (e.g., 2015)
test_year = 2015
cursor.execute('''
SELECT DISTINCT 
    d.driver_id,
    d.first_name || ' ' || d.last_name as driver_name,
    t.team_name,
    de.global_elo,
    COUNT(DISTINCT r.race_id) as races_that_year
FROM Driver d
JOIN Result res ON d.driver_id = res.driver_id
JOIN Race r ON res.race_id = r.race_id
JOIN Team t ON res.team_id = t.team_id
LEFT JOIN Driver_Elo de ON d.driver_id = de.driver_id
WHERE r.season_year = ?
GROUP BY d.driver_id, t.team_name
ORDER BY de.global_elo DESC
''', (test_year,))

print(f'\n{test_year} Season Rankings:')
results = cursor.fetchall()
for i, row in enumerate(results[:10], 1):
    print(f'{i}. {row[1]:<25} ({row[2]:<20}) - ELO: {row[3]:.0f}, Races: {row[4]}')

print(f'\nTotal drivers in {test_year}: {len(results)}')

conn.close()
