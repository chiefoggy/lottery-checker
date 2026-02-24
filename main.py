import os
import re
import cv2
import pandas as pd
import pytesseract
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def extract_toto_data(image_path):
    img = cv2.imread(image_path)
    if img is None:
        return {"Draw Date": "", "Numbers": []}
    
    # 1. THE SECRET SAUCE: Use the Red channel only
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
            if row_tuple not in seen_rows and not any(d in line for d in ["DRAW", "2025", "PM"]):
                data["Numbers"].append(list(row_tuple))
                seen_rows.add(row_tuple)
                
    return data

def get_toto_results(target_date=None):
    csv_path = "toto_history.csv"
    if not os.path.exists(csv_path):
        return None
    
    df = pd.read_csv(csv_path)
    if df.empty:
        return None

    # Normalize CSV dates: "Mon, 23 Feb 2026" -> "23/02/26"
    def normalize_csv_date(date_str):
        try:
            if ',' in date_str:
                date_str = date_str.split(',')[1].strip()
            dt = datetime.strptime(date_str, "%d %b %Y")
            return dt.strftime("%d/%m/%y")
        except:
            return date_str

    if target_date:
        df['norm_date'] = df['date'].apply(normalize_csv_date)
        match = df[df['norm_date'] == target_date]
        if not match.empty:
            row = match.iloc[-1]
        else:
            row = df.iloc[-1]
    else:
        row = df.iloc[-1]

    win_nums = [int(n) for n in str(row['win_nums']).split(',')]
    
    return {
        "draw_no": row['draw_no'],
        "draw_date": row['date'],
        "winning_numbers": win_nums,
        "additional_number": int(row['additional']),
        "group1_prize": "Refer to official site",
        "prize_dict": {}
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        user_data = extract_toto_data(filepath)
        target_date = user_data.get("Draw Date")
        official_results = get_toto_results(target_date)
        
        return render_template('results.html', 
                               user_data=user_data, 
                               official=official_results)

if __name__ == '__main__':
    app.jinja_env.add_extension('jinja2.ext.do')
    app.run(debug=True, port=5001)
