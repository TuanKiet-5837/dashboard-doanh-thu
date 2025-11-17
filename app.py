import streamlit as st
import pandas as pd
import plotly.express as px
import re

# --- 1. HÀM CHUẨN HÓA TÊN CỘT ---
def simple_normalize(col_name):
    if col_name is None:
        return None
    normalized = str(col_name).lower()
    normalized = re.sub(r'[àáạảãâầấậẩẫăằắặẳẵ]', 'a', normalized)
    normalized = re.sub(r'[èéẹẻẽêềếệểễ]', 'e', normalized)
    normalized = re.sub(r'[òóọỏõôồốộổỗơờớợởỡ]', 'o', normalized)
    normalized = re.sub(r'[ìíịỉĩ]', 'i', normalized)
    normalized = re.sub(r'[ùúụủũưừứựửữ]', 'u', normalized)
    normalized = re.sub(r'[ỳýỵỷỹ]', 'y', normalized)
    normalized = re.sub(r'[đ]', 'd', normalized)
    normalized = re.sub(r'[\s\.-]+', '_', normalized)
    normalized = re.sub(r'[^a-z0-9_]', '', normalized)
    return normalized.strip('_')

# --- 2. DANH SÁCH CÁC CỘT CẦN THIẾT ---
CANONICAL_COLUMNS = [
    'ngay_dat_hang',
    'ma_don_hang',
    'ten_san_pham',
    'danh_muc',
    'so_luong',
    'don_gia',
    'chi_phi'
]

# --- 3. BẢN ĐỒ ÁNH XẠ ---
COLUMN_MAP = {
    'ngay_dat_hang': 'ngay_dat_hang', 'ngay_dat': 'ngay_dat_hang', 'order_date': 'ngay_dat_hang', 'ngay_hang': 'ngay_dat_hang',
    'ma_don_hang': 'ma_don_hang', 'ma_don': 'ma_don_hang', 'order_id': 'ma_don_hang', 'ma_dh': 'ma_don_hang',
    'ten_san_pham': 'ten_san_pham', 'ten_sp': 'ten_san_pham', 'product_name': 'ten_san_pham',
    'danh_muc': 'danh_muc', 'category': 'danh_muc', 'phan_loai': 'danh_muc',
    'so_luong': 'so_luong', 'soluong': 'so_luong', 'quantity': 'so_luong', 'sl': 'so_luong',
    'don_gia': 'don_gia', 'dongia': 'don_gia', 'dGia': 'don_gia', 'gia_ban': 'don_gia', 'price': 'don_gia',
    'chi_phi': 'chi_phi', 'chiphi': 'chi_phi', 'gia_von': 'chi_phi', 'cost': 'chi_phi', 'gia_goc': 'chi_phi'
}

# --- HÀM ĐỔI TÊN VÀ KIỂM TRA ---
def rename_and_validate(df):
    original_cols = df.columns
    new_cols = []
    
    for col in original_cols:
        normalized_col = simple_normalize(col)
        canonical_name = COLUMN_MAP.get(normalized_col)
        
        if canonical_name:
            new_cols.append(canonical_name)
        else:
            new_cols.append(normalized_col)
    
    df.columns = new_cols
    
    uploaded_columns = set(df.columns)
    required_columns = set(CANONICAL_COLUMNS)
    
    if required_columns.issubset(uploaded_columns):
        return True, None
    else:
        missing_columns = list(required_columns - uploaded_columns)
        return False, missing_columns

# --- HÀM TÍNH TOÁN ---
def calculate_metrics(df):
    # Đảm bảo các cột số là kiểu số trước khi tính toán
    df['so_luong'] = pd.to_numeric(df['so_luong'], errors='coerce').fillna(0)
    df['don_gia'] = pd.to_numeric(df['don_gia'], errors='coerce').fillna(0)
    df['chi_phi'] = pd.to_numeric(df['chi_phi'], errors='coerce').fillna(0)
    
    # Xử lý cột ngày tháng: Chuyển đổi sang datetime, sau đó lọc bỏ NaT
    df['ngay_dat_hang'] = pd.to_datetime(df['ngay_dat_hang'], errors='coerce')
    df = df.dropna(subset=['ngay_dat_hang']) # Xóa các hàng có ngày tháng không hợp lệ

    # Chỉ tính toán nếu df vẫn còn dữ liệu
    if not df.empty:
        df['doanh_thu'] = df['so_luong'] * df['don_gia']
        df['loi_nhuan'] = df['doanh_thu'] - (df['so_luong'] * df['chi_phi'])
    return df

# --- HÀM DÀNH CHO NÚT TẢI XUỐNG ---
@st.cache_data
def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8-sig')

# --- CẤU HÌNH TRANG WEB ---
st.set_page_config(
    page_title="Dashboard Phân Tích Doanh Thu",
    page_icon="💰", 
    layout="wide"
)

