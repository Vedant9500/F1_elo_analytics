// F1 ELO Rankings - Main JavaScript

// State management
let currentFilter = 'current';
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
    loadRankings('current');
    loadLastUpdate();
});

// Setup event listeners
function setupEventListeners() {
    const filterButtons = document.querySelectorAll('.filter-btn');
    
    filterButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Update active state
            filterButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            // Get filter value and load rankings
            const filter = button.getAttribute('data-filter');
            currentFilter = filter;
            loadRankings(filter);
        });
    });
}

// Load rankings from API
async function loadRankings(filter = 'current') {
    const driverGrid = document.getElementById('driverGrid');
    driverGrid.innerHTML = '<div class="loading">Loading rankings...</div>';
    
    try {
        const response = await fetch(`/api/rankings?filter=${filter}`);
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
    card.style.setProperty('--team-color', teamColor);
    
    // Format ELO values
    const globalElo = Math.round(driver.global_elo || 1500);
    const qualifyingElo = Math.round(driver.qualifying_elo || 1500);
    const raceElo = Math.round(driver.race_elo || 1500);
    
    card.innerHTML = `
        <div class="driver-rank">#${rank}</div>
        <div class="driver-info">
            <div class="driver-name">${driver.driver_name}</div>
            <div class="driver-team">${driver.current_team || 'Unknown Team'}</div>
            <div class="driver-nationality">🏁 ${driver.nationality || 'N/A'}</div>
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
