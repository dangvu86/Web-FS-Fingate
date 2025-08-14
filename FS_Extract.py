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
st.title("FS Fingate")

# Hàm tải file ZIP từ Google Drive

def download_zip_from_drive(file_id):
    """Download ZIP file from Google Drive with multiple fallback methods"""
    
    # Method 1: Try gdown with direct download
    try:
        url = f"https://drive.google.com/uc?id={file_id}&export=download"
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_file:
            st.info(f"Đang tải file từ Google Drive...")
            gdown.download(url, tmp_file.name, quiet=False)
            
            if os.path.getsize(tmp_file.name) > 0:
                with open(tmp_file.name, "rb") as f:
                    content = f.read()
                os.unlink(tmp_file.name)  # Clean up
                return BytesIO(content)
    except Exception as e:
        st.warning(f"Method 1 failed: {e}")
    
    # Method 2: Try alternative gdown approach
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_file:
            st.info(f"Thử phương pháp thay thế...")
            gdown.download(f"https://drive.google.com/file/d/{file_id}/view?usp=sharing", 
                          tmp_file.name, quiet=False, fuzzy=True)
            
            if os.path.getsize(tmp_file.name) > 0:
                with open(tmp_file.name, "rb") as f:
                    content = f.read()
                os.unlink(tmp_file.name)  # Clean up
                return BytesIO(content)
    except Exception as e:
        st.warning(f"Method 2 failed: {e}")
    
    # Method 3: Direct requests approach
    try:
        import requests
        session = requests.Session()
        
        st.info("Thử tải trực tiếp...")
        
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
        st.error(f"Method 3 failed: {e}")
    
    st.error("Không thể tải file từ Google Drive. Vui lòng kiểm tra file ID và quyền truy cập.")
    return None


# Hàm trích xuất bảng từ HTML
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
            return f"Lỗi khi đọc bảng: {e}"
    return "Không tìm thấy bảng nào trong file HTML."

# ID của file ZIP trên Google Drive
drive_file_id = "1A0yeEBAvLkX64PlatHboPAHhHVIcJICw"

# Tải file ZIP
st.info("🔄 Đang tải dữ liệu tài chính mặc định...")
uploaded_file = download_zip_from_drive(drive_file_id)

html_tables = {}

# Xử lý file ZIP
if uploaded_file is not None:
    st.success("✅ Tải file thành công!")
    st.info("📊 Đang xử lý dữ liệu...")
else:
    st.error("❌ Không thể tải file. Vui lòng thử lại sau.")
    st.stop()

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
                    df_formatted[col] = df_formatted[col].apply(lambda x: f"{int(x):,}" if pd.notnull(x) else "")
                df_formatted.columns = df_formatted.columns.map(str)
                styles = [{'selector': 'th', 'props': [('text-align', 'center')]}]
                styles.append({'selector': 'td.col0', 'props': [('text-align', 'left')]} )
                for i in range(1, len(df_formatted.columns)):
                    styles.append({'selector': f'td.col{i}', 'props': [('text-align', 'right')]} )
                styled_table = df_formatted.style.set_table_styles(styles).set_table_attributes('style="font-size:12px;"')
                st.markdown(styled_table.to_html(), unsafe_allow_html=True)
            else:
                st.error(table)
else:
    st.info("Không tìm thấy bảng nào trong file ZIP hoặc lỗi khi xử lý file.")