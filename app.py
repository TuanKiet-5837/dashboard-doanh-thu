# app.py (Phiên bản cuối cùng - Đã bao gồm đổi tên cột + 3 nâng cấp)

import streamlit as st
import pandas as pd
import plotly.express as px
import re  # Thư viện để xử lý văn bản

# --- PHẦN 1: LOGIC ĐỔI TÊN CỘT "THÔNG MINH" (Phần bạn đang cần) ---

# --- 1.1. HÀM CHUẨN HÓA TÊN CỘT ---
def simple_normalize(col_name):
    """
    Hàm này "sơ chế" tên cột:
    1. Chuyển thành chữ thường.
    2. Bỏ dấu tiếng Việt.
    3. Thay thế khoảng trắng, dấu chấm, gạch ngang bằng dấu gạch dưới '_'.
    """
    if col_name is None:
        return None
    normalized = str(col_name).lower()
    # 2. Bỏ dấu tiếng Việt
    normalized = re.sub(r'[àáạảãâầấậẩẫăằắặẳẵ]', 'a', normalized)
    normalized = re.sub(r'[èéẹẻẽêềếệểễ]', 'e', normalized)
    normalized = re.sub(r'[òóọỏõôồốộổỗơờớợởỡ]', 'o', normalized)
    normalized = re.sub(r'[ìíịỉĩ]', 'i', normalized)
    normalized = re.sub(r'[ùúụủũưừứựửữ]', 'u', normalized)
    normalized = re.sub(r'[ỳýỵỷỹ]', 'y', normalized)
    normalized = re.sub(r'[đ]', 'd', normalized)
    # 3. Thay thế các ký tự phân cách
    normalized = re.sub(r'[\s\.-]+', '_', normalized)
    # 4. Xóa các ký tự đặc biệt còn lại
    normalized = re.sub(r'[^a-z0-9_]', '', normalized)
    return normalized.strip('_')

# --- 1.2. DANH SÁCH CÁC CỘT "CHUẨN" MÀ CHÚNG TA MUỐN ---
CANONICAL_COLUMNS = [
    'ngay_dat_hang',
    'ma_don_hang',
    'ten_san_pham',
    'danh_muc',
    'so_luong',
    'don_gia',
    'chi_phi'
]

# --- 1.3. BẢN ĐỒ ÁNH XẠ (MAPPING) ---
# Dạy cho máy tính biết các tên biến thể
COLUMN_MAP = {
    # Các biến thể của 'ngay_dat_hang'
    'ngay_dat_hang': 'ngay_dat_hang',
    'ngay_dat': 'ngay_dat_hang',
    'ngaydat_hang': 'ngay_dat_hang',
    'ngay_hang': 'ngay_dat_hang',
    'order_date': 'ngay_dat_hang',
    
    # Các biến thể của 'ma_don_hang'
    'ma_don_hang': 'ma_don_hang',
    'ma_don': 'ma_don_hang',
    'madon_hang': 'ma_don_hang',
    'order_id': 'ma_don_hang',
    'ma_dh': 'ma_don_hang',
    
    # Các biến thể của 'ten_san_pham'
    'ten_san_pham': 'ten_san_pham',
    'ten_sp': 'ten_san_pham',
    'tensan_pham': 'ten_san_pham',
    'product_name': 'ten_san_pham',
    
    # Các biến thể của 'danh_muc'
    'danh_muc': 'danh_muc',
    'category': 'danh_muc',
    'phan_loai': 'danh_muc',
    
    # Các biến thể của 'so_luong'
    'so_luong': 'so_luong',
    'soluong': 'so_luong',
    'quantity': 'so_luong',
    'sl': 'so_luong',
    
    # Các biến thể của 'don_gia'
    'don_gia': 'don_gia',
    'dongia': 'don_gia',
    'gia_ban': 'don_gia',
    'price': 'don_gia',
    
    # Các biến thể của 'chi_phi'
    'chi_phi': 'chi_phi',
    'chiphi': 'chi_phi',
    'gia_von': 'chi_phi',
    'cost': 'chi_phi',
    'gia_goc': 'chi_phi'
}

# --- 1.4. HÀM ĐỔI TÊN VÀ KIỂM TRA ---
def rename_and_validate(df):
    """
    Hàm này tự động đổi tên các cột của file tải lên theo tên "chuẩn"
    và kiểm tra xem có bị thiếu cột nào không.
    """
    original_cols = df.columns
    new_cols = []
    
    for col in original_cols:
        # 1. Chuẩn hóa tên cột
        normalized_col = simple_normalize(col)
        # 2. Tìm tên "chuẩn" trong bản đồ
        canonical_name = COLUMN_MAP.get(normalized_col)
        
        if canonical_name:
            new_cols.append(canonical_name)
        else:
            new_cols.append(normalized_col)
    
    # 3. Áp dụng tên mới cho DataFrame
    df.columns = new_cols
    
    # 4. Kiểm tra xem có thiếu cột "chuẩn" nào không
    uploaded_columns = set(df.columns)
    required_columns = set(CANONICAL_COLUMNS)
    
    if required_columns.issubset(uploaded_columns):
        return True, None # Hợp lệ!
    else:
        missing_columns = list(required_columns - uploaded_columns)
        return False, missing_columns

