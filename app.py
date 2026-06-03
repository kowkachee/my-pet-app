import streamlit as st
import pandas as pd
import os
from PIL import Image
from datetime import datetime, date

# ==================== 設定常數與資料庫檔案 ====================
IMAGE_DIR = "pet_photos"
DB_FILE = "pet_data.csv"
SERVICE_DB_FILE = "pet_service_records.csv"

if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

# 1. 寵物主檔案欄位
PET_COLUMNS = [
    '晶片號碼', '寵物名字', '種類', '品種', '性別', '已絕育', 
    '主人姓名', '主人手機', '會咬人', '疾病說明', '注意事項', 
    '照片檔名_1', '照片檔名_2', '照片檔名_3'
]

# 2. 服務紀錄流水帳欄位
SERVICE_COLUMNS = ['晶片號碼', '寵物名字', '主人手機', '服務日期', '服務金額', '備註事項']

# 🔄 初始化 1：寵物主資料庫
if not os.path.exists(DB_FILE):
    st.session_state.pet_db = pd.DataFrame(columns=PET_COLUMNS)
    st.session_state.pet_db.to_csv(DB_FILE, index=False, encoding='utf-8-sig')
else:
    loaded_df = pd.read_csv(DB_FILE, dtype={col: str for col in PET_COLUMNS})
    for col in PET_COLUMNS:
        if col not in loaded_df.columns:
            loaded_df[col] = "none" if "照片" in col else ""
    st.session_state.pet_db = loaded_df.reindex(columns=PET_COLUMNS)

# 🔄 初始化 2：服務紀錄資料庫
if not os.path.exists(SERVICE_DB_FILE):
    st.session_state.service_db = pd.DataFrame(columns=SERVICE_COLUMNS)
    st.session_state.service_db.to_csv(SERVICE_DB_FILE, index=False, encoding='utf-8-sig')
else:
    loaded_service_df = pd.read_csv(SERVICE_DB_FILE, dtype={'晶片號碼': str, '寵物名字': str, '主人手機': str, '服務日期': str, '備註事項': str})
    loaded_service_df['服務金額'] = pd.to_numeric(loaded_service_df['服務金額'], errors='coerce').fillna(0).astype(int)
    st.session_state.service_db = loaded_service_df.reindex(columns=SERVICE_COLUMNS)

st.set_page_config(layout="wide")

# ==================== ✨ 網址參數超連結跳轉核心邏輯 ✨ ====================
query_params = st.query_params

if "chip" in query_params:
    st.session_state.current_page = "🔍 晶片詳細查詢"
    st.session_state.target_chip = str(query_params["chip"])
    st.query_params.clear()
else:
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "📝 新增客戶主檔案"
    if 'target_chip' not in st.session_state:
        st.session_state.target_chip = ""

# 🌐 側邊欄導覽選單
st.sidebar.title("🐾 導覽選單")

menu_options = [
    "📝 新增客戶主檔案", 
    "📋 瀏覽所有資料庫", 
    "🔍 晶片詳細查詢", 
    "🔍 進階寵物搜尋",     
    "📊 營業金額統計",
    "✏️ 編輯客戶基本資料",
    "💰 新增服務消費紀錄",  
    "🛠️ 編輯服務消費紀錄"
]

if st.session_state.current_page not in menu_options:
    st.session_state.current_page = menu_options[0]

page_idx = menu_options.index(st.session_state.current_page)
selected_page = st.sidebar.radio("請選擇功能：", menu_options, index=page_idx)

if selected_page != st.session_state.current_page:
    st.session_state.current_page = selected_page
    st.rerun()

page = st.session_state.current_page

