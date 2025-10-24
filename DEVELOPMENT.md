# Development Guide - F1 ELO Rankings

A guide for extending and customizing the F1 ELO Rankings web application.

---

## 📂 Project Structure Explained

```
f1-elo/
├── app.py                    # Flask backend - API and routing
├── config.py                 # Configuration settings
├── requirements.txt          # Python dependencies
│
├── templates/
│   └── index.html           # Main HTML template (Jinja2)
│
├── static/
│   ├── css/
│   │   └── style.css       # All styling
│   └── js/
│       └── app.js          # Client-side logic
│
├── elo_calculation/
│   ├── calculate_driver_elo.py
│   └── calculate_team_elo.py
│
├── DB/
│   └── f1_database.db      # SQLite database
│
├── data/
│   └── 2025_race_results.csv
│
└── docs/                    # All .md files
    ├── README.md
    ├── QUICKSTART.md
    ├── ROADMAP.md
    └── ...
```

---

## 🔧 Common Development Tasks

### 1. Add a New API Endpoint

**File**: `app.py`

```python
@app.route('/api/your-new-endpoint')
def api_your_endpoint():
    """Description of what this endpoint does"""
    try:
        # Get parameters
        param = request.args.get('param', 'default')
        
        # Query database
        conn = get_db_connection()
        # ... your query ...
        conn.close()
        
        # Return JSON
        return jsonify({
            'success': True,
            'data': your_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

**Test**: `http://localhost:5000/api/your-new-endpoint`

---

### 2. Add a New Filter Option

#### Step 1: Update HTML
**File**: `templates/index.html`

```html
<button class="filter-btn" data-filter="decade">
    <span class="filter-title">Last Decade</span>
    <span class="filter-subtitle">2015-2025</span>
</button>
```

#### Step 2: Update Backend
**File**: `app.py`

```python
def get_driver_rankings(season_filter='all'):
    # Add new condition
    if season_filter == 'decade':
        year_condition = "AND r.year >= 2015"
    # ... rest of function
```

#### Step 3: Update Frontend
**File**: `static/js/app.js`

The filter will automatically work if the button has the correct `data-filter` attribute!

---

### 3. Add a New Statistic to Cards

#### Step 1: Update SQL Query
**File**: `app.py`

```python
query = f"""
SELECT 
    -- existing fields...
    (
        SELECT COUNT(*)
        FROM qualifying q
        WHERE q.driverId = d.driverId
        AND q.position = 1
    ) as pole_positions  -- NEW FIELD
FROM drivers d
-- rest of query...
"""
```

#### Step 2: Update Card Display
**File**: `static/js/app.js`

```javascript
function createDriverCard(driver, rank) {
    // ... existing code ...
    
    // Add to driver-stats div
    <div class="stat-item">
        <div class="stat-value">${driver.pole_positions || 0}</div>
        <div class="stat-label">Poles</div>
    </div>
}
```

---

### 4. Add Driver Photos

#### Step 1: Create Images Folder
```
static/images/drivers/
├── 1.jpg      # Verstappen
├── 4.jpg      # Norris
├── 16.jpg     # Leclerc
└── ...
```

#### Step 2: Update Card HTML
**File**: `static/js/app.js`

```javascript
card.innerHTML = `
    <div class="driver-rank">#${rank}</div>
    <div class="driver-photo-container">
        <img src="/static/images/drivers/${driver.driverId}.jpg" 
             alt="${driver.driver_name}"
             onerror="this.src='/static/images/default-driver.jpg'">
    </div>
    <!-- rest of card HTML -->
`;
```

#### Step 3: Add CSS Styling
**File**: `static/css/style.css`

```css
.driver-photo-container {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    overflow: hidden;
    margin: 0 auto 1rem;
}

.driver-photo-container img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}
```

---

### 5. Add Search Functionality

#### Step 1: Add Search Bar
**File**: `templates/index.html`

```html
<section class="search-section">
    <input type="text" 
           id="searchInput" 
           placeholder="Search drivers..."
           class="search-input">
</section>
```

