-- =============================================
-- F1 Database Data Import Script (PostgreSQL)
-- Import data from CSV files into the database
-- =============================================

-- NOTE: Update the file paths to match your actual CSV file locations

-- =============================================
-- 1. Import Status Data
-- =============================================
COPY Status(status_id, status_description)
FROM 'd:/f1-elo/archive/status.csv'
DELIMITER ','
CSV HEADER
QUOTE '"';

-- =============================================
-- 2. Import Team Data (from constructors.csv)
-- =============================================
CREATE TEMP TABLE temp_constructors (
    constructorId INT,
    constructorRef VARCHAR(100),
    name VARCHAR(100),
    nationality VARCHAR(50),
    url VARCHAR(255)
);

COPY temp_constructors
FROM 'd:/f1-elo/archive/constructors.csv'
DELIMITER ','
CSV HEADER
QUOTE '"';

INSERT INTO Team (team_id, team_name, base_country, principal_name, total_points, total_wins)
SELECT constructorId, name, nationality, NULL, 0, 0
FROM temp_constructors;

DROP TABLE temp_constructors;

-- =============================================
-- 3. Import Driver Data
-- =============================================
CREATE TEMP TABLE temp_drivers (
    driverId INT,
    driverRef VARCHAR(100),
    number VARCHAR(10),
    code VARCHAR(3),
    forename VARCHAR(50),
    surname VARCHAR(50),
    dob VARCHAR(20),
    nationality VARCHAR(50),
    url VARCHAR(255)
);

COPY temp_drivers
FROM 'd:/f1-elo/archive/drivers.csv'
DELIMITER ','
CSV HEADER
QUOTE '"'
NULL '\N';

INSERT INTO Driver (driver_id, first_name, last_name, nationality, birth_date, debut_year, current_team_id)
SELECT 
    driverId, 
    forename, 
    surname, 
    nationality,
    CASE WHEN dob = '\N' THEN NULL ELSE dob::DATE END,
    NULL,
    NULL
FROM temp_drivers;

DROP TABLE temp_drivers;

-- =============================================
-- 4. Import Circuit Data
-- =============================================
CREATE TEMP TABLE temp_circuits (
    circuitId INT,
    circuitRef VARCHAR(100),
    name VARCHAR(100),
    location VARCHAR(100),
    country VARCHAR(50),
    lat VARCHAR(20),
    lng VARCHAR(20),
    alt VARCHAR(20),
    url VARCHAR(255)
);

COPY temp_circuits
FROM 'd:/f1-elo/archive/circuits.csv'
DELIMITER ','
CSV HEADER
QUOTE '"'
NULL '\N';

INSERT INTO Circuit (circuit_id, circuit_name, location, country, lap_length_km, laps)
SELECT circuitId, name, location, country, NULL, NULL
FROM temp_circuits;

DROP TABLE temp_circuits;

-- =============================================
-- 5. Import Race Data
-- =============================================
CREATE TEMP TABLE temp_races (
    raceId INT,
    year INT,
    round INT,
    circuitId INT,
    name VARCHAR(100),
    date DATE,
    time VARCHAR(20),
    url VARCHAR(255),
    fp1_date VARCHAR(20),
    fp1_time VARCHAR(20),
    fp2_date VARCHAR(20),
    fp2_time VARCHAR(20),
    fp3_date VARCHAR(20),
    fp3_time VARCHAR(20),
    quali_date VARCHAR(20),
    quali_time VARCHAR(20),
    sprint_date VARCHAR(20),
    sprint_time VARCHAR(20)
);

COPY temp_races
FROM 'd:/f1-elo/archive/races.csv'
DELIMITER ','
CSV HEADER
QUOTE '"'
NULL '\N';

INSERT INTO Race (race_id, season_year, circuit_id, race_name, race_date, round_number)
SELECT raceId, year, circuitId, name, date, round
FROM temp_races;

DROP TABLE temp_races;

-- =============================================
-- 6. Import Result Data
-- =============================================
CREATE TEMP TABLE temp_results (
    resultId INT,
    raceId INT,
    driverId INT,
    constructorId INT,
    number VARCHAR(10),
    grid INT,
    position VARCHAR(10),
    positionText VARCHAR(10),
    positionOrder INT,
    points DECIMAL(5,2),
    laps INT,
    time VARCHAR(50),
    milliseconds VARCHAR(20),
    fastestLap VARCHAR(20),
    rank VARCHAR(10),
    fastestLapTime VARCHAR(20),
    fastestLapSpeed VARCHAR(20),
    statusId INT
);

COPY temp_results
FROM 'd:/f1-elo/archive/results.csv'
DELIMITER ','
CSV HEADER
QUOTE '"'
NULL '\N';

INSERT INTO Result (result_id, race_id, driver_id, team_id, position, points, fastest_lap, laps_completed, status)
SELECT 
    tr.resultId,
    tr.raceId,
    tr.driverId,
    tr.constructorId,
    CASE WHEN tr.position = '\N' THEN NULL ELSE tr.position::INT END,
    tr.points,
    CASE WHEN tr.fastestLapTime = '\N' THEN NULL ELSE tr.fastestLapTime::TIME END,
    tr.laps,
    s.status_description
FROM temp_results tr
LEFT JOIN Status s ON tr.statusId = s.status_id;

DROP TABLE temp_results;

-- =============================================
-- Update Team Statistics
-- =============================================
UPDATE Team t
SET total_points = COALESCE((
    SELECT SUM(r.points)
    FROM Result r
    WHERE r.team_id = t.team_id
), 0),
total_wins = COALESCE((
    SELECT COUNT(*)
    FROM Result r
    WHERE r.team_id = t.team_id AND r.position = 1
), 0);

-- =============================================
-- Update Driver Debut Year
-- =============================================
UPDATE Driver d
SET debut_year = (
    SELECT MIN(ra.season_year)
    FROM Result r
    JOIN Race ra ON r.race_id = ra.race_id
    WHERE r.driver_id = d.driver_id
);

-- =============================================
-- Update Driver Current Team (most recent race)
-- =============================================
UPDATE Driver d
SET current_team_id = (
    SELECT r.team_id
    FROM Result r
    JOIN Race ra ON r.race_id = ra.race_id
    WHERE r.driver_id = d.driver_id
    ORDER BY ra.race_date DESC
    LIMIT 1
);

-- =============================================
-- Verify Data Import
-- =============================================
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

-- =============================================
-- End of Data Import
-- =============================================
