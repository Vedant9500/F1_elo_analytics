DROP TABLE IF EXISTS Driver_Elo;
DROP TABLE IF EXISTS Team_Elo;
DROP TABLE IF EXISTS Result;
DROP TABLE IF EXISTS Race;
DROP TABLE IF EXISTS Circuit;
DROP TABLE IF EXISTS Driver;
DROP TABLE IF EXISTS Team;
DROP TABLE IF EXISTS Status;

CREATE TABLE Status (
    status_id INT PRIMARY KEY,
    status_description VARCHAR(100) NOT NULL
);

CREATE TABLE Team (
    team_id INT PRIMARY KEY,
    team_name VARCHAR(100) NOT NULL,
    base_country VARCHAR(50) NOT NULL,
    principal_name VARCHAR(100),
    total_points DECIMAL(10, 2) DEFAULT 0.00,
    total_wins INT DEFAULT 0,
    CONSTRAINT uk_team_name UNIQUE (team_name)
);

CREATE TABLE Driver (
    driver_id INT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    nationality VARCHAR(50) NOT NULL,
    birth_date DATE,
    debut_year INT,
    current_team_id INT,
    CONSTRAINT fk_driver_team FOREIGN KEY (current_team_id) 
        REFERENCES Team(team_id) ON DELETE SET NULL,
    CONSTRAINT uk_driver_name UNIQUE (first_name, last_name, birth_date)
);

CREATE TABLE Circuit (
    circuit_id INT PRIMARY KEY,
    circuit_name VARCHAR(100) NOT NULL,
    location VARCHAR(100) NOT NULL,
    country VARCHAR(50) NOT NULL,
    lap_length_km DECIMAL(6, 3),
    laps INT,
    CONSTRAINT uk_circuit_name UNIQUE (circuit_name)
);

CREATE TABLE Race (
    race_id INT PRIMARY KEY,
    season_year INT NOT NULL,
    circuit_id INT NOT NULL,
    race_name VARCHAR(100) NOT NULL,
    race_date DATE NOT NULL,
    round_number INT NOT NULL,
    CONSTRAINT fk_race_circuit FOREIGN KEY (circuit_id) 
        REFERENCES Circuit(circuit_id) ON DELETE RESTRICT,
    CONSTRAINT uk_race_season_round UNIQUE (season_year, round_number)
);

CREATE TABLE Result (
    result_id INT PRIMARY KEY,
    race_id INT NOT NULL,
    driver_id INT NOT NULL,
    team_id INT NOT NULL,
    position INT,
    points DECIMAL(5, 2) DEFAULT 0.00,
    fastest_lap TIME,
    laps_completed INT DEFAULT 0,
    status VARCHAR(50),
    session_type VARCHAR(20) DEFAULT 'race',
    CONSTRAINT fk_result_race FOREIGN KEY (race_id) 
        REFERENCES Race(race_id) ON DELETE CASCADE,
    CONSTRAINT fk_result_driver FOREIGN KEY (driver_id) 
        REFERENCES Driver(driver_id) ON DELETE CASCADE,
    CONSTRAINT fk_result_team FOREIGN KEY (team_id) 
        REFERENCES Team(team_id) ON DELETE CASCADE,
    CONSTRAINT uk_result_race_driver UNIQUE (race_id, driver_id)
);

CREATE TABLE Additional_Results (
    additional_result_id INT PRIMARY KEY AUTO_INCREMENT,
    original_result_id INT NOT NULL,
    race_id INT NOT NULL,
    driver_id INT NOT NULL,
    team_id INT NOT NULL,
    position INT,
    points DECIMAL(5, 2) DEFAULT 0.00,
    fastest_lap TIME,
    laps_completed INT DEFAULT 0,
    status VARCHAR(50),
    session_type VARCHAR(20) DEFAULT 'alternative',
    entry_sequence INT DEFAULT 1,
    notes TEXT,
    CONSTRAINT fk_additional_race FOREIGN KEY (race_id) 
        REFERENCES Race(race_id) ON DELETE CASCADE,
    CONSTRAINT fk_additional_driver FOREIGN KEY (driver_id) 
        REFERENCES Driver(driver_id) ON DELETE CASCADE,
    CONSTRAINT fk_additional_team FOREIGN KEY (team_id) 
        REFERENCES Team(team_id) ON DELETE CASCADE,
    CONSTRAINT fk_additional_original FOREIGN KEY (original_result_id)
        REFERENCES Result(result_id) ON DELETE CASCADE
);

CREATE TABLE Driver_Elo (
    elo_id INT PRIMARY KEY AUTO_INCREMENT,
    driver_id INT NOT NULL,
    race_id INT NOT NULL,
    elo_rating DECIMAL(10, 2) NOT NULL DEFAULT 1500.00,
    updated_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_driver_elo_driver FOREIGN KEY (driver_id) 
        REFERENCES Driver(driver_id) ON DELETE CASCADE,
    CONSTRAINT fk_driver_elo_race FOREIGN KEY (race_id) 
        REFERENCES Race(race_id) ON DELETE CASCADE,
    CONSTRAINT uk_driver_elo_race UNIQUE (driver_id, race_id)
);

CREATE TABLE Team_Elo (
    elo_id INT PRIMARY KEY AUTO_INCREMENT,
    team_id INT NOT NULL,
    race_id INT NOT NULL,
    elo_rating DECIMAL(10, 2) NOT NULL DEFAULT 1500.00,
    updated_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_team_elo_team FOREIGN KEY (team_id) 
        REFERENCES Team(team_id) ON DELETE CASCADE,
    CONSTRAINT fk_team_elo_race FOREIGN KEY (race_id) 
        REFERENCES Race(race_id) ON DELETE CASCADE,
    CONSTRAINT uk_team_elo_race UNIQUE (team_id, race_id)
);

CREATE INDEX idx_driver_nationality ON Driver(nationality);
CREATE INDEX idx_driver_current_team ON Driver(current_team_id);
CREATE INDEX idx_race_season ON Race(season_year);
CREATE INDEX idx_race_circuit ON Race(circuit_id);
CREATE INDEX idx_race_date ON Race(race_date);
CREATE INDEX idx_result_race ON Result(race_id);
CREATE INDEX idx_result_driver ON Result(driver_id);
CREATE INDEX idx_result_team ON Result(team_id);
CREATE INDEX idx_result_position ON Result(position);
CREATE INDEX idx_additional_race ON Additional_Results(race_id);
CREATE INDEX idx_additional_driver ON Additional_Results(driver_id);
CREATE INDEX idx_additional_team ON Additional_Results(team_id);
CREATE INDEX idx_additional_original ON Additional_Results(original_result_id);
CREATE INDEX idx_driver_elo_driver ON Driver_Elo(driver_id);
CREATE INDEX idx_driver_elo_race ON Driver_Elo(race_id);
CREATE INDEX idx_team_elo_team ON Team_Elo(team_id);
CREATE INDEX idx_team_elo_race ON Team_Elo(race_id);

