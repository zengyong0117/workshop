import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, time, timedelta
import os
import calendar
import numpy as np
import json

# --- 頁面設定 ---
st.set_page_config(page_title="Trading Dashboard", layout="wide", page_icon="📈")

# --- 設定檔案路徑 ---
DATA_FILE = 'journal_data.csv'
ACCOUNTS_FILE = 'accounts.json'
IMG_DIR = 'trade_images'

if not os.path.exists(IMG_DIR):
    os.makedirs(IMG_DIR)

# --- Session State 初始化 ---
if 'adding_account' not in st.session_state:
    st.session_state.adding_account = False
if 'temp_account' not in st.session_state:
    st.session_state.temp_account = None 
if 'selected_account_index' not in st.session_state:
    st.session_state.selected_account_index = 0
if 'cal_date' not in st.session_state:
    st.session_state.cal_date = date.today()

# --- CSS 樣式 ---
st.markdown("""
    <style>
    .block-container { padding-top: 1rem; padding-bottom: 3rem; }
    
    /* 卡片樣式 */
    .metric-card {
        background-color: #262730;
        border-radius: 8px;
        padding: 15px 20px;
        margin-bottom: 15px;
        border: 1px solid #363945;
        height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        position: relative;
    }
    .metric-label { font-size: 13px; color: #A0A0A0; font-weight: 500; text-transform: uppercase; margin-bottom: 4px; }
    .metric-value { font-size: 28px; font-weight: 700; color: #FFFFFF; margin: 0; }
    .metric-sub { font-size: 12px; color: #808080; margin-top: 4px; }

    /* 圓餅圖樣式 */
    .donut-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        height: 100%;
    }
    .donut-chart {
        width: 70px;
        height: 70px;
        border-radius: 50%;
        position: relative;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    .donut-chart::after {
        content: "";
        width: 50px;
        height: 50px;
        border-radius: 50%;
        background-color: #262730;
        position: absolute;
    }

    /* Trade Direction Badge */
    .direction-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        height: 100%;
    }
    .ring-container {
        position: relative;
        width: 80px;
        height: 80px;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    .ring-chart {
        width: 65px;
        height: 65px;
        border-radius: 50%;
    }
    .ring-mask {
        position: absolute;
        width: 55px;
        height: 55px;
        background-color: #262730;
        border-radius: 50%;
    }
    .badge {
        position: absolute;
        font-size: 11px;
        font-weight: bold;
        padding: 2px 6px;
        border-radius: 4px;
        background-color: #16171a;
        box-shadow: 0 0 2px rgba(0,0,0,0.5);
        z-index: 10;
    }
    .badge-left { left: -12px; color: #EF553B; border: 1px solid #3a1a1a; }
    .badge-right { right: -12px; color: #00CC96; border: 1px solid #1a3a2a; }

    /* --- 月曆 CSS Grid --- */
    .calendar-container {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 1px;
        background-color: #262730;
        border: 1px solid #363945;
        border-radius: 10px;
        padding: 10px;
        margin-top: 5px;
    }
    
    .cal-header {
        background-color: transparent;
        color: #A0A0A0;
        text-align: center;
        padding: 10px 0;
        font-size: 12px;
        font-weight: bold;
        text-transform: uppercase;
    }
    
    .cal-cell {
        background-color: #1A1C20;
        min-height: 100px;
        padding: 8px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-start;
        transition: background-color 0.15s;
        margin: 1px;
        border-radius: 4px;
    }
    
    .cal-cell-empty {
        background-color: #0E1117 !important;
        opacity: 0.3;
    }
    
    /* Colors */
    .win-bg { background-color: #1a4025 !important; }
    .cal-cell.win-bg:hover { background-color: #245735 !important; border: 1px solid #00CC96; cursor: pointer; }

    .loss-bg { background-color: #401a1a !important; }
    .cal-cell.loss-bg:hover { background-color: #572424 !important; border: 1px solid #EF553B; cursor: pointer; }

    .cal-cell:not(.cal-cell-empty):not(.win-bg):not(.loss-bg):hover {
        background-color: #000000 !important;
        border: 1px solid #555;
    }

    .cal-date { font-size: 13px; color: #D0D0D0; margin-bottom: 8px; }
    .cal-pnl { font-size: 20px; font-weight: 900; text-align: center; }
    .cal-trades { font-size: 11px; color: #909090; text-align: center; margin-top: 5px; }
    
    /* 週六格子樣式 */
    .cal-week-title {
        font-size: 14px;
        font-weight: bold;
        color: #FFFFFF;
        margin-top: 5px;
        margin-bottom: 2px;
    }
    .cal-week-pnl {
        font-size: 22px;
        font-weight: 900;
        margin-bottom: 2px;
        line-height: 1.2;
    }
    .cal-week-trades {
        font-size: 12px;
        color: #AAAAAA;
        font-weight: 500;
    }
    
    .text-green { color: #00CC96; }
    .text-red { color: #EF553B; }
    .text-white { color: #FFFFFF; }
    
    .today-border { border: 2px solid #00A6FF; z-index: 10; }
    
    /* --- 導航按鈕 --- */
    section[data-testid="stMain"] div[data-testid="column"] button {
        background-color: transparent !important;
        border: 0px solid transparent !important;
        outline: none !important;
        box-shadow: none !important;
        color: #808080 !important;
        padding: 0px !important;
        font-size: 32px !important;
        line-height: 1 !important;
        min-height: 0px !important;
        margin: 0 !important;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    section[data-testid="stMain"] div[data-testid="column"] button:hover,
    section[data-testid="stMain"] div[data-testid="column"] button:focus,
    section[data-testid="stMain"] div[data-testid="column"] button:active,
    section[data-testid="stMain"] div[data-testid="column"] button:focus:not(:active) {
        color: #FFFFFF !important;
        background-color: transparent !important;
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
        text-decoration: none !important;
    }
    
    .month-nav-title {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100%;
        font-size: 18px;
        font-weight: bold; 
        color: white;
        padding-top: 5px; 
    }
    
    .month-pl-display {
        text-align: center; 
        font-size: 24px; 
        font-weight: bold; 
        color: #A0A0A0;
    }

    /* --- V58: Radio Button 矩形樣式修正 --- */
    /* 隱藏預設圓點 */
    div[role="radiogroup"] > label > div:first-child {
        display: none !important;
    }
    /* 容器佈局 */
    div[role="radiogroup"] {
        display: flex;
        flex-direction: row;
        gap: 10px;
        width: 100%;
    }
    /* 選項樣式 */
    div[role="radiogroup"] label {
        background-color: #262730;
        border: 1px solid #444;
        border-radius: 6px;
        padding: 15px 0px; /* 高度加大 */
        flex: 1;
        display: flex;
        justify-content: center;
        align-items: center;
        cursor: pointer;
        transition: all 0.2s;
        margin: 0px !important;
    }
    div[role="radiogroup"] label:hover {
        background-color: #363945;
        border-color: #666;
    }
    /* 選中狀態 (Streamlit 會對選中的 label 內的 p 標籤變色，我們抓取這個特性或使用 data-testid) */
    /* 由於 Streamlit CSS class 變動大，我們用通用屬性 */
    div[role="radiogroup"] label[data-checked="true"] {
        background-color: #444 !important;
        border-color: #00A6FF !important;
    }
    /* 文字 */
    div[role="radiogroup"] p {
        font-size: 16px;
        font-weight: 700;
        margin: 0;
    }

    /* --- Sidebar form enhancement --- */
    .sidebar-form {
        background-color: #1b1d24;
        border: 1px solid #2f313d;
        border-radius: 12px;
        padding: 12px 14px;
        box-shadow: inset 0 0 0 1px rgba(255,255,255,0.02);
    }
    .section-title {
        font-size: 13px;
        letter-spacing: 0.3px;
        color: #9fa2ad;
        text-transform: uppercase;
        font-weight: 700;
        margin: 8px 0 4px 0;
    }
    .pill-label {
        font-size: 12px;
        color: #8b8e99;
        margin-bottom: -6px;
    }
    .preview-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 8px;
        margin-top: 6px;
    }
    .preview-chip {
        background: #13151c;
        border: 1px solid #2a2c35;
        border-radius: 10px;
        padding: 10px;
    }
    .preview-label { color: #b1b4bd; font-size: 11px; text-transform: uppercase; letter-spacing: 0.4px; }
    .preview-value { color: #fff; font-weight: 700; font-size: 18px; margin-top: 4px; }
    </style>
""", unsafe_allow_html=True)

