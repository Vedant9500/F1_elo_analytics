"""
Scraper for 2025 F1 Season Data from Pitwall.app
Extracts race results including grid positions, finishing positions, teams, and status
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from datetime import datetime

class PitwallScraper:
    def __init__(self):
        self.base_url = "https://pitwall.app"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def get_2025_races(self):
        """Get list of all 2025 races"""
        url = f"{self.base_url}/seasons/2025-formula-1-world-championship"
        
        print("Fetching 2025 season page...")
        response = self.session.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        races = []
        
        # Find race schedule table
        schedule_rows = soup.find_all('tr')
        
        for row in schedule_rows:
            cells = row.find_all('td')
            if len(cells) >= 2:
                # Get race link
                race_link = cells[1].find('a')
                if race_link and '/races/2025-' in race_link.get('href', ''):
                    race_url = race_link.get('href')
                    race_name = race_link.text.strip()
                    
                    # Get round number and date
                    round_num = cells[0].text.strip()
                    date_text = cells[2].text.strip() if len(cells) > 2 else ''
                    
                    races.append({
                        'round': round_num,
                        'name': race_name,
                        'url': race_url,
                        'date': date_text
                    })
        
        print(f"Found {len(races)} races")
        return races
    
    def scrape_race_results(self, race_url, round_num, race_name, race_date):
        """Scrape results from a single race"""
        full_url = f"{self.base_url}{race_url}"
        
        print(f"\nScraping: {race_name} (Round {round_num})...")
        
        try:
            response = self.session.get(full_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            results = []
            
            # Find results table (case-insensitive)
            results_section = soup.find('h3', string=re.compile('results', re.IGNORECASE))
            if not results_section:
                print(f"  No results found for {race_name}")
                return None
            
            # Find the table after the RESULTS heading
            table = results_section.find_next('table')
            if not table:
                print(f"  No results table found for {race_name}")
                return None
            
            rows = table.find_all('tr')[1:]  # Skip header
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 5:
                    # Extract position (1, 2, 3, or DNF, DNS, etc.)
                    position = cells[0].text.strip()
                    
                    # Extract driver info
                    driver_cell = cells[1]
                    driver_number = driver_cell.find('a')
                    if driver_number:
                        driver_num = driver_number.text.strip().replace('#', '')
                        driver_name = driver_cell.text.replace(f'#{driver_num}', '').strip()
                    else:
                        driver_num = ''
                        driver_name = driver_cell.text.strip()
                    
                    # Extract team
                    team = cells[2].text.strip()
                    
                    # Extract time/gap or status
                    time_gap = cells[3].text.strip()
                    
                    # Extract grid position (starting position)
                    grid_pos = cells[4].text.strip()
                    if grid_pos:
                        # Remove ordinal suffix (1st -> 1, 2nd -> 2, etc.)
                        grid_pos = re.sub(r'(st|nd|rd|th)', '', grid_pos)
                    
                    # Extract laps completed
                    laps = cells[5].text.strip() if len(cells) > 5 else ''
                    
                    # Determine status
                    if position == 'DNF':
                        status = time_gap if time_gap else 'Retired'
                        finish_pos = None
                    elif position == 'DNS':
                        status = 'Did not start'
                        finish_pos = None
                    elif position == 'DSQ':
                        status = 'Disqualified'
                        finish_pos = None
                    else:
                        status = 'Finished'
                        finish_pos = position
                    
                    results.append({
                        'round': round_num,
                        'race_name': race_name,
                        'race_date': race_date,
                        'position': finish_pos,
                        'driver_number': driver_num,
                        'driver_name': driver_name,
                        'team': team,
                        'grid_position': grid_pos,
                        'laps': laps,
                        'time_gap': time_gap,
                        'status': status
                    })
            
            print(f"  ✓ Scraped {len(results)} results")
            return results
            
        except Exception as e:
            print(f"  ✗ Error scraping {race_name}: {e}")
            return None
    
    def scrape_all_2025_races(self):
        """Scrape all 2025 race results"""
        races = self.get_2025_races()
        
        all_results = []
        
        for race in races:
            # Check if race has results (not future race)
            if race.get('url'):
                results = self.scrape_race_results(
                    race['url'],
                    race['round'],
                    race['name'],
                    race['date']
                )
                
                if results:
                    all_results.extend(results)
                
                # Be nice to the server
                time.sleep(2)
        
        return pd.DataFrame(all_results)
    
    def save_to_csv(self, df, filename='data/2025_race_results.csv'):
        """Save results to CSV"""
        import os
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        df.to_csv(filename, index=False)
        print(f"\n✓ Saved {len(df)} results to {filename}")


def main():
    scraper = PitwallScraper()
    
    print("="*70)
    print("PITWALL 2025 F1 SEASON SCRAPER")
    print("="*70)
    
    # Scrape all races
    df = scraper.scrape_all_2025_races()
    
    if not df.empty:
        # Display summary
        print("\n" + "="*70)
        print("SCRAPING COMPLETE")
        print("="*70)
        print(f"Total results: {len(df)}")
        print(f"Races completed: {df['round'].nunique()}")
        print(f"Unique drivers: {df['driver_name'].nunique()}")
        print(f"Unique teams: {df['team'].nunique()}")
        
        print("\nSample data:")
        print(df[['round', 'race_name', 'driver_name', 'team', 'grid_position', 'position', 'status']].head(10))
        
        # Save to CSV
        scraper.save_to_csv(df)
        
        print("\n✓ Ready to import into database!")
        print("  Next step: Run import script to add 2025 data to f1_database.db")
    else:
        print("\n✗ No data scraped")


if __name__ == "__main__":
    main()