# --- GIAO DIỆN CHÍNH ---
st.title("💰 Dashboard Phân Tích Doanh Thu")
st.markdown("---")

# --- THANH BÊN (SIDEBAR) ---
st.sidebar.header("Tải Lên File Của Bạn")
uploaded_file = st.sidebar.file_uploader("Chọn file Excel hoặc CSV", type=["xlsx", "csv"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file, engine='openpyxl') # Đã sửa lỗi 'open_xl'
        else:
            df = pd.read_csv(uploaded_file)
        
        is_valid, missing_or_duplicate_cols = rename_and_validate(df)
        
        if is_valid:
            # --- KIỂM TRA DATAFRAME RỖNG ---
            if df.empty:
                st.warning("File bạn tải lên không có dữ liệu để phân tích sau khi kiểm tra cấu trúc.")
            else:
                df = calculate_metrics(df)
                
                if df.empty:
                    st.warning("Không có dữ liệu hợp lệ để phân tích sau khi xử lý ngày tháng. Vui lòng kiểm tra lại cột ngày tháng.")
                else:
                    st.sidebar.header("Bộ Lọc:")
                    
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

                        # --- BIỂU ĐỒ ---
                        revenue_by_date = df_selection.set_index('ngay_dat_hang').resample('D')['doanh_thu'].sum().reset_index()
                        fig_revenue_over_time = px.line(
                            revenue_by_date, x="ngay_dat_hang", y="doanh_thu", title="<b>Doanh Thu Theo Thời Gian</b>"
                        )
                        fig_revenue_over_time.update_layout(plot_bgcolor="rgba(0,0,0,0)", xaxis=(dict(showgrid=False)))

                        # --- NÂNG CẤP: HIỂN THỊ LỢI NHUẬN ÂM CHUYÊN NGHIỆP ---
                        # (Code mới, thay thế cho code cũ)

                        # 1. Tính toán lợi nhuận cho từng sản phẩm
                        profit_by_product = df_selection.groupby("ten_san_pham")["loi_nhuan"].sum().sort_values().reset_index()

                        # 2. Lọc ra 5 sản phẩm lỗ nhiều nhất và 5 sản phẩm lãi nhiều nhất
                        # (Điều này giúp biểu đồ gọn gàng và tập trung vào vấn đề)
                        top_5_profit = profit_by_product.tail(5)
                        bottom_5_loss = profit_by_product.head(5)
                        profit_loss_df = pd.concat([bottom_5_loss, top_5_profit])

                        # 3. Tạo biểu đồ cột
                        fig_top_products = px.bar(
                            profit_loss_df,
                            x="loi_nhuan",
                            y="ten_san_pham",
                            orientation="h",
                            title="<b>Top 5 Sản Phẩm Lãi & Lỗ Nhiều Nhất</b>",
                            color="loi_nhuan",  # Thêm màu sắc để phân biệt
                            color_continuous_scale='RdYlGn' # Đỏ (lỗ) - Vàng (hòa vốn) - Xanh (lãi)
                        )
                        fig_top_products.update_layout(
                            plot_bgcolor="rgba(0,0,0,0)", 
                            yaxis_title="Tên Sản Phẩm",
                            xaxis_title="Tổng Lợi Nhuận (VNĐ)",
                            coloraxis_showscale=False # Ẩn thanh màu
                        )
                        
                        fig_pie_chart = px.pie(
                            df_selection,
                            names="danh_muc",
                            values="doanh_thu",
                            title="<b>Tỷ Trọng Doanh Thu Theo Danh Mục</b>"
                        )
                        fig_pie_chart.update_layout(plot_bgcolor="rgba(0,0,0,0)")
                        
                        st.plotly_chart(fig_revenue_over_time, use_container_width=True)
                        left_column, right_column = st.columns(2)
                        left_column.plotly_chart(fig_pie_chart, use_container_width=True)
                        right_column.plotly_chart(fig_top_products, use_container_width=True)
                        
                        
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

        # --- NẾU FILE KHÔNG HỢP LỆ ---
        else:
            st.error(f"""
                **Lỗi Cấu Trúc File!**
                \nFile của bạn đang bị thiếu những cột cần thiết.
                \nCác cột mà ứng dụng cần là: `{', '.join(CANONICAL_COLUMNS)}`
                \nCác cột bạn bị thiếu trong file là: `{', '.join(missing_or_duplicate_cols)}`
                \n**Gợi ý:** Vui lòng kiểm tra file Excel/CSV, đảm bảo file có các cột như "Ngày Đặt Hàng", "Số Lượng", "Đơn Giá"...
            """)

    except Exception as e:
        st.error(f"Đã có lỗi nghiêm trọng xảy ra. Có thể file của bạn bị hỏng hoặc có kiểu dữ liệu không đúng (ví dụ: cột 'Số Lượng' chứa chữ). Lỗi: {e}")
else:
    st.info("💡 Bắt đầu bằng cách tải lên file dữ liệu của bạn ở thanh bên.")