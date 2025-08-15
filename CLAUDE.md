# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

FS Fingate is a dual-platform financial data extraction application available as both Flask web app and Streamlit app. It extracts financial data tables from HTML files within ZIP archives, with automatic data processing, visualization, and Excel export capabilities. The app supports file uploads and Google Drive integration with Dragon Capital branding.

## Development Commands

### Local Development
```bash
# Flask App (primary development with rich UI)
python simple_run.py

# Streamlit App (alternative interface)
streamlit run FS_Extract.py --server.port 8501

# Alternative Flask servers for troubleshooting
python run.py
python alternative_server.py  # Fallback server
python basic_server.py       # Basic server

# Windows quick start
run.bat
```

### Dependencies
```bash
# Install dependencies
pip install -r requirements.txt

# Core dependencies: Flask, pandas, beautifulsoup4, gdown, xlsxwriter, lxml
```

### Production Deployment

#### Streamlit Cloud (Primary)
```bash
# Deploy to Streamlit Cloud (https://share.streamlit.io/)
git push origin master
# Main file: FS_Extract.py
# Requirements: requirements.txt (no version pins for cloud compatibility)
```

#### Render (Flask Alternative)
```bash
# Deploy via git push
git push origin master
# Production server configured via Procfile: web: python simple_run.py
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

#### Flask Application (Primary Development)
- **simple_app.py**: Main Flask application with routes and business logic
- **simple_run.py**: Application launcher with production/development mode detection  
- **templates/index.html**: Rich SPA with embedded JavaScript, Chart.js, and Dragon Capital styling

#### Streamlit Application (Production Alternative)
- **FS_Extract.py**: Main Streamlit app with data processing and Dragon Capital-styled UI
- **requirements.txt**: Streamlit Cloud dependencies (no version pins)

### Key Application Components

#### Flask App Routes
- `/`: Main application page with Dragon Capital branding and Chart.js visualizations
- `/auto_load` (POST): Downloads default ZIP from Google Drive (file ID: 1A0yeEBAvLkX64PlatHboPAHhHVIcJICw)
- `/upload` (POST): Handles ZIP file uploads with drag-and-drop UI
- `/download_drive` (POST): Downloads ZIP from Google Drive using provided file ID
- `/export_excel` (POST): Exports all tables to Excel format
- `/static/<path:filename>`: Custom static file serving for production
- `/debug`: Production debugging endpoint

#### Data Processing Pipeline
1. **ZIP Download/Upload**: Multiple fallback methods for Google Drive downloads using gdown library
2. **HTML Extraction**: Processes all HTML files within ZIP archives using zipfile
3. **Table Parsing**: BeautifulSoup extracts `<table>` elements with html.parser for cloud compatibility
4. **Data Cleaning**: Removes formatting characters (periods, parentheses, commas) and converts to numerical values
5. **Number Formatting**: Applies comma separators with decimal preservation (1,234,567.50 → 1,234,567.5)
6. **Chart Data Generation**: JavaScript processes table data for Chart.js visualization

#### Frontend Architecture
- **Single-page Flask template** with embedded JavaScript (no separate JS files)
- **Bootstrap 5.1.3** for responsive UI components
- **Chart.js** for financial data visualization (revenue, profit, margin analysis)
- **Dragon Capital Styling**: Custom CSS with color scheme (#0C4130, #08C179, #B78D51) and background image
- **Auto-load mechanism** fetches default financial data on page load
- **Dynamic table generation** with tabs for multiple HTML files

### Production vs Development Differences
- **Environment Detection**: Uses `'PORT' in os.environ` to detect production mode
- **Debug Mode**: `debug=True` in development, `debug=False` in production  
- **Static Files**: Custom `/static` route handler for production deployment
- **Logging**: Enhanced debug logging with `[DEBUG]`, `[ERROR]`, `[SUCCESS]` tags

### Google Drive Integration
- **Default File ID**: `1A0yeEBAvLkX64PlatHboPAHhHVIcJICw` (hardcoded financial data)
- **Multiple Download Methods**: Three fallback approaches for robust access
- **Temporary File Handling**: Uses `tempfile.NamedTemporaryFile` with automatic cleanup

### Chart Generation Logic
- **Data Extraction**: Identifies fiscal year columns and financial metrics (revenue, profit, margins)
- **Growth Calculations**: Handles profit/loss transitions with "LTP" (Loss to Profit) and "PTL" (Profit to Loss) indicators
- **Chart Types**: Combined bar/line charts for revenue/profit with growth rates
- **Error Handling**: Graceful fallback when Chart.js fails to load from CDN

## File Structure Notes

### Duplicate Directory Structure
The codebase has a nested directory structure with duplicated files:
```
D:\Web_FS_Fiingate\
├── FS_Extract.py                    # Streamlit version (root level) - ACTIVE
├── simple_app.py, simple_run.py     # Flask version (root level) - ACTIVE
├── templates/index.html              # Flask template (root level) - ACTIVE
├── static/background/DC.png          # Dragon Capital background - ACTIVE
└── Web-FS-Fingate/                  # Nested directory with duplicates
    ├── FS_Extract*.py                # Multiple Streamlit variants
    ├── simple_app.py, simple_run.py # Flask version (nested)
    ├── templates/index.html          # Flask template (nested)
    └── static/background/DC.png     # Static assets (nested)