# --- 輔助函數 ---
def format_duration(seconds):
    if pd.isna(seconds) or seconds == 0: return "-"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0: return f"{h}h {m}m"
    return f"{m} min {s} sec"

def format_currency(val):
    return f"${val:,.2f}"

def get_color(val):
    if val > 0: return "green"
    if val < 0: return "red"
    return None

def display_card(label, value, sub_value="", color=None):
    text_color = "white"
    if color == "green": text_color = "#00CC96"
    elif color == "red": text_color = "#EF553B"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value" style="color: {text_color}">{value}</div>
        <div class="metric-sub">{sub_value}</div>
    </div>
    """, unsafe_allow_html=True)

def display_trade_direction_card(long_pct, long_count, short_count):
    total = long_count + short_count
    short_pct = 100 - long_pct
    if total == 0:
        gradient = "#363945"
        main_value = "0.00%"
    else:
        gradient = f"conic-gradient(#EF553B 0% {short_pct}%, #00CC96 {short_pct}% 100%)"
        main_value = f"{long_pct:.2f}%"

    st.markdown(f"""
    <div class="metric-card">
        <div class="direction-container">
            <div>
                <div class="metric-label">Trade Direction %</div>
                <div class="metric-value">{main_value}</div>
            </div>
            <div class="ring-container">
                <div class="badge badge-left">{short_count}</div>
                <div class="ring-chart" style="background: {gradient};"></div>
                <div class="ring-mask"></div>
                <div class="badge badge-right">{long_count}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 核心數據讀取與帳戶管理 (V58: 強制修復缺失欄位) ---
