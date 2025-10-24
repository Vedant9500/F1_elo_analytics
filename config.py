"""
Configuration file for F1 ELO Web Application
Modify these settings to customize the app
"""

# Flask Configuration
DEBUG = True
HOST = '0.0.0.0'
PORT = 5000

# Database Configuration
DB_PATH = 'DB/f1_database.db'

# Application Settings
APP_TITLE = "F1 ELO Rankings"
CURRENT_SEASON = 2025

# ELO Settings
INITIAL_ELO = 1500
ELO_WEIGHTS = {
    'qualifying': 0.3,
    'race': 0.7
}

# Season Filter Settings
CENTURY_START_YEAR = 2000
ALL_TIME_START_YEAR = 1950

# Team Colors (can be customized)
TEAM_COLORS = {
    'McLaren': {'primary': '#FF8700', 'secondary': '#47C7FC'},
    'Red Bull': {'primary': '#0600EF', 'secondary': '#FF1E00'},
    'Ferrari': {'primary': '#DC0000', 'secondary': '#FFF500'},
    'Mercedes': {'primary': '#00D2BE', 'secondary': '#000000'},
    'Aston Martin': {'primary': '#006F62', 'secondary': '#00352F'},
    'Alpine': {'primary': '#0090FF', 'secondary': '#FF87BC'},
    'Williams': {'primary': '#005AFF', 'secondary': '#00A0DE'},
    'RB': {'primary': '#0600EF', 'secondary': '#1E41FF'},
    'Kick Sauber': {'primary': '#00E701', 'secondary': '#000000'},
    'Haas': {'primary': '#FFFFFF', 'secondary': '#B6BABD'},
}

# UI Theme Settings
THEME = {
    'primary_color': '#e10600',
    'background_dark': '#15151e',
    'background_light': '#1f1f2e',
    'text_primary': '#ffffff',
    'text_secondary': '#949498',
    'border_color': '#38383f',
}

# Feature Flags
FEATURES = {
    'show_qualifying_elo': True,
    'show_race_elo': True,
    'show_wins': True,
    'show_podiums': True,
    'show_total_races': True,
    'show_nationality': True,
}

# Pagination (for future use)
DRIVERS_PER_PAGE = 50

# Cache Settings (for future use)
CACHE_TIMEOUT = 300  # seconds

# API Settings
API_VERSION = 'v1'
API_RATE_LIMIT = 100  # requests per minute