# 🛠️ 輔助函式：利用 Streamlit 官方標準的 LinkColumn 機制建立「不崩潰超連結」表格
def show_safe_link_table(df, table_key):
    display_df = df.copy()
    
    hide_cols = [c for c in display_df.columns if "照片檔名" in c]
    if hide_cols:
        display_df = display_df.drop(columns=hide_cols)
        
    display_df['晶片號碼連結'] = display_df['晶片號碼'].apply(lambda x: f"/?chip={str(x).strip()}")
    
    cols = ['晶片號碼連結'] + [c for c in display_df.columns if c != '晶片號碼連結']
    display_df = display_df[cols]
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "晶片號碼連結": st.column_config.LinkColumn(
                "🔗 點擊晶片號碼直接跳轉",
                help="點擊即可直接跳轉至該寵物的詳細查詢頁面",
                display_text=r"^/\?chip=(.*)$"
            )
        },
        key=table_key
    )

# ==================== 頁面 1：新增客戶主檔案 ====================
if page == "📝 新增客戶主檔案":
    st.title("📝 建立全新寵物與主人基本檔案")
    col1, col2 = st.columns(2)
    with col1:
        chip_number = st.text_input("💾 寵物晶片號碼 (若無晶片請留空，系統將自動生成識別碼)")
        pet_name = st.text_input("寵物名字 *")
        pet_type = st.selectbox("寵物種類", ["狗", "貓", "其他"])
        pet_breed = st.text_input("品種")
        gender = st.radio("性別", ["公", "母"])
        is_neutered = st.checkbox("已絕育")
    with col2:
        owner_name = st.text_input("主人姓名")
        owner_phone = st.text_input("主人手機號碼 *")
        will_bite = st.checkbox("🔥 注意：這隻寵物會咬人！")
        disease_detail = st.text_area("具體病情說明")
        special_notes = st.text_area("美容特別注意事項")
        uploaded_files = st.file_uploader("📸 上傳寵物照片 (最多 3 張)", type=["jpg", "png", "jpeg"], accept_multiple_files=True)

    if st.button("💾 永久儲存基本檔案", use_container_width=True):
        # 檢查必填項目（名字與手機號碼）
        if not pet_name.strip() or not owner_phone.strip():
            st.warning("⚠️ 寵物名字與主人手機為必填欄位！")
        else:
            # ✨ 核心修正邏輯：如果晶片號碼留空，自動以「寵物名字_主人手機」作為代用晶片號碼
            final_chip = chip_number.strip()
            if not final_chip:
                final_chip = f"{pet_name.strip()}_{owner_phone.strip()}"
                st.info(f"💡 偵測到晶片號碼留空，系統已自動生成識別碼：`{final_chip}`")

            # 檢查這個識別碼是否已經存在於資料庫中
            if final_chip in st.session_state.pet_db['晶片號碼'].astype(str).values:
                st.error(f"❌ 錯誤：識別碼或晶片號碼 `{final_chip}` 已存在於系統中！")
            else:
                # 處理照片儲存
                photo_filenames = ["none", "none", "none"]
                for i, current_file in enumerate(uploaded_files[:3]):
                    file_ext = current_file.name.split(".")[-1]
                    filename = f"{final_chip}_{i+1}.{file_ext}"
                    photo_filenames[i] = filename
                    with open(os.path.join(IMAGE_DIR, filename), "wb") as f:
                        f.write(current_file.getbuffer())

                new_pet_data = {
                    '晶片號碼': final_chip, '寵物名字': pet_name.strip(), '種類': pet_type, '品種': pet_breed.strip(),
                    '性別': gender, '已絕育': "是" if is_neutered else "否", '主人姓名': owner_name.strip(), '主人手機': owner_phone.strip(),
                    '會咬人': "🚨會咬人" if will_bite else "否", '疾病說明': disease_detail, '注意事項': special_notes,
                    '照片檔名_1': photo_filenames[0], '照片檔名_2': photo_filenames[1], '照片檔名_3': photo_filenames[2]
                }
                st.session_state.pet_db = pd.concat([st.session_state.pet_db, pd.DataFrame([new_pet_data])], ignore_index=True)
                st.session_state.pet_db.to_csv(DB_FILE, index=False, encoding='utf-8-sig')
                st.success(f"🎉 {pet_name} 的基本檔案已成功永久儲存！(識別碼: {final_chip})")

