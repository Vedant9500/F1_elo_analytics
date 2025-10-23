LOAD DATA INFILE 'd:/f1-elo/archive/status.csv'
INTO TABLE Status
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(status_id, status_description);

LOAD DATA INFILE 'd:/f1-elo/archive/constructors.csv'
INTO TABLE Team
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(team_id, @dummy, team_name, base_country, @dummy)
SET principal_name = NULL,
    total_points = 0,
    total_wins = 0;

LOAD DATA INFILE 'd:/f1-elo/archive/drivers.csv'
INTO TABLE Driver
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(driver_id, @dummy, @dummy, @dummy, first_name, last_name, 
 @birth_date, nationality, @dummy)
SET birth_date = NULLIF(@birth_date, '\\N'),
    debut_year = NULL,
    current_team_id = NULL;

LOAD DATA INFILE 'd:/f1-elo/archive/circuits.csv'
INTO TABLE Circuit
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(circuit_id, @dummy, circuit_name, location, country, 
 @dummy, @dummy, @dummy, @dummy)
SET lap_length_km = NULL,
    laps = NULL;

LOAD DATA INFILE 'd:/f1-elo/archive/races.csv'
INTO TABLE Race
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(race_id, season_year, round_number, circuit_id, race_name, 
 race_date, @dummy, @dummy, @dummy, @dummy, @dummy, @dummy, 
 @dummy, @dummy, @dummy, @dummy, @dummy, @dummy);

LOAD DATA INFILE 'd:/f1-elo/archive/results.csv'
INTO TABLE Result
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(result_id, race_id, driver_id, team_id, @dummy, @dummy, 
 @position, @dummy, @dummy, points, laps_completed, @dummy, 
 @dummy, @dummy, @dummy, @fastest_lap, @dummy, @status_id)
SET position = NULLIF(@position, '\\N'),
    fastest_lap = NULLIF(@fastest_lap, '\\N'),
    status = (SELECT status_description FROM Status WHERE status_id = @status_id);

UPDATE Team t
SET total_points = (
    SELECT COALESCE(SUM(r.points), 0)
    FROM Result r
    WHERE r.team_id = t.team_id
),
total_wins = (
    SELECT COUNT(*)
    FROM Result r
    WHERE r.team_id = t.team_id AND r.position = 1
);

UPDATE Driver d
SET debut_year = (
    SELECT MIN(ra.season_year)
    FROM Result r
    JOIN Race ra ON r.race_id = ra.race_id
    WHERE r.driver_id = d.driver_id
);

UPDATE Driver d
SET current_team_id = (
    SELECT r.team_id
    FROM Result r
    JOIN Race ra ON r.race_id = ra.race_id
    WHERE r.driver_id = d.driver_id
    ORDER BY ra.race_date DESC
    LIMIT 1
);

SELECT 'Status' AS table_name, COUNT(*) AS record_count FROM Status
UNION ALL
SELECT 'Team', COUNT(*) FROM Team
UNION ALL
SELECT 'Driver', COUNT(*) FROM Driver
UNION ALL
SELECT 'Circuit', COUNT(*) FROM Circuit
UNION ALL
SELECT 'Race', COUNT(*) FROM Race
UNION ALL
SELECT 'Result', COUNT(*) FROM Result;

