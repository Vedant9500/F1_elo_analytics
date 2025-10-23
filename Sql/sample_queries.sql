-- =============================================
-- F1 Database - Sample Queries
-- Collection of useful SQL queries for analysis
-- =============================================

-- =============================================
-- DRIVER QUERIES
-- =============================================

-- 1. Top 10 drivers by total wins
SELECT 
    d.first_name || ' ' || d.last_name AS driver_name,
    d.nationality,
    COUNT(*) AS total_wins,
    d.debut_year
FROM Result r
JOIN Driver d ON r.driver_id = d.driver_id
WHERE r.position = 1
GROUP BY d.driver_id, d.first_name, d.last_name, d.nationality, d.debut_year
ORDER BY total_wins DESC
LIMIT 10;

-- 2. Drivers with most podium finishes
SELECT 
    d.first_name || ' ' || d.last_name AS driver_name,
    COUNT(*) AS podiums,
    SUM(CASE WHEN r.position = 1 THEN 1 ELSE 0 END) AS wins,
    SUM(CASE WHEN r.position = 2 THEN 1 ELSE 0 END) AS second_place,
    SUM(CASE WHEN r.position = 3 THEN 1 ELSE 0 END) AS third_place
FROM Result r
JOIN Driver d ON r.driver_id = d.driver_id
WHERE r.position IN (1, 2, 3)
GROUP BY d.driver_id, d.first_name, d.last_name
ORDER BY podiums DESC
LIMIT 20;

-- 3. Driver career statistics
SELECT 
    d.first_name || ' ' || d.last_name AS driver_name,
    COUNT(DISTINCT ra.race_id) AS races_entered,
    COUNT(DISTINCT ra.season_year) AS seasons,
    SUM(r.points) AS total_points,
    AVG(r.position) AS avg_position,
    COUNT(CASE WHEN r.position = 1 THEN 1 END) AS wins,
    t.team_name AS current_team
FROM Driver d
LEFT JOIN Result r ON d.driver_id = r.driver_id
LEFT JOIN Race ra ON r.race_id = ra.race_id
LEFT JOIN Team t ON d.current_team_id = t.team_id
GROUP BY d.driver_id, d.first_name, d.last_name, t.team_name
HAVING races_entered > 0
ORDER BY total_points DESC
LIMIT 20;

-- 4. Most improved drivers (comparing first and last season averages)
WITH driver_seasons AS (
    SELECT 
        d.driver_id,
        d.first_name || ' ' || d.last_name AS driver_name,
        ra.season_year,
        AVG(r.position) AS avg_position
    FROM Result r
    JOIN Driver d ON r.driver_id = d.driver_id
    JOIN Race ra ON r.race_id = ra.race_id
    WHERE r.position IS NOT NULL
    GROUP BY d.driver_id, d.first_name, d.last_name, ra.season_year
),
first_last_seasons AS (
    SELECT 
        driver_id,
        driver_name,
        MIN(season_year) AS first_season,
        MAX(season_year) AS last_season
    FROM driver_seasons
    GROUP BY driver_id, driver_name
    HAVING COUNT(DISTINCT season_year) >= 3
)
SELECT 
    fls.driver_name,
    ds1.avg_position AS first_season_avg,
    ds2.avg_position AS last_season_avg,
    ds1.avg_position - ds2.avg_position AS improvement
FROM first_last_seasons fls
JOIN driver_seasons ds1 ON fls.driver_id = ds1.driver_id AND fls.first_season = ds1.season_year
JOIN driver_seasons ds2 ON fls.driver_id = ds2.driver_id AND fls.last_season = ds2.season_year
WHERE ds1.avg_position - ds2.avg_position > 0
ORDER BY improvement DESC
LIMIT 15;

-- =============================================
-- TEAM QUERIES
-- =============================================

