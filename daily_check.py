import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
import base64
import time
import re

# Configuration
DB_FILE = "toto_history.csv"
BASE_URL = "https://www.singaporepools.com.sg/en/product/sr/Pages/toto_results.aspx"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"}

class TotoScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def get_encoded_url(self, draw_no):
        query = f"DrawNumber={draw_no}"
        encoded = base64.b64encode(query.encode()).decode()
        return f"{BASE_URL}?sppl={encoded}"

    def get_latest_draw_no(self):
        """Fetches the latest draw number from the landing page."""
        try:
            response = self.session.get(BASE_URL, timeout=10)
            if response.status_code != 200: return None
            soup = BeautifulSoup(response.content, 'html.parser')
            page_draw_text = soup.find(class_="drawNumber").get_text(strip=True)
            # Find digits in something like "Draw No. 4056"
            match = re.search(r'\d+', page_draw_text)
            return int(match.group()) if match else None
        except Exception as e:
            print(f"Error fetching latest draw: {e}")
            return None

    def scrape_draw(self, draw_no):
        """Scrapes a specific draw number."""
        try:
            url = self.get_encoded_url(draw_no)
            response = self.session.get(url, timeout=10)
            if response.status_code != 200: return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            page_draw_text = soup.find(class_="drawNumber").get_text(strip=True)
            
            if str(draw_no) not in page_draw_text:
                return None

            draw_date = soup.find(class_="drawDate").get_text(strip=True)
            win_nums = [n.get_text() for n in soup.find_all(class_=lambda x: x and x.startswith("win"))]
            add_num = soup.find(class_="additional").get_text(strip=True)
            
            return {
                "draw_no": int(draw_no),
                "date": draw_date,
                "win_nums": ",".join(win_nums),
                "additional": add_num
            }
        except Exception as e:
            print(f"Error scraping draw {draw_no}: {e}")
            return None

def update_database():
    scraper = TotoScraper()
    
    # 1. Load existing data
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        last_draw = df['draw_no'].max()
    else:
        df = pd.DataFrame(columns=["draw_no", "date", "win_nums", "additional"])
        last_draw = 3850 

    # 2. Get latest draw available on site
    import re
    latest_site_draw = scraper.get_latest_draw_no()
    if not latest_site_draw:
        print("Could not determine latest draw on site. Sequential check will follow.")
        latest_site_draw = 99999 # Fallback to large number

    if last_draw >= latest_site_draw:
        print(f"Database is already up to date (Last: {last_draw}, Site: {latest_site_draw}).")
        return

    print(f"Checking for draws after #{last_draw} up to #{latest_site_draw}...")
    
    # 3. Fetch new data
    new_data = []
    for current_check in range(last_draw + 1, latest_site_draw + 1):
        data = scraper.scrape_draw(current_check)
        if data:
            print(f"Found Draw {current_check} ({data['date']})")
            new_data.append(data)
            time.sleep(1) # Be polite
        else:
            print(f"Draw {current_check} not found or error occurred.")
            break
            
    # 4. Save results
    if new_data:
        new_df = pd.DataFrame(new_data)
        df = pd.concat([df, new_df], ignore_index=True)
        df.to_csv(DB_FILE, index=False)
        print(f"Successfully added {len(new_data)} draws to {DB_FILE}.")
    else:
        print("No new draws added.")

if __name__ == "__main__":
    update_database()