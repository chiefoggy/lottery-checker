import cv2
import pytesseract
import re

def extract_toto_data(image_path):
    img = cv2.imread(image_path)
    
    # 1. THE SECRET SAUCE: Use the Red channel only
    # On TOTO tickets, the logos are red. In the red channel, 
    # red logos become white (invisible), leaving only black text.
    b, g, r = cv2.split(img)
    
    # 2. Sharpen the image
    _, thresh = cv2.threshold(r, 150, 255, cv2.THRESH_BINARY)

    # 3. OCR
    custom_config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(thresh, config=custom_config)
    
    lines = text.split('\n')
    data = {"Draw Date": "", "Numbers": []}
    
    # Track seen rows to avoid duplicates
    seen_rows = set()

    for line in lines:
        # Get Draw Date (only the first one found)
        if not data["Draw Date"]:
            date_match = re.search(r'\d{2}/\d{2}/\d{2}', line)
            if date_match:
                data["Draw Date"] = date_match.group()

        # 4. STRICT FILTERING
        # TOTO numbers are 01-49. We look for exactly 6 of them.
        nums = re.findall(r'\b(0[1-9]|[1-4][0-9])\b', line)
        
        if len(nums) >= 6:
            row_tuple = tuple(nums[:6])
            # Only add if it's not the Draw Date or Serial Number hidden as numbers
            # A real TOTO row usually doesn't have the same year/date repeatedly
            if row_tuple not in seen_rows and not any(d in line for d in ["DRAW", "2025", "PM"]):
                data["Numbers"].append(list(row_tuple))
                seen_rows.add(row_tuple)
                
    return data

result = extract_toto_data('toto.jpg')
print(f"Final Extracted Data: {result}")