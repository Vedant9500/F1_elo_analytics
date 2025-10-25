// F1 ELO Rankings - Main JavaScript

// State management
let currentFilter = 'century'; // Default to Modern Era which has data
let allRankings = [];
let teamColors = {};

// Team color mappings
const teamColorMap = {
    'McLaren': { primary: '#FF8700', secondary: '#47C7FC' },
    'Red Bull': { primary: '#0600EF', secondary: '#FF1E00' },
    'Ferrari': { primary: '#DC0000', secondary: '#FFF500' },
    'Mercedes': { primary: '#00D2BE', secondary: '#000000' },
    'Aston Martin': { primary: '#006F62', secondary: '#00352F' },
    'Alpine': { primary: '#0090FF', secondary: '#FF87BC' },
    'Williams': { primary: '#005AFF', secondary: '#00A0DE' },
    'RB': { primary: '#0600EF', secondary: '#1E41FF' },
    'Kick Sauber': { primary: '#00E701', secondary: '#000000' },
    'Haas': { primary: '#FFFFFF', secondary: '#B6BABD' },
};

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    loadAvailableYears();
    loadRankings('century'); // Start with Modern Era
    loadLastUpdate();
});

// Setup event listeners
function setupEventListeners() {
    const filterButtons = document.querySelectorAll('.filter-btn');
    const yearSelect = document.getElementById('yearSelect');
    
    filterButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Clear year selection
            yearSelect.value = '';
            
            // Update active state
            filterButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            // Get filter value and load rankings
            const filter = button.getAttribute('data-filter');
            currentFilter = filter;
            loadRankings(filter);
        });
    });
    
    // Year selector handler
    yearSelect.addEventListener('change', (e) => {
        const selectedYear = e.target.value;
        if (selectedYear) {
            // Deactivate filter buttons
            filterButtons.forEach(btn => btn.classList.remove('active'));
            
            // Load rankings for specific year
            loadRankings('year', selectedYear);
        }
    });
}

