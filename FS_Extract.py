from io import StringIO, BytesIO
import streamlit as st
from bs4 import BeautifulSoup
import pandas as pd
import zipfile
import gdown
import tempfile
import os

# Cấu hình giao diện
st.set_page_config(layout="wide")

# Dragon Capital styling
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0C4130 0%, #08C179 100%);
    }
    .main .block-container {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem;
        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
    }
    h1 {
        background: linear-gradient(135deg, #0C4130 0%, #08C179 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 800;
        text-align: center;
    }
    .stButton > button {
        background: linear-gradient(135deg, #08C179 0%, #0C4130 100%);
        color: white;
        border: none;
        border-radius: 12px;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(8, 193, 121, 0.3);
    }
    .stDownloadButton > button {
        background: linear-gradient(135deg, #08C179 0%, #0C4130 100%);
        color: white;
        border: none;
        border-radius: 12px;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(8, 193, 121, 0.3);
    }
    /* Dragon Capital table styling with !important for Streamlit Cloud */
    .custom-table {
        border-collapse: collapse !important;
        width: 100% !important;
        margin: 1rem 0 !important;
        font-family: 'Arial', sans-serif !important;
        font-size: 11px !important;
    }
    .custom-table th {
        background: linear-gradient(135deg, #0C4130 0%, #08C179 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 8px !important;
        text-align: center !important;
        border: 1px solid #ddd !important;
        font-size: 11px !important;
    }
    .custom-table td {
        padding: 6px !important;
        border: 1px solid #ddd !important;
        background: white !important;
        font-size: 11px !important;
    }
    .custom-table .first-col {
        text-align: left !important;
        font-weight: 500 !important;
    }
    .custom-table .number-col {
        text-align: right !important;
    }
    .custom-table .audit-status-row td {
        background: linear-gradient(135deg, #0C4130 0%, #08C179 100%) !important;
        color: white !important;
        font-weight: 600 !important;
    }
    .custom-table .audit-status-row {
        background: linear-gradient(135deg, #0C4130 0%, #08C179 100%) !important;
    }
    /* Override Streamlit default table styling */
    .stMarkdown table {
        border-collapse: collapse !important;
    }
    .stMarkdown th {
        background: linear-gradient(135deg, #0C4130 0%, #08C179 100%) !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("FS Fingate")

# Hàm tải file ZIP từ Google Drive

def download_zip_from_drive(file_id):
    try:
        url = f"https://drive.google.com/uc?id={file_id}"
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_file:
            gdown.download(url, tmp_file.name, quiet=False)
            with open(tmp_file.name, "rb") as f:
                return BytesIO(f.read())
    except Exception as e:
        st.error(f"Lỗi khi tải file từ Google Drive: {e}")
        return None


# Hàm trích xuất bảng từ HTML
def extract_tables_from_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    tables = soup.find_all("table")
    if tables:
        try:
            df = pd.read_html(StringIO(str(tables[0])))[0]
            if isinstance(df.columns, pd.MultiIndex):
                # Handle MultiIndex properly - only take the first level if second level has unwanted text
                new_columns = []
                for col in df.columns:
                    if len(col) > 1:
                        # If second level contains Legal Regulation or Audit Status, only use first level
                        second_level = str(col[1]).strip().lower()
                        if 'legal regulation' in second_level or 'audit status' in second_level or second_level == 'nan':
                            new_columns.append(str(col[0]).strip())
                        else:
                            new_columns.append(' '.join(map(str, col)).strip())
                    else:
                        new_columns.append(str(col[0]).strip())
                df.columns = new_columns
            df.iloc[0, 0] = str(df.iloc[0, 0]).replace('.', '').replace(')', '').replace('(', '-').replace(',', '')
            for col in df.columns[1:]:
                df[col] = df[col].astype(str).str.replace('.', '', regex=False)
                df[col] = df[col].astype(str).str.replace(')', '', regex=False)
                df[col] = df[col].astype(str).str.replace('(', '-', regex=False)
                df[col] = df[col].astype(str).str.replace(',', '', regex=False)
                df[col] = pd.to_numeric(df[col], errors="coerce")
            return df
        except Exception as e:
            return f"Lỗi khi đọc bảng: {e}"
    return "Không tìm thấy bảng nào trong file HTML."

def create_growth_analysis_rows(df):
    """Create growth analysis rows for revenue, profit, and margins"""
    if df.empty or len(df) < 2:
        return ""
    
    # Find numeric columns (exclude first column)
    numeric_cols = []
    for col in df.columns[1:]:
        if df[col].dtype in ['int64', 'float64'] or pd.api.types.is_numeric_dtype(df[col]):
            numeric_cols.append(col)
    
    if len(numeric_cols) < 2:
        return ""
    
    growth_html = ""
    
    # 1. Net Revenue Growth
    revenue_row = None
    for idx, row in df.iterrows():
        first_cell = str(row.iloc[0]).lower()
        if 'net revenue' in first_cell or ('revenue' in first_cell and 'net' in first_cell):
            revenue_row = idx
            break
    
    if revenue_row is not None:
        growth_html += create_growth_row_html(df, revenue_row, numeric_cols, "Net Revenue Growth (%)", "revenue")
    
    # 2. Gross Profit Growth
    gross_profit_row = None
    for idx, row in df.iterrows():
        first_cell = str(row.iloc[0]).lower()
        if 'gross profit' in first_cell:
            gross_profit_row = idx
            break
    
    if gross_profit_row is not None:
        growth_html += create_growth_row_html(df, gross_profit_row, numeric_cols, "Gross Profit Growth (%)", "gross_profit")
    
    # 3. Net Profit Growth
    net_profit_row = None
    for idx, row in df.iterrows():
        first_cell = str(row.iloc[0]).lower()
        if 'net profit' in first_cell and 'after tax' in first_cell:
            net_profit_row = idx
            break
    
    if net_profit_row is not None:
        growth_html += create_growth_row_html(df, net_profit_row, numeric_cols, "Net Profit Growth (%)", "net_profit")
    
    # 4. Gross Margin
    if revenue_row is not None and gross_profit_row is not None:
        growth_html += create_margin_row_html(df, revenue_row, gross_profit_row, numeric_cols, "Gross Margin (%)")
    
    # 5. Net Margin  
    if revenue_row is not None and net_profit_row is not None:
        growth_html += create_margin_row_html(df, revenue_row, net_profit_row, numeric_cols, "Net Margin (%)")
    
    return growth_html

def create_growth_row_html(df, row_idx, numeric_cols, label, metric_type):
    """Create a growth row for a specific metric"""
    html = '<tr style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-top: 2px solid #0C4130;">'
    
    # First column - label
    icon = "📈" if metric_type == "revenue" else "💰"
    html += f'<td class="first-col" style="font-weight: 700; color: #0C4130;">{icon} {label}</td>'
    
    # Get values for this row
    values = []
    for col in numeric_cols:
        val = df.iloc[row_idx][col]
        values.append(val if pd.notnull(val) else 0)
    
    # Calculate growth for each year (skip first year)
    for i, col in enumerate(numeric_cols):
        if i == 0:
            # First year - no growth data
            html += '<td class="number-col"></td>'
        else:
            current = values[i]
            previous = values[i-1]
            
            if metric_type in ["gross_profit", "net_profit"]:
                # Special profit growth logic
                growth_display = calculate_profit_growth_display(current, previous)
            else:
                # Standard revenue growth
                growth_display = calculate_revenue_growth_display(current, previous)
            
            html += f'<td class="number-col" style="font-weight: 600;">{growth_display}</td>'
    
    html += '</tr>'
    return html

def create_margin_row_html(df, revenue_row_idx, profit_row_idx, numeric_cols, label):
    """Create a margin analysis row"""
    html = '<tr style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-top: 2px solid #0C4130;">'
    
    # First column - label
    html += f'<td class="first-col" style="font-weight: 700; color: #0C4130;">📊 {label}</td>'
    
    # Calculate margin for each year
    for col in numeric_cols:
        revenue = df.iloc[revenue_row_idx][col]
        profit = df.iloc[profit_row_idx][col]
        
        if pd.notnull(revenue) and pd.notnull(profit) and revenue != 0:
            margin = (profit / revenue * 100)
            if margin < 0:
                html += f'<td class="number-col" style="font-weight: 600; color: #dc3545;">-{abs(margin):.1f}%</td>'
            else:
                color = "#28a745" if margin > 0 else "#6c757d"
                html += f'<td class="number-col" style="font-weight: 600; color: {color};">{margin:.1f}%</td>'
        else:
            html += '<td class="number-col">-</td>'
    
    html += '</tr>'
    return html

def calculate_revenue_growth_display(current, previous):
    """Calculate standard revenue growth percentage"""
    if previous == 0:
        return '<span style="color: #6c757d;">-</span>'
    
    growth = ((current - previous) / abs(previous)) * 100
    color = "#28a745" if growth >= 0 else "#dc3545"
    arrow = "↗" if growth >= 0 else "↘"
    
    return f'<span style="color: {color};">{arrow} {growth:.1f}%</span>'

def calculate_profit_growth_display(current, previous):
    """Calculate profit growth with LTP/PTL logic"""
    prev_is_profit = previous > 0
    curr_is_profit = current > 0
    
    if not prev_is_profit and curr_is_profit:
        # Loss to Profit
        return '<span style="color: #28a745;">↗ LTP</span>'
    elif prev_is_profit and not curr_is_profit:
        # Profit to Loss
        return '<span style="color: #dc3545;">↘ PTL</span>'
    elif not prev_is_profit and not curr_is_profit:
        # Both years loss
        return '<span style="color: #ffc107;">━ Loss</span>'
    elif previous == 0:
        return '<span style="color: #6c757d;">-</span>'
    else:
        # Both years profit - normal calculation
        growth = ((current - previous) / abs(previous)) * 100
        color = "#28a745" if growth >= 0 else "#dc3545"
        arrow = "↗" if growth >= 0 else "↘"
        return f'<span style="color: {color};">{arrow} {growth:.1f}%</span>'

# ID của file ZIP trên Google Drive
drive_file_id = "1A0yeEBAvLkX64PlatHboPAHhHVIcJICw"

# Tải file ZIP
uploaded_file = download_zip_from_drive(drive_file_id)

html_tables = {}

# Xử lý file ZIP
if uploaded_file is not None:
    try:
        with zipfile.ZipFile(uploaded_file, "r") as zip_ref:
            html_files = [f for f in zip_ref.namelist() if f.lower().endswith(".html")]
            for html_file in html_files:
                with zip_ref.open(html_file) as file:
                    html_content = file.read().decode("utf-8")
                    result = extract_tables_from_html(html_content)
                    html_tables[html_file] = result
    except zipfile.BadZipFile:
        st.error("File tải về không phải là file ZIP hợp lệ.")
else:
    st.info("Không thể tải file ZIP từ Google Drive.")

# Hiển thị và xuất bảng
if html_tables:
    output_all = BytesIO()
    with pd.ExcelWriter(output_all, engine='xlsxwriter') as writer:
        for name, df in html_tables.items():
            if isinstance(df, pd.DataFrame):
                sheet_name = name[:31]
                df.to_excel(writer, index=False, sheet_name=sheet_name)
                workbook = writer.book
                worksheet = writer.sheets[sheet_name]
                for i, col in enumerate(df.columns):
                    column_len = max(df[col].astype(str).map(len).max(), len(str(col))) + 2
                    align_format = workbook.add_format({'align': 'left' if i == 0 else 'right'})
                    worksheet.set_column(i, i, column_len, align_format)
    output_all.seek(0)

    top_col1, top_col2 = st.columns([5, 1])
    with top_col2:
        st.download_button(
            label="📥 Tải tất cả bảng",
            data=output_all.getvalue(),
            file_name="all_tables.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    tabs = st.tabs(list(html_tables.keys()))
    for tab, name in zip(tabs, html_tables.keys()):
        with tab:
            table = html_tables[name]
            if isinstance(table, pd.DataFrame):
                df_formatted = table.copy()
                # Remove Legal Regulation row if exists
                if not df_formatted.empty and len(df_formatted) > 0:
                    legal_reg_mask = df_formatted.iloc[:, 0].astype(str).str.contains('Legal Regulation', case=False, na=False)
                    df_formatted = df_formatted[~legal_reg_mask]
                
                df_formatted.columns = df_formatted.columns.map(str)
                
                # Clean column names - extract only date part from long strings
                import re
                clean_columns = []
                for col in df_formatted.columns:
                    col_str = str(col).strip()
                    if col_str == "Fiscal Year End":
                        clean_columns.append(col_str)
                    else:
                        # Extract date part (format: 31-Dec-YYYY) from the beginning
                        date_match = re.match(r'(\d{1,2}-[A-Za-z]{3}-\d{4})', col_str)
                        if date_match:
                            clean_columns.append(date_match.group(1))
                        else:
                            clean_columns.append(col_str)
                
                df_formatted.columns = clean_columns
                
                # Create a copy for growth analysis before formatting numbers as strings
                df_for_growth = df_formatted.copy()
                
                # Create HTML table with enhanced styling for Streamlit Cloud compatibility
                html_table = '<div><table class="custom-table">'
                
                # Header row with Dragon Capital styling
                html_table += '<thead><tr>'
                for col in df_formatted.columns:
                    html_table += f'<th>{col}</th>'
                html_table += '</tr></thead><tbody>'
                
                # Data rows with special styling for Audit Status and number formatting
                for idx, row in df_formatted.iterrows():
                    first_cell = str(row.iloc[0]) if pd.notnull(row.iloc[0]) else ""
                    is_audit_status = 'audit status' in first_cell.lower()
                    
                    row_class = 'audit-status-row' if is_audit_status else ''
                    html_table += f'<tr class="{row_class}">'
                    
                    for i, cell in enumerate(row):
                        if i == 0:
                            # First column - keep as text
                            cell_value = str(cell) if pd.notnull(cell) else ""
                        else:
                            # Numeric columns - format with commas
                            if pd.notnull(cell) and isinstance(cell, (int, float)):
                                cell_value = f"{cell:,.2f}".rstrip('0').rstrip('.')
                            else:
                                cell_value = str(cell) if pd.notnull(cell) else ""
                        
                        col_class = 'first-col' if i == 0 else 'number-col'
                        html_table += f'<td class="{col_class}">{cell_value}</td>'
                    html_table += '</tr>'
                
                # Add growth analysis rows using the numeric dataframe
                growth_rows_html = create_growth_analysis_rows(df_for_growth)
                html_table += growth_rows_html
                
                html_table += '</tbody></table></div>'
                st.markdown(html_table, unsafe_allow_html=True)
            else:
                st.error(table)
else:
    st.info("Không tìm thấy bảng nào trong file ZIP hoặc lỗi khi xử lý file.")