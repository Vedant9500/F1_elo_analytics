# Year-Specific Rankings Feature

## Overview
The F1 ELO Rankings now supports viewing driver rankings for any specific year from 1950 to 2024.

## How It Works

### 1. Year Selector Dropdown
- Located below the filter buttons (Latest Season, Modern Era, All Time)
- Populated with all available years (75 years from 1950-2024)
- Years are listed in descending order (newest first)

### 2. Filtering Logic
When you select a specific year:
- Shows only drivers who participated in races that year
- Displays their **primary team** (team they raced most races for that year)
- Shows **year-specific statistics**: wins, podiums, and race count for that year only
- Ranks drivers by their **Global ELO** rating (accumulated career rating)

### 3. Key Information Displayed
For each driver in a specific year:
- **Name & Team**: Driver name and their primary team that year
- **Global ELO**: Their career ELO rating (not year-specific, for fair comparison)
- **Qualifying ELO & Race ELO**: Component ratings
- **Year Stats**: Wins, podiums, and total races in that specific year

## Examples

### 2015 Season
```
1. Max Verstappen (Toro Rosso) - ELO: 1794, Races: 19
2. Fernando Alonso (McLaren) - ELO: 1745, Races: 18
3. Lewis Hamilton (Mercedes) - ELO: 1732, Races: 19
4. Nico Rosberg (Mercedes) - ELO: 1696, Races: 19
5. Jenson Button (McLaren) - ELO: 1673, Races: 19
```
Total drivers: 22

### 2020 Season
```
1. Max Verstappen (Red Bull) - ELO: 1794, Races: 17
2. George Russell (Williams) - ELO: 1762, Races: 17
3. Lewis Hamilton (Mercedes) - ELO: 1732, Races: 17
4. Charles Leclerc (Ferrari) - ELO: 1699, Races: 17
5. Lando Norris (McLaren) - ELO: 1673, Races: 17
```
Total drivers: 22

## Technical Details

### API Endpoint
```
GET /api/rankings?filter=year&year=2015
```

### Response Structure
```json
{
  "success": true,
  "filter": "year",
  "year": 2015,
  "count": 22,
  "rankings": [...]
}
```

### Database Query
The query:
1. Filters drivers who raced in the specified year
2. Gets their primary team (most races with that team in that year)
3. Calculates year-specific stats (wins, podiums, races)
4. Sorts by Global ELO for fair historical comparison

### Why Use Global ELO?
Using accumulated career ELO rating allows fair comparison:
- Reflects driver's overall skill level at that point in their career
- Not skewed by single-season performance
- Enables comparison across different eras
- Shows how established drivers compared to rookies

## UI/UX Features

### Interaction
- Selecting a year deactivates filter buttons
- Clicking a filter button clears year selection
- Legend updates to show "Sorted by: [Year] Season ELO"

### Responsive Design
- Year selector adapts to screen size
- Dropdown styled to match F1 dark theme
- Custom dropdown arrow icon

## Future Enhancements
Possible improvements:
- Show ELO progression throughout the selected year
- Add season champion indicator
- Include constructor standings for that year
- Add year-to-year comparison feature
- Show driver photos/numbers from specific year
