import pandas as pd
import time
from toto_scraper import TotoScraper

DB_FILE = "toto_history.csv"

def main():
    scraper = TotoScraper()
    
    latest_site = scraper.get_latest_draw_no()
    if not latest_site:
        print("Could not determine latest draw. Aborting.")
        return
        
    start_draw = 3847
    print(f"Starting full scrape from #{start_draw} to #{latest_site}...")
    
    all_data = []
    
    for i, draw_no in enumerate(range(start_draw, latest_site + 1)):
        data = scraper.scrape_draw(draw_no)
        if data:
            print(f"Draw {draw_no}: SUCCESS ({data['date']})")
            all_data.append(data)
            time.sleep(1) 
        else:
            print(f"Draw {draw_no}: SKIPPED (Not found or error)")
            
        if (i + 1) % 20 == 0:
            pd.DataFrame(all_data).to_csv(DB_FILE, index=False)
            print(f"--- Periodic save at Draw {draw_no} ---")
            
    if all_data:
        pd.DataFrame(all_data).to_csv(DB_FILE, index=False)
        print(f"\nDone! Saved {len(all_data)} draws to {DB_FILE}.")
    else:
        print("\nNo data collected.")

if __name__ == "__main__":
    main()
