from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from io import StringIO, BytesIO
from bs4 import BeautifulSoup
import zipfile
import gdown
import tempfile
import os
import csv
import xlsxwriter

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def download_zip_from_drive(file_id):
    """Download ZIP file from Google Drive with multiple fallback methods"""
    
    # Method 1: Try gdown with direct download
    try:
        url = f"https://drive.google.com/uc?id={file_id}&export=download"
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_file:
            print(f"Attempting download from: {url}")
            gdown.download(url, tmp_file.name, quiet=False)
            
            if os.path.getsize(tmp_file.name) > 0:
                with open(tmp_file.name, "rb") as f:
                    content = f.read()
                os.unlink(tmp_file.name)  # Clean up
                return BytesIO(content)
    except Exception as e:
        print(f"Method 1 failed: {e}")
    
    # Method 2: Try alternative gdown approach
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_file:
            print(f"Trying alternative download for file ID: {file_id}")
            gdown.download(f"https://drive.google.com/file/d/{file_id}/view?usp=sharing", 
                          tmp_file.name, quiet=False, fuzzy=True)
            
            if os.path.getsize(tmp_file.name) > 0:
                with open(tmp_file.name, "rb") as f:
                    content = f.read()
                os.unlink(tmp_file.name)  # Clean up
                return BytesIO(content)
    except Exception as e:
        print(f"Method 2 failed: {e}")
    
    # Method 3: Direct requests approach
    try:
        import requests
        session = requests.Session()
        
        # First request to get confirmation token
        response = session.get(f"https://drive.google.com/uc?id={file_id}&export=download", 
                              stream=True)
        
        # Check for virus scan warning
        token = None
        for key, value in response.cookies.items():
            if key.startswith('download_warning'):
                token = value
                break
        
        if token:
            params = {'id': file_id, 'confirm': token, 'export': 'download'}
            response = session.get("https://drive.google.com/uc", params=params, stream=True)
        
        if response.status_code == 200 and response.headers.get('content-length', '0') != '0':
            return BytesIO(response.content)
            
    except Exception as e:
        print(f"Method 3 failed: {e}")
    
    return None

def extract_tables_from_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    tables = soup.find_all("table")
    if tables:
        try:
            # Extract table data manually without pandas
            table = tables[0]
            rows = table.find_all("tr")
            
            table_data = []
            headers = []
            
            for i, row in enumerate(rows):
                cells = row.find_all(["th", "td"])
                row_data = []
                for cell in cells:
                    text = cell.get_text(strip=True)
                    # Clean the data like in original
                    text = text.replace('.', '').replace(')', '').replace('(', '-').replace(',', '')
                    row_data.append(text)
                
                if i == 0:  # First row as headers
                    headers = row_data
                else:
                    table_data.append(dict(zip(headers, row_data)))
            
            # Reorder columns to put Fiscal Year End first
            if table_data and headers:
                fiscal_year_col = None
                for header in headers:
                    if 'fiscal' in header.lower() and 'year' in header.lower():
                        fiscal_year_col = header
                        break
                
                if fiscal_year_col:
                    # Reorder each row to put fiscal year first
                    reordered_data = []
                    other_headers = [h for h in headers if h != fiscal_year_col]
                    new_headers = [fiscal_year_col] + other_headers
                    
                    for row in table_data:
                        reordered_row = {}
                        reordered_row[fiscal_year_col] = row.get(fiscal_year_col, '')
                        for header in other_headers:
                            reordered_row[header] = row.get(header, '')
                        reordered_data.append(reordered_row)
                    
                    return reordered_data
            
            return table_data
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
        for name, table_data in tables.items():
            if isinstance(table_data, list):
                tables_data[name] = table_data
            else:
                tables_data[name] = {'error': str(table_data)}
        
        return jsonify({'tables': tables_data})
    
    return jsonify({'error': 'Please upload a ZIP file'})

@app.route('/download_drive', methods=['POST'])
def download_from_drive():
    data = request.get_json()
    file_id = data.get('file_id', '').strip()
    
    if not file_id:
        return jsonify({'error': 'No file ID provided'})
    
    # Clean file ID (extract from URL if needed)
    if 'drive.google.com' in file_id:
        import re
        match = re.search(r'/d/([a-zA-Z0-9-_]+)', file_id)
        if match:
            file_id = match.group(1)
        else:
            return jsonify({'error': 'Invalid Google Drive URL format'})
    
    print(f"Attempting to download file ID: {file_id}")
    
    zip_file = download_zip_from_drive(file_id)
    if zip_file is None:
        return jsonify({'error': 'Failed to download from Google Drive. Please check:\n1. File ID is correct\n2. File is publicly accessible\n3. File sharing is enabled'})
    
    tables = process_zip_file(zip_file)
    if tables is None:
        return jsonify({'error': 'Downloaded file is not a valid ZIP file'})
    
    if not tables:
        return jsonify({'error': 'No HTML files found in the ZIP archive'})
    
    tables_data = {}
    for name, table_data in tables.items():
        if isinstance(table_data, list):
            tables_data[name] = table_data
        else:
            tables_data[name] = {'error': str(table_data)}
    
    return jsonify({'tables': tables_data})

@app.route('/auto_load', methods=['POST'])
def auto_load():
    """Automatically load the default Google Drive file"""
    
    # Default file ID from the original fs_extract.py
    default_file_id = "1A0yeEBAvLkX64PlatHboPAHhHVIcJICw"
    
    print(f"Auto-loading default file ID: {default_file_id}")
    
    zip_file = download_zip_from_drive(default_file_id)
    if zip_file is None:
        return jsonify({'error': 'Failed to auto-load default data from Google Drive. Please check your internet connection.'})
    
    tables = process_zip_file(zip_file)
    if tables is None:
        return jsonify({'error': 'Default file is not a valid ZIP file'})
    
    if not tables:
        return jsonify({'error': 'No HTML files found in the default ZIP archive'})
    
    tables_data = {}
    for name, table_data in tables.items():
        if isinstance(table_data, list):
            tables_data[name] = table_data
        else:
            tables_data[name] = {'error': str(table_data)}
    
    print(f"Successfully loaded {len(tables_data)} tables from default file")
    return jsonify({'tables': tables_data})

@app.route('/export_excel', methods=['POST'])
def export_excel():
    data = request.get_json()
    tables_data = data.get('tables', {})
    
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    
    for name, table_data in tables_data.items():
        if 'error' not in table_data and isinstance(table_data, list) and len(table_data) > 0:
            sheet_name = name[:31].replace('/', '_').replace('\\', '_')
            worksheet = workbook.add_worksheet(sheet_name)
            
            # Write headers
            headers = list(table_data[0].keys())
            for col, header in enumerate(headers):
                worksheet.write(0, col, header)
            
            # Write data
            for row, record in enumerate(table_data, 1):
                for col, header in enumerate(headers):
                    value = record.get(header, '')
                    # Try to convert to number if possible
                    try:
                        if value and value != '':
                            value = float(value.replace(',', ''))
                    except:
                        pass
                    worksheet.write(row, col, value)
    
    workbook.close()
    output.seek(0)
    
    return send_file(
        output,
        as_attachment=True,
        download_name='all_tables.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)