# ==================== 頁面 2：瀏覽所有資料庫 ====================
elif page == "📋 瀏覽所有資料庫":
    st.title("📋 系統資料庫瀏覽")
    db_type = st.selectbox("請選擇要查看的資料庫：", ["🐾 寵物主基本資料庫 (pet_data.csv)", "💰 服務消費歷史流水帳 (pet_service_records.csv)"])
    st.markdown("---")
    
    if db_type == "🐾 寵物主基本資料庫 (pet_data.csv)":
        if st.session_state.pet_db.empty: 
            st.info("尚無資料。")
        else:
            st.markdown("💡 **提示：直接用滑鼠點擊表格第一欄藍色的「晶片號碼」，即可直接跳轉看詳細個人檔案與照片！**")
            show_safe_link_table(st.session_state.pet_db, "browse_table_safe")
    else:
        if st.session_state.service_db.empty: 
            st.info("尚無任何消費紀錄。")
        else: 
            st.dataframe(st.session_state.service_db, use_container_width=True)

# ==================== 頁面 3：詳細查詢 ====================
elif page == "🔍 晶片詳細查詢":
    st.title("🔍 寵物詳細檔案個別查詢")
    chip_list = st.session_state.pet_db['晶片號碼'].astype(str).tolist()
    if not chip_list: st.info("目前資料庫中尚無資料。")
    else:
        default_idx = 0
        if st.session_state.target_chip in chip_list:
            default_idx = chip_list.index(st.session_state.target_chip)
            st.session_state.target_chip = "" 

        search_chip = st.selectbox("請選擇要查詢的寵物晶片號碼 / 系統識別碼：", chip_list, index=default_idx)
        pet_info = st.session_state.pet_db[st.session_state.pet_db['晶片號碼'].astype(str) == search_chip].iloc[0]
        st.markdown("---")
        detail_col1, detail_col2 = st.columns([1, 1.2])
        with detail_col1:
            st.subheader("📷 寵物照片紀錄")
            has_any_photo = False
            for field in ['照片檔名_1', '照片檔名_2', '照片檔名_3']:
                filename = str(pet_info[field])
                if filename != "none" and filename != "nan" and os.path.exists(os.path.join(IMAGE_DIR, filename)):
                    st.image(Image.open(os.path.join(IMAGE_DIR, filename)), use_container_width=True)
                    has_any_photo = True
            if not has_any_photo: st.warning("🤖 此寵物尚未上傳任何照片。")
        with detail_col2:
            st.subheader(f"基本資料：{pet_info['寵物名字']} ({pet_info['種類']} - {pet_info['品種']})")
            st.write(f"**🧬 晶片號碼/識別碼：** {pet_info['晶片號碼']} | **🚻 性別：** {pet_info['性別']} | **✂️ 絕育：** {pet_info['已絕育']}")
            st.write(f"**👤 飼主姓名：** {pet_info['主人姓名']} | **📱 聯絡手機：** {pet_info['主人手機']}")
            if str(pet_info['會咬人']) == "🚨會咬人": st.error("⚠️ 警告：這隻寵物會咬人！")
            dis_val = "" if pd.isna(pet_info['疾病說明']) or str(pet_info['疾病說明']) == 'nan' else str(pet_info['疾病說明'])
            not_val = "" if pd.isna(pet_info['注意事項']) or str(pet_info['注意事項']) == 'nan' else str(pet_info['注意事項'])
            st.text_area("🏥 疾病說明", value=dis_val, disabled=True, key="view_dis")
            st.text_area("💈 美容特別注意事項", value=not_val, disabled=True, key="view_not")
            
            st.markdown("---")
            st.subheader("📜 歷史服務與消費紀錄")
            history_df = st.session_state.service_db[st.session_state.service_db['晶片號碼'].astype(str) == search_chip]
            if history_df.empty: st.info("該寵物目前尚無服務消費紀錄。")
            else:
                total_spend = history_df['服務金額'].astype(int).sum()
                st.metric(label="📊 歷史總消費次數", value=f"{len(history_df)} 次", delta=f"總累積金額: ${total_spend:,} 元")
                st.dataframe(history_df[['服務日期', '服務金額', '備註事項']], use_container_width=True)