@st.cache_data
def load_accounts():
    if not os.path.exists(ACCOUNTS_FILE):
        accounts = {}
        if os.path.exists(DATA_FILE):
            try:
                df = pd.read_csv(DATA_FILE)
                existing_names = [acc for acc in df['Account'].unique().tolist() if isinstance(acc, str) and acc]
                if not existing_names: existing_names = ['Main Account']
                for name in existing_names: accounts[name] = 50000.0
            except:
                accounts = {'Main Account': 50000.0}
        else:
            accounts = {'Main Account': 50000.0}
            
        with open(ACCOUNTS_FILE, 'w') as f: json.dump(accounts, f)
        return accounts
    
    with open(ACCOUNTS_FILE, 'r') as f: return json.load(f)

def save_accounts(accounts):
    with open(ACCOUNTS_FILE, 'w') as f: json.dump(accounts, f)
    load_accounts.clear()

@st.cache_data
def load_trades():
    columns = [
        'ID', 'Account', 'Date', 'Symbol', 'Direction', 'Size', 
        'Entry', 'Exit', 'SL', 'TP', 'Fees', 'Entry_Time', 'Exit_Time', 
        'PnL', 'Result', 'RR_Plan', 'RR_Actual', 'Strategy', 'Tags', 
        'Notes', 'Image', 'Week_Num'
    ]
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame(columns=columns)
    df = pd.read_csv(DATA_FILE)
    df = df.fillna('')
    
    # V58: 自動修復缺失欄位，防止 KeyError
    missing = False
    expected_cols = {
        'Entry_Time': '00:00:00',
        'Exit_Time': '00:00:00',
        'Account': 'Main Account',
        'Fees': 0.0,
        'Strategy': '',
        'Tags': ''
    }
    
    for col, default_val in expected_cols.items():
        if col not in df.columns:
            df[col] = default_val
            missing = True
    
    df['Date'] = pd.to_datetime(df['Date']).dt.date
    
    if missing: df.to_csv(DATA_FILE, index=False)
    return df

def save_trades(df):
    df.to_csv(DATA_FILE, index=False)
    load_trades.clear()

def change_month(n):
    curr = st.session_state.cal_date
    year, month = curr.year, curr.month
    month += n
    if month > 12:
        month = 1
        year += 1
    elif month < 1:
        month = 12
        year -= 1
    st.session_state.cal_date = date(year, month, 1)

@st.dialog("Create New Account")
def create_account_modal():
    st.write("Setup your new trading account.")
    new_name = st.text_input("Account Name", placeholder="e.g. Topstep 50K")
    initial_bal = st.number_input("Initial Balance ($)", min_value=0.0, value=50000.0, step=1000.0)
    if st.button("Create Account", type="primary"):
        if new_name:
            accounts = load_accounts()
            if new_name in accounts:
                st.error("Account name already exists!")
            else:
                accounts[new_name] = initial_bal
                save_accounts(accounts)
                st.session_state.selected_account_index = list(accounts.keys()).index(new_name)
                st.rerun()
        else:
            st.error("Please enter a name.")

