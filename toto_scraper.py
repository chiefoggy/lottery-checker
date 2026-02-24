import os
import re
import requests
from bs4 import BeautifulSoup
import base64

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
            draw_elem = soup.find(class_="drawNumber")
            if not draw_elem: return None
            match = re.search(r'\d+', draw_elem.get_text(strip=True))
            return int(match.group()) if match else None
        except Exception as e:
            print(f"Error fetching latest draw: {e}")
            return None

    def scrape_draw(self, draw_no):
        """Scrapes a specific draw number and returns its data including prizes."""
        try:
            url = self.get_encoded_url(draw_no)
            response = self.session.get(url, timeout=10)
            if response.status_code != 200: return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            draw_elem = soup.find(class_="drawNumber")
            if not draw_elem: return None
            if str(draw_no) not in draw_elem.get_text(strip=True):
                return None

            draw_date = soup.find(class_="drawDate").get_text(strip=True)
            win_nums = [n.get_text() for n in soup.find_all(class_=lambda x: x and x.startswith("win"))]
            add_num = soup.find(class_="additional").get_text(strip=True)
            
            prizes = {}
            prize_table = soup.find("table", class_="tableWinningShares")
            if prize_table:
                rows = prize_table.find("tbody").find_all("tr")[1:]
                for i, r in enumerate(rows):
                    cols = r.find_all("td")
                    if len(cols) >= 2:
                        prizes[f"g{i+1}_prize"] = cols[1].get_text(strip=True)
            
            for i in range(1, 8):
                if f"g{i}_prize" not in prizes:
                    prizes[f"g{i}_prize"] = "-"

            data = {
                "draw_no": int(draw_no),
                "date": draw_date,
                "win_nums": ",".join(win_nums),
                "additional": add_num
            }
            data.update(prizes)
            return data
        except Exception as e:
            print(f"Error scraping draw {draw_no}: {e}")
            return None