// Load available years
async function loadAvailableYears() {
    try {
        const response = await fetch('/api/years');
        const data = await response.json();
        
        if (data.success) {
            const yearSelect = document.getElementById('yearSelect');
            
            // Populate dropdown with years (newest first)
            data.years.sort((a, b) => b - a).forEach(year => {
                const option = document.createElement('option');
                option.value = year;
                option.textContent = year;
                yearSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading years:', error);
    }
}

// Load rankings from API
async function loadRankings(filter = 'current', year = null) {
    const driverGrid = document.getElementById('driverGrid');
    driverGrid.innerHTML = '<div class="loading">Loading rankings...</div>';
    
    // Determine API endpoint
    let apiUrl = `/api/rankings?filter=${filter}`;
    if (year) {
        apiUrl = `/api/rankings?filter=year&year=${year}`;
    }
    
    // Update legend based on filter
    updateLegend(filter, year);
    
    try {
        const response = await fetch(apiUrl);
        const data = await response.json();
        
        if (data.success) {
            allRankings = data.rankings;
            displayRankings(allRankings);
        } else {
            driverGrid.innerHTML = '<div class="loading">Error loading rankings</div>';
        }
    } catch (error) {
        console.error('Error fetching rankings:', error);
        driverGrid.innerHTML = '<div class="loading">Error loading rankings. Please try again.</div>';
    }
}

// Update legend based on current filter
function updateLegend(filter, year = null) {
    const legendNote = document.querySelector('.legend-note');
    if (legendNote) {
        if (year) {
            legendNote.textContent = `Sorted by: ${year} Season ELO`;
        } else if (filter === 'all') {
            legendNote.textContent = 'Sorted by: Global ELO Rating (Raw)';
        } else {
            legendNote.textContent = 'Sorted by: Era-Adjusted ELO Rating';
        }
    }
}

// Display rankings
function displayRankings(rankings) {
    const driverGrid = document.getElementById('driverGrid');
    
    if (!rankings || rankings.length === 0) {
        driverGrid.innerHTML = '<div class="loading">No rankings available for this filter</div>';
        return;
    }
    
    driverGrid.innerHTML = '';
    
    rankings.forEach((driver, index) => {
        const card = createDriverCard(driver, index + 1);
        driverGrid.appendChild(card);
    });
}

// Create driver card element
function createDriverCard(driver, rank) {
    const card = document.createElement('div');
    card.className = 'driver-card';
    
    // Get team color
    const teamColor = getTeamColor(driver.current_team);
    const teamColorRgb = hexToRgba(teamColor, 0.4);
    card.style.setProperty('--team-color', teamColor);
    card.style.setProperty('--team-color-rgb', teamColorRgb);
    
    // Format ELO values
    const globalElo = Math.round(driver.global_elo || 1500);
    const qualifyingElo = Math.round(driver.qualifying_elo || 1500);
    const raceElo = Math.round(driver.race_elo || 1500);
    
    // Get country flag emoji
    const flagEmoji = getCountryFlag(driver.nationality);
    
    // Split name into first name(s) and last name
    const nameParts = driver.driver_name.trim().split(' ');
    const lastName = nameParts[nameParts.length - 1];
    const firstName = nameParts.slice(0, -1).join(' ');
    
    card.innerHTML = `
        <div class="driver-rank">#${rank}</div>
        <div class="driver-info">
            <div class="driver-flag">${flagEmoji}</div>
            <div class="driver-details">
                <div class="driver-name">
                    <div class="driver-firstname">${firstName}</div>
                    <div class="driver-lastname">${lastName}</div>
                </div>
                <div class="driver-team">${driver.current_team || 'Unknown Team'}</div>
                <div class="driver-nationality">${driver.nationality || 'N/A'}</div>
            </div>
        </div>
        
        <div class="driver-elo-stats">
            <div class="elo-stat">
                <div class="elo-stat-value">${globalElo}</div>
                <div class="elo-stat-label">Global ELO</div>
            </div>
            <div class="elo-stat">
                <div class="elo-stat-value">${qualifyingElo}</div>
                <div class="elo-stat-label">Qual ELO</div>
            </div>
            <div class="elo-stat">
                <div class="elo-stat-value">${raceElo}</div>
                <div class="elo-stat-label">Race ELO</div>
            </div>
        </div>
        
        <div class="driver-stats">
            <div class="stat-item">
                <div class="stat-value">${driver.wins || 0}</div>
                <div class="stat-label">Wins</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">${driver.podiums || 0}</div>
                <div class="stat-label">Podiums</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">${driver.total_races || 0}</div>
                <div class="stat-label">Races</div>
            </div>
        </div>
    `;
    
    return card;
}

// Convert hex color to rgba
function hexToRgba(hex, alpha = 1) {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// Get country flag emoji
function getCountryFlag(nationality) {
    const flagMap = {
        'British': '🇬🇧',
        'German': '🇩🇪',
        'Spanish': '🇪🇸',
        'Dutch': '🇳🇱',
        'Australian': '🇦🇺',
        'Canadian': '🇨🇦',
        'French': '🇫🇷',
        'Italian': '🇮🇹',
        'Finnish': '🇫🇮',
        'Mexican': '🇲🇽',
        'Thai': '🇹🇭',
        'Japanese': '🇯🇵',
        'Chinese': '🇨🇳',
        'Danish': '🇩🇰',
        'Monegasque': '🇲🇨',
        'Brazilian': '🇧🇷',
        'Argentine': '🇦🇷',
        'American': '🇺🇸',
        'Belgian': '🇧🇪',
        'Polish': '🇵🇱',
        'Russian': '🇷🇺',
        'Venezuelan': '🇻🇪',
        'Colombian': '🇨🇴',
        'Austrian': '🇦🇹',
        'Swedish': '🇸🇪',
        'Swiss': '🇨🇭',
        'New Zealander': '🇳🇿',
        'South African': '🇿🇦',
        'Indian': '🇮🇳',
        'Portuguese': '🇵🇹',
        'Irish': '🇮🇪',
        'Argentinian': '🇦🇷',
        'Rhodesian': '🇿🇼',
        'East German': '🇩🇪',
        'Chilean': '🇨🇱',
        'Hungarian': '🇭🇺',
        'Czech': '🇨🇿'
    };
    
    return flagMap[nationality] || '🏁';
}

// Get team color
function getTeamColor(teamName) {
    if (!teamName) return '#e10600';
    
    // Try exact match first
    if (teamColorMap[teamName]) {
        return teamColorMap[teamName].primary;
    }
    
    // Try partial match
    for (const [team, colors] of Object.entries(teamColorMap)) {
        if (teamName.includes(team) || team.includes(teamName)) {
            return colors.primary;
        }
    }
    
    return '#e10600'; // Default F1 red
}

// Load last update timestamp
async function loadLastUpdate() {
    try {
        const response = await fetch('/api/last-update');
        const data = await response.json();
        
        const lastUpdateElement = document.getElementById('lastUpdate');
        
        if (data.last_race_date) {
            const raceDate = new Date(data.last_race_date);
            lastUpdateElement.textContent = `Last updated: ${raceDate.toLocaleDateString('en-US', { 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
            })}`;
        } else {
            lastUpdateElement.textContent = 'Last updated: N/A';
        }
    } catch (error) {
        console.error('Error fetching last update:', error);
    }
}

// Utility function to format numbers
function formatNumber(num) {
    if (!num) return '0';
    return num.toLocaleString();
}

// Export for potential future use
window.F1EloApp = {
    loadRankings,
    currentFilter,
    allRankings
};
