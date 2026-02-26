import os
import re
import cv2
import pandas as pd
import pytesseract
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.jinja_env.add_extension('jinja2.ext.do')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def extract_toto_data(image_path):
    img = cv2.imread(image_path)
    if img is None:
        return {"Draw Date": "", "Numbers": []}
    
    b, g, r = cv2.split(img)
    _, thresh = cv2.threshold(r, 150, 255, cv2.THRESH_BINARY)

    custom_config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(thresh, config=custom_config)
    
    lines = text.split('\n')
    data = {"Draw Date": "", "Numbers": []}
    seen_rows = set()

    for line in lines:
        upper_line = line.upper()
        date_match = re.search(r'\d{2}/\d{2}/\d{2}', line)
        
        if date_match:
            if "DRAW" in upper_line:
                data["Draw Date"] = date_match.group()
            elif not data["Draw Date"]:
                data["Draw Date"] = date_match.group()

        nums = re.findall(r'\b(0[1-9]|[1-4][0-9])\b', line)
        
        if len(nums) >= 6:
            row_tuple = tuple(nums[:6])
            if row_tuple not in seen_rows and not any(d in upper_line for d in ["DRAW", "2025", "PM"]):
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
            return None
    else:
        row = df.iloc[-1]

    win_nums = [int(n) for n in str(row['win_nums']).split(',')]
    
    prizes = {}
    jackpot = "Refer to official site"
    
    if 'g1_prize' in row and str(row['g1_prize']) != 'nan':
        jackpot = str(row['g1_prize'])
        for i in range(1, 8):
            col = f"g{i}_prize"
            if col in row:
                prizes[f"Group {i}"] = str(row[col])

    return {
        "draw_no": row['draw_no'],
        "draw_date": row['date'],
        "winning_numbers": win_nums,
        "additional_number": int(row['additional']),
        "group1_prize": jackpot,
        "prize_dict": prizes
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'GET':
        return redirect(url_for('index'))

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
    app.run(debug=True, port=5001)