# ==================== 頁面 4：進階寵物搜尋 ====================
elif page == "🔍 進階寵物搜尋":
    st.title("🔍 進階寵物客戶多條件搜尋")
    st.markdown("請在下方輸入搜尋條件（留空代表不限制該條件，支援部分文字模糊搜尋）：")
    
    search_col1, search_col2, search_col3 = st.columns(3)
    with search_col1:
        s_chip = st.text_input("🧬 搜尋晶片號碼 / 識別碼")
        s_pet_name = st.text_input("🐾 搜尋寵物名字")
    with search_col2:
        s_owner_name = st.text_input("👤 搜尋主人姓名")
        s_owner_phone = st.text_input("📱 搜尋主人手機")
    with search_col3:
        s_type = st.selectbox("種類篩選", ["全部", "狗", "貓", "其他"])
        s_breed = st.text_input("品種關鍵字")
        
    search_col4, search_col5 = st.columns(2)
    with search_col4:
        s_bite = st.selectbox("是否會咬人", ["全部", "🚨會咬人", "否"])
    with search_col5:
        s_neutered = st.selectbox("是否已絕育", ["全部", "是", "否"])

    st.markdown("---")
    
    if st.session_state.pet_db.empty:
        st.info("目前資料庫中尚無任何資料可供搜尋。")
    else:
        filtered_df = st.session_state.pet_db.copy()
        
        if s_chip:
            filtered_df = filtered_df[filtered_df['晶片號碼'].fillna('').str.contains(s_chip, case=False, na=False)]
        if s_pet_name:
            filtered_df = filtered_df[filtered_df['寵物名字'].fillna('').str.contains(s_pet_name, case=False, na=False)]
        if s_owner_name:
            filtered_df = filtered_df[filtered_df['主人姓名'].fillna('').str.contains(s_owner_name, case=False, na=False)]
        if s_owner_phone:
            filtered_df = filtered_df[filtered_df['主人手機'].fillna('').str.contains(s_owner_phone, case=False, na=False)]
        if s_breed:
            filtered_df = filtered_df[filtered_df['品種'].fillna('').str.contains(s_breed, case=False, na=False)]
            
        if s_type != "全部":
            filtered_df = filtered_df[filtered_df['種類'] == s_type]
        if s_bite != "全部":
            filtered_df = filtered_df[filtered_df['會咬人'] == s_bite]
        if s_neutered != "全部":
            filtered_df = filtered_df[filtered_df['已絕育'] == s_neutered]
            
        st.subheader(f"📊 搜尋結果 (共找到 {len(filtered_df)} 筆符合條件的資料)")
        
        if filtered_df.empty:
            st.warning("🔍 找不到符合上述條件的寵物資料，請修正搜尋字眼。")
        else:
            st.markdown("💡 **提示：直接用滑鼠點擊表格第一欄藍色的「晶片號碼」，即可直接跳轉看詳細個人檔案與照片！**")
            show_safe_link_table(filtered_df, "search_table_safe")

