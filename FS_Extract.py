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
                for col in df_formatted.select_dtypes(include='number').columns:
                    df_formatted[col] = df_formatted[col].apply(lambda x: f"{x:,.2f}".rstrip('0').rstrip('.') if pd.notnull(x) else "")
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
                
                # Create HTML table with enhanced styling for Streamlit Cloud compatibility
                html_table = '<div><table class="custom-table">'
                
                # Header row with Dragon Capital styling
                html_table += '<thead><tr>'
                for col in df_formatted.columns:
                    html_table += f'<th>{col}</th>'
                html_table += '</tr></thead><tbody>'
                
                # Data rows with special styling for Audit Status
                for idx, row in df_formatted.iterrows():
                    first_cell = str(row.iloc[0]) if pd.notnull(row.iloc[0]) else ""
                    is_audit_status = 'audit status' in first_cell.lower()
                    
                    row_class = 'audit-status-row' if is_audit_status else ''
                    html_table += f'<tr class="{row_class}">'
                    
                    for i, cell in enumerate(row):
                        cell_value = str(cell) if pd.notnull(cell) else ""
                        col_class = 'first-col' if i == 0 else 'number-col'
                        html_table += f'<td class="{col_class}">{cell_value}</td>'
                    html_table += '</tr>'
                
                html_table += '</tbody></table></div>'
                st.markdown(html_table, unsafe_allow_html=True)
            else:
                st.error(table)
else:
    st.info("Không tìm thấy bảng nào trong file ZIP hoặc lỗi khi xử lý file.")