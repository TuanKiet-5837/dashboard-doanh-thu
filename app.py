import streamlit as st
import pandas as pd
import plotly.express as px
import re
import numpy as np
from datetime import timedelta

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import PolynomialFeatures
from statsmodels.tsa.seasonal import seasonal_decompose

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
    'ngay_dat_hang', 'ma_don_hang', 'ten_san_pham', 
    'danh_muc', 'so_luong', 'don_gia', 'chi_phi'
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
    df['so_luong'] = pd.to_numeric(df['so_luong'], errors='coerce').fillna(0)
    df['don_gia'] = pd.to_numeric(df['don_gia'], errors='coerce').fillna(0)
    df['chi_phi'] = pd.to_numeric(df['chi_phi'], errors='coerce').fillna(0)
    df['ngay_dat_hang'] = pd.to_datetime(df['ngay_dat_hang'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['ngay_dat_hang'])
    if not df.empty:
        df['doanh_thu'] = df['so_luong'] * df['don_gia']
        df['loi_nhuan'] = df['doanh_thu'] - (df['so_luong'] * df['chi_phi'])
    return df

# --- HÀM DÀNH CHO NÚT TẢI XUỐNG ---
@st.cache_data
def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8-sig')

# --- CẤU HÌNH TRANG WEB ---
st.set_page_config(page_title="Dashboard Phân Tích Doanh Thu", page_icon="💰", layout="wide")

# --- GIAO DIỆN CHÍNH ---
st.title("💰 Dashboard Phân Tích Doanh Thu & Hỗ Trợ Quyết Định (AI)")
st.markdown("---")

# --- THANH BÊN ---
st.sidebar.header("Tải Lên File Của Bạn")
uploaded_file = st.sidebar.file_uploader("Chọn file Excel hoặc CSV", type=["xlsx", "csv"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file, engine='openpyxl') 
        else:
            df = pd.read_csv(uploaded_file)
        
        is_valid, missing_or_duplicate_cols = rename_and_validate(df)
        
        if is_valid:
            if df.empty:
                st.warning("File bạn tải lên không có dữ liệu để phân tích sau khi kiểm tra cấu trúc.")
            else:
                df = calculate_metrics(df)
                if df.empty:
                    st.warning("Không có dữ liệu hợp lệ để phân tích sau khi xử lý ngày tháng. Vui lòng kiểm tra lại cột ngày tháng.")
                else:
                    st.sidebar.header("Bộ Lọc:")
                    category = st.sidebar.multiselect(
                        "Chọn Danh Mục:", options=df["danh_muc"].unique(), default=df["danh_muc"].unique()
                    )
                    min_date = df["ngay_dat_hang"].min().date()
                    max_date = df["ngay_dat_hang"].max().date()
                    date_range = st.sidebar.date_input(
                        "Chọn Khoảng Thời Gian:", value=(min_date, max_date), min_value=min_date, max_value=max_date
                    )
                    
                    start_date = pd.to_datetime(date_range[0])
                    end_date = pd.to_datetime(date_range[1])
                    df_selection = df.query("danh_muc == @category & ngay_dat_hang >= @start_date & ngay_dat_hang <= @end_date")
                    
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

                        # --- GIAO DIỆN KPI ---
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

                        profit_by_product = df_selection.groupby("ten_san_pham")["loi_nhuan"].sum().sort_values().reset_index()
                        top_5_profit = profit_by_product.tail(5)
                        bottom_5_loss = profit_by_product.head(5)
                        profit_loss_df = pd.concat([bottom_5_loss, top_5_profit])

                        fig_top_products = px.bar(
                            profit_loss_df, x="loi_nhuan", y="ten_san_pham", orientation="h",
                            title="<b>Top 5 Sản Phẩm Lãi & Lỗ Nhiều Nhất</b>", color="loi_nhuan",  
                            color_continuous_scale='RdYlGn' 
                        )
                        fig_top_products.update_layout(
                            plot_bgcolor="rgba(0,0,0,0)", yaxis_title="Tên Sản Phẩm",
                            xaxis_title="Tổng Lợi Nhuận (VNĐ)", coloraxis_showscale=False 
                        )
                        
                        fig_pie_chart = px.pie(
                            df_selection, names="danh_muc", values="doanh_thu",
                            title="<b>Tỷ Trọng Doanh Thu Theo Danh Mục</b>"
                        )
                        fig_pie_chart.update_layout(plot_bgcolor="rgba(0,0,0,0)")
                        
                        st.plotly_chart(fig_revenue_over_time, use_container_width=True)
                        left_column, right_column = st.columns(2)
                        left_column.plotly_chart(fig_pie_chart, use_container_width=True)
                        right_column.plotly_chart(fig_top_products, use_container_width=True)

                        # =========================================================
                        # TÍCH HỢP AI
                        # =========================================================
                        st.markdown("---")
                        st.markdown("### 🤖 Tính Năng Tăng Cường Trí Tuệ Nhân Tạo (AI)")
                        
                        tab1, tab2, tab3, tab4 = st.tabs([
                            "🔮 Dự báo tương lai", 
                            "🛡️ Kiểm soát rủi ro", 
                            "💰 Tối ưu giá bán", 
                            "📅 Phân tích mùa vụ"
                        ])

                        with tab1:
                            st.markdown("#### Dự Báo Doanh Thu 30 Ngày Tiếp Theo")
                            df_ai = revenue_by_date.copy()
                            if len(df_ai) > 3:
                                # Nhận biết Thứ trong tuần
                                df_ai['ngay_so'] = (df_ai['ngay_dat_hang'] - df_ai['ngay_dat_hang'].min()).dt.days
                                df_ai['thu_trong_tuan'] = df_ai['ngay_dat_hang'].dt.dayofweek # 0 là Thứ 2, 6 là Chủ nhật
                                
                                # AI học dựa trên 2 yếu tố: Thời gian trôi qua + Là thứ mấy
                                X = df_ai[['ngay_so', 'thu_trong_tuan']]
                                y = df_ai['doanh_thu']
                                
                                model_lr = LinearRegression()
                                model_lr.fit(X, y)
                                
                                # Lên lịch 30 ngày tương lai
                                future_days = 30
                                future_dates = [df_ai['ngay_dat_hang'].max() + timedelta(days=i) for i in range(1, future_days + 1)]
                                
                                # Tạo dữ liệu cho 30 ngày tương lai
                                future_X = pd.DataFrame({
                                    'ngay_so': [(d - df_ai['ngay_dat_hang'].min()).days for d in future_dates],
                                    'thu_trong_tuan': [d.weekday() for d in future_dates]
                                })
                                
                                future_pred = model_lr.predict(future_X)
                                
                                df_future = pd.DataFrame({'ngay_dat_hang': future_dates, 'doanh_thu': future_pred, 'loai': 'Dự báo (AI)'})
                                df_ai['loai'] = 'Thực tế'
                                
                                df_final_lr = pd.concat([df_ai[['ngay_dat_hang', 'doanh_thu', 'loai']], df_future])
                                
                                fig_pred = px.line(df_final_lr, x='ngay_dat_hang', y='doanh_thu', color='loai',
                                                   color_discrete_map={'Thực tế': '#2E86C1', 'Dự báo (AI)': '#E74C3C'},
                                                   title="<b>Đường dự báo đã được AI học thêm quy luật ngày nghỉ</b>")
                                fig_pred.update_layout(plot_bgcolor="rgba(0,0,0,0)")
                                st.plotly_chart(fig_pred, use_container_width=True)
                            else:
                                st.warning("Cần nhiều dữ liệu ngày tháng hơn để hệ thống AI có thể học và dự báo.")

                        with tab2:
                            st.markdown("#### Phát Hiện Giao Dịch Bất Thường")
                            model_data = df_selection[['so_luong', 'don_gia', 'loi_nhuan']].dropna()
                            if len(model_data) > 10:
                                iso_forest = IsolationForest(contamination=0.05, random_state=42)
                                model_data['anomaly'] = iso_forest.fit_predict(model_data)
                                anomalies = df_selection.loc[model_data.index[model_data['anomaly'] == -1]]
                                if not anomalies.empty:
                                    st.error(f"⚠️ Phát hiện **{len(anomalies)}** giao dịch đáng ngờ.")
                                    fig_anom = px.scatter(model_data, x='don_gia', y='loi_nhuan', 
                                                          color=model_data['anomaly'].map({1: 'Bình thường', -1: 'Bất thường'}),
                                                          color_discrete_map={'Bình thường': '#2E86C1', 'Bất thường': '#E74C3C'})
                                    st.plotly_chart(fig_anom, use_container_width=True)
                                    st.dataframe(anomalies[['ma_don_hang', 'ten_san_pham', 'so_luong', 'don_gia', 'loi_nhuan']])
                                else:
                                    st.success("✅ Dữ liệu an toàn, không có điểm bất thường đáng kể.")
                            else:
                                st.warning("Cần ít nhất 10 dòng dữ liệu để chạy thuật toán.")

                        with tab3:
                            st.markdown("#### Tìm Mức Giá Để Tối Ưu Lợi Nhuận")
                            selected_product = st.selectbox("Chọn sản phẩm cần phân tích độ nhạy giá:", df_selection['ten_san_pham'].unique())
                            df_prod = df_selection[df_selection['ten_san_pham'] == selected_product]
                            if len(df_prod['don_gia'].unique()) > 2:
                                df_price = df_prod.groupby('don_gia')['so_luong'].sum().reset_index()
                                X_poly_feat = PolynomialFeatures(degree=2)
                                X_price = X_poly_feat.fit_transform(df_price[['don_gia']])
                                model_poly = LinearRegression()
                                model_poly.fit(X_price, df_price['so_luong'])
                                min_p, max_p = df_price['don_gia'].min() * 0.8, df_price['don_gia'].max() * 1.2
                                test_prices = np.linspace(min_p, max_p, 50).reshape(-1, 1)
                                pred_qty = model_poly.predict(X_poly_feat.transform(test_prices))
                                pred_rev = test_prices.flatten() * pred_qty
                                best_idx = np.argmax(pred_rev)
                                st.success(f"💡 AI Khuyến nghị: Mức giá tối ưu là **₫ {test_prices[best_idx][0]:,.0f}** mang lại dự kiến **₫ {pred_rev[best_idx]:,.0f}** doanh thu.")
                                fig_opt = px.line(x=test_prices.flatten(), y=pred_rev, labels={'x': 'Giá bán test', 'y': 'Doanh thu dự kiến'})
                                fig_opt.add_scatter(x=[test_prices[best_idx][0]], y=[pred_rev[best_idx]], mode='markers', marker=dict(color='red', size=12))
                                st.plotly_chart(fig_opt, use_container_width=True)
                            else:
                                st.warning("Sản phẩm này chưa có đủ sự biến động về giá để vẽ đường cong nhu cầu.")

                        with tab4:
                            st.markdown("#### Phân Rã Dữ Liệu Thời Gian")
                            df_ts = revenue_by_date.set_index('ngay_dat_hang')
                            idx = pd.date_range(df_ts.index.min(), df_ts.index.max())
                            df_ts = df_ts.reindex(idx, fill_value=0)
                            if len(df_ts) >= 14:
                                decomp = seasonal_decompose(df_ts['doanh_thu'], model='additive', period=7)
                                st.line_chart(decomp.seasonal, height=200)
                            else:
                                st.warning("Cần ít nhất 14 ngày dữ liệu liên tục để tìm ra quy luật mùa vụ.")

                        # --- BẢNG DỮ LIỆU & NÚT TẢI XUỐNG ---
                        st.markdown("### 📋 Dữ liệu chi tiết")
                        st.dataframe(df_selection)
                        
                        csv_data = convert_df_to_csv(df_selection)
                        st.download_button(
                            label="📥 Tải dữ liệu đã lọc (CSV)",
                            data=csv_data,
                            file_name='bao_cao_doanh_thu_da_loc.csv',
                            mime='text/csv',
                        )

        else:
            st.error(f"""
                **Lỗi Cấu Trúc File!**
                \nFile của bạn đang bị thiếu những cột cần thiết.
                \nCác cột mà ứng dụng cần là: `{', '.join(CANONICAL_COLUMNS)}`
                \nCác cột bạn bị thiếu trong file là: `{', '.join(missing_or_duplicate_cols)}`
            """)

    except Exception as e:
        st.error(f"Đã có lỗi nghiêm trọng xảy ra: {e}")
else:
    # --- HƯỚNG DẪN ---
    col_guide_1, col_guide_2 = st.columns(2)

    with col_guide_1:
        st.info("### 1. Cấu trúc File Exel/CSV")
        st.markdown("Để hệ thống hoạt động tốt nhất, file Excel/CSV của bạn nên có các cột sau:")
        st.markdown("""
        | Tên cột | Ý nghĩa | Ví dụ |
        | :--- | :--- | :--- |
        | **Ngày đặt hàng** | Ngày khách mua | `01/12/2025` |
        | **Mã đơn hàng** | Mã định danh | `DH-001` |
        | **Tên sản phẩm** | Tên hàng hóa | `iPhone 15` |
        | **Danh mục** | Loại hàng | `Điện tử` |
        | **Số lượng** | Số lượng bán | `2` |
        | **Đơn giá** | Giá bán ra | `30,000,000` |
        | **Chi phí** | Giá vốn nhập | `25,000,000` |
        """)

    with col_guide_2:
        st.success("### 2. Hệ thống sẽ giúp bạn")
        st.markdown("""
        Sau khi bạn tải file lên, hệ thống sẽ tự động thực hiện:
        * **Làm sạch dữ liệu:** Tự động sửa lỗi tên cột, xử lý trống/lỗi.
        * **Tính toán tự động:** Doanh thu, Lợi nhuận, Tỷ suất...
        * **Vẽ biểu đồ:** Xu hướng, Top sản phẩm, Lãi/Lỗ.
        * **Tăng cường AI:** Dự báo tương lai, kiểm soát rủi ro, tối ưu giá.
        """)

    st.warning("### 3. Hướng dẫn sử dụng nhanh")
    st.markdown("""
    1.  **Chuẩn bị file:** Đảm bảo file Excel/CSV của bạn có các cột như hướng dẫn.
    2.  **Tải lên:** Nhìn sang **cột bên trái**, nhấn nút **"Browse files"** để chọn file.
    3.  **Phân tích:** Đợi 1-2 giây, Dashboard sẽ hiện ra.
    4.  **Xuất báo cáo:** Kéo xuống cuối trang để tải file dữ liệu sạch.
    """)