# ==================== 頁面 5：📊 營業金額統計 ====================
elif page == "📊 營業金額統計":
    st.title("📊 寵物美容服務營業額與特定時段統計")
    st.markdown("請選擇你要統計與調閱紀錄的時間區間：")
    
    date_col1, date_col2 = st.columns(2)
    with date_col1:
        start_date = st.date_input("📅 請選擇開始日期", date(datetime.today().year, datetime.today().month, 1))
    with date_col2:
        end_date = st.date_input("📅 請選擇終止日期", datetime.today().date())
        
    st.markdown("---")
    
    if st.session_state.service_db.empty:
        st.info("目前服務紀錄資料庫中尚無任何消費數據。")
    else:
        service_df_temp = st.session_state.service_db.copy()
        service_df_temp['parsed_date'] = pd.to_datetime(service_df_temp['服務日期'], errors='coerce').dt.date
        
        period_records = service_df_temp[
            (service_df_temp['parsed_date'] >= start_date) & 
            (service_df_temp['parsed_date'] <= end_date)
        ]
        
        period_records = period_records.sort_values(by='服務日期', ascending=False)
        
        st.subheader(f"📋 區間服務流水帳 ({start_date} ~ {end_date})")
        
        if period_records.empty:
            st.warning(f"🔍 在 {start_date} 至 {end_date} 期間內，沒有找到任何服務消費紀錄。")
        else:
            st.markdown("💡 **提示：直接用滑鼠點擊表格第一欄藍色的「晶片號碼」，即可直接跳轉看該寵物的相片與詳細病歷！**")
            
            final_report_df = period_records[['晶片號碼', '寵物名字', '主人手機', '服務日期', '服務金額', '備註事項']]
            show_safe_link_table(final_report_df, "revenue_report_table")
            
            st.markdown("---")
            total_revenue = final_report_df['服務金額'].astype(int).sum()
            total_services = len(final_report_df)
            
            stat_col1, stat_col2 = st.columns(2)
            with stat_col1:
                st.metric(
                    label="💰 該時段總營業額累計 (Total Revenue)", 
                    value=f"$ {total_revenue:,} 元",
                    delta="實收新台幣現金/刷卡"
                )
            with stat_col2:
                st.metric(
                    label="🐾 該時段總服務寵物架次 (Total Services)", 
                    value=f"{total_services} 次"
                )

