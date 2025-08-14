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
        # Method 1: Try pandas read_html with different parsers
        for parser in ['lxml', 'html5lib', 'html.parser']:
            try:
                df = pd.read_html(StringIO(str(tables[0])), flavor=parser)[0]
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = [' '.join(map(str, col)).strip() for col in df.columns]
                
                # Clean data
                df.iloc[0, 0] = str(df.iloc[0, 0]).replace('.', '').replace(')', '').replace('(', '-').replace(',', '')
                for col in df.columns[1:]:
                    df[col] = df[col].astype(str).str.replace('.', '', regex=False)
                    df[col] = df[col].astype(str).str.replace(')', '', regex=False)
                    df[col] = df[col].astype(str).str.replace('(', '-', regex=False)
                    df[col] = df[col].astype(str).str.replace(',', '', regex=False)
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                return df
            except Exception as e:
                continue
        
        # Method 2: Manual parsing with BeautifulSoup as fallback
        try:
            table = tables[0]
            rows = table.find_all("tr")
            
            table_data = []
            headers = []
            
            for i, row in enumerate(rows):
                cells = row.find_all(["th", "td"])
                row_data = []
                for cell in cells:
                    text = cell.get_text(strip=True)
                    # Clean the data
                    text = text.replace('.', '').replace(')', '').replace('(', '-').replace(',', '')
                    row_data.append(text)
                
                if i == 0:  # Header row
                    headers = row_data
                else:
                    table_data.append(row_data)
            
            if headers and table_data:
                df = pd.DataFrame(table_data, columns=headers)
                
                # Convert numeric columns
                for col in df.columns[1:]:  # Skip first column (descriptions)
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                
                return df
            else:
                return "Không thể parse table structure"
                
        except Exception as e:
            return f"Lỗi manual parsing: {e}"
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
            all_files = zip_ref.namelist()
            st.info(f"📁 Tìm thấy {len(all_files)} files trong ZIP: {', '.join(all_files[:5])}{'...' if len(all_files) > 5 else ''}")
            
            html_files = [f for f in all_files if f.lower().endswith(".html")]
            st.info(f"📄 Tìm thấy {len(html_files)} HTML files: {', '.join(html_files)}")
            
            if not html_files:
                st.warning("⚠️ Không tìm thấy file HTML nào trong ZIP.")
                st.info("Danh sách tất cả files:")
                for f in all_files:
                    st.write(f"- {f}")
            
            for html_file in html_files:
                st.info(f"🔄 Đang xử lý {html_file}...")
                with zip_ref.open(html_file) as file:
                    html_content = file.read().decode("utf-8")
                    result = extract_tables_from_html(html_content)
                    html_tables[html_file] = result
                    
                    if isinstance(result, pd.DataFrame):
                        st.success(f"✅ Xử lý thành công {html_file} - {len(result)} rows")
                    else:
                        st.warning(f"⚠️ {html_file}: {result}")
                        
    except zipfile.BadZipFile:
        st.error("File tải về không phải là file ZIP hợp lệ.")
    except Exception as e:
        st.error(f"Lỗi khi xử lý ZIP file: {e}")
else:
    st.info("Không thể tải file ZIP từ Google Drive.")

# Hiển thị và xuất bảng
st.info(f"📊 Tổng số bảng được xử lý: {len(html_tables)}")

if html_tables:
    st.success("🎉 Tìm thấy dữ liệu! Đang hiển thị bảng...")
else:
    st.error("❌ Không tìm thấy bảng dữ liệu nào.")
    st.info("Có thể nguyên nhân:")
    st.write("- File ZIP không chứa file HTML")
    st.write("- File HTML không có bảng dữ liệu")
    st.write("- Lỗi trong quá trình xử lý")
    st.stop()

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

    tabs = st.tabs([name.replace('.html', '').upper() for name in html_tables.keys()])
    for tab, name in zip(tabs, html_tables.keys()):
        with tab:
            table = html_tables[name]
            if isinstance(table, pd.DataFrame):
                # Display table info
                st.info(f"📊 {name.replace('.html', '')} - {len(table)} rows x {len(table.columns)} columns")
                
                # Create formatted dataframe
                df_display = table.copy()
                
                # Format numeric columns with proper alignment
                column_config = {}
                for col in df_display.columns:
                    if col == df_display.columns[0]:  # First column (descriptions)
                        column_config[col] = st.column_config.TextColumn(
                            col,
                            help="Financial metrics",
                            width="large"
                        )
                    else:  # Numeric columns
                        if df_display[col].dtype in ['int64', 'float64']:
                            column_config[col] = st.column_config.NumberColumn(
                                col,
                                help="Financial data",
                                format="%.0f"
                            )
                        else:
                            column_config[col] = st.column_config.TextColumn(col)
                
                # Display with st.dataframe for better formatting
                st.dataframe(
                    df_display,
                    column_config=column_config,
                    use_container_width=True,
                    hide_index=True
                )
                
                # Add summary statistics
                numeric_cols = df_display.select_dtypes(include=['int64', 'float64']).columns
                if len(numeric_cols) > 1:
                    st.subheader("📈 Key Metrics")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    # Find revenue row
                    revenue_row = None
                    for idx, row in df_display.iterrows():
                        first_cell = str(row.iloc[0]).lower()
                        if 'revenue' in first_cell and 'net' in first_cell:
                            revenue_row = idx
                            break
                    
                    if revenue_row is not None:
                        latest_year = numeric_cols[-1]  # Last column
                        prev_year = numeric_cols[-2] if len(numeric_cols) > 1 else None
                        
                        latest_revenue = df_display.iloc[revenue_row][latest_year]
                        with col1:
                            st.metric(
                                label="Latest Revenue",
                                value=f"{latest_revenue/1e9:.1f}B VND" if pd.notnull(latest_revenue) else "N/A"
                            )
                        
                        if prev_year is not None:
                            prev_revenue = df_display.iloc[revenue_row][prev_year]
                            if pd.notnull(prev_revenue) and pd.notnull(latest_revenue) and prev_revenue != 0:
                                growth = ((latest_revenue - prev_revenue) / abs(prev_revenue)) * 100
                                with col2:
                                    st.metric(
                                        label="Revenue Growth",
                                        value=f"{growth:.1f}%",
                                        delta=f"{growth:.1f}%"
                                    )
                    
                    # Find profit row
                    profit_row = None
                    for idx, row in df_display.iterrows():
                        first_cell = str(row.iloc[0]).lower()
                        if 'net profit' in first_cell and 'after tax' in first_cell:
                            profit_row = idx
                            break
                    
                    if profit_row is not None:
                        latest_profit = df_display.iloc[profit_row][latest_year]
                        with col3:
                            st.metric(
                                label="Latest Net Profit",
                                value=f"{latest_profit/1e9:.1f}B VND" if pd.notnull(latest_profit) else "N/A"
                            )
                            
            else:
                st.error(f"❌ Error processing {name}: {table}")
else:
    st.info("Không tìm thấy bảng nào trong file ZIP hoặc lỗi khi xử lý file.")