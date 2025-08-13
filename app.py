from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from io import StringIO, BytesIO
from bs4 import BeautifulSoup
import pandas as pd
import zipfile
import gdown
import tempfile
import os

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def download_zip_from_drive(file_id):
    try:
        url = f"https://drive.google.com/uc?id={file_id}"
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_file:
            gdown.download(url, tmp_file.name, quiet=False)
            with open(tmp_file.name, "rb") as f:
                return BytesIO(f.read())
    except Exception as e:
        return None

def extract_tables_from_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    tables = soup.find_all("table")
    if tables:
        try:
            df = pd.read_html(StringIO(str(tables[0])))[0]
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [' '.join(map(str, col)).strip() for col in df.columns]
            df.iloc[0, 0] = str(df.iloc[0, 0]).replace('.', '').replace(')', '').replace('(', '-').replace(',', '')
            for col in df.columns[1:]:
                df[col] = df[col].astype(str).str.replace('.', '', regex=False)
                df[col] = df[col].astype(str).str.replace(')', '', regex=False)
                df[col] = df[col].astype(str).str.replace('(', '-', regex=False)
                df[col] = df[col].astype(str).str.replace(',', '', regex=False)
                df[col] = pd.to_numeric(df[col], errors="coerce")
            return df
        except Exception as e:
            return f"Error reading table: {e}"
    return "No tables found in HTML file."

def process_zip_file(zip_file):
    html_tables = {}
    try:
        with zipfile.ZipFile(zip_file, "r") as zip_ref:
            html_files = [f for f in zip_ref.namelist() if f.lower().endswith(".html")]
            for html_file in html_files:
                with zip_ref.open(html_file) as file:
                    html_content = file.read().decode("utf-8")
                    result = extract_tables_from_html(html_content)
                    html_tables[html_file] = result
    except zipfile.BadZipFile:
        return None
    return html_tables

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'})
    
    if file and file.filename.lower().endswith('.zip'):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        with open(file_path, 'rb') as f:
            zip_file = BytesIO(f.read())
        
        tables = process_zip_file(zip_file)
        os.remove(file_path)
        
        if tables is None:
            return jsonify({'error': 'Invalid ZIP file'})
        
        tables_data = {}
        for name, df in tables.items():
            if isinstance(df, pd.DataFrame):
                tables_data[name] = df.to_dict('records')
            else:
                tables_data[name] = {'error': str(df)}
        
        return jsonify({'tables': tables_data})
    
    return jsonify({'error': 'Please upload a ZIP file'})

@app.route('/download_drive', methods=['POST'])
def download_from_drive():
    data = request.get_json()
    file_id = data.get('file_id', '')
    
    if not file_id:
        return jsonify({'error': 'No file ID provided'})
    
    zip_file = download_zip_from_drive(file_id)
    if zip_file is None:
        return jsonify({'error': 'Failed to download from Google Drive'})
    
    tables = process_zip_file(zip_file)
    if tables is None:
        return jsonify({'error': 'Invalid ZIP file'})
    
    tables_data = {}
    for name, df in tables.items():
        if isinstance(df, pd.DataFrame):
            tables_data[name] = df.to_dict('records')
        else:
            tables_data[name] = {'error': str(df)}
    
    return jsonify({'tables': tables_data})

@app.route('/export_excel', methods=['POST'])
def export_excel():
    data = request.get_json()
    tables_data = data.get('tables', {})
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for name, table_data in tables_data.items():
            if 'error' not in table_data:
                df = pd.DataFrame(table_data)
                sheet_name = name[:31]
                df.to_excel(writer, index=False, sheet_name=sheet_name)
                
                workbook = writer.book
                worksheet = writer.sheets[sheet_name]
                for i, col in enumerate(df.columns):
                    column_len = max(df[col].astype(str).map(len).max(), len(str(col))) + 2
                    align_format = workbook.add_format({'align': 'left' if i == 0 else 'right'})
                    worksheet.set_column(i, i, column_len, align_format)
    
    output.seek(0)
    return send_file(
        output,
        as_attachment=True,
        download_name='all_tables.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)