import streamlit as st
import pandas as pd
import os
import hashlib
from PIL import Image
from datetime import datetime, date

# ==================== 設定常數與資料庫檔案 ====================
IMAGE_DIR = "pet_photos"
DB_FILE = "pet_data.csv"
SERVICE_DB_FILE = "pet_service_records.csv"
USER_DB_FILE = "user_db.csv"  # 新增：使用者帳密資料庫

# 自動建立相片資料夾
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

# 3. 使用者帳密欄位
USER_COLUMNS = ['帳號', '密碼雜湊']

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

# 🔄 初始化 3：使用者帳密資料庫
if not os.path.exists(USER_DB_FILE):
    st.session_state.user_db = pd.DataFrame(columns=USER_COLUMNS)
    st.session_state.user_db.to_csv(USER_DB_FILE, index=False, encoding='utf-8-sig')
else:
    st.session_state.user_db = pd.read_csv(USER_DB_FILE, dtype=str)

# 設定網頁佈局
st.set_page_config(layout="wide", page_title="🐾 寵物美容管理系統", page_icon="🐶")

# ==================== 🔑 密碼加密與帳號驗證函式 ====================
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_login(username, password):
    hashed_pwd = make_hashes(password)
    db = st.session_state.user_db
    # 檢查帳號與加密後的密碼是否相符
    match = db[(db['帳號'] == username) & (db['密碼雜湊'] == hashed_pwd)]
    return not match.empty

def register_user(username, password):
    db = st.session_state.user_db
    if username in db['帳號'].values:
        return False
    hashed_pwd = make_hashes(password)
    new_user = pd.DataFrame([{'帳號': username, '密碼雜湊': hashed_pwd}])
    st.session_state.user_db = pd.concat([db, new_user], ignore_index=True)
    st.session_state.user_db.to_csv(USER_DB_FILE, index=False, encoding='utf-8-sig')
    return True

# ==================== 狀態初始化 ====================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_name' not in st.session_state:
    st.session_state.user_name = ""
if 'current_page' not in st.session_state:
    st.session_state.current_page = "📝 新增客戶主檔案"
if 'target_chip' not in st.session_state:
    st.session_state.target_chip = ""

# ==================== 📋 登入與註冊頁面 UI ====================
if not st.session_state.logged_in:
    st.title("🔐 寵物美容管理系統 - 請先登入")
    
    login_tab, register_tab = st.tabs(["🔑 使用者登入", "🆕 註冊新帳號"])
    
    with login_tab:
        login_user = st.text_input("帳戶名稱", key="login_user_input").strip()
        login_pass = st.text_input("密碼", type="password", key="login_pass_input")
        
        if st.button("確認登入", use_container_width=True):
            if not login_user or not login_pass:
                st.warning("請輸入帳號與密碼！")
            elif check_login(login_user, login_pass):
                st.session_state.logged_in = True
                st.session_state.user_name = login_user
                st.success(f"🎉 歡迎回來，{login_user}！正在載入系統...")
                st.rerun()
            else:
                st.error("❌ 帳號或密碼錯誤，請重新輸入。")
                
    with register_tab:
        st.info("💡 商業提示：首位使用者登入前，請先在此建立管理員帳號。")
        new_user = st.text_input("建立新帳戶名稱", key="reg_user_input").strip()
        new_pass = st.text_input("建立新密碼", type="password", key="reg_pass_input")
        confirm_pass = st.text_input("再次輸入新密碼", type="password", key="reg_pass_confirm")
        
        if st.button("註冊帳號", use_container_width=True):
            if not new_user or not new_pass:
                st.warning("帳號與密碼不能留空！")
            elif new_pass != confirm_pass:
                st.error("❌ 兩次輸入的密碼不一致！")
            else:
                if register_user(new_user, new_pass):
                    st.success("🎉 帳號註冊成功！請切換至「使用者登入」分頁進行登入。")
                else:
                    st.error("❌ 該帳戶名稱已存在，請更換名稱。")
    st.stop()  # 阻斷後續程式碼，未登入前不顯示任何功能頁面

# ==================== ✨ 網址參數超連結跳轉核心邏輯 ====================
query_params = st.query_params
if "chip" in query_params:
    captured_chip = str(query_params["chip"]).strip()
    if st.session_state.target_chip != captured_chip or st.session_state.current_page != "🔍 晶片詳細查詢":
        st.session_state.current_page = "🔍 晶片詳細查詢"
        st.session_state.target_chip = captured_chip
        st.query_params.clear()
        st.rerun()

# ==================== 🌐 後台側邊欄導覽選單 (已登入狀態) ====================
st.sidebar.title(f"👤 當前使用者: {st.session_state.user_name}")

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