# ==========================================
# 資料載入
# ==========================================
with st.spinner('Loading...'):
    accounts_data = load_accounts()
    trades_df = load_trades()

# ==========================================
# 側邊欄 (UI Updated V58)
# ==========================================
st.sidebar.header("Account")
account_names = list(accounts_data.keys())

if st.session_state.selected_account_index >= len(account_names):
    st.session_state.selected_account_index = 0

selected_account = st.sidebar.selectbox("Select Account", account_names, index=st.session_state.selected_account_index)
st.session_state.selected_account_index = account_names.index(selected_account)

current_balance = accounts_data[selected_account]
st.sidebar.caption(f"Initial Balance: {format_currency(current_balance)}")

if st.sidebar.button("➕ Add New Account"):
    create_account_modal()

with st.sidebar.expander("⚠️ Account Settings"):
    if st.button("Delete This Account", type="primary"):
        if len(account_names) <= 1:
            st.error("Cannot delete the last account.")
        else:
            del accounts_data[selected_account]
            save_accounts(accounts_data)
            trades_df = trades_df[trades_df['Account'] != selected_account]
            save_trades(trades_df)
            st.session_state.selected_account_index = 0
            st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("📝 New Trade Entry")

# 定義常用選項
STRATEGIES = ["Trend Following", "Reversal", "Breakout", "Scalp", "News Fade", "Other"]
MISTAKES = ["FOMO", "Revenge Trading", "Over Sizing", "Hesitation", "Did Not Follow Plan"]
SYMBOLS = ["NQ", "ES", "RTY", "CL", "GC", "BTC", "ETH", "Other"]