#### Step 2: Add Search Logic
**File**: `static/js/app.js`

```javascript
function setupEventListeners() {
    // Existing code...
    
    // Add search listener
    const searchInput = document.getElementById('searchInput');
    searchInput.addEventListener('input', (e) => {
        const searchTerm = e.target.value.toLowerCase();
        const filteredRankings = allRankings.filter(driver => 
            driver.driver_name.toLowerCase().includes(searchTerm) ||
            driver.current_team.toLowerCase().includes(searchTerm) ||
            driver.nationality.toLowerCase().includes(searchTerm)
        );
        displayRankings(filteredRankings);
    });
}
```

#### Step 3: Style Search Bar
**File**: `static/css/style.css`

```css
.search-section {
    padding: 2rem;
    text-align: center;
}

.search-input {
    width: 100%;
    max-width: 600px;
    padding: 1rem;
    font-size: 1rem;
    border: 2px solid var(--border-color);
    border-radius: 8px;
    background-color: var(--background-light);
    color: var(--text-primary);
}
```

---

### 6. Add Charts (with Chart.js)

#### Step 1: Add Chart.js
**File**: `templates/index.html`

```html
<head>
    <!-- existing head content -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
```

#### Step 2: Add Canvas Element
```html
<section class="charts-section">
    <canvas id="eloDistributionChart"></canvas>
</section>
```

#### Step 3: Create Chart
**File**: `static/js/app.js`

```javascript
function createEloDistributionChart(rankings) {
    const ctx = document.getElementById('eloDistributionChart');
    
    const eloValues = rankings.map(d => d.global_elo);
    const driverNames = rankings.slice(0, 10).map(d => d.driver_name);
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: driverNames,
            datasets: [{
                label: 'Global ELO',
                data: eloValues.slice(0, 10),
                backgroundColor: '#e10600'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Top 10 Drivers by ELO'
                }
            }
        }
    });
}
```

---

### 7. Add Dark/Light Mode Toggle

#### Step 1: Add Toggle Button
**File**: `templates/index.html`

```html
<header>
    <div class="header-content">
        <!-- existing content -->
        <button id="themeToggle" class="theme-toggle">🌙</button>
    </div>
</header>
```

#### Step 2: Add Toggle Logic
**File**: `static/js/app.js`

```javascript
// Add to setupEventListeners()
const themeToggle = document.getElementById('themeToggle');
themeToggle.addEventListener('click', () => {
    document.body.classList.toggle('light-mode');
    themeToggle.textContent = 
        document.body.classList.contains('light-mode') ? '☀️' : '🌙';
    localStorage.setItem('theme', 
        document.body.classList.contains('light-mode') ? 'light' : 'dark');
});

// Load saved theme
if (localStorage.getItem('theme') === 'light') {
    document.body.classList.add('light-mode');
    themeToggle.textContent = '☀️';
}
```

#### Step 3: Add Light Mode Styles
**File**: `static/css/style.css`

```css
body.light-mode {
    --background-dark: #ffffff;
    --background-light: #f5f5f5;
    --text-primary: #000000;
    --text-secondary: #666666;
    --border-color: #cccccc;
}
```

---

## 🗄️ Database Queries

### Common Query Patterns

#### Get Top N Drivers
```sql
SELECT * FROM driver_elo 
ORDER BY global_elo DESC 
LIMIT 10;
```

#### Get Drivers by Team
```sql
SELECT d.*, c.name as team
FROM drivers d
JOIN results r ON d.driverId = r.driverId
JOIN constructors c ON r.constructorId = c.constructorId
WHERE c.name = 'McLaren'
GROUP BY d.driverId;
```

#### Get Historical ELO
```sql
SELECT de.*, r.date
FROM driver_elo_history de
JOIN races r ON de.raceId = r.raceId
WHERE de.driverId = 1
ORDER BY r.date;
```