# ==================== 頁面 6：編輯客戶基本資料 ====================
elif page == "✏️ 編輯客戶基本資料":
    st.title("✏️ 修改已存在之寵物基本資料")
    chip_list = st.session_state.pet_db['晶片號碼'].astype(str).tolist()
    if not chip_list: st.info("目前資料庫中尚無資料可供修改。")
    else:
        edit_chip = st.selectbox("請選擇要修改的寵物晶片號碼/識別碼：", chip_list, key="edit_select_chip")
        current_idx = st.session_state.pet_db[st.session_state.pet_db['晶片號碼'].astype(str) == edit_chip].index[0]
        pet_info = st.session_state.pet_db.loc[current_idx]
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("🧬 寵物晶片號碼 / 識別碼 (不可修改)", value=str(pet_info['晶片號碼']), disabled=True)
            new_pet_name = st.text_input("寵物名字", value=str(pet_info['寵物名字']))
            type_options = ["狗", "貓", "其他"]
            type_idx = type_options.index(pet_info['種類']) if str(pet_info['種類']) in type_options else 0
            new_pet_type = st.selectbox("寵物種類", type_options, index=type_idx)
            breed_init = "" if pd.isna(pet_info['品種']) or str(pet_info['品種']) == 'nan' else str(pet_info['品種'])
            new_pet_breed = st.text_input("品種", value=breed_init)
            gender_options = ["公", "母"]
            gender_idx = gender_options.index(pet_info['性別']) if str(pet_info['性別']) in gender_options else 0
            new_gender = st.radio("性別", gender_options, index=gender_idx)
            new_is_neutered = st.checkbox("已絕育", value=(str(pet_info['已絕育']) == "是"))
        with col2:
            new_owner_name = st.text_input("主人姓名", value=str(pet_info['主人姓名']))
            new_owner_phone = st.text_input("主人手機號碼", value=str(pet_info['主人手機']))
            new_will_bite = st.checkbox("🔥 注意：這隻寵物會咬人！", value=(str(pet_info['會咬人']) == "🚨會咬人"))
            old_dis = "" if pd.isna(pet_info['疾病說明']) or str(pet_info['疾病說明']) == 'nan' else str(pet_info['疾病說明'])
            old_not = "" if pd.isna(pet_info['注意事項']) or str(pet_info['注意事項']) == 'nan' else str(pet_info['注意事項'])
            new_disease_detail = st.text_area("具體病情說明", value=old_dis)
            new_special_notes = st.text_area("美容特別注意事項", value=old_not)
            new_uploaded_files = st.file_uploader("📸 更新照片 (留空則保留原相片)", type=["jpg", "png", "jpeg"], accept_multiple_files=True, key="edit_photos")

        if st.button("🔥 確定修改並更新基本資料庫", use_container_width=True):
            if not new_pet_name.strip() or not new_owner_phone.strip(): st.warning("⚠️ 寵物名字與主人手機為必填欄位！")
            else:
                p1, p2, p3 = pet_info['照片檔名_1'], pet_info['照片檔名_2'], pet_info['照片檔名_3']
                if new_uploaded_files:
                    photo_filenames = ["none", "none", "none"]
                    for i, current_file in enumerate(new_uploaded_files[:3]):
                        file_ext = current_file.name.split(".")[-1]
                        filename = f"{edit_chip}_{i+1}.{file_ext}"
                        photo_filenames[i] = filename
                        with open(os.path.join(IMAGE_DIR, filename), "wb") as f: f.write(current_file.getbuffer())
                    p1, p2, p3 = photo_filenames[0], photo_filenames[1], photo_filenames[2]

                st.session_state.pet_db.loc[current_idx, '寵物名字'] = new_pet_name.strip()
                st.session_state.pet_db.loc[current_idx, '種類'] = new_pet_type
                st.session_state.pet_db.loc[current_idx, '品種'] = new_pet_breed.strip()
                st.session_state.pet_db.loc[current_idx, '性別'] = new_gender
                st.session_state.pet_db.loc[current_idx, '已絕育'] = "是" if new_is_neutered else "否"
                st.session_state.pet_db.loc[current_idx, '主人姓名'] = new_owner_name.strip()
                st.session_state.pet_db.loc[current_idx, '主人手機'] = new_owner_phone.strip()
                st.session_state.pet_db.loc[current_idx, '會咬人'] = "🚨會咬人" if new_will_bite else "否"
                st.session_state.pet_db.loc[current_idx, '疾病說明'] = new_disease_detail
                st.session_state.pet_db.loc[current_idx, '注意事項'] = new_special_notes
                st.session_state.pet_db.loc[current_idx, '照片檔名_1'] = p1
                st.session_state.pet_db.loc[current_idx, '照片檔名_2'] = p2
                st.session_state.pet_db.loc[current_idx, '照片檔名_3'] = p3
                st.session_state.pet_db.to_csv(DB_FILE, index=False, encoding='utf-8-sig')
                st.success(f"✨ 基本資料已完美更新！")
                st.rerun()

# ==================== 頁面 7：新增服務消費紀錄 ====================
elif page == "💰 新增服務消費紀錄":
    st.title("💰 紀錄老客戶本次光臨消費流水帳")
    chip_list = st.session_state.pet_db['晶片號碼'].astype(str).tolist()
    if not chip_list:
        st.info("目前系統內尚無任何寵物客戶主檔案，請先去「新增客戶主檔案」建立資料。")
    else:
        select_chip = st.selectbox("請選擇來店消費的寵物晶片號碼/識別碼：", chip_list, key="add_record_select")
        pet_info = st.session_state.pet_db[st.session_state.pet_db['晶片號碼'].astype(str) == select_chip].iloc[0]
        
        st.success(f"🔍 識別成功！ 寵物名字：{pet_info['寵物名字']} ({pet_info['種類']}) | 主人手機：{pet_info['主人手機']}")
        if str(pet_info['會咬人']) == "🚨會咬人": st.error("🚨 警告：這隻寵物會咬人！美容時請特別小心！")
        
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            service_date = st.date_input("📅 服務日期", datetime.today())
            service_price = st.number_input("💰 服務金額", min_value=0, step=100, value=0)
        with col2:
            service_notes = st.text_area("✍️ 本次服務特別備註事項 (例如：洗藥浴、剪短、拔耳毛等)")

        if st.button("➕ 確認並永久加載此筆消費流水帳", use_container_width=True):
            new_service_data = {
                '晶片號碼': str(pet_info['晶片號碼']), 
                '寵物名字': str(pet_info['寵物名字']), 
                '主人手機': str(pet_info['主人手機']),
                '服務日期': service_date.strftime('%Y-%m-%d'), 
                '服務金額': int(service_price), 
                '備註事項': service_notes
            }
            st.session_state.service_db = pd.concat([st.session_state.service_db, pd.DataFrame([new_service_data])], ignore_index=True)
            st.session_state.service_db.to_csv(SERVICE_DB_FILE, index=False, encoding='utf-8-sig')
            st.success(f"🎉 已成功為 {pet_info['寵物名字']} 追加一筆 ${int(service_price)} 元的歷史服務紀錄！")

