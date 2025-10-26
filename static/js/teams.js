// F1 Team ELO Rankings - Frontend JavaScript

// Team colors mapping
const teamColors = {
    'Red Bull': '#0600EF',
    'Red Bull Racing': '#0600EF',
    'Ferrari': '#DC0000',
    'Mercedes': '#00D2BE',
    'McLaren': '#FF8700',
    'Aston Martin': '#006F62',
    'Alpine': '#0090FF',
    'Williams': '#005AFF',
    'Haas': '#FFFFFF',
    'RB': '#0600EF',
    'AlphaTauri': '#2B4562',
    'Alfa Romeo': '#900000',
    'Racing Point': '#F596C8',
    'Renault': '#FFF500',
    'Force India': '#F596C8',
    'Toro Rosso': '#469BFF',
    'Sauber': '#9B0000',
    'Manor': '#DA291C',
    'Lotus': '#FFB800',
    'Caterham': '#005030',
    'Marussia': '#DA291C',
    'HRT': '#D3D3D3',
    'Brawn': '#00FF00',
    'BMW Sauber': '#005AAA',
    'Toyota': '#FF0000',
    'Honda': '#FFFFFF',
    'Super Aguri': '#FF6600'
};

// Country flag emoji mapping
function getCountryFlag(country) {
    const flagMap = {
        'British': '🇬🇧',
        'German': '🇩🇪',
        'Italian': '🇮🇹',
        'French': '🇫🇷',
        'Austrian': '🇦🇹',
        'Swiss': '🇨🇭',
        'American': '🇺🇸',
        'Japanese': '🇯🇵',
        'Malaysian': '🇲🇾',
        'Indian': '🇮🇳',
        'Spanish': '🇪🇸',
        'Dutch': '🇳🇱',
        'Russian': '🇷🇺',
        'Australian': '🇦🇺',
        'New Zealand': '🇳🇿',
        'South African': '🇿🇦',
        'Canadian': '🇨🇦',
        'Belgian': '🇧🇪',
        'Thai': '🇹🇭',
        'Swedish': '🇸🇪',
        'Irish': '🇮🇪',
        'UK': '🇬🇧',
        'USA': '🇺🇸',
        'England': '🇬🇧'
    };
    return flagMap[country] || '🏁';
}

// Convert hex color to rgba
function hexToRgba(hex, alpha = 1) {
    if (!hex) return `rgba(225, 6, 0, ${alpha})`;
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// State management
let currentFilter = 'century';

// Create team card
function createTeamCard(team, rank) {
    const card = document.createElement('div');
    card.className = 'driver-card';
    
    // Get team color
    const teamColor = teamColors[team.team_name] || '#E10600';
    const teamColorRgb = hexToRgba(teamColor, 0.4);
    
    // Set CSS variables for team color
    card.style.setProperty('--team-color', teamColor);
    card.style.setProperty('--team-color-rgb', teamColorRgb);
    
    const globalElo = Math.round(team.era_adjusted_elo || team.global_elo || 1500);
    const qualifyingElo = Math.round(team.qualifying_elo || 1500);
    const raceElo = Math.round(team.race_elo || 1500);
    
    // Get country flag emoji
    const flagEmoji = getCountryFlag(team.base_country);
    
    // Format team name for display
    const teamName = team.team_name.toUpperCase();
    
    // Calculate years active
    const yearsActive = `${team.first_year}-${team.last_year === team.first_year ? '' : team.last_year}`;
    
    card.innerHTML = `
        <div class="driver-rank">#${rank}</div>
        <div class="driver-info">
            <div class="driver-flag">${flagEmoji}</div>
            <div class="driver-details">
                <div class="driver-name">
                    <div class="driver-lastname">${teamName}</div>
                </div>
                <div class="driver-team">${team.base_country || 'Unknown'}</div>
                <div class="driver-nationality">${yearsActive}</div>
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
                <div class="stat-value">${team.total_wins || 0}</div>
                <div class="stat-label">Wins</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">${Math.round(team.total_points || 0)}</div>
                <div class="stat-label">Points</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">${team.total_races || 0}</div>
                <div class="stat-label">Races</div>
            </div>
        </div>
    `;
    
    return card;
}

// Load team rankings
async function loadTeamRankings(filter = 'century') {
    const teamGrid = document.getElementById('teamGrid');
    teamGrid.innerHTML = '<div class="loading">Loading rankings...</div>';
    
    try {
        const response = await fetch(`/api/team-rankings?filter=${filter}`);
        const teams = await response.json();
        
        teamGrid.innerHTML = '';
        
        if (teams.length === 0) {
            teamGrid.innerHTML = '<div class="loading">No team rankings available. Please run team ELO calculation.</div>';
            return;
        }
        
        teams.forEach((team, index) => {
            const card = createTeamCard(team, index + 1);
            teamGrid.appendChild(card);
        });
        
    } catch (error) {
        console.error('Error loading team rankings:', error);
        teamGrid.innerHTML = '<div class="loading">Error loading rankings. Please try again.</div>';
    }
}

// Load last update date
async function loadLastUpdate() {
    try {
        const response = await fetch('/api/last-update');
        const data = await response.json();
        
        const lastUpdateElement = document.getElementById('lastUpdate');
        if (data.last_race_date) {
            const date = new Date(data.last_race_date);
            lastUpdateElement.textContent = `Last updated: ${date.toLocaleDateString('en-US', { 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
            })}`;
        } else {
            lastUpdateElement.textContent = 'Last updated: Unknown';
        }
    } catch (error) {
        console.error('Error loading last update:', error);
        document.getElementById('lastUpdate').textContent = 'Last updated: Error loading date';
    }
}

// Handle filter button clicks
function setupFilterButtons() {
    const filterButtons = document.querySelectorAll('.filter-btn');
    
    filterButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Update active state
            filterButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            // Get filter value and load rankings
            const filter = button.getAttribute('data-filter');
            currentFilter = filter;
            loadTeamRankings(filter);
        });
    });
}

// Initialize page
document.addEventListener('DOMContentLoaded', () => {
    setupFilterButtons();
    loadTeamRankings('century');
    loadLastUpdate();
});