```

### Application Entry Points by Priority
1. **simple_run.py + simple_app.py**: Primary Flask application with rich UI and Dragon Capital branding
2. **FS_Extract.py**: Streamlit application with Dragon Capital styling
3. **run.py + app.py**: Legacy Flask versions
4. **alternative_server.py, basic_server.py**: Fallback servers for troubleshooting

### Working Directory Sensitivity
Flask applications look for templates and static files relative to the working directory:
- **Running from `D:\Web_FS_Fiingate\`**: Uses root-level templates (RECOMMENDED)
- **Running from `D:\Web_FS_Fiingate\Web-FS-Fingate\`**: Uses nested templates

### Static Assets and Templates
- **templates/index.html**: Complete SPA with Dragon Capital styling, number formatting, and Chart.js
- **static/background/DC.png**: Dragon Capital logo for background
- **Deployment Configuration**: Procfile, runtime.txt (Python 3.11.8), requirements.txt

## Critical Implementation Details

### Number Formatting (FIXED)
Both Flask and Streamlit versions now properly format numbers with comma separators:

#### Flask Version (JavaScript)
```javascript
function formatNumberWithCommas(value) {
    // Uses regex pattern for reliable comma insertion
    // Handles decimals with trailing zero removal
    // Preserves negative signs
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}
```

#### Streamlit Version (Python)
```python
df_formatted[col] = df_formatted[col].apply(
    lambda x: f"{x:,.2f}".rstrip('0').rstrip('.') if pd.notnull(x) else ""
)
```

### Dragon Capital Branding (APPLIED)
Both versions now use consistent Dragon Capital styling:

#### Color Scheme
- **Primary Dark**: #0C4130 (dark green)
- **Primary Bright**: #08C179 (bright green)  
- **Accent**: #B78D51 (gold)

#### Flask Implementation
- Background gradient with DC.png image overlay
- Header titles with gradient text
- Button styling with Dragon Capital colors
- Table headers with gradient backgrounds

#### Streamlit Implementation
- Custom CSS applied via st.markdown with unsafe_allow_html=True
- Gradient backgrounds matching Flask version
- Button styling consistency

### Data Processing Compatibility
- **BeautifulSoup**: Uses html.parser (built-in) for cloud compatibility
- **Pandas Integration**: Streamlit version uses pandas, Flask has manual fallbacks
- **Number Detection**: Fixed logic ensures string numbers are properly formatted
- **Excel Export**: xlsxwriter engine for both versions

### Chart.js Integration (Flask Only)
- Revenue/profit visualization with growth calculations
- Margin analysis with separate line charts
- Error handling for CDN failures
- Dynamic data extraction from processed tables

### Google Drive Download Robustness
Three-tier fallback system:
1. Direct gdown download with export=download
2. Alternative gdown method without export parameter  
3. Fallback error handling with user notification

## Current Deployment Status

### Active Deployments
- **Streamlit Cloud**: https://fsfingate.streamlit.app/ (Primary production)
- **Local Flask**: http://localhost:5000 (Development with rich UI)

### UI Feature Comparison
- **Flask Version**: Full Dragon Capital branding, Chart.js visualizations, advanced styling, number formatting
- **Streamlit Version**: Dragon Capital styling, number formatting, basic UI, Excel export

### Recent Fixes Applied
1. **Number Formatting**: Fixed isNumber detection logic, implemented reliable comma formatting
2. **Dragon Capital Branding**: Applied consistent color scheme and background across both platforms
3. **Cross-Platform Compatibility**: Ensured all fixes work in both Flask and Streamlit deployments

## Important Development Notes

### Template Editing
When editing Flask templates, ensure changes are made to the **root-level** `templates/index.html` as this is the active version when running from the recommended working directory.

### Static File Management
Dragon Capital background image must be present at both:
- `static/background/DC.png` (root level - active)
- `Web-FS-Fingate/static/background/DC.png` (nested - backup)

### Number Formatting Function
The Flask version uses a custom JavaScript function `formatNumberWithCommas()` that:
- Uses regex for reliable comma insertion across all browsers/locales
- Handles decimal preservation and trailing zero removal
- Maintains negative number formatting
- Is more robust than relying on `toLocaleString()`

### Streamlit Styling
Custom CSS is injected via `st.markdown()` with `unsafe_allow_html=True` to maintain Dragon Capital branding consistency with the Flask version.