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
        season_filter: 'current' (2024), 'century' (2000-2024), 'all' (all-time)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if Driver_Elo table exists (case-sensitive check)
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
        
        # Determine which ELO to use and year filter based on era
        if season_filter == 'current':
            # Latest season - use era_adjusted_elo, filter by 2024 participation
            elo_column = "de.era_adjusted_elo"
            year_filter = """
                AND EXISTS (
                    SELECT 1 FROM Result r 
                    JOIN Race ra ON r.race_id = ra.race_id 
                    WHERE r.driver_id = d.driver_id AND ra.season_year = 2024
                )
            """
            order_by = "de.era_adjusted_elo DESC"
            
        elif season_filter == 'century':
            # Modern era (2000+) - use era_adjusted_elo, filter by debut year
            elo_column = "de.era_adjusted_elo"
            year_filter = "AND de.debut_year >= 2000"
            order_by = "de.era_adjusted_elo DESC"
            
        else:
            # All time - use raw global_elo for fair historical comparison
            elo_column = "de.global_elo"
            year_filter = ""
            order_by = "de.global_elo DESC"
        
        # Query to get driver rankings with stats
        query = f"""
        SELECT 
            d.driver_id as driverId,
            d.first_name || ' ' || d.last_name as driver_name,
            SUBSTR(UPPER(d.last_name), 1, 3) as driver_code,
            d.nationality,
            de.qualifying_elo,
            de.race_elo,
            de.global_elo,
            de.era_adjusted_elo,
            {elo_column} as display_elo,
            de.qualifying_races,
            de.race_races,
            de.debut_year,
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
                WHERE res3.driver_id = d.driver_id
            ) as total_races,
            (
                SELECT COUNT(*)
                FROM Result res4
                JOIN Race r4 ON res4.race_id = r4.race_id
                WHERE res4.driver_id = d.driver_id 
                AND res4.position = 1
            ) as wins,
            (
                SELECT COUNT(*)
                FROM Result res5
                JOIN Race r5 ON res5.race_id = r5.race_id
                WHERE res5.driver_id = d.driver_id 
                AND res5.position <= 3
                AND res5.position > 0
            ) as podiums
        FROM Driver d
        INNER JOIN {elo_table} de ON d.driver_id = de.driver_id
        WHERE de.global_elo IS NOT NULL
        {year_filter}
        ORDER BY {order_by}
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Rename display_elo to global_elo for frontend consistency
        if 'display_elo' in df.columns:
            df['global_elo'] = df['display_elo']
        
        return df.to_dict('records')
        
    except Exception as e:
        print(f"Error fetching rankings: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def get_driver_rankings_by_year(year):
    """
    Get driver rankings for a specific year using historical ELO snapshots
    Shows drivers who raced in that year with their ELO at the end of that season
    
    Args:
        year: Specific year to filter by
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if Driver_Elo_History table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='Driver_Elo_History'
        """)
        
        if not cursor.fetchone():
            print("Warning: Driver_Elo_History table not found.")
            conn.close()
            return []
        
        # Query to get drivers with their ELO at the end of the specified year
        # Only include drivers who actually raced in that year
        query = """
        SELECT 
            d.driver_id as driverId,
            d.first_name || ' ' || d.last_name as driver_name,
            SUBSTR(UPPER(d.last_name), 1, 3) as driver_code,
            d.nationality,
            deh.qualifying_elo,
            deh.race_elo,
            deh.global_elo,
            (
                SELECT t2.team_name 
                FROM Result res2
                JOIN Team t2 ON res2.team_id = t2.team_id
                JOIN Race r2 ON res2.race_id = r2.race_id
                WHERE res2.driver_id = d.driver_id AND r2.season_year = ?
                GROUP BY t2.team_name
                ORDER BY COUNT(*) DESC
                LIMIT 1
            ) as current_team,
            (
                SELECT COUNT(DISTINCT r3.race_id)
                FROM Result res3
                JOIN Race r3 ON res3.race_id = r3.race_id
                WHERE res3.driver_id = d.driver_id AND r3.season_year = ?
            ) as total_races,
            (
                SELECT COUNT(*)
                FROM Result res4
                JOIN Race r4 ON res4.race_id = r4.race_id
                WHERE res4.driver_id = d.driver_id 
                AND res4.position = 1
                AND r4.season_year = ?
            ) as wins,
            (
                SELECT COUNT(*)
                FROM Result res5
                JOIN Race r5 ON res5.race_id = r5.race_id
                WHERE res5.driver_id = d.driver_id 
                AND res5.position <= 3
                AND res5.position > 0
                AND r5.season_year = ?
            ) as podiums
        FROM Driver d
        INNER JOIN Driver_Elo_History deh ON d.driver_id = deh.driver_id
        WHERE deh.season_year = ?
        AND EXISTS (
            SELECT 1 FROM Result r 
            JOIN Race ra ON r.race_id = ra.race_id 
            WHERE r.driver_id = d.driver_id AND ra.season_year = ?
        )
        ORDER BY deh.global_elo DESC
        """
        
        df = pd.read_sql_query(query, conn, params=(year, year, year, year, year, year))
        conn.close()
        
        return df.to_dict('records')
        
    except Exception as e:
        print(f"Error fetching rankings for year {year}: {str(e)}")
        import traceback
        traceback.print_exc()
        return []
        return df.to_dict('records')
        
    except Exception as e:
        print(f"Error fetching rankings: {str(e)}")
        import traceback
        traceback.print_exc()
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
    year = request.args.get('year', None)
    
    # Handle specific year filter
    if season_filter == 'year' and year:
        rankings = get_driver_rankings_by_year(int(year))
        return jsonify({
            'success': True,
            'filter': 'year',
            'year': int(year),
            'count': len(rankings),
            'rankings': rankings
        })
    
    # Handle regular filters
    if season_filter not in ['current', 'century', 'all']:
        season_filter = 'all'
    
    rankings = get_driver_rankings(season_filter)
    return jsonify({
        'success': True,
        'filter': season_filter,
        'count': len(rankings),
        'rankings': rankings
    })

@app.route('/api/years')
def api_years():
    """API endpoint to get available years"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT DISTINCT season_year FROM Race ORDER BY season_year DESC')
        years = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'years': years
        })
    except Exception as e:
        print(f"Error fetching years: {str(e)}")
        return jsonify({
            'success': False,
            'years': []
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
