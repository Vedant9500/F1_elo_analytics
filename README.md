# F1 ELO Rankings Web Application

A web application for displaying Formula 1 driver rankings based on ELO rating system.

## Features

- **Dynamic Rankings**: View driver rankings based on ELO ratings
- **Multiple Time Periods**: 
  - Current Season (2025)
  - Current Century (2000-2025)
  - All Time (1950-2025)
- **Real-time Updates**: Automatically updates after each race
- **Team Colors**: Visual representation with team-specific colors
- **Detailed Stats**: 
  - Global ELO rating
  - Qualifying ELO
  - Race ELO
  - Wins, Podiums, Total Races

## Project Structure

```
f1-elo/
├── app.py                      # Flask backend application
├── templates/
│   └── index.html             # Main HTML template
├── static/
│   ├── css/
│   │   └── style.css         # Stylesheet
│   └── js/
│       └── app.js            # Frontend JavaScript
├── elo_calculation/
│   ├── calculate_driver_elo.py
│   └── calculate_team_elo.py
├── DB/
│   └── f1_database.db        # SQLite database
├── data/
│   └── 2025_race_results.csv
└── requirements.txt
```

## Setup and Installation

### Prerequisites
- Python 3.8+
- SQLite database with F1 data and ELO calculations

### Installation Steps

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Ensure database is set up**:
   - Make sure `DB/f1_database.db` exists
   - Run ELO calculations if not already done:
     ```bash
     python elo_calculation/calculate_driver_elo.py
     ```

3. **Run the web application**:
   ```bash
   python app.py
   ```

4. **Open browser**:
   - Navigate to `http://localhost:5000`

## Usage

### Viewing Rankings
- Click on filter buttons to switch between:
  - **Current Season**: Shows only 2025 drivers
  - **Current Century**: Shows drivers from 2000 onwards
  - **All Time**: Shows all drivers from F1 history

### Understanding ELO Ratings
- **Global ELO**: Combined rating (30% Qualifying, 70% Race)
- **Qualifying ELO**: Based on qualifying performance vs teammate
- **Race ELO**: Based on race performance vs teammate

### API Endpoints

#### Get Rankings
```
GET /api/rankings?filter=current|century|all
```
Returns driver rankings filtered by time period.

#### Get Team Colors
```
GET /api/team-colors
```
Returns team color schemes.

#### Get Last Update
```
GET /api/last-update
```
Returns timestamp of last database update.

## Future Enhancements

- [ ] Add driver detail pages with historical performance
- [ ] Add race-by-race ELO progression graphs
- [ ] Add head-to-head comparison tool
- [ ] Add team rankings page
- [ ] Implement custom theme/color scheme selector
- [ ] Add search and filter functionality
- [ ] Add mobile-responsive improvements
- [ ] Add data export functionality
- [ ] Add historical ELO charts
- [ ] Add season-by-season breakdown

## Data Updates

To update with new race data:

1. Add new race results to `data/2025_race_results.csv`
2. Run the ELO calculation:
   ```bash
   python elo_calculation/calculate_driver_elo.py
   ```
3. Refresh the web page - rankings will update automatically

## Technology Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Database**: SQLite
- **Data Processing**: Pandas, NumPy

## License

This project uses publicly available F1 data for educational purposes.

## Credits

Based on the teammate-based ELO rating system for Formula 1 drivers.
