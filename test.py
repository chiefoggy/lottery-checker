import requests
from bs4 import BeautifulSoup
import base64

def get_toto_results(draw_number=None):
    # 1. Setup URL (Base64 if draw_number provided, else latest)
    url = "https://www.singaporepools.com.sg/en/product/sr/Pages/toto_results.aspx"
    if draw_number:
        query = f"DrawNumber={draw_number}"
        encoded = base64.b64encode(query.encode()).decode()
        url += f"?sppl={encoded}"

    # 2. Mimic a real browser (Crucial for Singapore Pools)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # 3. Extract Data with error handling
        draw_info = soup.find(class_="drawDate").get_text(strip=True) if soup.find(class_="drawDate") else "Unknown Date"
        
        # Get Winning Numbers (usually class 'win1', 'win2', etc.)
        winning_nums = [int(n.get_text()) for n in soup.select(".winning-numbers li") if n.get_text().isdigit()]
        # If the above selector fails due to UI changes, use your lambda fallback:
        if not winning_nums:
            winning_nums = [int(num.get_text(strip=True)) for num in soup.find_all(class_=lambda x: x and x.startswith("win"))]

        additional_num = int(soup.find(class_="additional").get_text(strip=True))
        
        # 4. Extract Prize Table into a clean dictionary
        prize_dict = {}
        rows = soup.select(".tableWinningShares tbody tr")
        for row in rows[1:]:  # Skip header
            cols = row.find_all("td")
            if len(cols) >= 2:
                group = cols[0].get_text(strip=True).replace("Group ", "")
                amount = cols[1].get_text(strip=True)
                prize_dict[group] = amount

        return {
            "date": draw_info,
            "numbers": winning_nums,
            "additional": additional_num,
            "prizes": prize_dict
        }
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def check_winnings(user_numbers, draw_data):
    if not draw_data: return
    
    win_set = set(draw_data["numbers"])
    user_set = set(user_numbers)
    
    matches = len(user_set.intersection(win_set))
    has_additional = draw_data["additional"] in user_set
    
    # Logic mapping based on official TOTO rules
    # 
    win_logic = {
        (6, False): "1",
        (5, True):  "2",
        (5, False): "3",
        (4, True):  "4",
        (4, False): "5",
        (3, True):  "6",
        (3, False): "7",
    }
    
    group = win_logic.get((matches, has_additional))
    
    print(f"--- Results for {draw_data['date']} ---")
    print(f"Winning Numbers: {draw_data['numbers']} | Add: {draw_data['additional']}")
    print(f"Your Numbers:    {user_numbers}")
    print(f"Matches: {matches} {'+ Additional' if has_additional else ''}")
    
    if group:
        prize = draw_data["prizes"].get(group, "TBD")
        print(f"CONGRATS! You won Group {group} Prize: {prize}")
    else:
        print("Better luck next time!")

# --- EXECUTION ---
my_numbers = [9, 14, 26, 29, 31, 42]
# Use 4120 for Oct 9, 2025 or None for latest
data = get_toto_results(draw_number=4120) 
check_winnings(my_numbers, data)