# 登出按鈕
st.sidebar.markdown("---")
if st.sidebar.button("🚪 安全登出系統", use_container_width=True):
    st.session_state.logged_in = False
    st.session_state.user_name = ""
    st.rerun()

page = st.session_state.current_page

# 🛠️ 輔助函式：建立「安全跳轉」表格
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
        if not pet_name.strip() or not owner_phone.strip():
            st.warning("⚠️ 寵物名字與主人手機為必填欄位！")
        else:
            final_chip = chip_number.strip()
            if not final_chip:
                final_chip = f"{pet_name.strip()}_{owner_phone.strip()}"
                st.info(f"💡 偵測到晶片號碼留空，系統已自動生成識別碼：`{final_chip}`")

            if final_chip in st.session_state.pet_db['晶片號碼'].astype(str).values:
                st.error(f"❌ 錯誤：識別碼或晶片號碼 `{final_chip}` 已存在於系統中！")
            else:
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
elif page == "🔍 開階寵物搜尋":
    # (此處保持原邏輯不變，為節省空間簡寫)
    st.title("🔍 進階寵物客戶多條件搜尋")
    # ...[保持你原本進階搜尋頁面的所有程式碼內容]...
    pass

# ==================== 頁面 5：📊 營業金額統計 ====================
elif page == "📊 營業金額統計":
    st.title("📊 寵物美容服務營業額與特定時段統計")
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
        period_records = service_df_temp[(service_df_temp['parsed_date'] >= start_date) & (service_df_temp['parsed_date'] <= end_date)]
        period_records = period_records.sort_values(by='服務日期', ascending=False)
        
        if period_records.empty:
            st.warning(f"🔍 在 {start_date} 至 {end_date} 期間內，沒有找到任何服務消費紀錄。")
        else:
            final_report_df = period_records[['晶片號碼', '寵物名字', '主人手機', '服務日期', '服務金額', '備註事項']]
            show_safe_link_table(final_report_df, "revenue_report_table")
            total_revenue = final_report_df['服務金額'].astype(int).sum()
            total_services = len(final_report_df)
            stat_col1, stat_col2 = st.columns(2)
            with stat_col1:
                st.metric(label="💰 該時段總營業額累計", value=f"$ {total_revenue:,} 元")
            with stat_col2:
                st.metric(label="🐾 該時段總服務寵物架次", value=f"{total_services} 次")

# ==================== 頁面 6：編輯客戶基本資料 ====================
elif page == "✏️ 編輯客戶基本資料":
    st.title("✏️ 修改已存在之寵物基本資料")
    chip_list = st.session_state.pet_db['晶片號碼'].astype(str).tolist()
    if not chip_list: st.info("目前資料庫中尚無資料可供修改。")
    else:
        edit_chip = st.selectbox("請選擇要修改的寵物晶片號碼/識別碼：", chip_list, key="edit_select_chip")
        current_idx = st.session_state.pet_db[st.session_state.pet_db['晶片號碼'].astype(str) == edit_chip].index[0]
        pet_info = st.session_state.pet_db.loc[current_idx]
        
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("🧬 寵物晶片號碼 / 識別碼 (不可修改)", value=str(pet_info['晶片號碼']), disabled=True)
            new_pet_name = st.text_input("寵物名字", value=str(pet_info['寵物名字']))
            type_options = ["狗", "貓", "其他"]
            type_idx = type_options.index(pet_info['種類']) if str(pet_info['種類']) in type_options else 0
            new_pet_type = st.selectbox("寵物種類", type_options, index=type_idx)
            new_pet_breed = st.text_input("品種", value="" if pd.isna(pet_info['品種']) else str(pet_info['品種']))
            new_gender = st.radio("性別", ["公", "母"], index=0 if pet_info['性別']=="公" else 1)
            new_is_neutered = st.checkbox("已絕育", value=(str(pet_info['已絕育']) == "是"))
        with col2:
            new_owner_name = st.text_input("主人姓名", value=str(pet_info['主人姓名']))
            new_owner_phone = st.text_input("主人手機號碼", value=str(pet_info['主人手機']))
            new_will_bite = st.checkbox("🔥 注意：這隻寵物會咬人！", value=(str(pet_info['會咬人']) == "🚨會咬人"))
            new_disease_detail = st.text_area("具體病情說明", value="" if pd.isna(pet_info['疾病說明']) else str(pet_info['疾病說明']))
            new_special_notes = st.text_area("美容特別注意事項", value="" if pd.isna(pet_info['注意事項']) else str(pet_info['注意事項']))
            new_uploaded_files = st.file_uploader("📸 更新照片 (留空則保留原相片)", type=["jpg", "png", "jpeg"], accept_multiple_files=True)

        if st.button("🔥 確定修改並更新基本資料庫", use_container_width=True):
            if not new_pet_name.strip() or not new_owner_phone.strip(): st.warning("⚠️ 欄位必填！")
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

                # 寫入更新
                st.session_state.pet_db.loc[current_idx, ['寵物名字', '種類', '品種', '性別', '已絕育', '主人姓名', '主人手機', '會咬人', '疾病說明', '注意事項', '照片檔名_1', '照片檔名_2', '照片檔名_3']] = [
                    new_pet_name.strip(), new_pet_type, new_pet_breed.strip(), new_gender, "是" if new_is_neutered else "否",
                    new_owner_name.strip(), new_owner_phone.strip(), "🚨會咬人" if new_will_bite else "否", new_disease_detail, new_special_notes, p1, p2, p3
                ]
                st.session_state.pet_db.to_csv(DB_FILE, index=False, encoding='utf-8-sig')
                st.success("✨ 基本資料已完美更新！")
                st.rerun()