-- 5. Team championship standings by season
SELECT 
    ra.season_year,
    t.team_name,
    SUM(r.points) AS total_points,
    COUNT(CASE WHEN r.position = 1 THEN 1 END) AS wins,
    COUNT(CASE WHEN r.position <= 3 THEN 1 END) AS podiums
FROM Result r
JOIN Team t ON r.team_id = t.team_id
JOIN Race ra ON r.race_id = ra.race_id
WHERE ra.season_year = 2023  -- Change year as needed
GROUP BY ra.season_year, t.team_id, t.team_name
ORDER BY total_points DESC;

-- 6. Most dominant teams (all-time)
SELECT 
    t.team_name,
    t.base_country,
    COUNT(DISTINCT ra.season_year) AS seasons_competed,
    t.total_wins,
    t.total_points,
    ROUND(t.total_points / COUNT(DISTINCT r.race_id), 2) AS points_per_race,
    ROUND(100.0 * t.total_wins / COUNT(DISTINCT r.race_id), 2) AS win_percentage
FROM Team t
JOIN Result r ON t.team_id = r.team_id
JOIN Race ra ON r.race_id = ra.race_id
GROUP BY t.team_id, t.team_name, t.base_country, t.total_wins, t.total_points
ORDER BY t.total_points DESC
LIMIT 15;

-- 7. Team performance by circuit
SELECT 
    c.circuit_name,
    t.team_name,
    COUNT(*) AS races,
    COUNT(CASE WHEN r.position = 1 THEN 1 END) AS wins,
    AVG(r.position) AS avg_position,
    SUM(r.points) AS total_points
FROM Result r
JOIN Team t ON r.team_id = t.team_id
JOIN Race ra ON r.race_id = ra.race_id
JOIN Circuit c ON ra.circuit_id = c.circuit_id
WHERE c.circuit_name = 'Monaco'  -- Change circuit as needed
GROUP BY c.circuit_id, c.circuit_name, t.team_id, t.team_name
HAVING races >= 5
ORDER BY wins DESC, avg_position ASC
LIMIT 10;

-- =============================================
-- CIRCUIT QUERIES
-- =============================================

-- 8. Most competitive circuits (smallest point spread)
SELECT 
    c.circuit_name,
    c.country,
    COUNT(DISTINCT ra.race_id) AS races_held,
    AVG(r.position) AS avg_finish_position,
    ROUND(AVG(CASE WHEN r.position = 1 THEN r.points END), 2) AS avg_winner_points,
    COUNT(DISTINCT CASE WHEN r.position = 1 THEN r.driver_id END) AS different_winners
FROM Circuit c
JOIN Race ra ON c.circuit_id = ra.circuit_id
JOIN Result r ON ra.race_id = r.race_id
GROUP BY c.circuit_id, c.circuit_name, c.country
HAVING races_held >= 10
ORDER BY different_winners DESC
LIMIT 10;

-- 9. Circuit masters (drivers with most wins at each circuit)
WITH circuit_wins AS (
    SELECT 
        c.circuit_name,
        d.first_name || ' ' || d.last_name AS driver_name,
        COUNT(*) AS wins,
        ROW_NUMBER() OVER (PARTITION BY c.circuit_id ORDER BY COUNT(*) DESC) AS rank
    FROM Result r
    JOIN Driver d ON r.driver_id = d.driver_id
    JOIN Race ra ON r.race_id = ra.race_id
    JOIN Circuit c ON ra.circuit_id = c.circuit_id
    WHERE r.position = 1
    GROUP BY c.circuit_id, c.circuit_name, d.driver_id, d.first_name, d.last_name
)
SELECT circuit_name, driver_name, wins
FROM circuit_wins
WHERE rank = 1
ORDER BY wins DESC, circuit_name;

-- =============================================
-- RACE QUERIES
-- =============================================