st.sidebar.markdown("<div class='sidebar-form'>", unsafe_allow_html=True)
with st.sidebar.form("trade_form", clear_on_submit=True):
    st.markdown("<div class='section-title'>Trade Setup</div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1.2, 1, 1])
    with c1:
        symbol_input = st.selectbox("Symbol", SYMBOLS) 
    with c2:
        size = st.number_input("Lots", min_value=0.01, value=1.0, step=0.1)
    with c3:
        direction = st.radio("Direction", ["Long", "Short"], horizontal=True)

    st.markdown("<div class='section-title'>Execution</div>", unsafe_allow_html=True)
    trade_date = st.date_input("Date", date.today(), max_value=date.today())
    col_entry1, col_entry2 = st.columns(2)
    with col_entry1:
        entry_time = st.time_input("Entry Time", time(9, 30))
        entry_price = st.number_input("Entry Price", format="%.2f")
    with col_entry2:
        exit_time = st.time_input("Exit Time", time(9, 35))
        exit_price = st.number_input("Exit Price", format="%.2f")

    st.markdown("<div class='section-title'>Risk & Targets</div>", unsafe_allow_html=True)
    col_risk1, col_risk2, col_fee = st.columns([1, 1, 1])
    with col_risk1:
        sl_price = st.number_input("Stop Loss", format="%.2f")
    with col_risk2:
        tp_price = st.number_input("Take Profit", format="%.2f")
    with col_fee:
        fees = st.number_input("Fees ($)", min_value=0.0, value=4.0, step=0.5)

    # Preview calculations for better context
    risk = abs(entry_price - sl_price) if sl_price > 0 and entry_price > 0 else 0
    reward = abs(tp_price - entry_price) if tp_price > 0 and entry_price > 0 else 0
    rr_plan = round(reward / risk, 2) if risk > 0 else 0
    potential_pnl = (tp_price - entry_price) * size if direction == "Long" else (entry_price - tp_price) * size
    potential_net = potential_pnl - fees
    risk_amount = risk * size

    preview_html = f"""
    <div class='preview-grid'>
        <div class='preview-chip'>
            <div class='preview-label'>Planned R:R</div>
            <div class='preview-value'>{rr_plan:.2f}</div>
        </div>
        <div class='preview-chip'>
            <div class='preview-label'>Risk per Position</div>
            <div class='preview-value'>${risk_amount:,.2f}</div>
        </div>
        <div class='preview-chip'>
            <div class='preview-label'>TP Gross</div>
            <div class='preview-value'>${potential_pnl:,.2f}</div>
        </div>
        <div class='preview-chip'>
            <div class='preview-label'>TP After Fees</div>
            <div class='preview-value'>${potential_net:,.2f}</div>
        </div>
    </div>
    """
    st.markdown(preview_html, unsafe_allow_html=True)

    st.markdown("<div class='section-title'>Journal & Review</div>", unsafe_allow_html=True)
    strategy = st.selectbox("Strategy", STRATEGIES)
    tags = st.multiselect("Tags / Mistakes", MISTAKES)
    notes = st.text_area("Trade Notes", placeholder="Why did you take this trade?")
    uploaded_file = st.file_uploader("Chart Screenshot", type=['png', 'jpg'])
    
    if st.form_submit_button("💾 Save Trade Log", type="primary", use_container_width=True):
        raw_pnl = (exit_price - entry_price) * size if direction == "Long" else (entry_price - exit_price) * size
        net_pnl = raw_pnl - fees 
        
        risk = abs(entry_price - sl_price) if sl_price > 0 else 1
        reward = abs(tp_price - entry_price) if tp_price > 0 else 0
        actual = abs(exit_price - entry_price)
        
        rr_plan = round(reward / risk, 2) if risk > 0 else 0
        rr_actual = round(actual / risk, 2) if risk > 0 else 0
        
        if net_pnl > 0: result = "Win"
        elif net_pnl < 0: result = "Loss"
        else: result = "Break Even"
        
        img_path = ""
        if uploaded_file:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            img_path = os.path.join(IMG_DIR, f"{ts}.png")
            with open(img_path, "wb") as f: f.write(uploaded_file.getbuffer())

        tags_str = ", ".join(tags)

        new_row = {
            'ID': datetime.now().strftime("%Y%m%d%H%M%S"),
            'Account': selected_account,
            'Date': trade_date, 'Symbol': symbol_input, 'Direction': direction, 'Size': size,
            'Entry': entry_price, 'Exit': exit_price, 'SL': sl_price, 'TP': tp_price, 'Fees': fees,
            'Entry_Time': entry_time, 'Exit_Time': exit_time,
            'PnL': net_pnl, 'Result': result, 'RR_Plan': rr_plan, 'RR_Actual': rr_actual,
            'Strategy': strategy, 'Tags': tags_str,
            'Notes': notes, 'Image': img_path, 'Week_Num': trade_date.isocalendar()[1]
        }
        
        trades_df = pd.concat([trades_df, pd.DataFrame([new_row])], ignore_index=True)
        save_trades(trades_df)
        st.success(f"Saved: {direction} {symbol_input} | PnL: ${net_pnl:.2f}")
        st.rerun()
st.sidebar.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 主版面佈局
# ==========================================
spacer_left, main_container, spacer_right = st.columns([1, 10, 1])

with main_container:
    current_df = trades_df[trades_df['Account'] == selected_account].copy()
    initial_balance = accounts_data.get(selected_account, 50000.0)

    st.title(f"Dashboard: {selected_account}")
    st.markdown("---")

    # 初始化
    total_pnl = 0.0; total_trades = 0; total_lots = 0; win_rate = 0.0
    day_win_rate = 0.0; avg_wl_ratio = 0.0; profit_factor = 0.0
    best_day_pct = 0.0; gross_profit = 0.0; gross_loss = 0.0
    avg_duration = 0; avg_win_duration = 0; avg_loss_duration = 0
    avg_win = 0.0; avg_loss = 0.0
    best_trade = 0.0; worst_trade = 0.0; long_pct = 0.0; long_count = 0; short_count = 0
    most_active_day = "-"; most_profitable_day = "-"; least_profitable_day = "-"
    most_profitable_day_val = 0; least_profitable_day_val = 0
    best_trade_detail = ""; worst_trade_detail = ""

    if not current_df.empty:
        total_pnl = current_df['PnL'].sum()
        total_trades = len(current_df)
        total_lots = current_df['Size'].sum()
        wins = current_df[current_df['Result'] == 'Win']
        losses = current_df[current_df['Result'] == 'Loss']
        
        long_trades = current_df[current_df['Direction'] == 'Long']
        short_trades = current_df[current_df['Direction'] == 'Short']
        long_count = len(long_trades)
        short_count = len(short_trades)
        
        if total_trades > 0:
            win_rate = (len(wins) / total_trades) * 100
            long_pct = (long_count / total_trades) * 100

        if not wins.empty: avg_win = wins['PnL'].mean()
        if not losses.empty: avg_loss = abs(losses['PnL'].mean())
        
        gross_profit = wins['PnL'].sum()
        gross_loss = abs(losses['PnL'].sum())
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else gross_profit
        avg_wl_ratio = (avg_win / avg_loss) if avg_loss > 0 else 0
        
        daily_stats = current_df.groupby('Date')['PnL'].sum()
        total_days = len(daily_stats)
        winning_days = len(daily_stats[daily_stats > 0])
        day_win_rate = (winning_days / total_days * 100) if total_days > 0 else 0
        max_day_profit = daily_stats.max()
        if max_day_profit > 0 and gross_profit > 0: best_day_pct = (max_day_profit / gross_profit) * 100
        
        best_row = current_df.loc[current_df['PnL'].idxmax()]
        worst_row = current_df.loc[current_df['PnL'].idxmin()]
        best_trade = best_row['PnL']
        worst_trade = worst_row['PnL']
        best_trade_detail = f"{best_row['Direction']} {best_row['Symbol']}"
        worst_trade_detail = f"{worst_row['Direction']} {worst_row['Symbol']}"

        current_df['Day_Name'] = pd.to_datetime(current_df['Date']).dt.day_name()
        daily_sum = current_df.groupby('Day_Name')['PnL'].sum()
        daily_count = current_df['Day_Name'].value_counts()
        if not daily_count.empty: most_active_day = daily_count.idxmax()
        if not daily_sum.empty:
            most_profitable_day = daily_sum.idxmax()
            most_profitable_day_val = daily_sum.max()
            least_profitable_day = daily_sum.idxmin()
            least_profitable_day_val = daily_sum.min()

        def calc_seconds(row):
            try:
                dt_date = pd.to_datetime(row['Date']).date()
                et = datetime.strptime(str(row['Entry_Time']), "%H:%M:%S").time()
                xt = datetime.strptime(str(row['Exit_Time']), "%H:%M:%S").time()
                start = datetime.combine(dt_date, et); end = datetime.combine(dt_date, xt)
                if end < start: return 0 
                return (end - start).total_seconds()
            except: return 0

        current_df['Duration_Sec'] = current_df.apply(calc_seconds, axis=1)
        avg_duration = current_df['Duration_Sec'].mean()
        if not wins.empty: avg_win_duration = current_df[current_df['Result'] == 'Win']['Duration_Sec'].mean()
        if not losses.empty: avg_loss_duration = current_df[current_df['Result'] == 'Loss']['Duration_Sec'].mean()

    # --- Grid Layout (V54 Fixed Order) ---
    r1c1, r1c2, r1c3 = st.columns(3)
    with r1c1: display_card("Total P&L", format_currency(total_pnl), color=get_color(total_pnl))
    with r1c2: display_card("Trade Win %", f"{win_rate:.1f}%")
    with r1c3: 
        sub_html = f'<span style="color:#00CC96">{format_currency(avg_win)}</span> &nbsp; <span style="color:#EF553B">-{format_currency(avg_loss)}</span>'
        display_card("Avg Win / Avg Loss", f"{avg_wl_ratio:.2f}", sub_html)

    r2c1, r2c2, r2c3 = st.columns(3)
    with r2c1: display_card("Day Win %", f"{day_win_rate:.1f}%")
    with r2c2: 
        sub_html = f'<span style="color:#00CC96">{format_currency(gross_profit)}</span> &nbsp; <span style="color:#EF553B">-{format_currency(gross_loss)}</span>'
        display_card("Profit Factor", f"{profit_factor:.2f}", sub_html)
    with r2c3: display_card("Best Day % of Total Profit", f"{best_day_pct:.1f}%")

    st.markdown("---")

    d1c1, d1c2, d1c3 = st.columns(3)
    with d1c1: display_card("Most Active Day", most_active_day)
    with d1c2: display_card("Most Profitable Day", most_profitable_day, format_currency(most_profitable_day_val), get_color(most_profitable_day_val))
    with d1c3: display_card("Least Profitable Day", least_profitable_day, format_currency(least_profitable_day_val), get_color(least_profitable_day_val))

    d2c1, d2c2, d2c3 = st.columns(3)
    with d2c1: display_card("Total Trades", str(total_trades))
    with d2c2: display_card("Total Lots", str(total_lots))
    with d2c3: display_card("Avg Duration", format_duration(avg_duration))

    # Row 3: Time Duration (2 Cols)
    d3c1, d3c2 = st.columns(2)
    with d3c1: display_card("Avg Win Duration", format_duration(avg_win_duration))
    with d3c2: display_card("Avg Loss Duration", format_duration(avg_loss_duration))

    # Row 4: Money & Direction (3 Cols)
    d4c1, d4c2, d4c3 = st.columns(3)
    with d4c1: display_card("Avg Winning Trade", format_currency(avg_win), color=get_color(avg_win))
    with d4c2: display_card("Avg Losing Trade", format_currency(avg_loss), color=get_color(-avg_loss)) 
    with d4c3: display_trade_direction_card(long_pct, long_count, short_count)

    d5c1, d5c2 = st.columns(2)
    with d5c1: display_card("Best Trade", format_currency(best_trade), best_trade_detail, get_color(best_trade))
    with d5c2: display_card("Worst Trade", format_currency(worst_trade), worst_trade_detail, get_color(worst_trade))

    st.markdown("---")

    # --- 1. 資金曲線 ---
    st.markdown("### Daily Account Balance")
    
    if not current_df.empty:
        df_sorted = current_df.sort_values('Date')
        daily_pnl = df_sorted.groupby('Date')['PnL'].sum().reset_index()
        daily_pnl['Cumulative_PnL'] = daily_pnl['PnL'].cumsum()
        daily_pnl['Balance'] = initial_balance + daily_pnl['Cumulative_PnL']
        
        start_date = daily_pnl['Date'].min() - timedelta(days=1)
        start_row = pd.DataFrame({'Date': [start_date], 'Balance': [initial_balance]})
        chart_df = pd.concat([start_row, daily_pnl[['Date', 'Balance']]], ignore_index=True)
        
        fig_equity = px.area(chart_df, x='Date', y='Balance', template="plotly_dark")
        y_min = chart_df['Balance'].min(); y_max = chart_df['Balance'].max()
        padding = max((y_max - y_min) * 0.1, 100)
        min_range = y_min - padding; max_range = y_max + padding
        fig_equity.update_traces(line_color='#00CC96', fillcolor='rgba(0, 204, 150, 0.2)')
    else:
        dates = [date.today() - timedelta(days=i) for i in range(5, -1, -1)]
        fig_equity = px.line(x=dates, y=[initial_balance]*6, template="plotly_dark")
        fig_equity.update_traces(line_color='#808080')
        min_range = initial_balance - 300; max_range = initial_balance + 300

    fig_equity.update_layout(
        yaxis=dict(range=[min_range, max_range], dtick=None, tickformat=".0f", gridcolor="#363945", title="Balance", fixedrange=True),
        xaxis=dict(tickformat="%m/%d", fixedrange=True),
        margin=dict(l=10, r=10, t=30, b=30),
        height=350,
        dragmode=False
    )
    st.plotly_chart(fig_equity, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': False})

    st.markdown("---")

    # --- 2. 月曆 ---
    cal_year = st.session_state.cal_date.year
    cal_month = st.session_state.cal_date.month
    
    if not current_df.empty:
        current_df['DateObj'] = pd.to_datetime(current_df['Date'])
        monthly_df = current_df[
            (current_df['DateObj'].dt.year == cal_year) & 
            (current_df['DateObj'].dt.month == cal_month)
        ]
        monthly_pnl_sum = monthly_df['PnL'].sum()
    else:
        monthly_pnl_sum = 0.0
    
    month_str = st.session_state.cal_date.strftime("%b %Y")
    pnl_color = "#00CC96" if monthly_pnl_sum >= 0 else "#EF553B"

    c_nav_left, c_nav_center, c_nav_right = st.columns([1, 1, 1])
    with c_nav_left:
        c_btn_p, c_m_txt, c_btn_n, c_d = st.columns([0.2, 0.5, 0.2, 1.1]) 
        with c_btn_p: 
            if st.button("‹", key="prev_month"): change_month(-1); st.rerun()
        with c_m_txt:
            st.markdown(f"<div class='month-nav-title'>{month_str}</div>", unsafe_allow_html=True)
        with c_btn_n:
            if st.button("›", key="next_month"): change_month(1); st.rerun()
            
    with c_nav_center:
        st.markdown(f"""
            <div class='month-pl-display'>Monthly P/L: <span style="color: {pnl_color};">{format_currency(monthly_pnl_sum)}</span></div>
        """, unsafe_allow_html=True)

    today = date.today()
    calendar.setfirstweekday(6)
    cal = calendar.monthcalendar(cal_year, cal_month)
    week_num = 1
    while len(cal) < 6: cal.append([0]*7)
    
    pnl_map = {}; count_map = {}
    if not current_df.empty:
        daily_groups = current_df.groupby('Date')
        for d, group in daily_groups:
            if d.year == cal_year and d.month == cal_month:
                pnl_map[d.day] = group['PnL'].sum(); count_map[d.day] = len(group)
    
    html_content = '<div class="calendar-container">'
    headers = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    for h in headers: html_content += f'<div class="cal-header">{h}</div>'
    
    for week in cal:
        week_pnl = 0
        week_trades = 0
        for day_num in week:
            if day_num != 0:
                week_pnl += pnl_map.get(day_num, 0)
                week_trades += count_map.get(day_num, 0)

        for i, day_num in enumerate(week):
            cell_inner = ""; bg_cls = ""; border_cls = ""; empty_cls = ""
            
            if day_num == 0:
                empty_cls = "cal-cell-empty"
            else:
                pnl = pnl_map.get(day_num, 0); trades = count_map.get(day_num, 0)
                pnl_html = ""
                
                if trades > 0:
                    if pnl > 0: bg_cls = "win-bg"
                    elif pnl < 0: bg_cls = "loss-bg"
                    p_txt_cls = ""
                    if pnl > 0: p_txt_cls = "text-green"
                    elif pnl < 0: p_txt_cls = "text-red"
                    else: p_txt_cls = "text-white"
                    
                    pnl_html = f'<div class="cal-pnl {p_txt_cls}">{format_currency(pnl)}</div><div class="cal-trades">{trades} trades</div>'
                
                cell_inner += f'<div class="cal-date">{day_num}</div>{pnl_html}'

                if i == 6:
                    wk_cls = "text-white"
                    if week_pnl > 0: wk_cls = "text-green"
                    elif week_pnl < 0: wk_cls = "text-red"
                    cell_inner += f'<div class="cal-week-title">Week {week_num}</div><div class="cal-week-pnl {wk_cls}">{format_currency(week_pnl)}</div><div class="cal-week-trades">{week_trades} trades</div>'
                
                if day_num == today.day and cal_month == today.month and cal_year == today.year: border_cls = "today-border"
            
            html_content += f'<div class="cal-cell {bg_cls} {border_cls} {empty_cls}">{cell_inner}</div>'
        week_num += 1
            
    html_content += '</div>'
    st.markdown(html_content, unsafe_allow_html=True)

    # --- 詳細記錄 ---
    st.markdown("---")
    st.subheader("Trades Log")
    sel_date = st.date_input("Filter Date", date.today())
    if not current_df.empty:
        d_trades = current_df[current_df['Date'] == sel_date]
        if not d_trades.empty:
            for i, r in d_trades.iterrows():
                # V58: r['Fees'] 可能為 NaN, 使用 get 或 0.0
                fees = r.get('Fees', 0.0)
                if pd.isna(fees): fees = 0.0
                
                title = f"{r['Symbol']} {r['Direction']} | PnL: {format_currency(r['PnL'])}"
                with st.expander(title):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write(f"**Time:** {r['Entry_Time']} - {r['Exit_Time']}")
                        st.write(f"**Price:** {r['Entry']} -> {r['Exit']}")
                        st.write(f"**Fees:** ${fees:.2f}")
                    with c2:
                        st.write(f"**Strategy:** {r.get('Strategy', '')}")
                        st.write(f"**Tags:** {r.get('Tags', '')}")
                        if r['Notes']: st.info(f"Notes: {r['Notes']}")
                    
                    if isinstance(r['Image'], str) and r['Image'] and os.path.exists(r['Image']): 
                        st.image(r['Image'])
        else: st.caption("No trades found.")