# --- (Hết phần logic đổi tên) ---


# --- HÀM TÍNH TOÁN (Sử dụng tên cột "chuẩn") ---
def calculate_metrics(df):
    df['ngay_dat_hang'] = pd.to_datetime(df['ngay_dat_hang'])
    df['so_luong'] = pd.to_numeric(df['so_luong'])
    df['don_gia'] = pd.to_numeric(df['don_gia'])
    df['chi_phi'] = pd.to_numeric(df['chi_phi'])

    df['doanh_thu'] = df['so_luong'] * df['don_gia']
    df['loi_nhuan'] = df['doanh_thu'] - (df['so_luong'] * df['chi_phi'])
    return df

# --- HÀM DÀNH CHO NÚT TẢI XUỐNG ---
@st.cache_data
def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8-sig')


# --- GIAO DIỆN CHÍNH ---
st.set_page_config(
    page_title="Dashboard Phân Tích Doanh Thu",
    page_icon="💰",
    layout="wide"
)
st.title("💰 Dashboard Phân Tích Doanh Thu")
st.markdown("---")

# --- THANH BÊN (SIDEBAR) ---
st.sidebar.image("https://www.oneclickitsolutions.com/wp-content/uploads/2022/12/Data-Analytics-1.png")
st.sidebar.header("Tải Lên File Của Bạn")
uploaded_file = st.sidebar.file_uploader("Chọn file Excel hoặc CSV", type=["xlsx", "csv"])

