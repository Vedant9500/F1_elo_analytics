"""
F1 ELO Rankings Web Application
Flask backend to serve driver rankings based on ELO ratings
"""

from flask import Flask, render_template, jsonify, request
import sqlite3
import pandas as pd
from datetime import datetime

app = Flask(__name__)

DB_PATH = 'DB/f1_database.db'

def get_db_connection():
    """Create database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_driver_rankings(season_filter='all'):
    """
    Get driver rankings with ELO scores
    
    Args:
        season_filter: 'current' (2025), 'century' (2000-2025), 'all' (all-time)
    """
    try:
        conn = get_db_connection()
        
        # Determine year range based on filter (using season_year for your schema)
        if season_filter == 'current':
            year_condition = "AND r.season_year = 2025"
        elif season_filter == 'century':
            year_condition = "AND r.season_year >= 2000"
        else:
            year_condition = ""
        
        # First, check if Driver_Elo table exists (case-sensitive check)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND (name='driver_elo' OR name='Driver_Elo')
        """)
        
        table_result = cursor.fetchone()
        if not table_result:
            print("Warning: Driver_Elo table not found. Please run ELO calculation first.")
            conn.close()
            return []
        
        # Use the actual table name found
        elo_table = table_result[0]
        
        # Query to get latest ELO ratings for drivers
        # Modified to handle missing data more gracefully and work with your table names
        query = f"""
        SELECT 
            d.driver_id as driverId,
            d.first_name || ' ' || d.last_name as driver_name,
            d.driver_code as driver_code,
            d.nationality,
            COALESCE(de.qualifying_elo, 1500) as qualifying_elo,
            COALESCE(de.race_elo, 1500) as race_elo,
            COALESCE(de.global_elo, 1500) as global_elo,
            COALESCE(de.qualifying_experience, 0) as qualifying_races,
            COALESCE(de.race_experience, 0) as race_races,
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
                SELECT t2.team_name 
                FROM Result res2
                JOIN Team t2 ON res2.team_id = t2.team_id
                JOIN Race r2 ON res2.race_id = r2.race_id
                WHERE res2.driver_id = d.driver_id
                ORDER BY r2.race_date DESC
                LIMIT 1
            ) as team_ref,
            (
                SELECT COUNT(DISTINCT r3.race_id)
                FROM Result res3
                JOIN Race r3 ON res3.race_id = r3.race_id
                WHERE res3.driver_id = d.driver_id {year_condition.replace('r.year', 'r3.season_year') if year_condition else ''}
            ) as total_races,
            (
                SELECT COUNT(*)
                FROM Result res4
                JOIN Race r4 ON res4.race_id = r4.race_id
                WHERE res4.driver_id = d.driver_id 
                AND res4.finish_position = 1
                {year_condition.replace('r.year', 'r4.season_year') if year_condition else ''}
            ) as wins,
            (
                SELECT COUNT(*)
                FROM Result res5
                JOIN Race r5 ON res5.race_id = r5.race_id
                WHERE res5.driver_id = d.driver_id 
                AND res5.finish_position <= 3
                {year_condition.replace('r.year', 'r5.season_year') if year_condition else ''}
            ) as podiums
        FROM Driver d
        INNER JOIN {elo_table} de ON d.driver_id = de.driver_id
        WHERE de.global_elo IS NOT NULL
        ORDER BY de.global_elo DESC
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Filter out drivers with no races in the selected period
        if season_filter != 'all':
            df = df[df['total_races'] > 0]
        
        return df.to_dict('records')
        
    except Exception as e:
        print(f"Error fetching rankings: {str(e)}")
        return []

def get_team_colors():
    """Get team colors for styling"""
    return {
        'mclaren': {'primary': '#FF8700', 'secondary': '#47C7FC'},
        'redbull': {'primary': '#0600EF', 'secondary': '#FF1E00'},
        'ferrari': {'primary': '#DC0000', 'secondary': '#FFF500'},
        'mercedes': {'primary': '#00D2BE', 'secondary': '#000000'},
        'aston_martin': {'primary': '#006F62', 'secondary': '#00352F'},
        'alpine': {'primary': '#0090FF', 'secondary': '#FF87BC'},
        'williams': {'primary': '#005AFF', 'secondary': '#00A0DE'},
        'rb': {'primary': '#0600EF', 'secondary': '#1E41FF'},
        'kick_sauber': {'primary': '#00E701', 'secondary': '#000000'},
        'haas': {'primary': '#FFFFFF', 'secondary': '#B6BABD'},
    }

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/rankings')
def api_rankings():
    """API endpoint for driver rankings"""
    season_filter = request.args.get('filter', 'all')
    
    if season_filter not in ['current', 'century', 'all']:
        season_filter = 'all'
    
    rankings = get_driver_rankings(season_filter)
    return jsonify({
        'success': True,
        'filter': season_filter,
        'count': len(rankings),
        'rankings': rankings
    })

@app.route('/api/team-colors')
def api_team_colors():
    """API endpoint for team colors"""
    return jsonify(get_team_colors())

@app.route('/api/last-update')
def api_last_update():
    """Get last race update timestamp"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if Race table exists (try both cases)
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND (name='races' OR name='Race')
        """)
        
        table_result = cursor.fetchone()
        if table_result:
            race_table = table_result[0]
            # Get the latest race date from the database
            cursor.execute(f"""
                SELECT MAX(race_date) as last_race
                FROM {race_table}
                WHERE race_date <= date('now')
            """)
            result = cursor.fetchone()
            last_race_date = result['last_race'] if result else None
        else:
            # Fallback: use current date
            last_race_date = "2025-10-24"
        
        conn.close()
        
        return jsonify({
            'last_race_date': last_race_date,
            'updated_at': datetime.now().isoformat()
        })
    except Exception as e:
        print(f"Error in last_update: {str(e)}")
        return jsonify({
            'last_race_date': None,
            'updated_at': datetime.now().isoformat(),
            'error': 'Could not fetch last race date'
        })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