# ==================== 頁面 7：新增服務消費紀錄 ====================
elif page == "💰 新增服務消費紀錄":
    st.title("💰 紀錄老客戶本次光臨消費流水帳")
    chip_list = st.session_state.pet_db['晶片號碼'].astype(str).tolist()
    if not chip_list: st.info("請先去新增客戶檔案。")
    else:
        select_chip = st.selectbox("請選擇來店消費的寵物晶片號碼/識別碼：", chip_list)
        pet_info = st.session_state.pet_db[st.session_state.pet_db['晶片號碼'].astype(str) == select_chip].iloc[0]
        
        st.success(f"🔍 識別成功！ 寵物名字：{pet_info['寵物名字']} | 主人手機：{pet_info['主人手機']}")
        if str(pet_info['會咬人']) == "🚨會咬人": st.error("🚨 警告：這隻寵物會咬人！美容時請特別小心！")
        
        col1, col2 = st.columns(2)
        with col1:
            service_date = st.date_input("📅 服務日期", datetime.today())
            service_price = st.number_input("💰 服務金額", min_value=0, step=100)
        with col2:
            service_notes = st.text_area("✍️ 本次服務特別備註事項")

        if st.button("➕ 確認並永久加載此筆消費流水帳", use_container_width=True):
            new_service_data = {
                '晶片號碼': str(pet_info['晶片號碼']), '寵物名字': str(pet_info['寵物名字']), '主人手機': str(pet_info['主人手機']),
                '服務日期': service_date.strftime('%Y-%m-%d'), '服務金額': int(service_price), '備註事項': service_notes
            }
            st.session_state.service_db = pd.concat([st.session_state.service_db, pd.DataFrame([new_service_data])], ignore_index=True)
            st.session_state.service_db.to_csv(SERVICE_DB_FILE, index=False, encoding='utf-8-sig')
            st.success(f"🎉 已成功追加消費紀錄！")

# ==================== 頁面 8：編輯服務消費紀錄 ====================
elif page == "🛠️ 編輯服務消費紀錄":
    st.title("🛠️ 修改過往之服務與消費歷史紀錄")
    if st.session_state.service_db.empty: st.info("尚無消費數據。")
    else:
        unique_chips_in_service = st.session_state.service_db['晶片號碼'].unique().tolist()
        select_chip = st.selectbox("請選擇欲修改紀錄的寵物晶片號碼：", unique_chips_in_service)
        pet_records = st.session_state.service_db[st.session_state.service_db['晶片號碼'] == select_chip]
        
        record_options = [(idx, f"【序號 {idx}】 日期: {pet_records.loc[idx, '服務日期']} | 金額: {pet_records.loc[idx, '服務金額']} 元") for idx in pet_records.index]
        selected_record_tuple = st.selectbox("請選擇欲修改的具體日期消費紀錄：", record_options, format_func=lambda x: x[1])
        
        target_db_idx = selected_record_tuple[0]
        record_info = st.session_state.service_db.loc[target_db_idx]
        
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("寵物名字 (不可修改)", value=str(record_info['寵物名字']), disabled=True)
        with col2:
            edit_service_date = st.date_input("📅 服務日期修改", datetime.strptime(str(record_info['服務日期']), '%Y-%m-%d'))
            edit_service_price = st.number_input("💰 服務金額修改", min_value=0, value=int(record_info['服務金額']))
            edit_service_notes = st.text_area("✍️ 服務備註事項修改", value="" if pd.isna(record_info['備註事項']) else str(record_info['備註事項']))

        if st.button("🔥 確定修正此筆消費紀錄並更新檔案", use_container_width=True):
            st.session_state.service_db.loc[target_db_idx, ['服務日期', '服務金額', '備註事項']] = [edit_service_date.strftime('%Y-%m-%d'), int(edit_service_price), edit_service_notes]
            st.session_state.service_db.to_csv(SERVICE_DB_FILE, index=False, encoding='utf-8-sig')
            st.success("✨ 消費紀錄已完美更新存檔！")
            st.rerun()