if uploaded_file is not None:
    try:
        # Đọc file
        if uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file, engine='openpyxl')
        else:
            df = pd.read_csv(uploaded_file)
        
        # --- BƯỚC QUAN TRỌNG: TỰ ĐỘNG ĐỔI TÊN VÀ KIỂM TRA ---
        is_valid, missing_or_duplicate_cols = rename_and_validate(df)
        
        if is_valid:
            df = calculate_metrics(df)

            st.sidebar.header("Bộ Lọc:")
            
            # --- BỘ LỌC (Sử dụng tên cột "chuẩn") ---
            category = st.sidebar.multiselect(
                "Chọn Danh Mục:",
                options=df["danh_muc"].unique(),
                default=df["danh_muc"].unique()
            )

            min_date = df["ngay_dat_hang"].min().date()
            max_date = df["ngay_dat_hang"].max().date()
            date_range = st.sidebar.date_input(
                "Chọn Khoảng Thời Gian:",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
            
            start_date = pd.to_datetime(date_range[0])
            end_date = pd.to_datetime(date_range[1])

            # Áp dụng bộ lọc (Sử dụng tên cột "chuẩn")
            df_selection = df.query(
                "danh_muc == @category & ngay_dat_hang >= @start_date & ngay_dat_hang <= @end_date"
            )
            
            if df_selection.empty:
                st.warning("Không có dữ liệu nào phù hợp với bộ lọc của bạn!")
            else:
                # --- TÍNH TOÁN CÁC CHỈ SỐ KPI ---
                total_revenue = int(df_selection["doanh_thu"].sum())
                total_profit = int(df_selection["loi_nhuan"].sum())
                total_orders = df_selection["ma_don_hang"].nunique()
                
                # --- NÂNG CẤP 1: TÍNH TOÁN THÊM 2 KPI MỚI ---
                if total_orders > 0:
                    average_order_value = total_revenue / total_orders
                else:
                    average_order_value = 0
                
                if total_revenue > 0:
                    profit_margin = (total_profit / total_revenue) * 100
                else:
                    profit_margin = 0

                st.markdown("### 📈 Các Chỉ Số Chính")
                col1, col2, col3 = st.columns(3)
                col4, col5 = st.columns(2)
                
                # ... (Phần code HTML cho thẻ KPI giữ nguyên) ...
                with col1:
                    st.markdown(f"""
                    <div style="padding: 15px; border-radius: 10px; border: 2px solid #262730; background-color: #0E1117;">
                        <h5 style="text-align: center; color: #FAFAFA;">Tổng Doanh Thu</h5>
                        <h3 style="text-align: center; color: #61dafb;">₫ {total_revenue:,}</h3>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.markdown(f"""
                    <div style="padding: 15px; border-radius: 10px; border: 2px solid #262730; background-color: #0E1117;">
                        <h5 style="text-align: center; color: #FAFAFA;">Tổng Lợi Nhuận</h5>
                        <h3 style="text-align: center; color: #61dafb;">₫ {total_profit:,}</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with col3:
                    st.markdown(f"""
                    <div style="padding: 15px; border-radius: 10px; border: 2px solid #262730; background-color: #0E1117;">
                        <h5 style="text-align: center; color: #FAFAFA;">Tổng Số Đơn Hàng</h5>
                        <h3 style="text-align: center; color: #61dafb;">{total_orders}</h3>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    st.markdown(f"""
                    <div style="padding: 15px; border-radius: 10px; border: 2px solid #262730; background-color: #0E1117;">
                        <h5 style="text-align: center; color: #FAFAFA;">Giá trị ĐH Trung bình</h5>
                        <h3 style="text-align: center; color: #61dafb;">₫ {average_order_value:,.0f}</h3>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col5:
                    st.markdown(f"""
                    <div style="padding: 15px; border-radius: 10px; border: 2px solid #262730; background-color: #0E1117;">
                        <h5 style="text-align: center; color: #FAFAFA;">Tỷ Suất Lợi Nhuận</h5>
                        <h3 style="text-align: center; color: #61dafb;">{profit_margin:.1f} %</h3>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True) 

                # --- BIỂU ĐỒ (Sử dụng tên cột "chuẩn") ---
                
                # 1. BIỂU ĐỒ ĐƯỜNG
                revenue_by_date = df_selection.set_index('ngay_dat_hang').resample('D')['doanh_thu'].sum().reset_index()
                fig_revenue_over_time = px.line(
                    revenue_by_date, x="ngay_dat_hang", y="doanh_thu", title="<b>Doanh Thu Theo Thời Gian</b>"
                )
                fig_revenue_over_time.update_layout(plot_bgcolor="rgba(0,0,0,0)", xaxis=(dict(showgrid=False)))

                # 2. BIỂU ĐỒ CỘT
                sales_by_product = df_selection.groupby("ten_san_pham")["so_luong"].sum().sort_values(ascending=True).reset_index()
                fig_top_products = px.bar(
                    sales_by_product.tail(10), x="so_luong", y="ten_san_pham", orientation="h",
                    title="<b>Top 10 Sản Phẩm Bán Chạy Nhất</b>"
                )
                fig_top_products.update_layout(plot_bgcolor="rgba(0,0,0,0)", yaxis=dict(title=''))
                
                # 3. BIỂU ĐỒ TRÒN
                fig_pie_chart = px.pie(
                    df_selection,
                    names="danh_muc",
                    values="doanh_thu",
                    title="<b>Tỷ Trọng Doanh Thu Theo Danh Mục</b>"
                )
                fig_pie_chart.update_layout(plot_bgcolor="rgba(0,0,0,0)")
                
                # Sắp xếp lại bố cục biểu đồ
                st.plotly_chart(fig_revenue_over_time, use_container_width=True)
                left_column, right_column = st.columns(2)
                left_column.plotly_chart(fig_pie_chart, use_container_width=True)
                right_column.plotly_chart(fig_top_products, use_container_width=True)
                
                
                # --- HIỂN THỊ DỮ LIỆU GỐC ---
                st.markdown("### 📋 Dữ liệu chi tiết")
                st.dataframe(df_selection)
                
                # --- NÚT TẢI XUỐNG ---
                csv_data = convert_df_to_csv(df_selection)
                st.download_button(
                    label="📥 Tải dữ liệu đã lọc (CSV)",
                    data=csv_data,
                    file_name='bao_cao_doanh_thu_da_loc.csv',
                    mime='text/csv',
                )

        # --- NẾU FILE KHÔNG HỢP LỆ (Báo lỗi từ hàm đổi tên) ---
        else:
            st.error(f"""
                **Lỗi Cấu Trúc File!**
                Ứng dụng đã cố gắng "sơ chế" file của bạn nhưng vẫn không tìm thấy các cột "chuẩn" cần thiết.
                Các cột "chuẩn" mà ứng dụng cần là: `{', '.join(CANONICAL_COLUMNS)}`
                Các cột "chuẩn" bị thiếu trong file của bạn là: `{', '.join(missing_or_duplicate_cols)}`
                **Gợi ý:** Vui lòng kiểm tra file Excel/CSV, đảm bảo bạn có các cột như "Ngày Đặt Hàng", "Số Lượng", "Đơn Giá"...
            """)

    except Exception as e:
        st.error(f"Đã có lỗi nghiêm trọng xảy ra. Có thể file của bạn bị hỏng hoặc có kiểu dữ liệu không đúng (ví dụ: cột 'Số Lượng' chứa chữ). Lỗi: {e}")
else:
    st.info("💡 Bắt đầu bằng cách tải lên file dữ liệu của bạn ở thanh bên.")