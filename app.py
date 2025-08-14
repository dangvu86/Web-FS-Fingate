from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename
from io import StringIO, BytesIO
from bs4 import BeautifulSoup
import pandas as pd
import zipfile
import gdown
import tempfile
import os
import numpy as np

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

@app.route('/static/background/<filename>')
def background_file(filename):
    return send_from_directory('background', filename)

@app.route('/static/color/<filename>')
def color_file(filename):
    return send_from_directory('Color', filename)

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
            # Replace NaN values with empty string, then convert to dict and replace with None
            df_clean = df.fillna('')
            records = df_clean.to_dict('records')
            # Convert empty strings back to None for proper JSON null values
            for record in records:
                for key, value in record.items():
                    if value == '':
                        record[key] = None
            tables_data[name] = records
        else:
            tables_data[name] = {'error': str(df)}
    
    return jsonify({'tables': tables_data})

@app.route('/auto_load', methods=['POST'])
def auto_load():
    # Auto-load from Google Drive with configured file ID
    file_id = '1A0yeEBAvLkX64PlatHboPAHhHVIcJICw'
    
    zip_file = download_zip_from_drive(file_id)
    if zip_file is None:
        return jsonify({'error': 'Failed to download from Google Drive'})
    
    tables = process_zip_file(zip_file)
    if tables is None:
        return jsonify({'error': 'Invalid ZIP file'})
    
    tables_data = {}
    for name, df in tables.items():
        if isinstance(df, pd.DataFrame):
            # Replace NaN values with empty string, then convert to dict and replace with None
            df_clean = df.fillna('')
            records = df_clean.to_dict('records')
            # Convert empty strings back to None for proper JSON null values
            for record in records:
                for key, value in record.items():
                    if value == '':
                        record[key] = None
            tables_data[name] = records
        else:
            tables_data[name] = {'error': str(df)}
    
    return jsonify({'tables': tables_data})

