import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import hashlib
import secrets
import base64
from datetime import datetime, timedelta
import os
import re
from pathlib import Path
import plotly.graph_objects as go
import requests
import time
import urllib.parse
import json
import platform
import sys
import uuid

# ------------------------------
# PAGE CONFIG
# ------------------------------
st.set_page_config(
    page_title="GPS Extractor • Secure Access",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ------------------------------
# SESSION STATE
# ------------------------------
if 'page' not in st.session_state:
    st.session_state.page = 'main'
if 'df' not in st.session_state:
    st.session_state.df = None
if 'generated_tokens' not in st.session_state:
    st.session_state.generated_tokens = []
if 'admin_tab' not in st.session_state:
    st.session_state.admin_tab = 0
if 'token_to_validate' not in st.session_state:
    st.session_state.token_to_validate = None

# ------------------------------
# SECURITY CONFIG
# ------------------------------
TOKEN_EXPIRY_DAYS = 30
SECRET_KEY = "YOUR_SECRET_KEY_HERE_CHANGE_THIS_TO_A_RANDOM_STRING_12345"

# ------------------------------
# EXCEL DATA LOADER
# ------------------------------
@st.cache_data
def load_excel_data(file_path):
    """Load data from Excel file"""
    try:
        if not os.path.exists(file_path):
            return None
        df = pd.read_excel(file_path, engine='openpyxl')
        return df
    except Exception as e:
        return None

def get_site_by_plaid(df, plaid):
    if df is None or df.empty:
        return None
    site = df[df['PLAID'].astype(str).str.strip() == str(plaid).strip()]
    if not site.empty:
        return site.iloc[0].to_dict()
    return None

def get_site_by_name(df, site_name):
    if df is None or df.empty:
        return None
    site = df[df['SITE'].astype(str).str.strip().str.upper() == str(site_name).strip().upper()]
    if not site.empty:
        return site.iloc[0].to_dict()
    return None

def get_all_sites(df):
    if df is None or df.empty:
        return []
    sites = []
    for idx, row in df.iterrows():
        sites.append({
            'index': idx,
            'plaid': str(row.get('PLAID', '')),
            'site': str(row.get('SITE', '')),
            'region': str(row.get('REGION', ''))
        })
    return sites

def safe_str(val):
    if pd.isna(val):
        return ""
    return str(val).strip()

def get_online_time():
    """Get current UTC time from online API"""
    try:
        time_apis = [
            "https://worldtimeapi.org/api/timezone/Etc/UTC",
            "https://timeapi.io/api/time/current/utc",
        ]
        for api in time_apis:
            try:
                response = requests.get(api, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if 'utc_datetime' in data:
                        return datetime.fromisoformat(data['utc_datetime'].replace('Z', '+00:00'))
                    elif 'dateTime' in data:
                        return datetime.fromisoformat(data['dateTime'].replace('Z', '+00:00'))
                    elif 'unixtime' in data:
                        return datetime.fromtimestamp(data['unixtime'])
            except:
                continue
        return None
    except:
        return None

def generate_secure_token(site_plaid, user_email, user_name, mac_addresses="", imei_numbers=""):
    """
    Generate a secure token with embedded MAC addresses and IMEI numbers.
    These are pre-approved by the admin and cannot be changed by the user.
    """
    current_time = get_online_time()
    if current_time is None:
        current_time = datetime.utcnow()
    
    expiry = current_time + timedelta(days=TOKEN_EXPIRY_DAYS)
    
    # Collect all allowed devices
    allowed_devices = []
    
    # Add MAC addresses
    if mac_addresses:
        mac_list = [m.strip() for m in mac_addresses.split(',') if m.strip()]
        for mac in mac_list:
            # Validate MAC format (simplified)
            mac_clean = mac.upper().replace('-', ':')
            allowed_devices.append(f"MAC:{mac_clean}")
    
    # Add IMEI numbers
    if imei_numbers:
        imei_list = [i.strip() for i in imei_numbers.split(',') if i.strip()]
        for imei in imei_list:
            # Validate IMEI format (15 digits)
            imei_clean = re.sub(r'\D', '', imei)
            allowed_devices.append(f"IMEI:{imei_clean}")
    
    # Hash each device for security
    hashed_devices = [hashlib.sha256(d.encode()).hexdigest() for d in allowed_devices]
    
    payload = {
        'c': current_time.isoformat(),
        'e': expiry.isoformat(),
        's': site_plaid,
        'u': user_email,
        'n': user_name,
        'd': hashed_devices,  # Hashed MAC/IMEI
        'm': mac_addresses,   # Store plain for display (optional)
        'i': imei_numbers,    # Store plain for display (optional)
    }
    
    payload_json = json.dumps(payload, separators=(',', ':'))
    signature = hashlib.sha256(f"{payload_json}|{SECRET_KEY}".encode()).hexdigest()
    token_data = f"{payload_json}|{signature}"
    token = token_data.encode().hex()
    
    return token

def validate_device(device_to_check, allowed_devices_hashed):
    """
    Validate a device string against the allowed hashed devices.
    Supports MAC:XX:XX:XX:XX:XX:XX and IMEI:123456789012345 formats.
    """
    if not device_to_check or not allowed_devices_hashed:
        return False
    
    # Hash the provided device
    hashed = hashlib.sha256(device_to_check.encode()).hexdigest()
    return hashed in allowed_devices_hashed

def validate_token(token, df, provided_device=""):
    """
    Validate a token and return site data if valid.
    Validates provided MAC/IMEI against allowed devices.
    """
    try:
        token = token.strip()
        if '%' in token:
            token = urllib.parse.unquote(token)
        
        try:
            token_data = bytes.fromhex(token).decode('utf-8')
        except ValueError:
            return None, "Invalid token format - not valid hex"
        
        parts = token_data.rsplit('|', 1)
        if len(parts) != 2:
            return None, "Invalid token format - expected 2 parts"
        
        payload_json, signature = parts
        expected_signature = hashlib.sha256(f"{payload_json}|{SECRET_KEY}".encode()).hexdigest()
        if signature != expected_signature:
            return None, "Invalid token signature - token may be tampered"
        
        try:
            payload = json.loads(payload_json)
        except json.JSONDecodeError:
            return None, "Invalid token payload"
        
        created_str = payload.get('c')
        expires_str = payload.get('e')
        site_plaid = payload.get('s')
        user_email = payload.get('u')
        user_name = payload.get('n')
        allowed_devices = payload.get('d', [])
        mac_addresses = payload.get('m', '')
        imei_numbers = payload.get('i', '')
        
        if not all([created_str, expires_str, site_plaid]):
            return None, "Missing required token data"
        
        current_time = get_online_time()
        if current_time is None:
            current_time = datetime.utcnow()
        
        try:
            created = datetime.fromisoformat(created_str)
            expires = datetime.fromisoformat(expires_str)
        except ValueError as e:
            return None, f"Invalid date format in token: {str(e)}"
        
        if current_time > expires:
            return None, f"Token expired on {expires.strftime('%B %d, %Y at %I:%M %p')}"
        
        if current_time < created - timedelta(minutes=5):
            return None, "Token is from the future - possible fraud attempt"
        
        # DEVICE VALIDATION - Check provided MAC/IMEI against allowed list
        if allowed_devices and provided_device:
            if not validate_device(provided_device, allowed_devices):
                return None, "Device not authorized. Please use your registered device."
        elif allowed_devices:
            return None, "Device verification required. Please register your device."
        
        site_data = get_site_by_plaid(df, site_plaid)
        if site_data is None:
            return None, f"Site not found: {site_plaid}"
        
        site_data['_user_email'] = user_email
        site_data['_user_name'] = user_name
        site_data['_token_created'] = created_str
        site_data['_token_expires'] = expires_str
        site_data['_device_restricted'] = bool(allowed_devices)
        site_data['_device_count'] = len(allowed_devices)
        site_data['_mac_addresses'] = mac_addresses
        site_data['_imei_numbers'] = imei_numbers
        
        return site_data, None
        
    except Exception as e:
        return None, f"Token validation error: {str(e)}"

# ------------------------------
# DARK THEME CSS
# ------------------------------
st.markdown("""
    <style>
    .main .block-container {
        padding: 0.5rem 0.8rem 5rem 0.8rem;
        background: #0a0a0f;
        max-width: 100% !important;
    }
    .stApp { background: #0a0a0f; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stTextInput label, .stSelectbox label, .stCheckbox label {
        color: #e8e8f0 !important;
        font-weight: 500 !important;
    }
    .stTextInput input, .stSelectbox select {
        color: #e8e8f0 !important;
        background: #1a1a2e !important;
        border: 1px solid #2a2a44 !important;
        border-radius: 8px !important;
    }
    .stTextInput input:focus {
        border-color: #4f8cf7 !important;
        box-shadow: 0 0 0 2px rgba(79, 140, 247, 0.2) !important;
    }
    .stButton button {
        color: #e8e8f0 !important;
        font-weight: 600 !important;
    }
    .app-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #2a1a3e 100%);
        padding: 0.8rem 1rem;
        margin: -0.5rem -0.8rem 1rem -0.8rem;
        border-bottom: 1px solid #2a2a44;
        position: sticky;
        top: 0;
        z-index: 999;
        backdrop-filter: blur(10px);
    }
    .app-header-content {
        display: flex;
        align-items: center;
        justify-content: space-between;
        max-width: 1200px;
        margin: 0 auto;
        flex-wrap: wrap;
        gap: 0.5rem;
    }
    .app-logo { display: flex; align-items: center; gap: 0.5rem; }
    .app-logo-icon { font-size: 1.5rem; }
    .app-logo-text { 
        font-size: 1.1rem; 
        font-weight: 700; 
        color: #e8e8f0;
        text-shadow: 0 0 10px rgba(79, 140, 247, 0.3);
    }
    .app-logo-badge {
        background: rgba(79, 140, 247, 0.2);
        color: #4f8cf7;
        padding: 0.15rem 0.6rem;
        border-radius: 40px;
        font-size: 0.6rem;
        font-weight: 500;
        border: 1px solid rgba(79, 140, 247, 0.2);
        margin-left: 0.3rem;
    }
    .secure-card {
        background: #1a1a2e;
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid #2a2a44;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }
    .secure-card h2 { color: #e8e8f0; margin-bottom: 0.5rem; font-weight: 700; }
    .secure-card p { color: #c0c0d0; font-size: 0.95rem; line-height: 1.6; }
    .secure-card .sub-text { color: #8a8aa0; font-size: 0.85rem; }
    .site-card {
        background: #1a1a2e;
        border-radius: 16px;
        padding: 1.2rem;
        margin-bottom: 0.8rem;
        border: 1px solid #2a2a44;
        animation: fadeIn 0.4s ease-out;
        transition: all 0.3s;
    }
    .site-card:hover { border-color: #4f8cf7; box-shadow: 0 0 20px rgba(79, 140, 247, 0.05); }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
    .site-name { font-size: 1.1rem; font-weight: 600; color: #e8e8f0; }
    .site-plaid {
        background: rgba(139, 92, 246, 0.25);
        color: #a78bfa;
        padding: 0.15rem 0.6rem;
        border-radius: 40px;
        font-size: 0.65rem;
        font-weight: 600;
        border: 1px solid rgba(139, 92, 246, 0.2);
        display: inline-block;
        margin-left: 0.3rem;
    }
    .site-location { font-size: 0.85rem; color: #b0b0c8; margin-bottom: 0.5rem; }
    .detail-item { display: flex; flex-direction: column; gap: 0.05rem; }
    .detail-label {
        color: #7a7a95;
        font-size: 0.6rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 600;
    }
    .detail-value { color: #d0d0e0; font-weight: 500; font-size: 0.85rem; }
    .detail-value.fo-name { color: #60a5fa; font-weight: 600; }
    .detail-value.highlight { color: #fbbf24; font-weight: 600; }
    .detail-value.missing { color: #f87171; font-style: italic; }
    .btn {
        padding: 0.5rem 1.2rem;
        border-radius: 40px;
        border: none;
        font-weight: 600;
        font-size: 0.8rem;
        cursor: pointer;
        transition: all 0.2s;
        text-decoration: none;
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        color: white;
    }
    .btn-primary { background: #4f8cf7; }
    .btn-primary:hover { background: #3a7bd5; transform: scale(1.02); box-shadow: 0 4px 15px rgba(79, 140, 247, 0.3); }
    .btn-success { background: #34d399; color: #0a0a0f; }
    .btn-success:hover { background: #2bb386; transform: scale(1.02); }
    .btn-danger { background: #ef4444; }
    .btn-danger:hover { background: #dc2626; transform: scale(1.02); }
    .btn-outline { background: transparent; border: 1px solid #2a2a44; color: #b0b0c8; }
    .btn-outline:hover { background: #1a1a2e; border-color: #4f8cf7; color: #e8e8f0; }
    .btn-purple { background: #8b5cf6; }
    .btn-purple:hover { background: #7c3aed; transform: scale(1.02); }
    .token-box {
        background: #0d0d1a;
        border-radius: 8px;
        padding: 0.8rem;
        border: 1px solid #2a2a44;
        font-family: 'Courier New', monospace;
        color: #fbbf24;
        word-break: break-all;
        font-size: 0.8rem;
        margin: 0.5rem 0;
    }
    .token-box .label { color: #7a7a95; font-size: 0.6rem; text-transform: uppercase; letter-spacing: 0.5px; }
    .token-box code { color: #fbbf24; font-size: 0.75rem; }
    .site-details-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.5rem 1.5rem;
        margin: 0.5rem 0;
        font-size: 0.85rem;
    }
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 0.6rem;
        margin: 0.5rem 0 1rem 0;
    }
    .stat-card {
        background: #14141e;
        border-radius: 12px;
        padding: 0.8rem;
        border: 1px solid #2a2a44;
        text-align: center;
    }
    .stat-number { font-size: 1.6rem; font-weight: 700; color: #e8e8f0; display: block; }
    .stat-label { font-size: 0.7rem; color: #8a8aa0; display: block; margin-top: 0.15rem; }
    .time-status {
        background: #14141e;
        border-radius: 8px;
        padding: 0.4rem 0.8rem;
        border: 1px solid #2a2a44;
        font-size: 0.7rem;
        color: #8a8aa0;
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
    }
    .time-status .online { color: #34d399; }
    .time-status .offline { color: #f87171; }
    .tag {
        padding: 0.15rem 0.6rem;
        border-radius: 40px;
        font-size: 0.6rem;
        font-weight: 500;
        border: 1px solid transparent;
        display: inline-block;
    }
    .tag-territory { background: rgba(52, 211, 153, 0.15); color: #34d399; border-color: rgba(52, 211, 153, 0.2); }
    .tag-towerco { background: rgba(251, 191, 36, 0.15); color: #fbbf24; border-color: rgba(251, 191, 36, 0.2); }
    .bottom-nav {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: #14141e;
        border-top: 1px solid #2a2a44;
        display: flex;
        justify-content: space-around;
        padding: 0.4rem 0.5rem;
        z-index: 1000;
        backdrop-filter: blur(10px);
    }
    .nav-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.1rem;
        padding: 0.3rem 0.8rem;
        border-radius: 12px;
        background: transparent;
        border: none;
        color: #6b6b85;
        font-size: 0.55rem;
        font-weight: 500;
        cursor: pointer;
    }
    .nav-item .nav-icon { font-size: 1.2rem; }
    .nav-item.active { color: #4f8cf7; }
    .batch-result {
        background: #14141e;
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        border: 1px solid #2a2a44;
    }
    .batch-result.success { border-color: #34d399; }
    .batch-result.error { border-color: #ef4444; }
    .batch-result .site-item {
        padding: 0.3rem 0;
        border-bottom: 1px solid #1a1a2e;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 0.5rem;
    }
    .batch-result .site-item:last-child { border-bottom: none; }

    .device-warning {
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid #ef4444;
        border-radius: 8px;
        padding: 0.8rem;
        margin: 0.5rem 0;
    }
    .device-warning .title {
        color: #ef4444;
        font-weight: 600;
    }
    .device-warning .body {
        color: #f87171;
        font-size: 0.85rem;
    }

    @media (min-width: 769px) {
        .main .block-container { padding: 1rem 2rem 6rem 2rem; max-width: 1200px !important; margin: 0 auto; }
        .site-details-grid { grid-template-columns: repeat(3, 1fr); }
        .stats-grid { grid-template-columns: repeat(4, 1fr); }
        .bottom-nav { display: none; }
        .site-card { padding: 1.5rem; }
    }
    @media (max-width: 640px) {
        .site-details-grid { grid-template-columns: 1fr 1fr; }
        .app-header-content { flex-direction: column; align-items: stretch; }
        .secure-card { padding: 1rem; }
    }
    @media (max-width: 380px) {
        .site-details-grid { grid-template-columns: 1fr; }
        .site-name { font-size: 0.95rem; }
    }
    </style>
""", unsafe_allow_html=True)

# ------------------------------
# APP HEADER
# ------------------------------
def app_header():
    online_time = get_online_time()
    time_status = "✅ Online" if online_time else "⚠️ Offline (system time)"
    time_class = "online" if online_time else "offline"
    
    st.markdown(f"""
    <div class="app-header">
        <div class="app-header-content">
            <div class="app-logo">
                <span class="app-logo-icon">🔒</span>
                <span class="app-logo-text">GPS Extractor</span>
                <span class="app-logo-badge">Secure Access</span>
            </div>
            <div style="display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap;">
                <span class="time-status">
                    🕐 <span class="{time_class}">{time_status}</span>
                </span>
                <button class="btn btn-outline" onclick="location.href='/'">🏠 Home</button>
                <button class="btn btn-outline" onclick="location.href='?page=admin'">⚙️ Admin</button>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ------------------------------
# ADMIN PAGE
# ------------------------------
def show_admin():
    app_header()
    
    df = load_excel_data("database.xlsx")
    if df is None:
        possible_paths = ["data/database.xlsx", "./data/database.xlsx"]
        for path in possible_paths:
            df = load_excel_data(path)
            if df is not None:
                break
    
    if df is None or df.empty:
        st.warning("⚠️ No data available. Please upload an Excel file.")
        uploaded_file = st.file_uploader("Upload Excel file (.xlsx)", type=["xlsx"])
        if uploaded_file is not None:
            df = pd.read_excel(uploaded_file, engine='openpyxl')
            if df is not None and not df.empty:
                st.success(f"✅ Loaded {len(df)} records")
                st.session_state.df = df
                st.rerun()
        return
    
    st.session_state.df = df
    
    st.markdown("""
    <div class="secure-card">
        <h2>⚙️ Admin Dashboard</h2>
        <p>Generate secure time-verified links with <strong style="color: #4f8cf7;">MAC Address / IMEI</strong> restrictions.</p>
        <p class="sub-text">
            🔍 Search by PLAID or Site Name (exact match) · Batch generate links with comma-separated values<br>
            📱 Add <strong style="color: #34d399;">MAC Addresses</strong> (AA:BB:CC:DD:EE:FF) and/or <strong style="color: #fbbf24;">IMEI numbers</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    tab_labels = ["📊 Sites", "🔑 Generate Token", "📦 Batch Generate"]
    tabs = st.tabs(tab_labels)
    
    # Tab 0: Sites
    with tabs[0]:
        st.subheader("📊 Sites")
        
        search_col1, search_col2 = st.columns([3, 1])
        with search_col1:
            search_term = st.text_input("🔍 Search (exact match)", placeholder="Enter PLAID or Site Name...", key="site_search")
        with search_col2:
            if st.button("🔍 Search", key="site_search_btn", use_container_width=True):
                if search_term:
                    st.session_state.search_result = search_term
                    st.rerun()
        
        if hasattr(st.session_state, 'search_result') and st.session_state.search_result:
            search_term = st.session_state.search_result
            found = False
            
            site_data = get_site_by_plaid(df, search_term)
            if site_data:
                found = True
                st.success(f"✅ Found site: {site_data.get('SITE', '')}")
                display_site_card(site_data)
            else:
                site_data = get_site_by_name(df, search_term)
                if site_data:
                    found = True
                    st.success(f"✅ Found site: {site_data.get('SITE', '')}")
                    display_site_card(site_data)
            
            if not found:
                st.warning(f"⚠️ No site found matching: '{search_term}'")
            
            if st.button("Clear Search", key="clear_search"):
                del st.session_state.search_result
                st.rerun()
        
        sites = get_all_sites(df)
        st.markdown(f"**Total Sites:** {len(sites)}")
        
        for site in sites[:50]:
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.markdown(f"**{site['site']}**")
            with col2:
                st.markdown(f"`{site['plaid']}` · {site['region']}")
            with col3:
                if st.button(f"🔗 Link", key=f"gen_link_{site['index']}"):
                    st.session_state.gen_site_plaid = site['plaid']
                    st.rerun()
        
        if len(sites) > 50:
            st.info(f"Showing first 50 of {len(sites)} sites. Use search to find specific sites.")
    
    # Tab 1: Single Token
    with tabs[1]:
        st.subheader("🔑 Generate Single Token with Device Restriction")
        
        sites = get_all_sites(df)
        site_options = {f"{s['site']} ({s['plaid']})": s['plaid'] for s in sites}
        
        if site_options:
            selected_site_display = st.selectbox("Select Site", list(site_options.keys()), key="single_site_select")
            selected_site_plaid = site_options[selected_site_display]
            
            st.markdown("""
            <div class="secure-card" style="background: #14141e; padding: 0.8rem; margin: 0.5rem 0; border-color: #4f8cf7;">
                <p style="color: #4f8cf7; font-weight: 600; margin: 0;">
                    ⚠️ IMPORTANT: Only enter MAC addresses and IMEI numbers that are 
                    <strong style="color: #fbbf24;">pre-approved and registered</strong> to the user's device.
                </p>
                <p style="color: #8a8aa0; font-size: 0.8rem; margin: 0.3rem 0 0 0;">
                    These will be <strong style="color: #34d399;">embedded in the token</strong> and cannot be changed by the user.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                user_email = st.text_input("User Email", placeholder="subcon@company.com", key="single_email")
            with col2:
                user_name = st.text_input("User Name", placeholder="John Doe", key="single_name")
            
            st.markdown("""
            <div style="background: #1a1a2e; border-radius: 12px; padding: 1rem; border: 1px solid #2a2a44; margin: 0.5rem 0;">
                <p style="color: #8a8aa0; font-size: 0.8rem; margin: 0;">
                    📱 Enter the user's actual device identifiers:<br>
                    <span style="color: #34d399;">MAC Address</span> format: <code>AA:BB:CC:DD:EE:FF</code><br>
                    <span style="color: #fbbf24;">IMEI</span> format: <code>123456789012345</code> (15 digits)
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            mac_addresses = st.text_input(
                "MAC Addresses (comma separated)",
                placeholder="AA:BB:CC:DD:EE:FF, 11:22:33:44:55:66",
                key="single_mac",
                help="Enter the MAC addresses of the user's authorized devices"
            )
            
            imei_numbers = st.text_input(
                "IMEI Numbers (comma separated)",
                placeholder="123456789012345, 987654321098765",
                key="single_imei",
                help="Enter the IMEI numbers of the user's authorized devices"
            )
            
            if st.button("🔗 Generate Link", key="single_generate", use_container_width=True):
                if user_email and user_name and selected_site_plaid:
                    if not mac_addresses and not imei_numbers:
                        st.warning("⚠️ Please enter at least one MAC Address or IMEI number")
                    else:
                        token = generate_secure_token(
                            selected_site_plaid, 
                            user_email, 
                            user_name, 
                            mac_addresses, 
                            imei_numbers
                        )
                        base_url = st.get_option('server.baseUrlPath') or ""
                        link = f"{base_url}/?token={token}"
                        
                        st.success("✅ Link generated successfully!")
                        
                        online_time = get_online_time()
                        if online_time:
                            expiry = online_time + timedelta(days=TOKEN_EXPIRY_DAYS)
                        else:
                            expiry = datetime.utcnow() + timedelta(days=TOKEN_EXPIRY_DAYS)
                        
                        mac_count = len([m for m in mac_addresses.split(',') if m.strip()]) if mac_addresses else 0
                        imei_count = len([i for i in imei_numbers.split(',') if i.strip()]) if imei_numbers else 0
                        total_devices = mac_count + imei_count
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"""
                            <div class="token-box">
                                <div class="label">🔗 Secure Link</div>
                                <code style="word-break: break-all; font-size: 0.7rem;">{link}</code>
                            </div>
                            """, unsafe_allow_html=True)
                        with col2:
                            st.markdown(f"""
                            <div class="token-box">
                                <div class="label">📋 Token Info</div>
                                <div style="color: #d0d0e0;">👤 User: {user_name}</div>
                                <div style="color: #d0d0e0;">📧 Email: {user_email}</div>
                                <div style="color: #d0d0e0;">⏰ Expires: {expiry.strftime('%B %d, %Y at %I:%M %p UTC')}</div>
                                <div style="color: #d0d0e0;">📍 Site: {selected_site_display}</div>
                                <div style="color: #34d399;">📱 MACs: {mac_count} device(s)</div>
                                <div style="color: #fbbf24;">📱 IMEIs: {imei_count} device(s)</div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                        st.info("🔒 This link is bound to specific MAC addresses and/or IMEI numbers. Only registered devices can access.")
                else:
                    st.warning("⚠️ Please fill in all required fields")
        else:
            st.warning("No sites available.")
    
    # Tab 2: Batch Generate
    with tabs[2]:
        st.subheader("📦 Batch Generate Links with Device Restriction")
        
        st.markdown("""
        <div class="secure-card" style="background: #14141e; padding: 1rem;">
            <p style="color: #b0b0c8; font-size: 0.9rem;">
                Enter multiple PLAIDs or Site Names separated by commas.<br>
                Example: <code>MIN881, MIN806, Site Alpha</code>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        batch_input = st.text_area(
            "Enter PLAIDs or Site Names (comma-separated)",
            placeholder="MIN881, MIN806, MIN807, Site Alpha",
            key="batch_input",
            height=100
        )
        
        col1, col2 = st.columns(2)
        with col1:
            batch_email = st.text_input("User Email (for all links)", placeholder="subcon@company.com", key="batch_email")
        with col2:
            batch_name = st.text_input("User Name (for all links)", placeholder="John Doe", key="batch_name")
        
        st.markdown("""
        <div style="background: #1a1a2e; border-radius: 12px; padding: 1rem; border: 1px solid #2a2a44; margin: 0.5rem 0;">
            <p style="color: #8a8aa0; font-size: 0.8rem; margin: 0;">
                📱 Enter device identifiers that will apply to ALL generated links:<br>
                <span style="color: #34d399;">MAC Address</span> format: <code>AA:BB:CC:DD:EE:FF</code><br>
                <span style="color: #fbbf24;">IMEI</span> format: <code>123456789012345</code> (15 digits)
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        batch_mac = st.text_input(
            "MAC Addresses (comma separated - applies to all)",
            placeholder="AA:BB:CC:DD:EE:FF, 11:22:33:44:55:66",
            key="batch_mac"
        )
        
        batch_imei = st.text_input(
            "IMEI Numbers (comma separated - applies to all)",
            placeholder="123456789012345, 987654321098765",
            key="batch_imei"
        )
        
        if st.button("🔗 Generate All Links", key="batch_generate", use_container_width=True):
            if not batch_input:
                st.warning("⚠️ Please enter at least one PLAID or Site Name")
            elif not batch_email or not batch_name:
                st.warning("⚠️ Please enter user email and name")
            else:
                items = [item.strip() for item in batch_input.split(',') if item.strip()]
                
                if not items:
                    st.warning("⚠️ No valid entries found")
                else:
                    st.success(f"📦 Processing {len(items)} items...")
                    
                    results = []
                    for item in items:
                        site_data = get_site_by_plaid(df, item)
                        if site_data:
                            plaid = safe_str(site_data.get('PLAID', ''))
                            site_name = safe_str(site_data.get('SITE', ''))
                            token = generate_secure_token(plaid, batch_email, batch_name, batch_mac, batch_imei)
                            base_url = st.get_option('server.baseUrlPath') or ""
                            link = f"{base_url}/?token={token}"
                            results.append({
                                'input': item,
                                'plaid': plaid,
                                'site': site_name,
                                'status': 'success',
                                'link': link
                            })
                        else:
                            site_data = get_site_by_name(df, item)
                            if site_data:
                                plaid = safe_str(site_data.get('PLAID', ''))
                                site_name = safe_str(site_data.get('SITE', ''))
                                token = generate_secure_token(plaid, batch_email, batch_name, batch_mac, batch_imei)
                                base_url = st.get_option('server.baseUrlPath') or ""
                                link = f"{base_url}/?token={token}"
                                results.append({
                                    'input': item,
                                    'plaid': plaid,
                                    'site': site_name,
                                    'status': 'success',
                                    'link': link
                                })
                            else:
                                results.append({
                                    'input': item,
                                    'plaid': '',
                                    'site': '',
                                    'status': 'error',
                                    'link': ''
                                })
                    
                    st.markdown("---")
                    st.subheader("📋 Batch Results")
                    
                    success_count = sum(1 for r in results if r['status'] == 'success')
                    error_count = sum(1 for r in results if r['status'] == 'error')
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.markdown(f"**Total:** {len(results)}")
                    with col2:
                        st.markdown(f"**✅ Success:** {success_count}")
                    with col3:
                        st.markdown(f"**❌ Failed:** {error_count}")
                    
                    for result in results:
                        if result['status'] == 'success':
                            st.markdown(f"""
                            <div class="batch-result success">
                                <div class="site-item">
                                    <div>
                                        <strong style="color: #e8e8f0;">{result['site']}</strong>
                                        <span style="color: #8a8aa0; font-size: 0.8rem; margin-left: 0.5rem;">{result['plaid']}</span>
                                    </div>
                                    <div>
                                        <span style="color: #34d399; font-size: 0.8rem;">✅ Generated</span>
                                    </div>
                                </div>
                                <code style="color: #fbbf24; font-size: 0.7rem; word-break: break-all;">{result['link']}</code>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div class="batch-result error">
                                <div class="site-item">
                                    <div>
                                        <strong style="color: #f87171;">{result['input']}</strong>
                                    </div>
                                    <div>
                                        <span style="color: #f87171; font-size: 0.8rem;">❌ Not found</span>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    if success_count > 0:
                        st.markdown("---")
                        st.subheader("📥 Export All Links")
                        
                        export_data = []
                        for r in results:
                            if r['status'] == 'success':
                                export_data.append({
                                    'Site': r['site'],
                                    'PLAID': r['plaid'],
                                    'Link': r['link']
                                })
                        
                        if export_data:
                            export_df = pd.DataFrame(export_data)
                            csv = export_df.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                "⬇️ Download All Links as CSV",
                                data=csv,
                                file_name=f"generated_links_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                                mime="text/csv",
                                use_container_width=True
                            )

def display_site_card(site_data):
    """Display site information in a formatted card"""
    site_name = safe_str(site_data.get('SITE', ''))
    plaid = safe_str(site_data.get('PLAID', ''))
    region = safe_str(site_data.get('REGION', ''))
    province = safe_str(site_data.get('PROVINCE', ''))
    municipality = safe_str(site_data.get('MUNICIPALITY', ''))
    barangay = safe_str(site_data.get('BARANGAY', ''))
    territory = safe_str(site_data.get('TERRITORY', ''))
    lat = safe_str(site_data.get('LATITUDE', ''))
    lon = safe_str(site_data.get('LONGITUDE', ''))
    site_add = safe_str(site_data.get('SITE_ADD', ''))
    assign_hub = safe_str(site_data.get('ASSIGN_HUB', ''))
    towerco = safe_str(site_data.get('TOWERCO', ''))
    
    fo_onsite = safe_str(site_data.get('NEW ENGINEER_ANM1', ''))
    if not fo_onsite:
        fo_onsite = safe_str(site_data.get('NEW  ENGINEER_ANM1', ''))
    contact = safe_str(site_data.get('CONTACT NUMBER', ''))
    
    fo_display = fo_onsite if fo_onsite else "No FO assigned"
    fo_class = "fo-name" if fo_onsite else "missing"
    
    st.markdown(f"""
    <div class="site-card">
        <div style="display: flex; justify-content: space-between; flex-wrap: wrap; align-items: flex-start;">
            <div>
                <span class="site-name">{site_name}</span>
                <span class="site-plaid">{plaid}</span>
            </div>
            <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
                <span class="tag tag-territory">Territory {territory}</span>
                <span class="tag tag-towerco">{towerco}</span>
            </div>
        </div>
        <div class="site-location">{region} · {province} · {municipality} · {barangay}</div>
        <div class="site-details-grid">
            <div class="detail-item">
                <span class="detail-label">Address</span>
                <span class="detail-value">{site_add}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">📋 ASSIGN HUB</span>
                <span class="detail-value">{assign_hub if assign_hub else "No assigned"}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">👤 FO ONSITE</span>
                <span class="detail-value {fo_class}">{fo_display}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">📞 FO NUMBER</span>
                <span class="detail-value">{contact if contact else "No contact"}</span>
            </div>
        </div>
        <div style="margin-top: 0.5rem;">
            <button class="btn btn-primary" onclick="location.href='?page=admin&generate={plaid}'">🔗 Generate Link</button>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ------------------------------
# SITE VIEWER PAGE - DEVICE VERIFICATION REQUIRED
# ------------------------------
def show_site_viewer(token):
    app_header()
    
    df = st.session_state.df
    if df is None:
        df = load_excel_data("database.xlsx")
        if df is None:
            possible_paths = ["data/database.xlsx", "./data/database.xlsx"]
            for path in possible_paths:
                df = load_excel_data(path)
                if df is not None:
                    break
        if df is not None:
            st.session_state.df = df
    
    if df is None or df.empty:
        st.markdown("""
        <div class="secure-card" style="border-color: #f59e0b;">
            <h2 style="color: #f59e0b;">⚠️ Data Not Available</h2>
            <p>The site data is not available. Please contact the administrator.</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Clean the token
    token = token.strip()
    if '%' in token:
        try:
            token = urllib.parse.unquote(token)
        except:
            pass
    
    # Store token in session for validation
    st.session_state.token_to_validate = token
    
    # First, try to validate without device (to check if token requires device)
    temp_site_data, temp_error = validate_token(token, df, "")
    
    if temp_error and "Device verification required" in temp_error:
        # Token requires device verification - show input form
        st.markdown("""
        <div class="secure-card" style="border-color: #4f8cf7;">
            <h2 style="color: #4f8cf7;">📱 Device Verification Required</h2>
            <p style="color: #c0c0d0;">
                This token is secured with <strong style="color: #34d399;">MAC Address</strong> and/or 
                <strong style="color: #fbbf24;">IMEI</strong> verification.
            </p>
            <p style="color: #8a8aa0; font-size: 0.85rem;">
                Please enter your device's MAC Address or IMEI to verify your identity.
                <br><strong style="color: #ef4444;">Note:</strong> This information is checked against the token's allowed devices.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Device input form
        with st.form("device_verification_form"):
            st.markdown("""
            <div style="background: #1a1a2e; border-radius: 12px; padding: 1rem; border: 1px solid #2a2a44; margin: 0.5rem 0;">
                <p style="color: #8a8aa0; font-size: 0.8rem; margin: 0;">
                    Enter <span style="color: #34d399;">MAC Address</span> (AA:BB:CC:DD:EE:FF) or 
                    <span style="color: #fbbf24;">IMEI</span> (15 digits)
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            device_input = st.text_input(
                "Your Device MAC Address or IMEI",
                placeholder="AA:BB:CC:DD:EE:FF or 123456789012345",
                help="Enter the MAC Address or IMEI of your current device"
            )
            
            submitted = st.form_submit_button("🔓 Verify & Access", use_container_width=True)
            
            if submitted:
                if device_input:
                    # Clean the input
                    device_clean = device_input.strip().upper()
                    
                    # Try to validate with the provided device
                    site_data, error = validate_token(token, df, device_clean)
                    
                    if error:
                        st.markdown(f"""
                        <div class="device-warning">
                            <div class="title">❌ Access Denied</div>
                            <div class="body">{error}</div>
                            <div style="color: #8a8aa0; font-size: 0.8rem; margin-top: 0.3rem;">
                                Please ensure you are using the correct MAC Address or IMEI.
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.success("✅ Device verified successfully!")
                        display_site_content(site_data)
                else:
                    st.warning("⚠️ Please enter your device MAC Address or IMEI")
        
        return
    
    elif temp_error:
        # Other error
        st.markdown(f"""
        <div class="secure-card" style="border-color: #ef4444;">
            <h2 style="color: #ef4444;">🔒 Access Denied</h2>
            <p style="color: #d0d0e0;">{temp_error}</p>
            <p style="color: #8a8aa0; font-size: 0.85rem;">The link may have expired or been invalidated.</p>
            <br>
            <button class="btn btn-primary" onclick="location.href='/'">🏠 Return to Home</button>
        </div>
        """, unsafe_allow_html=True)
        return
    
    elif temp_site_data:
        # No device restriction, show site directly
        display_site_content(temp_site_data)
    else:
        st.markdown("""
        <div class="secure-card" style="border-color: #f59e0b;">
            <h2 style="color: #f59e0b;">⚠️ Site Not Found</h2>
            <p>The requested site could not be found in the database.</p>
            <button class="btn btn-primary" onclick="location.href='/'">🏠 Return to Home</button>
        </div>
        """, unsafe_allow_html=True)

def display_site_content(site_data):
    """Display site content after successful validation"""
    
    online_time = get_online_time()
    if online_time:
        time_source = "🔒 Time verified: Online (UTC)"
    else:
        time_source = "⚠️ Time source: System (offline - contact admin)"
    
    device_status = "✅ Device Restricted" if site_data.get('_device_restricted', False) else "ℹ️ No device restriction"
    device_count = site_data.get('_device_count', 0)
    
    # Display MAC and IMEI info if available
    mac_info = ""
    if site_data.get('_mac_addresses'):
        mac_info = f"<div style='color: #34d399; font-size: 0.7rem;'>📱 MAC: {site_data['_mac_addresses']}</div>"
    
    imei_info = ""
    if site_data.get('_imei_numbers'):
        imei_info = f"<div style='color: #fbbf24; font-size: 0.7rem;'>📱 IMEI: {site_data['_imei_numbers']}</div>"
    
    st.markdown(f"""
    <div class="secure-card" style="border-color: #34d399;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
            <div>
                <h2 style="color: #e8e8f0; margin: 0;">{site_data.get('SITE', 'Unknown Site')}</h2>
                <span class="site-plaid">{site_data.get('PLAID', 'No ID')}</span>
            </div>
            <div style="text-align: right;">
                <span style="background: rgba(52, 211, 153, 0.2); color: #34d399; padding: 0.15rem 0.6rem; border-radius: 40px; font-size: 0.65rem; border: 1px solid rgba(52, 211, 153, 0.2);">
                    🔒 Secure Access
                </span>
                <br>
                <span style="color: #8a8aa0; font-size: 0.7rem;">
                    {time_source}
                </span>
                <br>
                <span style="color: #8a8aa0; font-size: 0.7rem;">
                    👤 {site_data.get('_user_name', 'Authorized User')}
                </span>
                <br>
                <span style="color: #34d399; font-size: 0.7rem;">
                    {device_status} {f"({device_count} device(s))" if device_count > 0 else ""}
                </span>
                {mac_info}
                {imei_info}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Site details (same as before)
    site_name = safe_str(site_data.get('SITE', ''))
    plaid = safe_str(site_data.get('PLAID', ''))
    region = safe_str(site_data.get('REGION', ''))
    province = safe_str(site_data.get('PROVINCE', ''))
    municipality = safe_str(site_data.get('MUNICIPALITY', ''))
    barangay = safe_str(site_data.get('BARANGAY', ''))
    territory = safe_str(site_data.get('TERRITORY', ''))
    lat = safe_str(site_data.get('LATITUDE', ''))
    lon = safe_str(site_data.get('LONGITUDE', ''))
    site_add = safe_str(site_data.get('SITE_ADD', ''))
    assign_hub = safe_str(site_data.get('ASSIGN_HUB', ''))
    towerco = safe_str(site_data.get('TOWERCO', ''))
    
    fo_onsite = safe_str(site_data.get('NEW ENGINEER_ANM1', ''))
    if not fo_onsite:
        fo_onsite = safe_str(site_data.get('NEW  ENGINEER_ANM1', ''))
    contact = safe_str(site_data.get('CONTACT NUMBER', ''))
    
    fo_display = fo_onsite if fo_onsite else "No FO assigned"
    fo_class = "fo-name" if fo_onsite else "missing"
    hub_display = assign_hub if assign_hub else "No assigned"
    
    # Map button
    map_button = ''
    if lat and lon:
        try:
            float(lat); float(lon)
            maps_url = f"https://www.google.com/maps?q={lat},{lon}"
            map_button = f'<a href="{maps_url}" target="_blank" class="btn btn-primary">🗺️ Navigate to Google Maps</a>'
        except:
            map_button = '<span class="btn btn-outline" style="cursor: not-allowed; opacity: 0.5;">⚠️ Invalid coordinates</span>'
    else:
        map_button = '<span class="btn btn-outline" style="cursor: not-allowed; opacity: 0.5;">⚠️ No coordinates available</span>'
    
    # Call button
    call_button = ''
    if contact:
        clean_contact = ''.join(ch for ch in contact if ch.isdigit() or ch == '+')
        if clean_contact:
            call_button = f'<a href="tel:{clean_contact}" class="btn btn-success">📞 Call FO</a>'
        else:
            call_button = f'<span class="btn btn-outline" style="cursor: not-allowed; opacity: 0.5;">📞 {contact}</span>'
    else:
        call_button = '<span class="btn btn-outline" style="cursor: not-allowed; opacity: 0.5;">📞 No contact</span>'
    
    st.markdown(f"""
    <div class="site-card">
        <div class="site-location">{region} · {province} · {municipality} · {barangay}</div>
        <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 0.5rem;">
            <span class="tag tag-territory">Territory {territory}</span>
            <span class="tag tag-towerco">{towerco}</span>
        </div>
        <div class="site-details-grid">
            <div class="detail-item">
                <span class="detail-label">Address</span>
                <span class="detail-value">{site_add}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">📋 ASSIGN HUB</span>
                <span class="detail-value">{hub_display}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">👤 FO ONSITE</span>
                <span class="detail-value {fo_class}">{fo_display}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">📞 FO NUMBER</span>
                <span class="detail-value">{contact if contact else "No contact"}</span>
            </div>
        </div>
        <div style="display: flex; gap: 0.5rem; margin-top: 0.7rem; flex-wrap: wrap;">
            {map_button}
            {call_button}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if site_data.get('_token_created') and site_data.get('_token_expires'):
        try:
            created = datetime.fromisoformat(site_data['_token_created'])
            expires = datetime.fromisoformat(site_data['_token_expires'])
            st.markdown(f"""
            <div style="color: #6b6b85; font-size: 0.7rem; text-align: center; margin-top: 1rem; padding: 0.5rem; border-top: 1px solid #2a2a44;">
                🔒 Secure access granted · Created: {created.strftime('%B %d, %Y')} · Expires: {expires.strftime('%B %d, %Y')}
                {" · 📱 Device restricted" if site_data.get('_device_restricted', False) else ""}
            </div>
            """, unsafe_allow_html=True)
        except:
            pass

# ------------------------------
# BOTTOM NAVIGATION
# ------------------------------
def bottom_nav():
    st.markdown("""
    <div class="bottom-nav">
        <span class="nav-item active">
            <span class="nav-icon">📍</span>
            Site
        </span>
    </div>
    """, unsafe_allow_html=True)

# ------------------------------
# MAIN
# ------------------------------
def show_main():
    app_header()
    
    query_params = st.query_params
    token = query_params.get('token', None)
    
    if token:
        show_site_viewer(token)
        return
    
    st.markdown("""
    <div class="secure-card">
        <h2>🔐 Secure Site Access</h2>
        <p>Enter your secure link to access site details.</p>
        <p class="sub-text">
            ⏰ Time is verified online to prevent fraud<br>
            🔒 Each link is unique and expires after 30 days<br>
            📱 Device verification using <strong style="color: #34d399;">MAC Address</strong> or <strong style="color: #fbbf24;">IMEI</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        token_input = st.text_input("", placeholder="Paste your secure link or token here...", label_visibility="collapsed", key="main_token_input")
    with col2:
        if st.button("🔓 Access", key="main_access_btn", use_container_width=True):
            if token_input:
                if "token=" in token_input:
                    token = token_input.split("token=")[-1].split("&")[0]
                else:
                    token = token_input
                st.query_params["token"] = token
                st.rerun()
    
    st.markdown("""
    <div style="text-align: center; color: #8a8aa0; font-size: 0.8rem; margin-top: 1rem;">
        🔒 All access is encrypted and time-verified<br>
        Links expire after 30 days • Device verification required
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("⚙️ Admin Panel", key="admin_btn_main", use_container_width=True):
        st.query_params["page"] = "admin"
        st.rerun()
    
    bottom_nav()

# ------------------------------
# ROUTING
# ------------------------------
query_params = st.query_params

if 'page' in query_params and query_params['page'] == 'admin':
    show_admin()
elif 'token' in query_params and query_params['token']:
    show_site_viewer(query_params['token'])
else:
    show_main()
