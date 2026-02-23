import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
import base64
import time

# Configuration
DB_FILE = "toto_history.csv"
BASE_URL = "/Users/weidong/Documents/development/lottery-checker/toto_history.csv" #have to use full directory for CRON job
#BASE_URL = "https://www.singaporepools.com.sg/en/product/sr/Pages/toto_results.aspx"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"}

def get_encoded_url(draw_no):
    query = f"DrawNumber={draw_no}"
    encoded = base64.b64encode(query.encode()).decode()
    return f"{BASE_URL}?sppl={encoded}"

def scrape_draw(draw_no):
    """Scrapes a specific draw number and returns a dictionary of data."""
    try:
        url = get_encoded_url(draw_no)
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200: return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Verify if draw exists on page (site often redirects to latest if draw_no is invalid)
        page_draw_text = soup.find(class_="drawNumber").get_text(strip=True)
        if str(draw_no) not in page_draw_text:
            return None # Draw doesn't exist yet

        draw_date = soup.find(class_="drawDate").get_text(strip=True)
        win_nums = [n.get_text() for n in soup.find_all(class_=lambda x: x and x.startswith("win"))]
        add_num = soup.find(class_="additional").get_text(strip=True)
        
        return {
            "draw_no": int(draw_no),
            "date": draw_date,
            "win_nums": ",".join(win_nums),
            "additional": add_num
        }
    except:
        return None

def update_database():
    # 1. Load existing data
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        last_draw = df['draw_no'].max()
    else:
        # If no DB, start from 3 years ago (approx Draw 3850)
        df = pd.DataFrame(columns=["draw_no", "date", "win_nums", "additional"])
        last_draw = 3850 

    print(f"Checking for draws after #{last_draw}...")
    
    # 2. Sequential check for new draws
    new_data = []
    current_check = last_draw + 1
    
    while True:
        data = scrape_draw(current_check)
        if data:
            print(f"Found Draw {current_check} ({data['date']})")
            new_data.append(data)
            current_check += 1
            time.sleep(1) # Be polite to the server
        else:
            print("No newer draws found.")
            break
            
    # 3. Save if new data found
    if new_data:
        new_df = pd.DataFrame(new_data)
        df = pd.concat([df, new_df], ignore_index=True)
        df.to_csv(DB_FILE, index=False)
        print(f"Successfully added {len(new_data)} draws to {DB_FILE}.")
    else:
        print("Database is already up to date.")

# --- RUN ---
update_database()
#0 22 * * * /usr/bin/python3 /Users/weidong/Documents/development/lottery-checker/daily_check.py >> /Users/weidong/Documents/development/lottery-checker/toto_project/cron_log.txt 2>&1