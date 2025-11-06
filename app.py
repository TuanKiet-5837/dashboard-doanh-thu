# app.py

import streamlit as st
import pandas as pd
import plotly.express as px

# --- CẤU HÌNH TRANG WEB ---
st.set_page_config(
    page_title="Dashboard Phân Tích Doanh Thu",
    page_icon="📊",
    layout="wide"
)

# --- HÀM ĐỂ TÍNH TOÁN ---
def calculate_metrics(df):
    """Hàm tính toán các chỉ số chính từ DataFrame."""
    # Chuyển đổi cột ngày thành kiểu datetime
    df['Ngay_Dat_Hang'] = pd.to_datetime(df['Ngay_Dat_Hang'])
    
    # Tính toán Doanh thu và Lợi nhuận
    df['Doanh_Thu'] = df['So_Luong'] * df['Don_Gia']
    df['Loi_Nhuan'] = df['Doanh_Thu'] - (df['So_Luong'] * df['Chi_Phi'])
    
    return df

# --- GIAO DIỆN CHÍNH ---
st.title("📊 Dashboard Phân Tích Doanh Thu")
st.markdown("---")

# --- THANH BÊN (SIDEBAR) ---
st.sidebar.header("Tải Lên File Của Bạn")
uploaded_file = st.sidebar.file_uploader("Chọn file Excel hoặc CSV", type=["xlsx", "csv"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file, engine='openpyxl')
        else:
            df = pd.read_csv(uploaded_file)
            
        # Tính toán các chỉ số
        df = calculate_metrics(df)

        st.sidebar.header("Bộ Lọc:")
        
        # --- BỘ LỌC THEO DANH MỤC ---
        category = st.sidebar.multiselect(
            "Chọn Danh Mục:",
            options=df["Danh_Muc"].unique(),
            default=df["Danh_Muc"].unique()
        )

        # --- BỘ LỌC THEO NGÀY ---
        min_date = df["Ngay_Dat_Hang"].min().date()
        max_date = df["Ngay_Dat_Hang"].max().date()
        date_range = st.sidebar.date_input(
            "Chọn Khoảng Thời Gian:",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        # Chuyển đổi date_range về datetime64 để so sánh
        start_date = pd.to_datetime(date_range[0])
        end_date = pd.to_datetime(date_range[1])

        # Áp dụng bộ lọc vào DataFrame
        df_selection = df.query(
            "Danh_Muc == @category & Ngay_Dat_Hang >= @start_date & Ngay_Dat_Hang <= @end_date"
        )
        
        if df_selection.empty:
            st.warning("Không có dữ liệu nào phù hợp với bộ lọc của bạn!")
        else:
            # --- HIỂN THỊ CÁC CHỈ SỐ CHÍNH (KPIs) ---
            total_revenue = int(df_selection["Doanh_Thu"].sum())
            total_profit = int(df_selection["Loi_Nhuan"].sum())
            total_orders = df_selection["Ma_Don_Hang"].nunique()

            col1, col2, col3 = st.columns(3)
            with col1:
                st.subheader("Tổng Doanh Thu")
                st.subheader(f"₫ {total_revenue:,}")
            with col2:
                st.subheader("Tổng Lợi Nhuận")
                st.subheader(f"₫ {total_profit:,}")
            with col3:
                st.subheader("Tổng Số Đơn Hàng")
                st.subheader(f"{total_orders}")

            st.markdown("---")

            # --- BIỂU ĐỒ ---
            
            # 1. BIỂU ĐỒ ĐƯỜNG: DOANH THU THEO THỜI GIAN
            revenue_by_date = df_selection.groupby(df_selection['Ngay_Dat_Hang'].dt.date)['Doanh_Thu'].sum().reset_index()
            fig_revenue_over_time = px.line(
                revenue_by_date,
                x="Ngay_Dat_Hang",
                y="Doanh_Thu",
                title="<b>Doanh Thu Theo Thời Gian</b>",
                template="plotly_white"
            )
            fig_revenue_over_time.update_layout(xaxis_title='Ngày', yaxis_title='Doanh Thu')

            # 2. BIỂU ĐỒ CỘT: TOP SẢN PHẨM BÁN CHẠY
            sales_by_product = df_selection.groupby("Ten_San_Pham")["So_Luong"].sum().sort_values(ascending=False).reset_index()
            fig_top_products = px.bar(
                sales_by_product.head(10), # Lấy top 10 sản phẩm
                x="So_Luong",
                y="Ten_San_Pham",
                orientation="h",
                title="<b>Top 10 Sản Phẩm Bán Chạy Nhất</b>",
                template="plotly_white"
            )
            fig_top_products.update_layout(xaxis_title='Tổng Số Lượng Bán', yaxis_title='Tên Sản Phẩm')
            
            # Hiển thị biểu đồ
            left_column, right_column = st.columns(2)
            left_column.plotly_chart(fig_revenue_over_time, use_container_width=True)
            right_column.plotly_chart(fig_top_products, use_container_width=True)

            # --- HIỂN THỊ DỮ LIỆU GỐC ---
            st.markdown("### Dữ liệu chi tiết")
            st.dataframe(df_selection)

    except Exception as e:
        st.error(f"Đã có lỗi xảy ra khi đọc file: {e}")
else:
    st.info("Vui lòng tải lên một file Excel hoặc CSV để bắt đầu.")