-- 10. Most dramatic races (most DNFs/retirements)
SELECT 
    ra.race_name,
    ra.race_date,
    ra.season_year,
    c.circuit_name,
    COUNT(*) AS total_participants,
    COUNT(CASE WHEN r.status NOT IN ('Finished', '+1 Lap', '+2 Laps') THEN 1 END) AS dnfs,
    ROUND(100.0 * COUNT(CASE WHEN r.status NOT IN ('Finished', '+1 Lap', '+2 Laps') THEN 1 END) / COUNT(*), 2) AS dnf_percentage
FROM Race ra
JOIN Circuit c ON ra.circuit_id = c.circuit_id
JOIN Result r ON ra.race_id = r.race_id
GROUP BY ra.race_id, ra.race_name, ra.race_date, ra.season_year, c.circuit_name
ORDER BY dnf_percentage DESC
LIMIT 20;

-- 11. Closest finishes (smallest time gaps)
SELECT 
    ra.race_name,
    ra.race_date,
    d.first_name || ' ' || d.last_name AS winner,
    t.team_name,
    r.points
FROM Race ra
JOIN Result r ON ra.race_id = r.race_id
JOIN Driver d ON r.driver_id = d.driver_id
JOIN Team t ON r.team_id = t.team_id
WHERE r.position = 1
ORDER BY ra.race_date DESC
LIMIT 20;

-- 12. Season championship battles (points difference between top 2)
WITH season_standings AS (
    SELECT 
        ra.season_year,
        d.driver_id,
        d.first_name || ' ' || d.last_name AS driver_name,
        SUM(r.points) AS total_points,
        ROW_NUMBER() OVER (PARTITION BY ra.season_year ORDER BY SUM(r.points) DESC) AS position
    FROM Result r
    JOIN Driver d ON r.driver_id = d.driver_id
    JOIN Race ra ON r.race_id = ra.race_id
    GROUP BY ra.season_year, d.driver_id, d.first_name, d.last_name
)
SELECT 
    s1.season_year,
    s1.driver_name AS champion,
    s1.total_points AS champion_points,
    s2.driver_name AS runner_up,
    s2.total_points AS runner_up_points,
    s1.total_points - s2.total_points AS points_gap
FROM season_standings s1
JOIN season_standings s2 ON s1.season_year = s2.season_year AND s2.position = 2
WHERE s1.position = 1
ORDER BY points_gap ASC
LIMIT 15;

-- =============================================
-- ELO RATING QUERIES (after running calculate_elo.py)
-- =============================================

-- 13. Current top 20 drivers by ELO rating
SELECT 
    d.first_name || ' ' || d.last_name AS driver_name,
    t.team_name AS current_team,
    de.elo_rating,
    ra.race_date AS last_race
FROM Driver_Elo de
JOIN Driver d ON de.driver_id = d.driver_id
LEFT JOIN Team t ON d.current_team_id = t.team_id
JOIN Race ra ON de.race_id = ra.race_id
WHERE de.race_id = (SELECT MAX(race_id) FROM Race)
ORDER BY de.elo_rating DESC
LIMIT 20;

-- 14. Driver ELO progression over time
SELECT 
    ra.race_date,
    ra.race_name,
    de.elo_rating
FROM Driver_Elo de
JOIN Race ra ON de.race_id = ra.race_id
WHERE de.driver_id = (SELECT driver_id FROM Driver WHERE last_name = 'Hamilton')  -- Change driver
ORDER BY ra.race_date;

-- 15. Peak ELO ratings achieved by each driver
SELECT 
    d.first_name || ' ' || d.last_name AS driver_name,
    MAX(de.elo_rating) AS peak_elo,
    ra.race_name AS peak_race,
    ra.race_date AS peak_date
FROM Driver_Elo de
JOIN Driver d ON de.driver_id = d.driver_id
JOIN (
    SELECT driver_id, MAX(elo_rating) AS max_elo
    FROM Driver_Elo
    GROUP BY driver_id
) max_elos ON de.driver_id = max_elos.driver_id AND de.elo_rating = max_elos.max_elo
JOIN Race ra ON de.race_id = ra.race_id
GROUP BY d.driver_id, d.first_name, d.last_name, ra.race_name, ra.race_date
ORDER BY peak_elo DESC
LIMIT 20;

