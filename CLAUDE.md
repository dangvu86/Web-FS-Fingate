# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

FS Fingate is a Flask web application that extracts financial data tables from HTML files within ZIP archives, with automatic data processing and Excel export capabilities. The app supports both file uploads and Google Drive integration, featuring a JavaScript-powered frontend with Chart.js visualizations.

## Development Commands

### Local Development
```bash
# Primary development server (recommended)
python simple_run.py

# Alternative if simple_run.py has issues
python run.py

# Windows quick start
run.bat

# Direct Flask command (if needed)
set FLASK_APP=simple_app.py
python -m flask run --host=0.0.0.0 --port=5000
```

### Dependencies
```bash
# Install requirements
pip install -r requirements.txt

# Core dependencies: Flask==2.3.3, beautifulsoup4==4.12.2, gdown==4.7.1, xlsxwriter==3.1.9, requests==2.31.0, Werkzeug==2.3.7
```

### Production Deployment (Render)
```bash
# Deploy via git push (auto-deployed to Render)
git push origin master

# Production server is configured via Procfile: web: python simple_run.py
# Environment detection: Production mode when PORT env var exists
```

### Debug and Testing
```bash
# Access debug endpoint in production
curl https://web-fs-fingate.onrender.com/debug

# Test auto-load functionality
curl -X POST https://web-fs-fingate.onrender.com/auto_load
```

## Architecture

### Core Application Structure
- **simple_app.py**: Main Flask application with all routes and business logic
- **simple_run.py**: Application launcher with production/development mode detection
- **templates/index.html**: Single-page application with embedded JavaScript for tables, charts, and UI

### Key Application Components

#### Backend Flask Routes
- `/`: Main application page
- `/auto_load` (POST): Downloads default ZIP from Google Drive (file ID: 1A0yeEBAvLkX64PlatHboPAHhHVIcJICw)  
- `/upload` (POST): Handles ZIP file uploads
- `/download_drive` (POST): Downloads ZIP from Google Drive using provided file ID
- `/export_excel` (POST): Exports all tables to Excel format
- `/static/<path:filename>`: Custom static file serving for production
- `/debug`: Production debugging endpoint

#### Data Processing Pipeline
1. **ZIP Download/Upload**: Multiple fallback methods for Google Drive downloads using gdown library
2. **HTML Extraction**: Processes all HTML files within ZIP archives using zipfile
3. **Table Parsing**: BeautifulSoup extracts `<table>` elements without pandas dependency
4. **Data Cleaning**: Removes formatting characters (periods, parentheses, commas) and converts to numerical values
5. **Chart Data Generation**: JavaScript processes table data for Chart.js visualization

#### Frontend Architecture
- **Single-page Flask template** with embedded JavaScript (no separate JS files)
- **Bootstrap 5.1.3** for responsive UI components
- **Chart.js** for financial data visualization (revenue, profit, margin analysis)
- **Auto-load mechanism** on page load fetches default financial data
- **Dynamic table generation** with tabs for multiple HTML files

### Production vs Development Differences
- **Environment Detection**: Uses `'PORT' in os.environ` to detect production mode
- **Debug Mode**: `debug=True` in development, `debug=False` in production  
- **Static Files**: Custom `/static` route handler for production deployment on Render
- **Logging**: Enhanced debug logging with `[DEBUG]`, `[ERROR]`, `[SUCCESS]` tags and `flush=True`

### Google Drive Integration
- **Default File ID**: `1A0yeEBAvLkX64PlatHboPAHhHVIcJICw` (hardcoded financial data)
- **Multiple Download Methods**: Three fallback approaches for robust Google Drive access
- **Temporary File Handling**: Uses `tempfile.NamedTemporaryFile` with automatic cleanup

### Chart Generation Logic
- **Data Extraction**: Identifies fiscal year columns and financial metrics (revenue, profit, margins)
- **Growth Calculations**: Handles profit/loss transitions with special "LTP" (Loss to Profit) and "PTL" (Profit to Loss) indicators
- **Chart Types**: Combined bar/line charts for revenue/profit with growth rates, separate line chart for margins
- **Error Handling**: Graceful fallback when chart libraries fail to load from CDN

## File Structure Notes

### Multiple Application Entry Points
The codebase contains several Flask application files serving different purposes:
- **simple_app.py + simple_run.py**: Production-ready version (used by Procfile)
- **app.py + run.py**: Alternative/legacy version
- **alternative_server.py, basic_server.py**: Fallback servers for troubleshooting

### Static Assets
- **static/background/DC.png**: Company logo (duplicated from background/ for Flask static serving)
- **templates/index.html**: Complete single-page application with embedded CSS and JavaScript

### Deployment Configuration  
- **Procfile**: Render deployment configuration
- **runtime.txt**: Python 3.11.8 specification for Render (avoid Python 3.13 compatibility issues)
- **requirements.txt**: Minimal dependencies without pandas/lxml to avoid build issues

## Important Implementation Details

### Data Processing Without Pandas
The application manually processes HTML tables without pandas dependency to avoid Python 3.13 compatibility issues in production deployment. BeautifulSoup handles HTML parsing with Python's built-in HTML parser.

### Chart.js Error Handling
Comprehensive error handling for chart creation includes checking for CDN library availability, validating chart data, and graceful degradation when Chart.js fails to load.

### Google Drive Download Robustness  
Three-tier fallback system handles various Google Drive access scenarios including virus scan warnings, download token requirements, and network connectivity issues.

### Production Debugging
Debug endpoint `/debug` provides environment information, file system status, and dependency verification for production troubleshooting.