# F1 ELO Rankings

A modern web application for displaying Formula 1 driver rankings based on a teammate-comparison ELO rating system. Features a sleek F1-inspired design with historical data spanning from 1950 to 2024.

![F1 ELO Rankings](https://img.shields.io/badge/F1-ELO%20Rankings-E10600?style=for-the-badge&logo=formula1)

## ✨ Features

### 📊 Comprehensive Rankings
- **Historical Year Selection**: View rankings from any F1 season (1950-2024)
- **Era-Based Filtering**: 
  - Latest Season (2024)
  - Modern Era (2000-2024)
  - All Time (1950-2024)
- **Season-by-Season Snapshots**: See accurate historical ELO ratings at the end of each season

### 🎨 Professional Design
- **Official F1 Typography**: Uses Formula1-Display fonts (Regular, Bold, Wide)
- **Team-Colored Accents**: Dynamic borders reflecting each driver's team colors
- **Circular Flag Icons**: Country flags for driver nationalities
- **Responsive Grid Layout**: 4-column card layout optimized for modern displays
- **Clean, Modern UI**: Inspired by official F1 digital design language

### 📈 Detailed Statistics
- **Three ELO Ratings**:
  - Global ELO (combined rating)
  - Qualifying ELO (grid performance)
  - Race ELO (race-day performance)
- **Career Statistics**: Wins, podiums, and total races
- **Real-time Filtering**: Instant updates when switching years or eras

## 🏗️ Project Structure

```
f1-elo/
├── app.py                          # Flask backend with optimized queries
├── config.py                       # Database configuration
├── requirements.txt                # Python dependencies
├── import_data.py                  # Data import script
├── update_rankings.py              # ELO ranking updates
├── templates/
│   └── index.html                 # Single-page application template
├── static/
│   ├── css/
│   │   └── style.css             # F1-inspired styling with gradients
│   └── js/
│       └── app.js                # Frontend logic with flag mapping
├── elo_calculation/
│   ├── calculate_driver_elo.py   # Driver ELO with season snapshots
│   └── calculate_team_elo.py     # Team ELO calculations
├── scripts/
│   ├── start_app.bat             # Windows startup script
│   └── start_app.sh              # Linux/Mac startup script
├── DB/
│   └── f1_database.db            # SQLite database (39,493 historical snapshots)
├── archive/                       # Historical F1 data (1950-2024)
│   ├── circuits.csv
│   ├── drivers.csv
│   ├── races.csv
│   ├── results.csv
│   └── ... (other historical data)
├── data/
│   └── 2025_race_results.csv     # Latest season data
└── Sql/
    ├── create_database.sql        # Database schema
    └── import_data.sql            # Data import scripts
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- SQLite3

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Vedant9500/F1_elo_analytics.git
   cd F1_elo_analytics
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up the database** (if not already populated):
   ```bash
   python import_data.py
   python elo_calculation/calculate_driver_elo.py
   ```

4. **Run the application**:
   ```bash
   python app.py
   ```
   Or use the convenience scripts:
   - Windows: `scripts\start_app.bat`
   - Linux/Mac: `./scripts/start_app.sh`

5. **Open your browser**:
   ```
   http://localhost:5000
   ```

## 📖 How It Works

### ELO Rating System
This system ranks drivers based on **head-to-head performance against teammates**, not race results. This isolates driver skill from car performance.

- **Qualifying ELO**: Calculated from qualifying session head-to-heads
- **Race ELO**: Calculated from race finish position comparisons
- **Global ELO**: Weighted combination (30% Qualifying + 70% Race)

**Key Insight**: A driver can have a high ELO despite few wins if they consistently outperform their teammate. Example: Fernando Alonso in 2014 (0 wins, but dominated Kimi Räikkönen 16-3 in qualifying).

### Historical Data
- **39,493 season snapshots** stored in `Driver_Elo_History` table
- ELO ratings captured at the end of each season after normalization
- Accurate historical rankings for any year from 1950-2024

## 🔧 API Endpoints

### Get Driver Rankings
```http
GET /api/rankings?filter=current|century|all
```
Returns all-time rankings filtered by era.

### Get Year-Specific Rankings
```http
GET /api/rankings?year=2015
```
Returns historical rankings from end of specified season.

### Get Available Years
```http
GET /api/years
```
Returns list of all seasons with ELO data (1950-2024).

### Get Team Colors
```http
GET /api/team-colors
```
Returns team color schemes for visual styling.

### Get Last Update
```http
GET /api/last-update
```
Returns timestamp of last database update.

## 🎨 Design Features

- **F1 Official Fonts**: Formula1-Display-Regular, Bold, and Wide
- **Color Palette**:
  - Primary: F1 Red (#E10600)
  - Background: Deep gradient (#0A0A0F → #12121A)
  - Text: White (#FFFFFF) with gray hierarchy (#C0C0C0, #909090)
- **Pill-Shaped Buttons**: 50px border-radius with glowing effects
- **4-Column Grid**: Optimized card size for modern displays
- **Team Borders**: Dynamic coloring based on current team

## 📊 Database Schema

### Key Tables
- **Drivers**: Driver information and metadata
- **Driver_Elo_History**: Season-by-season ELO snapshots (39,493 records)
- **Results**: Race results from 1950-2024
- **Qualifying**: Qualifying session data
- **Constructors**: Team information

### Performance Optimizations
- CTE-based queries for aggregations
- Window functions for ranking
- Single-pass statistics calculation
- Indexed lookups on driver_id and season_year

## 🔄 Updating Data

To add new race results:

1. **Add race data** to `data/2025_race_results.csv`
2. **Import to database**:
   ```bash
   python import_data.py
   ```
3. **Recalculate ELO ratings**:
   ```bash
   python elo_calculation/calculate_driver_elo.py
   ```
4. **Refresh browser** - new rankings appear automatically

## 🛠️ Technology Stack

| Component | Technology |
|-----------|-----------|
| Backend | Flask (Python 3.8+) |
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Database | SQLite3 |
| Data Processing | Pandas, NumPy |
| Fonts | Formula1-Display (Regular, Bold, Wide) |
| Design | F1 Official Color Palette |

## 📝 License

This project uses publicly available Formula 1 data for educational and analytical purposes.

## 🙏 Credits

- **ELO System**: Teammate-based comparison methodology
- **Data Source**: Historical F1 data (1950-2024)
- **Design Inspiration**: Official Formula 1 digital platforms
- **Fonts**: Formula1-Display font family

## 👤 Author

**Vedant Patel**
- GitHub: [@Vedant9500](https://github.com/Vedant9500)

---

⭐ Star this repo if you find it useful! 🏎️💨