#### Get Head-to-Head
```sql
SELECT 
    d1.surname as driver1,
    d2.surname as driver2,
    COUNT(*) as races_together
FROM results r1
JOIN results r2 ON r1.raceId = r2.raceId 
    AND r1.constructorId = r2.constructorId
    AND r1.driverId < r2.driverId
JOIN drivers d1 ON r1.driverId = d1.driverId
JOIN drivers d2 ON r2.driverId = d2.driverId
GROUP BY r1.driverId, r2.driverId;
```

---

## 🎨 CSS Customization

### Changing Colors

#### Global Color Variables
```css
:root {
    --primary-color: #e10600;
    --secondary-color: #15151e;
    /* Change these to theme the entire site */
}
```

#### Team-Specific Styling
```css
.driver-card[data-team="McLaren"] {
    --team-color: #FF8700;
}
```

### Adding Animations

#### Fade In on Load
```css
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

.driver-card {
    animation: fadeIn 0.5s ease-out;
}
```

#### Pulsing ELO Badge
```css
@keyframes pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.05); }
}

.stat-value {
    animation: pulse 2s infinite;
}
```

---

## 🧪 Testing

### Test API Endpoints

Using Python:
```python
import requests

response = requests.get('http://localhost:5000/api/rankings?filter=current')
data = response.json()
print(f"Found {data['count']} drivers")
```

Using curl:
```bash
curl http://localhost:5000/api/rankings?filter=current
```

### Test Database Queries

```python
import sqlite3

conn = sqlite3.connect('DB/f1_database.db')
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM driver_elo")
print(f"Total drivers with ELO: {cursor.fetchone()[0]}")
conn.close()
```

---

## 🐛 Debugging Tips

### Backend Issues

1. **Check Flask logs** in terminal
2. **Add print statements**:
   ```python
   print(f"Debug: {variable}")
   ```
3. **Check SQL queries**:
   ```python
   print(query)  # Print before executing
   ```

### Frontend Issues

1. **Open browser DevTools** (F12)
2. **Check Console** for JavaScript errors
3. **Check Network tab** for API responses
4. **Add console.log**:
   ```javascript
   console.log('Debug:', variable);
   ```

### Database Issues

1. **Use DB Browser for SQLite** to inspect database
2. **Test queries directly**:
   ```bash
   sqlite3 DB/f1_database.db "SELECT * FROM driver_elo LIMIT 5;"
   ```

---

## 📊 Performance Optimization

### Backend

```python
# Add caching
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@app.route('/api/rankings')
@cache.cached(timeout=300)  # Cache for 5 minutes
def api_rankings():
    # ...
```

### Database

```sql
-- Add indexes
CREATE INDEX idx_driver_elo ON driver_elo(global_elo DESC);
CREATE INDEX idx_race_year ON races(year);
```

### Frontend

```javascript
// Lazy load images
<img loading="lazy" src="...">

// Debounce search
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func(...args), wait);
    };
}
```

---

## 🚀 Deployment Checklist

- [ ] Set `DEBUG = False` in config.py
- [ ] Add error handling for all routes
- [ ] Optimize database queries
- [ ] Add rate limiting to API
- [ ] Minify CSS and JavaScript
- [ ] Set up proper logging
- [ ] Add security headers
- [ ] Configure CORS if needed
- [ ] Set up backup system
- [ ] Test on different browsers

---

## 📚 Useful Resources

- **Flask Docs**: https://flask.palletsprojects.com/
- **SQLite Docs**: https://www.sqlite.org/docs.html
- **Chart.js**: https://www.chartjs.org/
- **CSS Grid**: https://css-tricks.com/snippets/css/complete-guide-grid/
- **Fetch API**: https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API

---

## 💡 Pro Tips

1. **Use VS Code Extensions**:
   - Python
   - SQLite
   - Live Server
   - Prettier

2. **Git Workflow**:
   ```bash
   git checkout -b feature-name
   # Make changes
   git add .
   git commit -m "Add: description"
   git push origin feature-name
   ```

3. **Keep It Simple**: Start with basic features, then enhance

4. **Test Frequently**: Run the app after each change

5. **Document Changes**: Update README when adding features

---

Happy coding! 🏎️💨