-- 16. Team ELO rankings (current)
SELECT 
    t.team_name,
    t.base_country,
    te.elo_rating,
    ra.race_date AS last_race
FROM Team_Elo te
JOIN Team t ON te.team_id = t.team_id
JOIN Race ra ON te.race_id = ra.race_id
WHERE te.race_id = (SELECT MAX(race_id) FROM Race)
ORDER BY te.elo_rating DESC;

-- =============================================
-- ADVANCED ANALYSIS QUERIES
-- =============================================

-- 17. Head-to-head comparison between two drivers
SELECT 
    d1.first_name || ' ' || d1.last_name AS driver1,
    d2.first_name || ' ' || d2.last_name AS driver2,
    COUNT(CASE WHEN r1.position < r2.position THEN 1 END) AS driver1_wins,
    COUNT(CASE WHEN r2.position < r1.position THEN 1 END) AS driver2_wins,
    COUNT(CASE WHEN r1.position = r2.position THEN 1 END) AS ties,
    AVG(r1.position) AS driver1_avg_position,
    AVG(r2.position) AS driver2_avg_position
FROM Result r1
JOIN Result r2 ON r1.race_id = r2.race_id
JOIN Driver d1 ON r1.driver_id = d1.driver_id
JOIN Driver d2 ON r2.driver_id = d2.driver_id
WHERE d1.last_name = 'Hamilton'  -- Change driver
  AND d2.last_name = 'Verstappen'  -- Change driver
  AND r1.position IS NOT NULL
  AND r2.position IS NOT NULL;

-- 18. Reliability analysis by team
SELECT 
    t.team_name,
    ra.season_year,
    COUNT(*) AS races,
    COUNT(CASE WHEN r.status = 'Finished' THEN 1 END) AS finished,
    ROUND(100.0 * COUNT(CASE WHEN r.status = 'Finished' THEN 1 END) / COUNT(*), 2) AS finish_rate,
    COUNT(CASE WHEN r.status LIKE '%Engine%' THEN 1 END) AS engine_failures,
    COUNT(CASE WHEN r.status IN ('Accident', 'Collision') THEN 1 END) AS crashes
FROM Result r
JOIN Team t ON r.team_id = t.team_id
JOIN Race ra ON r.race_id = ra.race_id
GROUP BY t.team_id, t.team_name, ra.season_year
HAVING races >= 10
ORDER BY ra.season_year DESC, finish_rate DESC;

-- 19. Qualifying vs Race performance (top 10 grid positions)
SELECT 
    d.first_name || ' ' || d.last_name AS driver_name,
    COUNT(*) AS races,
    AVG(CASE WHEN r.position <= 10 THEN 1 ELSE 0 END) AS top10_finish_rate,
    SUM(r.points) AS total_points
FROM Result r
JOIN Driver d ON r.driver_id = d.driver_id
GROUP BY d.driver_id, d.first_name, d.last_name
HAVING races >= 50
ORDER BY top10_finish_rate DESC
LIMIT 20;

-- 20. Career trajectory (points by season)
SELECT 
    ra.season_year,
    d.first_name || ' ' || d.last_name AS driver_name,
    SUM(r.points) AS season_points,
    COUNT(*) AS races,
    ROUND(SUM(r.points) / COUNT(*), 2) AS points_per_race
FROM Result r
JOIN Driver d ON r.driver_id = d.driver_id
JOIN Race ra ON r.race_id = ra.race_id
WHERE d.last_name = 'Hamilton'  -- Change driver
GROUP BY ra.season_year, d.driver_id, d.first_name, d.last_name
ORDER BY ra.season_year;

-- =============================================
-- End of Sample Queries
-- =============================================
