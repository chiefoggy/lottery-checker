import os
import pandas as pd
import time
from toto_scraper import TotoScraper

DB_FILE = "toto_history.csv"

def update_database():
    scraper = TotoScraper()
    
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        last_draw = df['draw_no'].max()
    else:
        df = pd.DataFrame(columns=["draw_no", "date", "win_nums", "additional", 
                                   "g1_prize", "g2_prize", "g3_prize", "g4_prize", 
                                   "g5_prize", "g6_prize", "g7_prize"])
        last_draw = 3846

    latest_site_draw = scraper.get_latest_draw_no()
    if not latest_site_draw:
        print("Could not determine latest draw on site.")
        return

    if last_draw >= latest_site_draw:
        print(f"Database is already up to date (Last: {last_draw}, Site: {latest_site_draw}).")
        return

    print(f"Checking for draws after #{last_draw} up to #{latest_site_draw}...")
    
    new_data = []
    for draw_no in range(last_draw + 1, latest_site_draw + 1):
        data = scraper.scrape_draw(draw_no)
        if data:
            print(f"Found Draw {draw_no} ({data['date']})")
            new_data.append(data)
            time.sleep(1)
        else:
            print(f"Draw {draw_no} not found.")
            break
            
    if new_data:
        new_df = pd.DataFrame(new_data)
        df = pd.concat([df, new_df], ignore_index=True)
        df.to_csv(DB_FILE, index=False)
        print(f"Added {len(new_data)} draws to {DB_FILE}.")
    else:
        print("No new draws added.")

if __name__ == "__main__":
    update_database()