# ==================== 頁面 8：編輯服務消費紀錄 ====================
elif page == "🛠️ 編輯服務消費紀錄":
    st.title("🛠️ 修改過往之服務與消費歷史紀錄")
    if st.session_state.service_db.empty:
        st.info("目前流水帳資料庫中尚無任何服務紀錄可供修改。")
    else:
        unique_chips_in_service = st.session_state.service_db['晶片號碼'].unique().tolist()
        select_chip = st.selectbox("請選擇欲修改紀錄的寵物晶片號碼/識別碼：", unique_chips_in_service, key="edit_record_select_chip")
        
        pet_records = st.session_state.service_db[st.session_state.service_db['晶片號碼'] == select_chip]
        
        record_options = []
        for idx in pet_records.index:
            row = pet_records.loc[idx]
            note_summary = str(row['備註事項'])[:15] if not pd.isna(row['備註事項']) else ""
            option_text = f"【紀錄序號 {idx}】 日期: {row['服務日期']} | 金額: {row['服務金額']} 元 | 備註: {note_summary}..."
            record_options.append((idx, option_text))
            
        selected_record_tuple = st.selectbox(
            "請選擇欲修改的「那一筆」具體日期消費紀錄：", 
            record_options, 
            format_func=lambda x: x[1]
        )
        
        target_db_idx = selected_record_tuple[0]
        record_info = st.session_state.service_db.loc[target_db_idx]
        
        st.markdown("---")
        st.info(f"🔮 正在編輯 寵物：{record_info['寵物名字']} 的歷史紀錄。")
        
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("🧬 寵物晶片號碼 (不可修改)", value=str(record_info['晶片號碼']), disabled=True)
            st.text_input("寵物名字 (不可修改)", value=str(record_info['寵物名字']), disabled=True)
            st.text_input("主人手機 (不可修改)", value=str(record_info['主人手機']), disabled=True)
        with col2:
            try: old_date = datetime.strptime(str(record_info['服務日期']), '%Y-%m-%d')
            except: old_date = datetime.today()
            
            edit_service_date = st.date_input("📅 服務日期修改", old_date)
            edit_service_price = st.number_input("💰 服務金額修改", min_value=0, step=100, value=int(record_info['服務金額']))
            
            old_notes_val = "" if pd.isna(record_info['備註事項']) or str(record_info['備註事項']) == 'nan' else str(record_info['備註事項'])
            edit_service_notes = st.text_area("✍️ 服務備註事項修改", value=old_notes_val)

        if st.button("🔥 確定修正此筆消費紀錄並更新檔案", use_container_width=True):
            st.session_state.service_db.loc[target_db_idx, '服務日期'] = edit_service_date.strftime('%Y-%m-%d')
            st.session_state.service_db.loc[target_db_idx, '服務金額'] = int(edit_service_price)
            st.session_state.service_db.loc[target_db_idx, '備註事項'] = edit_service_notes
            
            st.session_state.service_db.to_csv(SERVICE_DB_FILE, index=False, encoding='utf-8-sig')
            st.success(f"✨ 序號 {target_db_idx} 的消費紀錄已完美更新存檔！")
            st.rerun()