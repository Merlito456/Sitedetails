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
if 'admin_tab' not in st.session_state:
    st.session_state.admin_tab = 0
if 'device_fingerprint' not in st.session_state:
    st.session_state.device_fingerprint = None
if 'access_granted' not in st.session_state:
    st.session_state.access_granted = False
if 'admin_authenticated' not in st.session_state:
    st.session_state.admin_authenticated = False
if 'batch_links' not in st.session_state:
    st.session_state.batch_links = []
if 'generated_tokens' not in st.session_state:
    st.session_state.generated_tokens = []

# ------------------------------
# SECURITY CONFIG
# ------------------------------
TOKEN_EXPIRY_DAYS = 30
SECRET_KEY = "YOUR_SECRET_KEY_HERE_CHANGE_THIS_TO_A_RANDOM_STRING_12345"
ADMIN_PASSWORD = "N0k1A"

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
    .stTextInput input, .stSelectbox select, .stTextArea textarea {
        color: #e8e8f0 !important;
        background: #1a1a2e !important;
        border: 1px solid #2a2a44 !important;
        border-radius: 8px !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #4f8cf7 !important;
        box-shadow: 0 0 0 2px rgba(79, 140, 247, 0.2) !important;
    }
    .stTextArea textarea {
        color: #e8e8f0 !important;
    }
    
    .stButton button {
        color: #e8e8f0 !important;
        font-weight: 600 !important;
        background: #1a1a2e !important;
        border: 1px solid #2a2a44 !important;
        border-radius: 8px !important;
        transition: all 0.2s !important;
    }
    .stButton button:hover {
        background: #222244 !important;
        border-color: #4f8cf7 !important;
        color: #e8e8f0 !important;
    }
    
    .stTabs [data-baseweb="tab-list"] { gap: 0.5rem; }
    .stTabs [data-baseweb="tab"] {
        background: #1a1a2e !important;
        border: 1px solid #2a2a44 !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
        color: #a0a0b8 !important;
    }
    .stTabs [aria-selected="true"] {
        background: #2a2a44 !important;
        border-color: #4f8cf7 !important;
        color: #e8e8f0 !important;
    }
    
    .stDownloadButton button {
        color: #e8e8f0 !important;
        background: #1a1a2e !important;
        border: 1px solid #2a2a44 !important;
        border-radius: 8px !important;
    }
    .stDownloadButton button:hover {
        background: #222244 !important;
        border-color: #4f8cf7 !important;
    }
    
    .stAlert {
        background: #1a1a2e !important;
        border-color: #2a2a44 !important;
        color: #e8e8f0 !important;
    }
    
    .stDataFrame {
        border: 1px solid #2a2a44 !important;
        border-radius: 12px !important;
        overflow: hidden !important;
    }
    .stDataFrame > div {
        background: #1a1a2e !important;
    }
    
    .streamlit-expanderHeader {
        background: #1a1a2e !important;
        border-color: #2a2a44 !important;
        color: #e8e8f0 !important;
    }
    .streamlit-expanderContent {
        background: #1a1a2e !important;
        border-color: #2a2a44 !important;
    }
    
    code {
        color: #fbbf24 !important;
        background: #0d0d1a !important;
    }
    
    .stTabs [data-baseweb="tab"] p { color: #a0a0b8 !important; }
    .stTabs [aria-selected="true"] p { color: #e8e8f0 !important; }
    
    .stSelectbox div[data-baseweb="select"] { background: #1a1a2e !important; }
    .stSelectbox div[data-baseweb="select"] > div {
        background: #1a1a2e !important;
        border-color: #2a2a44 !important;
        color: #e8e8f0 !important;
    }
    
    .stMultiSelect div[data-baseweb="select"] { background: #1a1a2e !important; }
    
    .stFileUploader {
        background: #1a1a2e !important;
        border: 1px solid #2a2a44 !important;
        border-radius: 8px !important;
        padding: 1rem !important;
    }
    
    .stMetric {
        background: #1a1a2e !important;
        border: 1px solid #2a2a44 !important;
        border-radius: 12px !important;
        padding: 0.5rem !important;
    }
    .stMetric label { color: #8a8aa0 !important; }
    .stMetric div { color: #e8e8f0 !important; }

    .token-display-box {
        background: #0d0d1a;
        border-radius: 8px;
        padding: 0.8rem;
        border: 1px solid #2a2a44;
        font-family: 'Courier New', monospace;
        margin: 0.5rem 0;
        transition: all 0.3s;
    }
    .token-display-box:hover {
        border-color: #4f8cf7;
        box-shadow: 0 0 20px rgba(79, 140, 247, 0.05);
    }
    .token-label {
        color: #7a7a95;
        font-size: 0.6rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 600;
    }
    .token-value {
        color: #fbbf24;
        font-size: 0.75rem;
        word-break: break-all;
        font-family: 'Courier New', monospace;
        margin-top: 0.3rem;
        padding: 0.5rem;
        background: #14141e;
        border-radius: 4px;
        border: 1px solid #1a1a2e;
    }
    .token-copy-btn {
        background: #2a2a44;
        color: #a0a0b8;
        border: none;
        border-radius: 4px;
        padding: 0.2rem 0.8rem;
        font-size: 0.7rem;
        cursor: pointer;
        transition: all 0.2s;
        margin-top: 0.3rem;
    }
    .token-copy-btn:hover {
        background: #3a3a5e;
        color: #e8e8f0;
    }

    .token-list-container {
        background: #1a1a2e;
        border-radius: 12px;
        padding: 1rem;
        border: 1px solid #2a2a44;
        margin: 0.5rem 0;
    }
    .token-list-title {
        color: #4f8cf7;
        font-size: 0.85rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    .token-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.4rem 0.5rem;
        border-bottom: 1px solid #1a1a2e;
        gap: 0.5rem;
        flex-wrap: wrap;
    }
    .token-item:last-child { border-bottom: none; }
    .token-item .t-number {
        color: #4f8cf7;
        font-weight: 600;
        font-size: 0.8rem;
        min-width: 30px;
    }
    .token-item .t-value {
        color: #fbbf24;
        font-family: monospace;
        font-size: 0.7rem;
        word-break: break-all;
        flex: 1;
    }
    .token-item .t-copy {
        background: #2a2a44;
        color: #a0a0b8;
        border: none;
        border-radius: 4px;
        padding: 0.15rem 0.6rem;
        font-size: 0.6rem;
        cursor: pointer;
    }
    .token-item .t-copy:hover {
        background: #3a3a5e;
        color: #e8e8f0;
    }

    .combined-tokens-box {
        background: #0d0d1a;
        border-radius: 12px;
        padding: 1rem;
        border: 2px solid #4f8cf7;
        margin: 0.5rem 0;
    }
    .combined-tokens-box .title {
        color: #4f8cf7;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    .combined-tokens-box .tokens {
        color: #fbbf24;
        font-family: monospace;
        font-size: 0.7rem;
        word-break: break-all;
        padding: 0.5rem;
        background: #14141e;
        border-radius: 4px;
        border: 1px solid #1a1a2e;
        max-height: 200px;
        overflow-y: auto;
        white-space: pre-wrap;
    }
    .combined-tokens-box .copy-all-btn {
        background: #4f8cf7;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 0.4rem 1rem;
        font-size: 0.8rem;
        cursor: pointer;
        margin-top: 0.5rem;
        transition: all 0.2s;
        font-weight: 600;
    }
    .combined-tokens-box .copy-all-btn:hover {
        background: #3a7bd5;
        transform: scale(1.02);
    }

    /* Date picker styling */
    .stDateInput label {
        color: #e8e8f0 !important;
    }
    .stDateInput input {
        color: #e8e8f0 !important;
        background: #1a1a2e !important;
        border: 1px solid #2a2a44 !important;
        border-radius: 8px !important;
    }
    .stDateInput input:focus {
        border-color: #4f8cf7 !important;
        box-shadow: 0 0 0 2px rgba(79, 140, 247, 0.2) !important;
    }

    @media (max-width: 640px) {
        .main .block-container {
            padding: 0.5rem 0.5rem 5rem 0.5rem !important;
        }
        .token-item {
            flex-direction: column;
            align-items: stretch;
        }
        .token-item .t-value {
            font-size: 0.6rem;
        }
        .combined-tokens-box .tokens {
            font-size: 0.6rem;
            max-height: 150px;
        }
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================
# SECTION 1: DEVICE FINGERPRINT FUNCTIONS
# ============================================================
def get_device_fingerprint():
    query_params = st.query_params
    fp = query_params.get('device_fp', None)
    if fp:
        st.session_state.device_fingerprint = fp
        return fp
    
    if st.session_state.device_fingerprint:
        return st.session_state.device_fingerprint
    
    import platform
    info = [
        platform.system(),
        platform.node(),
        platform.release(),
        str(uuid.getnode()),
        str(sys.getsizeof(object()))
    ]
    info_str = "|".join(str(i) for i in info)
    fp = hashlib.md5(info_str.encode()).hexdigest()[:16]
    
    st.session_state.device_fingerprint = fp
    return fp

def get_device_id():
    fp = get_device_fingerprint()
    if fp and len(fp) >= 16:
        return f"DEV-{fp[:8].upper()}-{fp[-8:].upper()}"
    return "DEV-UNKNOWN"

# ============================================================
# SECTION 2: EXCEL DATA LOADER AND HELPERS
# ============================================================
@st.cache_data
def load_excel_data(file_path):
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

# ============================================================
# SECTION 3: TIME FUNCTIONS
# ============================================================
def get_online_time():
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

# ============================================================
# SECTION 4: TOKEN GENERATION AND VALIDATION
# ============================================================
def generate_secure_token(site_plaid, start_date, end_date, device_identifiers=""):
    """
    Generate token with embedded MAC addresses, IMEI, Android IDs, and date range.
    """
    current_time = get_online_time()
    if current_time is None:
        current_time = datetime.utcnow()
    
    # Use provided dates or fallback to defaults
    if start_date:
        expiry = datetime.combine(end_date, datetime.max.time()) if end_date else datetime.combine(start_date, datetime.max.time())
    else:
        expiry = current_time + timedelta(days=TOKEN_EXPIRY_DAYS)
    
    devices = []
    if device_identifiers:
        device_list = [d.strip() for d in device_identifiers.split(',') if d.strip()]
        for device in device_list:
            hashed = hashlib.sha256(device.encode()).hexdigest()
            devices.append(hashed)
    
    payload = {
        'c': current_time.isoformat(),
        'e': expiry.isoformat(),
        's': site_plaid,
        'sd': start_date.isoformat() if start_date else '',
        'ed': end_date.isoformat() if end_date else '',
        'd': devices,
        'raw': device_identifiers
    }
    
    payload_json = json.dumps(payload, separators=(',', ':'))
    signature = hashlib.sha256(f"{payload_json}|{SECRET_KEY}".encode()).hexdigest()
    token_data = f"{payload_json}|{signature}"
    token = token_data.encode().hex()
    
    return token

def validate_device(device_to_check, allowed_devices_hashed):
    if not device_to_check or not allowed_devices_hashed:
        return False
    
    hashed = hashlib.sha256(device_to_check.encode()).hexdigest()
    if hashed in allowed_devices_hashed:
        return True
    
    prefixes = ['MAC:', 'IMEI:', 'ANDROID:', 'ANDROIDID:']
    for prefix in prefixes:
        if device_to_check.startswith(prefix):
            without_prefix = device_to_check[len(prefix):]
            hashed = hashlib.sha256(without_prefix.encode()).hexdigest()
            if hashed in allowed_devices_hashed:
                return True
    
    return False

def validate_token(token, df, device_fingerprint=None):
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
        start_date_str = payload.get('sd', '')
        end_date_str = payload.get('ed', '')
        allowed_devices = payload.get('d', [])
        raw_devices = payload.get('raw', '')
        
        if not all([created_str, expires_str, site_plaid]):
            return None, "Missing required token data"
        
        current_time = get_online_time()
        if current_time is None:
            current_time = datetime.utcnow()
        
        try:
            created = datetime.fromisoformat(created_str)
            expires = datetime.fromisoformat(expires_str)
        except ValueError:
            return None, "Invalid date format"
        
        if current_time > expires:
            return None, f"Token expired on {expires.strftime('%B %d, %Y')}"
        
        if current_time < created - timedelta(minutes=5):
            return None, "Token is from the future - possible fraud"
        
        if allowed_devices and device_fingerprint:
            if not validate_device(device_fingerprint, allowed_devices):
                return None, "Device not authorized. MAC Address, IMEI, or Android ID not recognized."
        elif allowed_devices:
            return None, "Device verification required. Please ensure your device is registered."
        
        site_data = get_site_by_plaid(df, site_plaid)
        if site_data is None:
            return None, f"Site not found: {site_plaid}"
        
        site_data['_user_name'] = "Authorized User"
        site_data['_token_created'] = created_str
        site_data['_token_expires'] = expires_str
        site_data['_device_restricted'] = bool(allowed_devices)
        site_data['_device_count'] = len(allowed_devices)
        site_data['_raw_devices'] = raw_devices
        site_data['_start_date'] = start_date_str
        site_data['_end_date'] = end_date_str
        
        return site_data, None
        
    except Exception as e:
        return None, f"Validation error: {str(e)}"

# ============================================================
# SECTION 5: JAVASCRIPT INJECTIONS
# ============================================================
def inject_device_fingerprint_script():
    fingerprint_js = """
    <script>
    function getDeviceFingerprint() {
        var screen = window.screen;
        var nav = navigator;
        
        var components = [
            nav.userAgent,
            nav.platform,
            nav.language,
            screen.width + 'x' + screen.height,
            screen.colorDepth,
            new Date().getTimezoneOffset(),
            nav.hardwareConcurrency || 'unknown',
            nav.deviceMemory || 'unknown'
        ];
        
        var fingerprint = components.join('|');
        var hash = 0;
        for (var i = 0; i < fingerprint.length; i++) {
            var char = fingerprint.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash;
        }
        var fp = Math.abs(hash).toString(16).padStart(16, '0');
        
        var url = new URL(window.location);
        url.searchParams.set('device_fp', fp);
        window.history.replaceState({}, '', url);
        
        return fp;
    }
    getDeviceFingerprint();
    </script>
    """
    components.html(fingerprint_js, height=0)

# ============================================================
# SECTION 6: UI COMPONENTS
# ============================================================
def app_header():
    online_time = get_online_time()
    time_status = "✅ Online" if online_time else "⚠️ Offline (system time)"
    time_class = "online" if online_time else "offline"
    
    device_id = get_device_id()
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1a1a2e 0%, #2a1a3e 100%); 
                padding: 0.8rem 1rem; 
                margin: -0.5rem -0.8rem 1rem -0.8rem; 
                border-bottom: 1px solid #2a2a44; 
                position: sticky; 
                top: 0; 
                z-index: 999; 
                backdrop-filter: blur(10px);">
        <div style="display: flex; 
                    align-items: center; 
                    justify-content: space-between; 
                    max-width: 1200px; 
                    margin: 0 auto; 
                    flex-wrap: wrap; 
                    gap: 0.5rem;">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <span style="font-size: 1.5rem;">🔒</span>
                <span style="font-size: 1.1rem; font-weight: 700; color: #e8e8f0; text-shadow: 0 0 10px rgba(79, 140, 247, 0.3);">GPS Extractor</span>
                <span style="background: rgba(79, 140, 247, 0.2); 
                           color: #4f8cf7; 
                           padding: 0.15rem 0.6rem; 
                           border-radius: 40px; 
                           font-size: 0.6rem; 
                           font-weight: 500; 
                           border: 1px solid rgba(79, 140, 247, 0.2); 
                           margin-left: 0.3rem;">Secure Access</span>
            </div>
            <div style="display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap;">
                <span style="background: #14141e; 
                           border-radius: 8px; 
                           padding: 0.3rem 0.8rem; 
                           border: 1px solid #2a2a44; 
                           font-size: 0.7rem; 
                           color: #8a8aa0; 
                           display: inline-flex; 
                           align-items: center; 
                           gap: 0.5rem;">
                    🕐 <span style="color: { '#34d399' if online_time else '#f87171' };">{time_status}</span>
                </span>
                <span style="background: #14141e; 
                           border-radius: 8px; 
                           padding: 0.3rem 0.8rem; 
                           border: 1px solid #34d399; 
                           font-size: 0.6rem; 
                           color: #8a8aa0; 
                           display: inline-flex; 
                           align-items: center; 
                           gap: 0.5rem;">
                    📱 <span style="color:#34d399;">{device_id}</span>
                </span>
                <button onclick="location.href='/'" 
                        style="background: transparent; 
                               border: 1px solid #2a2a44; 
                               color: #b0b0c8; 
                               padding: 0.4rem 0.8rem; 
                               border-radius: 40px; 
                               font-size: 0.75rem; 
                               font-weight: 500; 
                               cursor: pointer; 
                               transition: all 0.2s;">🏠 Home</button>
                <button onclick="location.href='?page=admin'" 
                        style="background: transparent; 
                               border: 1px solid #2a2a44; 
                               color: #b0b0c8; 
                               padding: 0.4rem 0.8rem; 
                               border-radius: 40px; 
                               font-size: 0.75rem; 
                               font-weight: 500; 
                               cursor: pointer; 
                               transition: all 0.2s;">⚙️ Admin</button>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def site_card(site_data, search_term=""):
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
    
    if search_term:
        site_name = site_name.replace(search_term, f'<span style="background: #fbbf24; color: #0a0a0f; padding: 0.05rem 0.2rem; border-radius: 3px; font-weight: 600;">{search_term}</span>')
        plaid = plaid.replace(search_term, f'<span style="background: #fbbf24; color: #0a0a0f; padding: 0.05rem 0.2rem; border-radius: 3px; font-weight: 600;">{search_term}</span>')
    
    st.markdown(f"""
    <div style="background: #1a1a2e; 
                border-radius: 16px; 
                padding: 1.2rem; 
                margin-bottom: 0.8rem; 
                border: 1px solid #2a2a44; 
                transition: all 0.3s; 
                animation: fadeIn 0.4s ease-out;">
        <div style="display: flex; 
                    flex-wrap: wrap; 
                    justify-content: space-between; 
                    align-items: flex-start; 
                    gap: 0.5rem; 
                    margin-bottom: 0.5rem;">
            <div>
                <span style="font-size: 1.1rem; font-weight: 600; color: #e8e8f0;">{site_name}</span>
                <span style="background: rgba(139, 92, 246, 0.25); 
                           color: #a78bfa; 
                           padding: 0.15rem 0.6rem; 
                           border-radius: 40px; 
                           font-size: 0.65rem; 
                           font-weight: 600; 
                           border: 1px solid rgba(139, 92, 246, 0.2); 
                           display: inline-block; 
                           margin-left: 0.3rem;">{plaid}</span>
            </div>
            <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
                <span style="background: rgba(52, 211, 153, 0.15); 
                           color: #34d399; 
                           padding: 0.15rem 0.6rem; 
                           border-radius: 40px; 
                           font-size: 0.6rem; 
                           font-weight: 500; 
                           border: 1px solid rgba(52, 211, 153, 0.2);">Territory {territory}</span>
                <span style="background: rgba(251, 191, 36, 0.15); 
                           color: #fbbf24; 
                           padding: 0.15rem 0.6rem; 
                           border-radius: 40px; 
                           font-size: 0.6rem; 
                           font-weight: 500; 
                           border: 1px solid rgba(251, 191, 36, 0.2);">{towerco}</span>
            </div>
        </div>
        <div style="font-size: 0.85rem; color: #b0b0c8; margin-bottom: 0.5rem;">{region} · {province} · {municipality} · {barangay}</div>
        <div style="display: grid; 
                    grid-template-columns: 1fr 1fr; 
                    gap: 0.3rem 1rem; 
                    margin: 0.5rem 0; 
                    font-size: 0.8rem;">
            <div style="display: flex; flex-direction: column; gap: 0.05rem;">
                <span style="color: #7a7a95; font-size: 0.6rem; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;">Address</span>
                <span style="color: #d0d0e0; font-weight: 500; font-size: 0.85rem;">{site_add}</span>
            </div>
            <div style="display: flex; flex-direction: column; gap: 0.05rem;">
                <span style="color: #7a7a95; font-size: 0.6rem; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;">📋 ASSIGN HUB</span>
                <span style="color: #d0d0e0; font-weight: 500; font-size: 0.85rem;">{assign_hub if assign_hub else "No assigned"}</span>
            </div>
            <div style="display: flex; flex-direction: column; gap: 0.05rem;">
                <span style="color: #7a7a95; font-size: 0.6rem; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;">👤 FO ONSITE</span>
                <span style="color: #60a5fa; font-weight: 600; font-size: 0.85rem;">{fo_display}</span>
            </div>
            <div style="display: flex; flex-direction: column; gap: 0.05rem;">
                <span style="color: #7a7a95; font-size: 0.6rem; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;">📞 FO NUMBER</span>
                <span style="color: #d0d0e0; font-weight: 500; font-size: 0.85rem;">{contact if contact else "No contact"}</span>
            </div>
        </div>
        <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.7rem;">
    """, unsafe_allow_html=True)
    
    if lat and lon:
        try:
            float(lat); float(lon)
            maps_url = f"https://www.google.com/maps?q={lat},{lon}"
            st.markdown(f'<a href="{maps_url}" target="_blank" style="background: #4f8cf7; color: white; padding: 0.5rem 1.2rem; border-radius: 40px; font-size: 0.8rem; font-weight: 600; text-decoration: none; display: inline-flex; align-items: center; gap: 0.4rem; border: none; cursor: pointer;">🗺️ Navigate</a>', unsafe_allow_html=True)
        except:
            st.markdown('<span style="background: #2a2a44; color: #6b6b85; padding: 0.3rem 1rem; border-radius: 40px; font-size: 0.85rem;">⚠️ Invalid coordinates</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span style="background: #2a2a44; color: #6b6b85; padding: 0.3rem 1rem; border-radius: 40px; font-size: 0.85rem;">⚠️ No coordinates</span>', unsafe_allow_html=True)
    
    if contact:
        clean_contact = ''.join(ch for ch in contact if ch.isdigit() or ch == '+')
        if clean_contact:
            st.markdown(f'<a href="tel:{clean_contact}" style="background: #34d399; color: #0a0a0f; padding: 0.5rem 1.2rem; border-radius: 40px; font-size: 0.8rem; font-weight: 600; text-decoration: none; display: inline-flex; align-items: center; gap: 0.4rem; border: none; cursor: pointer;">📞 Call FO</a>', unsafe_allow_html=True)
        else:
            st.markdown(f'<span style="background: #2a2a44; color: #6b6b85; padding: 0.3rem 1rem; border-radius: 40px; font-size: 0.85rem;">📞 {contact}</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span style="background: #2a2a44; color: #6b6b85; padding: 0.3rem 1rem; border-radius: 40px; font-size: 0.85rem;">📞 No contact</span>', unsafe_allow_html=True)
    
    st.markdown("""
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# SECTION 7: ADMIN LOGIN
# ============================================================
def show_admin_login():
    st.markdown("""
    <div style="display: flex; 
                justify-content: center; 
                align-items: center; 
                min-height: 70vh; 
                padding: 2rem;">
        <div style="background: #1a1a2e; 
                    border-radius: 16px; 
                    padding: 2.5rem; 
                    max-width: 420px; 
                    width: 100%; 
                    border: 1px solid #2a2a44; 
                    box-shadow: 0 8px 30px rgba(0,0,0,0.5);">
            <h2 style="color: #e8e8f0; text-align: center; margin-bottom: 0.5rem; font-size: 1.5rem;">🔒 Admin Access</h2>
            <p style="color: #8a8aa0; text-align: center; margin-bottom: 1.5rem; font-size: 0.9rem;">Enter the admin password to access the dashboard</p>
    """, unsafe_allow_html=True)
    
    with st.form("admin_login_form", clear_on_submit=False):
        password = st.text_input(
            "Password",
            placeholder="Enter Admin Password",
            type="password",
            label_visibility="collapsed"
        )
        submitted = st.form_submit_button("🔓 Unlock", use_container_width=True)
        
        if submitted:
            if password == ADMIN_PASSWORD:
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("❌ Invalid password. Please try again.")
    
    st.markdown("""
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# SECTION 8: ADMIN DASHBOARD
# ============================================================
def show_admin_dashboard():
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
    <div style="background: #1a1a2e; 
                border-radius: 16px; 
                padding: 1.5rem; 
                margin: 1rem 0; 
                border: 1px solid #2a2a44; 
                box-shadow: 0 4px 20px rgba(0,0,0,0.5);">
        <h2 style="color: #e8e8f0; margin-bottom: 0.5rem; font-weight: 700;">⚙️ Admin Dashboard</h2>
        <p style="color: #c0c0d0; font-size: 0.95rem; line-height: 1.6;">
            Generate secure links with <strong style="color: #34d399;">MAC Address / IMEI / Android ID</strong> verification.
        </p>
        <p style="color: #8a8aa0; font-size: 0.85rem;">
            🔍 Search by PLAID or Site Name · Batch generate links<br>
            📱 Device is verified by <strong style="color: #fbbf24;">MAC Address, IMEI, or Android ID</strong> - No user input required!
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    device_id = get_device_id()
    st.markdown(f"""
    <div style="background: #14141e; 
                border-radius: 12px; 
                padding: 0.8rem; 
                border: 1px solid #34d399; 
                margin: 0.5rem 0;">
        <div style="color: #34d399; font-size: 0.6rem; text-transform: uppercase; letter-spacing: 0.5px;">📱 Your Device ID (For Testing)</div>
        <div style="color: #d0d0e0; font-family: monospace; font-size: 0.85rem;">{device_id}</div>
        <div style="color: #8a8aa0; font-size: 0.7rem;">For Android app, use actual MAC Address, IMEI, or Android ID</div>
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
                site_card(site_data, search_term)
            else:
                site_data = get_site_by_name(df, search_term)
                if site_data:
                    found = True
                    st.success(f"✅ Found site: {site_data.get('SITE', '')}")
                    site_card(site_data, search_term)
            
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
        st.subheader("🔑 Generate Single Token")
        
        sites = get_all_sites(df)
        site_options = {f"{s['site']} ({s['plaid']})": s['plaid'] for s in sites}
        
        if site_options:
            selected_site_display = st.selectbox("Select Site", list(site_options.keys()), key="single_site_select")
            selected_site_plaid = site_options[selected_site_display]
            
            st.markdown("""
            <div style="background: #14141e; 
                        padding: 0.8rem; 
                        margin: 0.5rem 0; 
                        border: 1px solid #34d399; 
                        border-radius: 12px;">
                <p style="color: #34d399; font-weight: 600; margin: 0;">📱 <strong>MAC Address / IMEI / Android ID Verification</strong></p>
                <p style="color: #8a8aa0; font-size: 0.8rem; margin: 0.3rem 0 0 0;">
                    Enter the user's actual device identifiers:<br>
                    <span style="color: #34d399;">MAC Address</span>: <code style="color: #fbbf24;">AA:BB:CC:DD:EE:FF</code><br>
                    <span style="color: #fbbf24;">IMEI</span>: <code style="color: #fbbf24;">123456789012345</code> (15 digits)<br>
                    <span style="color: #60a5fa;">Android ID</span>: <code style="color: #fbbf24;">ANDROID:abc123def456</code>
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Date range inputs
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input(
                    "Start Date",
                    value=datetime.now().date(),
                    key="single_start_date"
                )
            with col2:
                end_date = st.date_input(
                    "End Date",
                    value=datetime.now().date() + timedelta(days=TOKEN_EXPIRY_DAYS),
                    key="single_end_date"
                )
            
            device_identifiers = st.text_area(
                "Device Identifiers (one per line, or comma separated)",
                placeholder="MAC:AA:BB:CC:DD:EE:FF\nIMEI:123456789012345\nANDROID:abc123def456",
                key="single_devices",
                help="Format: MAC:AA:BB:CC:DD:EE:FF or IMEI:123456789012345 or ANDROID:abc123def456"
            )
            
            if st.button("🔗 Generate Link", key="single_generate", use_container_width=True):
                if selected_site_plaid and device_identifiers:
                    clean_devices = device_identifiers.replace('\n', ',').replace(' ', '')
                    clean_devices = ','.join([d.strip() for d in clean_devices.split(',') if d.strip()])
                    
                    token = generate_secure_token(
                        selected_site_plaid, 
                        start_date, 
                        end_date, 
                        clean_devices
                    )
                    base_url = st.get_option('server.baseUrlPath') or ""
                    link = f"{base_url}/?token={token}"
                    
                    st.success("✅ Link generated successfully!")
                    
                    online_time = get_online_time()
                    if online_time:
                        expiry = online_time + timedelta(days=TOKEN_EXPIRY_DAYS)
                    else:
                        expiry = datetime.utcnow() + timedelta(days=TOKEN_EXPIRY_DAYS)
                    
                    device_count = len([d for d in clean_devices.split(',') if d.strip()])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"""
                        <div style="background: #0d0d1a; 
                                    border-radius: 8px; 
                                    padding: 0.8rem; 
                                    border: 1px solid #2a2a44; 
                                    margin: 0.5rem 0;">
                            <div style="color: #7a7a95; font-size: 0.6rem; text-transform: uppercase; letter-spacing: 0.5px;">🔗 Secure Link</div>
                            <code style="color: #fbbf24; word-break: break-all; font-size: 0.7rem;">{link}</code>
                        </div>
                        """, unsafe_allow_html=True)
                    with col2:
                        st.markdown(f"""
                        <div style="background: #0d0d1a; 
                                    border-radius: 8px; 
                                    padding: 0.8rem; 
                                    border: 1px solid #2a2a44; 
                                    margin: 0.5rem 0;">
                            <div style="color: #7a7a95; font-size: 0.6rem; text-transform: uppercase; letter-spacing: 0.5px;">📋 Token Info</div>
                            <div style="color: #d0d0e0;">📅 Start: {start_date.strftime('%B %d, %Y')}</div>
                            <div style="color: #d0d0e0;">📅 End: {end_date.strftime('%B %d, %Y')}</div>
                            <div style="color: #d0d0e0;">📍 Site: {selected_site_display}</div>
                            <div style="color: #34d399;">📱 Devices: {device_count}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    st.info("🔒 This link is bound to specific MAC Addresses, IMEI numbers, or Android IDs. Only registered devices can access.")
                else:
                    st.warning("⚠️ Please select a site and enter device identifiers")
        else:
            st.warning("No sites available.")
    
    # Tab 2: Batch Generate
    with tabs[2]:
        st.subheader("📦 Batch Generate Links")
        
        st.markdown("""
        <div style="background: #14141e; 
                    padding: 1rem; 
                    border: 1px solid #2a2a44; 
                    border-radius: 12px; 
                    margin: 0.5rem 0;">
            <p style="color: #b0b0c8; font-size: 0.9rem;">Enter multiple PLAIDs or Site Names separated by commas.<br>Example: <code style="color: #fbbf24;">MIN881, MIN806, Site Alpha</code></p>
        </div>
        """, unsafe_allow_html=True)
        
        batch_input = st.text_area(
            "Enter PLAIDs or Site Names (comma-separated)",
            placeholder="MIN881, MIN806, MIN807, Site Alpha",
            key="batch_input",
            height=100
        )
        
        # Date range inputs for batch
        col1, col2 = st.columns(2)
        with col1:
            batch_start_date = st.date_input(
                "Start Date (for all links)",
                value=datetime.now().date(),
                key="batch_start_date"
            )
        with col2:
            batch_end_date = st.date_input(
                "End Date (for all links)",
                value=datetime.now().date() + timedelta(days=TOKEN_EXPIRY_DAYS),
                key="batch_end_date"
            )
        
        st.markdown("""
        <div style="background: #14141e; 
                    padding: 0.8rem; 
                    margin: 0.5rem 0; 
                    border: 1px solid #34d399; 
                    border-radius: 12px;">
            <p style="color: #34d399; font-size: 0.8rem; margin: 0;">
                📱 Device identifiers that will apply to ALL generated links:<br>
                <span style="color: #34d399;">MAC Address</span>: <code style="color: #fbbf24;">AA:BB:CC:DD:EE:FF</code><br>
                <span style="color: #fbbf24;">IMEI</span>: <code style="color: #fbbf24;">123456789012345</code><br>
                <span style="color: #60a5fa;">Android ID</span>: <code style="color: #fbbf24;">ANDROID:abc123def456</code>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        batch_devices = st.text_area(
            "Device Identifiers (one per line, or comma separated - applies to all)",
            placeholder="MAC:AA:BB:CC:DD:EE:FF\nIMEI:123456789012345\nANDROID:d094968680211a30",
            key="batch_devices"
        )
        
        if st.button("🔗 Generate All Links", key="batch_generate", use_container_width=True):
            if not batch_input:
                st.warning("⚠️ Please enter at least one PLAID or Site Name")
            elif not batch_devices:
                st.warning("⚠️ Please enter device identifiers")
            else:
                items = [item.strip() for item in batch_input.split(',') if item.strip()]
                clean_devices = batch_devices.replace('\n', ',').replace(' ', '')
                clean_devices = ','.join([d.strip() for d in clean_devices.split(',') if d.strip()])
                
                if not items:
                    st.warning("⚠️ No valid entries found")
                else:
                    st.success(f"📦 Processing {len(items)} items...")
                    
                    results = []
                    generated_links = []
                    combined_tokens = []
                    
                    for idx, item in enumerate(items):
                        site_data = get_site_by_plaid(df, item)
                        if site_data:
                            plaid = safe_str(site_data.get('PLAID', ''))
                            site_name = safe_str(site_data.get('SITE', ''))
                            token = generate_secure_token(plaid, batch_start_date, batch_end_date, clean_devices)
                            base_url = st.get_option('server.baseUrlPath') or ""
                            link = f"{base_url}/?token={token}"
                            results.append({
                                'input': item,
                                'plaid': plaid,
                                'site': site_name,
                                'status': 'success',
                                'link': link,
                                'index': idx + 1
                            })
                            generated_links.append({
                                'number': idx + 1,
                                'link': link,
                                'site': site_name
                            })
                            combined_tokens.append(f"t{idx + 1}: {link}")
                        else:
                            site_data = get_site_by_name(df, item)
                            if site_data:
                                plaid = safe_str(site_data.get('PLAID', ''))
                                site_name = safe_str(site_data.get('SITE', ''))
                                token = generate_secure_token(plaid, batch_start_date, batch_end_date, clean_devices)
                                base_url = st.get_option('server.baseUrlPath') or ""
                                link = f"{base_url}/?token={token}"
                                results.append({
                                    'input': item,
                                    'plaid': plaid,
                                    'site': site_name,
                                    'status': 'success',
                                    'link': link,
                                    'index': idx + 1
                                })
                                generated_links.append({
                                    'number': idx + 1,
                                    'link': link,
                                    'site': site_name
                                })
                                combined_tokens.append(f"t{idx + 1}: {link}")
                            else:
                                results.append({
                                    'input': item,
                                    'plaid': '',
                                    'site': '',
                                    'status': 'error',
                                    'link': '',
                                    'index': idx + 1
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
                    
                    # Display combined tokens
                    st.markdown("---")
                    st.subheader("🔗 Combined Tokens")
                    st.markdown("Copy all tokens at once (t1, t2, t3...)")
                    
                    combined_text = "\n".join(combined_tokens)
                    
                    st.markdown(f"""
                    <div class="combined-tokens-box">
                        <div class="title">📋 All Tokens (Combined)</div>
                        <div class="tokens">{combined_text}</div>
                        <button class="copy-all-btn" onclick="navigator.clipboard.writeText(`{combined_text.replace('`', '\\`')}`)">📋 Copy All Tokens</button>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Display individual tokens
                    st.markdown("---")
                    st.subheader("🔗 Individual Tokens")
                    st.markdown("Paste Token or Batch (t1, t2...)")
                    
                    st.markdown(f"""
                    <div class="token-list-container">
                        <div class="token-list-title">📋 Generated Tokens</div>
                    """, unsafe_allow_html=True)
                    
                    for link_info in generated_links:
                        st.markdown(f"""
                        <div class="token-item">
                            <span class="t-number">t{link_info['number']}</span>
                            <span class="t-value">{link_info['link']}</span>
                            <button class="t-copy" onclick="navigator.clipboard.writeText('{link_info['link']}')">📋 Copy</button>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Full links
                    st.markdown("""
                        <div style="margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px solid #2a2a44;">
                            <div style="color: #7a7a95; font-size: 0.6rem; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;">Full Links</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    for link_info in generated_links:
                        st.markdown(f"""
                        <div class="token-display-box">
                            <div class="token-label">t{link_info['number']} - {link_info['site']}</div>
                            <div class="token-value">{link_info['link']}</div>
                            <button class="token-copy-btn" onclick="navigator.clipboard.writeText('{link_info['link']}')">📋 Copy Link</button>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Export
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
                            
                            combined_export = "\n".join([f"t{idx+1}: {r['link']}" for idx, r in enumerate(results) if r['status'] == 'success'])
                            st.download_button(
                                "⬇️ Download Combined Tokens as Text",
                                data=combined_export.encode('utf-8'),
                                file_name=f"combined_tokens_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                                mime="text/plain",
                                use_container_width=True
                            )

# ============================================================
# SECTION 9: SITE VIEWER
# ============================================================
def show_site_viewer(token):
    inject_device_fingerprint_script()
    app_header()
    
    device_fp = get_device_fingerprint()
    
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
        <div style="background: #1a1a2e; 
                    border-radius: 16px; 
                    padding: 1.5rem; 
                    border: 1px solid #f59e0b; 
                    box-shadow: 0 4px 20px rgba(0,0,0,0.5);">
            <h2 style="color: #f59e0b;">⚠️ Data Not Available</h2>
            <p style="color: #c0c0d0;">The site data is not available. Please contact the administrator.</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    token = token.strip()
    if '%' in token:
        try:
            token = urllib.parse.unquote(token)
        except:
            pass
    
    site_data, error = validate_token(token, df, device_fp)
    
    if error:
        st.markdown(f"""
        <div style="background: #1a1a2e; 
                    border-radius: 16px; 
                    padding: 1.5rem; 
                    border: 1px solid #ef4444; 
                    box-shadow: 0 4px 20px rgba(0,0,0,0.5);">
            <h2 style="color: #ef4444;">🔒 Access Denied</h2>
            <p style="color: #d0d0e0;">{error}</p>
            <p style="color: #8a8aa0; font-size: 0.85rem;">Your device could not be verified. Please ensure your device is registered.</p>
            <div style="background: #1a1a2e; 
                        border-radius: 8px; 
                        padding: 0.5rem; 
                        margin: 0.5rem 0; 
                        border: 1px solid #2a2a44;">
                <div style="color: #34d399; font-size: 0.7rem;">Your Device ID: <code style="color: #60a5fa;">{get_device_id()}</code></div>
                <div style="color: #8a8aa0; font-size: 0.6rem;">Contact the administrator to register this device</div>
            </div>
            <br>
            <button onclick="location.href='/'" 
                    style="background: #4f8cf7; 
                           color: white; 
                           padding: 0.5rem 1.2rem; 
                           border-radius: 40px; 
                           font-size: 0.8rem; 
                           font-weight: 600; 
                           border: none; 
                           cursor: pointer;">🏠 Return to Home</button>
        </div>
        """, unsafe_allow_html=True)
        return
    
    if not site_data:
        st.markdown("""
        <div style="background: #1a1a2e; 
                    border-radius: 16px; 
                    padding: 1.5rem; 
                    border: 1px solid #f59e0b; 
                    box-shadow: 0 4px 20px rgba(0,0,0,0.5);">
            <h2 style="color: #f59e0b;">⚠️ Site Not Found</h2>
            <p style="color: #c0c0d0;">The requested site could not be found in the database.</p>
            <button onclick="location.href='/'" 
                    style="background: #4f8cf7; 
                           color: white; 
                           padding: 0.5rem 1.2rem; 
                           border-radius: 40px; 
                           font-size: 0.8rem; 
                           font-weight: 600; 
                           border: none; 
                           cursor: pointer;">🏠 Return to Home</button>
        </div>
        """, unsafe_allow_html=True)
        return
    
    online_time = get_online_time()
    time_source = "🔒 Time verified: Online (UTC)" if online_time else "⚠️ Time source: System (offline - contact admin)"
    
    device_status = "✅ Device Verified" if site_data.get('_device_restricted', False) else "ℹ️ No device restriction"
    device_count = site_data.get('_device_count', 0)
    
    # Get date info
    start_date_str = site_data.get('_start_date', '')
    end_date_str = site_data.get('_end_date', '')
    
    date_info = ""
    if start_date_str and end_date_str:
        try:
            start = datetime.fromisoformat(start_date_str)
            end = datetime.fromisoformat(end_date_str)
            date_info = f"📅 {start.strftime('%B %d, %Y')} - {end.strftime('%B %d, %Y')}"
        except:
            pass
    
    st.markdown(f"""
    <div style="background: #1a1a2e; 
                border-radius: 16px; 
                padding: 1.5rem; 
                border: 1px solid #34d399; 
                box-shadow: 0 4px 20px rgba(0,0,0,0.5);">
        <div style="display: flex; 
                    justify-content: space-between; 
                    align-items: center; 
                    flex-wrap: wrap;">
            <div>
                <h2 style="color: #e8e8f0; margin: 0;">{site_data.get('SITE', 'Unknown Site')}</h2>
                <span style="background: rgba(139, 92, 246, 0.25); 
                           color: #a78bfa; 
                           padding: 0.15rem 0.6rem; 
                           border-radius: 40px; 
                           font-size: 0.65rem; 
                           font-weight: 600; 
                           border: 1px solid rgba(139, 92, 246, 0.2); 
                           display: inline-block;">{site_data.get('PLAID', 'No ID')}</span>
                {f'<br><span style="color: #fbbf24; font-size: 0.7rem;">{date_info}</span>' if date_info else ''}
            </div>
            <div style="text-align: right;">
                <span style="background: rgba(52, 211, 153, 0.2); 
                           color: #34d399; 
                           padding: 0.15rem 0.6rem; 
                           border-radius: 40px; 
                           font-size: 0.65rem; 
                           border: 1px solid rgba(52, 211, 153, 0.2);">🔒 Secure Access</span>
                <br>
                <span style="color: #8a8aa0; font-size: 0.7rem;">{time_source}</span>
                <br>
                <span style="color: #34d399; font-size: 0.7rem;">{device_status} {f"({device_count} device(s))" if device_count > 0 else ""}</span>
                <br>
                <span style="color: #8a8aa0; font-size: 0.6rem;">📱 Device: {get_device_id()}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    site_card(site_data)

# ============================================================
# SECTION 10: API ENDPOINT
# ============================================================
def api_validate():
    try:
        token = st.query_params.get('token', '').strip()
        device_fingerprint = st.query_params.get('device_fp', '').strip()
        device_id = st.query_params.get('device_id', '').strip()
        
        if not token:
            st.json({
                'success': False,
                'error': 'Missing token parameter'
            })
            return
        
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
            st.json({
                'success': False,
                'error': 'No data available'
            })
            return
        
        site_data, error = validate_token(token, df, device_fingerprint)
        
        if site_data:
            clean_data = {k: v for k, v in site_data.items() if not k.startswith('_')}
            st.json({
                'success': True,
                'data': clean_data
            })
        else:
            st.json({
                'success': False,
                'error': error or 'Validation failed'
            })
            
    except Exception as e:
        st.json({
            'success': False,
            'error': f'Server error: {str(e)}'
        })

# ============================================================
# SECTION 11: MAIN
# ============================================================
def show_main():
    inject_device_fingerprint_script()
    app_header()
    
    query_params = st.query_params
    token = query_params.get('token', None)
    
    if token:
        show_site_viewer(token)
        return
    
    st.markdown("""
    <div style="background: #1a1a2e; 
                border-radius: 16px; 
                padding: 1.5rem; 
                border: 1px solid #2a2a44; 
                box-shadow: 0 4px 20px rgba(0,0,0,0.5);">
        <h2 style="color: #e8e8f0; margin-bottom: 0.5rem; font-weight: 700;">🔐 Secure Site Access</h2>
        <p style="color: #c0c0d0; font-size: 0.95rem; line-height: 1.6;">Enter your secure link to access site details.</p>
        <p style="color: #8a8aa0; font-size: 0.85rem;">
            ⏰ Time is verified online to prevent fraud<br>
            🔒 Each link is unique and expires after 30 days<br>
            📱 <strong style="color: #34d399;">MAC Address / IMEI / Android ID</strong> verification
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
        Links expire after 30 days • MAC/IMEI/Android ID verification
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("⚙️ Admin Panel", key="admin_btn_main", use_container_width=True):
        st.query_params["page"] = "admin"
        st.rerun()
    
    st.markdown("""
    <div style="position: fixed; 
                bottom: 0; 
                left: 0; 
                right: 0; 
                background: #14141e; 
                border-top: 1px solid #2a2a44; 
                display: flex; 
                justify-content: space-around; 
                padding: 0.4rem 0.5rem; 
                z-index: 1000; 
                backdrop-filter: blur(10px);">
        <span style="display: flex; 
                     flex-direction: column; 
                     align-items: center; 
                     gap: 0.1rem; 
                     padding: 0.3rem 0.8rem; 
                     border-radius: 12px; 
                     color: #4f8cf7; 
                     font-size: 0.55rem; 
                     font-weight: 500;">
            <span style="font-size: 1.2rem;">📍</span>
            Site
        </span>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# ROUTING
# ============================================================
query_params = st.query_params

if 'api' in query_params and query_params['api'] == 'validate':
    api_validate()
elif 'page' in query_params and query_params['page'] == 'admin':
    if not st.session_state.admin_authenticated:
        show_admin_login()
    else:
        show_admin_dashboard()
elif 'token' in query_params and query_params['token']:
    show_site_viewer(query_params['token'])
else:
    show_main()
