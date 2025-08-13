# FS Fingate - Web Table Extractor

A Flask web application that extracts HTML tables from ZIP files and exports them to Excel format. Based on the original Streamlit application.

## Features

- **File Upload**: Drag and drop or browse to upload ZIP files containing HTML files
- **Google Drive Integration**: Download ZIP files directly from Google Drive using file ID
- **Table Extraction**: Automatically extracts tables from HTML files in the ZIP archive
- **Data Processing**: Cleans and formats numerical data in tables
- **Excel Export**: Export all extracted tables to a single Excel file with multiple sheets
- **Responsive UI**: Bootstrap-based interface that works on desktop and mobile

## Installation & Running

### Option 1: Quick Start (Windows)
```bash
# Double-click run.bat or run in command prompt:
run.bat
```

### Option 2: Manual Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run the improved launcher
python run.py
```

### Option 3: If Flask doesn't work
```bash
# Try the alternative simple server
python alternative_server.py
```

### Option 4: Direct Flask command
```bash
# Set environment and run Flask directly
set FLASK_APP=app.py
python -m flask run --host=0.0.0.0 --port=5000
```

## Troubleshooting

If `localhost` doesn't work:
- Try `http://127.0.0.1:5000` instead
- Check Windows Firewall settings
- Run Command Prompt as Administrator  
- Use the alternative server: `python alternative_server.py`

## Usage

### Upload ZIP File
1. Click the upload area or drag and drop a ZIP file
2. The application will process all HTML files in the ZIP
3. Extracted tables will be displayed in separate tabs

### Download from Google Drive
1. Get the Google Drive file ID from the share URL
2. Enter the file ID in the input field
3. Click "Download" to process the file

### Export to Excel
- Click "Export All to Excel" to download all tables as an Excel file
- Each table becomes a separate sheet in the workbook

## File Structure

```
├── app.py              # Main Flask application
├── templates/
│   └── index.html      # Web interface template
├── uploads/            # Temporary file storage (auto-created)
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Configuration

- Maximum file size: 16MB
- Supported file types: ZIP files containing HTML files
- Temporary files are automatically cleaned up after processing