def add_analysis_rows(df):
    """Add growth and margin analysis rows to match web display"""
    if df.empty or len(df.columns) < 2:
        return df
    
    # Get column names
    columns = list(df.columns)
    first_col = columns[0]  # Should be 'Fiscal Year' 
    numeric_cols = columns[1:]  # All other columns are numeric
    
    # Find revenue row
    revenue_row_idx = None
    for idx, row in df.iterrows():
        if pd.notna(row[first_col]) and 'revenue' in str(row[first_col]).lower():
            revenue_row_idx = idx
            break
    
    # Find gross profit row  
    gross_profit_row_idx = None
    for idx, row in df.iterrows():
        if pd.notna(row[first_col]) and 'gross' in str(row[first_col]).lower() and 'profit' in str(row[first_col]).lower():
            gross_profit_row_idx = idx
            break
            
    # Find net profit row (row 18)
    net_profit_row_idx = None
    for idx, row in df.iterrows():
        if pd.notna(row[first_col]) and '18' in str(row[first_col]) and 'net profit' in str(row[first_col]).lower() and 'after tax' in str(row[first_col]).lower():
            net_profit_row_idx = idx
            break
    
    # Prepare new rows to add
    new_rows = []
    
    # Net Revenue Growth
    if revenue_row_idx is not None:
        revenue_row = df.iloc[revenue_row_idx]
        growth_row = {first_col: 'Net Revenue Growth (%)'}
        
        for i, col in enumerate(numeric_cols):
            if i == 0:
                growth_row[col] = ''  # First year has no growth
            else:
                prev_col = numeric_cols[i-1]
                curr_val = pd.to_numeric(revenue_row[col], errors='coerce')
                prev_val = pd.to_numeric(revenue_row[prev_col], errors='coerce')
                
                if pd.notna(curr_val) and pd.notna(prev_val) and prev_val != 0:
                    growth_rate = ((curr_val - prev_val) / abs(prev_val) * 100)
                    growth_row[col] = f"{growth_rate:.1f}%"
                else:
                    growth_row[col] = ''
        
        new_rows.append(growth_row)
    
    # Gross Profit Growth
    if gross_profit_row_idx is not None:
        gross_row = df.iloc[gross_profit_row_idx]
        growth_row = {first_col: 'Gross Profit Growth (%)'}
        
        for i, col in enumerate(numeric_cols):
            if i == 0:
                growth_row[col] = ''
            else:
                prev_col = numeric_cols[i-1]
                curr_val = pd.to_numeric(gross_row[col], errors='coerce')
                prev_val = pd.to_numeric(gross_row[prev_col], errors='coerce')
                
                if pd.notna(curr_val) and pd.notna(prev_val):
                    # Special logic for profit/loss transitions
                    if prev_val <= 0 and curr_val > 0:
                        growth_row[col] = 'LTP'  # Loss to Profit
                    elif prev_val > 0 and curr_val <= 0:
                        growth_row[col] = 'PTL'  # Profit to Loss
                    elif prev_val <= 0 and curr_val <= 0:
                        growth_row[col] = 'Loss'  # Both years loss
                    else:
                        growth_rate = ((curr_val - prev_val) / prev_val * 100)
                        growth_row[col] = f"{growth_rate:.1f}%"
                else:
                    growth_row[col] = ''
        
        new_rows.append(growth_row)
    
    # Net Profit Growth
    if net_profit_row_idx is not None:
        net_row = df.iloc[net_profit_row_idx]
        growth_row = {first_col: 'Net Profit Growth (%)'}
        
        for i, col in enumerate(numeric_cols):
            if i == 0:
                growth_row[col] = ''
            else:
                prev_col = numeric_cols[i-1]
                curr_val = pd.to_numeric(net_row[col], errors='coerce')
                prev_val = pd.to_numeric(net_row[prev_col], errors='coerce')
                
                if pd.notna(curr_val) and pd.notna(prev_val):
                    # Special logic for profit/loss transitions
                    if prev_val <= 0 and curr_val > 0:
                        growth_row[col] = 'LTP'
                    elif prev_val > 0 and curr_val <= 0:
                        growth_row[col] = 'PTL'
                    elif prev_val <= 0 and curr_val <= 0:
                        growth_row[col] = 'Loss'
                    else:
                        growth_rate = ((curr_val - prev_val) / prev_val * 100)
                        growth_row[col] = f"{growth_rate:.1f}%"
                else:
                    growth_row[col] = ''
        
        new_rows.append(growth_row)
    
    # Gross Margin
    if revenue_row_idx is not None and gross_profit_row_idx is not None:
        revenue_row = df.iloc[revenue_row_idx]
        gross_row = df.iloc[gross_profit_row_idx]
        margin_row = {first_col: 'Gross Margin (%)'}
        
        for col in numeric_cols:
            revenue_val = pd.to_numeric(revenue_row[col], errors='coerce')
            gross_val = pd.to_numeric(gross_row[col], errors='coerce')
            
            if pd.notna(revenue_val) and pd.notna(gross_val) and revenue_val != 0:
                margin = (gross_val / revenue_val * 100)
                if margin < 0:
                    margin_row[col] = 'Neg'
                else:
                    margin_row[col] = f"{margin:.1f}%"
            else:
                margin_row[col] = '-'
        
        new_rows.append(margin_row)
    
    # Net Margin
    if revenue_row_idx is not None and net_profit_row_idx is not None:
        revenue_row = df.iloc[revenue_row_idx]
        net_row = df.iloc[net_profit_row_idx]
        margin_row = {first_col: 'Net Margin (%)'}
        
        for col in numeric_cols:
            revenue_val = pd.to_numeric(revenue_row[col], errors='coerce')
            net_val = pd.to_numeric(net_row[col], errors='coerce')
            
            if pd.notna(revenue_val) and pd.notna(net_val) and revenue_val != 0:
                margin = (net_val / revenue_val * 100)
                if margin < 0:
                    margin_row[col] = 'Neg'
                else:
                    margin_row[col] = f"{margin:.1f}%"
            else:
                margin_row[col] = '-'
        
        new_rows.append(margin_row)
    
    # Add new rows to dataframe
    if new_rows:
        new_df = pd.DataFrame(new_rows)
        df = pd.concat([df, new_df], ignore_index=True)
    
    return df

@app.route('/export_excel', methods=['POST'])
def export_excel():
    data = request.get_json()
    tables_data = data.get('tables', {})
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for name, table_data in tables_data.items():
            if 'error' not in table_data:
                df = pd.DataFrame(table_data)
                
                # Reorder columns to match web display (audit status column first)
                all_headers = list(df.columns)
                
                # Find the audit status column
                audit_status_header = None
                for header in all_headers:
                    if ('fiscal' in header.lower() and 
                        'audit' in header.lower() and 
                        'status' in header.lower()):
                        audit_status_header = header
                        break
                
                # Reorder columns: audit status first, then the rest
                if audit_status_header:
                    ordered_columns = [audit_status_header]
                    ordered_columns.extend([h for h in all_headers if h != audit_status_header])
                    df = df[ordered_columns]
                    
                    # Rename audit status column header to match web display
                    df = df.rename(columns={audit_status_header: 'Fiscal Year'})
                
                # Add analysis rows (growth and margin calculations) like on web
                df = add_analysis_rows(df)
                
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