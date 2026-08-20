import streamlit as st
import pandas as pd
import base64
from pathlib import Path
from datetime import datetime
import plotly.graph_objects as go
import os
import re

# ------------------------------
# PAGE CONFIG
# ------------------------------
st.set_page_config(
    page_title="GPS Extractor • Globe FO",
    page_icon="📍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ------------------------------
# SESSION STATE INIT
# ------------------------------
if 'df' not in st.session_state:
    st.session_state.df = None
if 'search_term' not in st.session_state:
    st.session_state.search_term = ''
if 'has_searched' not in st.session_state:
    st.session_state.has_searched = False
if 'search_results' not in st.session_state:
    st.session_state.search_results = None
if 'page' not in st.session_state:
    st.session_state.page = 'main'
if 'debug_info' not in st.session_state:
    st.session_state.debug_info = None

# ------------------------------
# ACTUAL COLUMN MAPPINGS FROM YOUR EXCEL
# ------------------------------
# Your actual headers from the image:
# PLAID, SITE, WIRELINE_NAME (NMS NAMES), BCF_NAME, REGION, PROVINCE, 
# MUNICIPALITY, BARANGAY, TERRITORY, LATITUDE, LONGITUDE, SITE_ADD, 
# ASSIGN_HUB, TOWERCO, NEW ASSIGN_AREA, NEW ASSIGN_AREA NAME, 
# NEW ASSIGN_HUB, NEW ENGINEER_AH, NEW ENGINEER_ANM1, 
# NEW ENGINEER_ANM1 ID NUMBER, CONTACT NUMBER, NEW ANM HEAD, NEW ROH

# Note: Some columns may have underscores (_) instead of spaces
COLUMN_MAPPINGS = {
    'PLAID': ['PLAID'],
    'SITE': ['SITE'],
    'REGION': ['REGION'],
    'PROVINCE': ['PROVINCE'],
    'MUNICIPALITY': ['MUNICIPALITY'],
    'BARANGAY': ['BARANGAY'],
    'TERRITORY': ['TERRITORY'],
    'LATITUDE': ['LATITUDE'],
    'LONGITUDE': ['LONGITUDE'],
    'SITE_ADD': ['SITE_ADD', 'SITE ADD'],
    'ASSIGN_HUB': ['ASSIGN_HUB', 'ASSIGN HUB'],
    'TOWERCO': ['TOWERCO'],
    'NEW_ASSIGN_HUB': ['NEW ASSIGN_HUB', 'NEW ASSIGN HUB', 'NEW_ASSIGN_HUB'],  # GLOBE HUB
    'FO_ONSITE': ['NEW ENGINEER_ANM1', 'NEW ENGINEER_ANM1', 'NEW_ENGINEER_ANM1'],  # FO ONSITE
    'CONTACT_NUMBER': ['CONTACT NUMBER', 'CONTACT_NUMBER', 'CONTACT NO'],  # FO NUMBER
    'NEW_ENGINEER_AH': ['NEW ENGINEER_AH', 'NEW ENGINEER AH'],
    'NEW_ANM_HEAD': ['NEW ANM HEAD', 'NEW_ANM_HEAD'],
    'NEW_ROH': ['NEW ROH', 'NEW_ROH'],
    'NEW_ASSIGN_AREA': ['NEW ASSIGN_AREA', 'NEW ASSIGN AREA'],
    'NEW_ASSIGN_AREA_NAME': ['NEW ASSIGN_AREA NAME', 'NEW ASSIGN AREA NAME'],
}

# Display names for the UI
DISPLAY_NAMES = {
    'NEW ASSIGN_HUB': '🌐 GLOBE HUB',
    'NEW ENGINEER_ANM1': '👤 FO ONSITE',
    'CONTACT NUMBER': '📞 FO NUMBER',
    'ASSIGN_HUB': '📋 ASSIGN HUB',
    'NEW ENGINEER_AH': '👤 AH',
    'NEW ANM HEAD': '👤 ANM HEAD',
    'NEW ROH': '📋 ROH',
}

# ------------------------------
# DARK THEME CUSTOM CSS (condensed for space)
# ------------------------------
st.markdown("""
    <style>
    /* ========================================
       CSS VARIABLES
       ======================================== */
    :root {
        --bg-primary: #0a0a0f;
        --bg-secondary: #14141e;
        --bg-card: #1a1a2e;
        --bg-card-hover: #222244;
        --bg-input: #1e1e32;
        --text-primary: #e8e8f0;
        --text-secondary: #a0a0b8;
        --text-muted: #6b6b85;
        --border-color: #2a2a44;
        --accent-blue: #4f8cf7;
        --accent-blue-hover: #3a7bd5;
        --accent-green: #34d399;
        --accent-green-hover: #2bb386;
        --accent-purple: #8b5cf6;
        --accent-orange: #f59e0b;
        --accent-red: #ef4444;
        --shadow-color: rgba(0, 0, 0, 0.5);
        --highlight-yellow: #fbbf24;
        --safe-top: env(safe-area-inset-top, 0px);
        --safe-bottom: env(safe-area-inset-bottom, 0px);
    }

    * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }

    .main .block-container {
        padding: 0.5rem 0.8rem 5rem 0.8rem;
        background: var(--bg-primary);
        max-width: 100% !important;
    }

    .stApp { background: var(--bg-primary); }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* ========================================
       APP HEADER
       ======================================== */
    .app-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #2a1a3e 100%);
        padding: 0.8rem 1rem;
        margin: -0.5rem -0.8rem 1rem -0.8rem;
        border-bottom: 1px solid var(--border-color);
        position: sticky;
        top: 0;
        z-index: 999;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
    }

    .app-header-content {
        display: flex;
        align-items: center;
        justify-content: space-between;
        max-width: 1200px;
        margin: 0 auto;
    }

    .app-logo {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .app-logo-icon { font-size: 1.5rem; }
    .app-logo-text {
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--text-primary);
        white-space: nowrap;
    }

    .app-logo-badge {
        background: rgba(79, 140, 247, 0.2);
        color: var(--accent-blue);
        padding: 0.15rem 0.6rem;
        border-radius: 40px;
        font-size: 0.6rem;
        font-weight: 500;
        border: 1px solid rgba(79, 140, 247, 0.2);
        margin-left: 0.3rem;
    }

    .app-nav {
        display: flex;
        gap: 0.3rem;
        align-items: center;
    }

    .nav-btn {
        background: transparent;
        border: 1px solid var(--border-color);
        color: var(--text-secondary);
        padding: 0.4rem 0.8rem;
        border-radius: 40px;
        font-size: 0.75rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
        text-decoration: none;
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        white-space: nowrap;
    }

    .nav-btn:hover, .nav-btn.active {
        background: var(--bg-card);
        border-color: var(--accent-blue);
        color: var(--text-primary);
    }

    /* Debug info */
    .debug-container {
        background: var(--bg-secondary);
        border-radius: 12px;
        padding: 0.8rem;
        border: 1px solid var(--border-color);
        margin: 0.5rem 0;
        font-family: monospace;
        font-size: 0.75rem;
        color: var(--text-secondary);
        max-height: 200px;
        overflow: auto;
    }

    .debug-container .found { color: var(--accent-green); }
    .debug-container .missing { color: var(--accent-red); }
    .debug-container .info { color: var(--accent-blue); }

    /* ========================================
       SEARCH SECTION
       ======================================== */
    .search-section {
        background: var(--bg-secondary);
        border-radius: 16px;
        padding: 1rem;
        border: 1px solid var(--border-color);
        margin-bottom: 1rem;
    }

    .search-hint {
        color: var(--text-muted);
        font-size: 0.7rem;
        margin-top: 0.3rem;
        padding: 0 0.3rem;
    }

    .search-hint code {
        background: var(--bg-input);
        padding: 0.1rem 0.4rem;
        border-radius: 4px;
        font-size: 0.7rem;
        color: var(--text-secondary);
        border: 1px solid var(--border-color);
    }

    .search-bar {
        display: flex;
        gap: 0.5rem;
        align-items: center;
    }

    .search-input-wrapper {
        flex: 1;
        position: relative;
    }

    .search-input-wrapper .search-icon {
        position: absolute;
        left: 12px;
        top: 50%;
        transform: translateY(-50%);
        color: var(--text-muted);
        font-size: 1rem;
    }

    .search-input-wrapper input {
        width: 100%;
        padding: 0.7rem 0.7rem 0.7rem 2.5rem;
        background: var(--bg-input);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        color: var(--text-primary);
        font-size: 0.95rem;
        transition: all 0.2s;
        outline: none;
    }

    .search-input-wrapper input:focus {
        border-color: var(--accent-blue);
        box-shadow: 0 0 0 3px rgba(79, 140, 247, 0.15);
    }

    .search-input-wrapper input::placeholder {
        color: var(--text-muted);
    }

    .search-actions {
        display: flex;
        gap: 0.4rem;
    }

    .search-btn, .clear-btn {
        padding: 0.7rem 1rem;
        border-radius: 12px;
        border: none;
        font-weight: 600;
        font-size: 0.85rem;
        cursor: pointer;
        transition: all 0.2s;
        white-space: nowrap;
        min-width: 60px;
    }

    .search-btn {
        background: var(--accent-blue);
        color: white;
    }

    .search-btn:hover {
        background: var(--accent-blue-hover);
        transform: scale(1.02);
    }

    .clear-btn {
        background: var(--bg-card);
        color: var(--text-secondary);
        border: 1px solid var(--border-color);
    }

    .clear-btn:hover {
        background: var(--bg-card-hover);
        color: var(--text-primary);
    }

    /* ========================================
       STATS CARDS
       ======================================== */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 0.6rem;
        margin: 0.5rem 0 1rem 0;
    }

    .stat-card {
        background: var(--bg-secondary);
        border-radius: 12px;
        padding: 0.8rem;
        border: 1px solid var(--border-color);
        text-align: center;
    }

    .stat-number {
        font-size: 1.4rem;
        font-weight: 700;
        color: var(--text-primary);
        display: block;
    }

    .stat-label {
        font-size: 0.7rem;
        color: var(--text-muted);
        display: block;
        margin-top: 0.15rem;
    }

    /* ========================================
       SITE CARDS
       ======================================== */
    .site-card {
        background: var(--bg-card);
        border-radius: 16px;
        padding: 1rem;
        margin-bottom: 0.8rem;
        border: 1px solid var(--border-color);
        transition: all 0.3s ease;
        box-shadow: 0 4px 20px var(--shadow-color);
        animation: fadeIn 0.4s ease-out;
    }

    .site-card:active { transform: scale(0.98); }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(12px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .site-header {
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        align-items: flex-start;
        gap: 0.5rem;
        margin-bottom: 0.5rem;
    }

    .site-name {
        font-size: 1rem;
        font-weight: 600;
        color: var(--text-primary);
        word-break: break-word;
    }

    .site-plaid {
        background: rgba(139, 92, 246, 0.2);
        color: var(--accent-purple);
        padding: 0.15rem 0.6rem;
        border-radius: 40px;
        font-size: 0.65rem;
        font-weight: 600;
        border: 1px solid rgba(139, 92, 246, 0.2);
        display: inline-block;
        margin-left: 0.3rem;
        white-space: nowrap;
    }

    .site-location {
        font-size: 0.8rem;
        color: var(--text-secondary);
        margin-bottom: 0.5rem;
        word-break: break-word;
    }

    .site-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 0.3rem;
        margin-bottom: 0.5rem;
    }

    .tag {
        padding: 0.15rem 0.6rem;
        border-radius: 40px;
        font-size: 0.6rem;
        font-weight: 500;
        border: 1px solid transparent;
    }

    .tag-territory {
        background: rgba(52, 211, 153, 0.15);
        color: var(--accent-green);
        border-color: rgba(52, 211, 153, 0.2);
    }

    .tag-towerco {
        background: rgba(251, 191, 36, 0.15);
        color: var(--highlight-yellow);
        border-color: rgba(251, 191, 36, 0.2);
    }

    .site-details {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.3rem 1rem;
        margin: 0.5rem 0;
        font-size: 0.8rem;
    }

    .detail-item {
        display: flex;
        flex-direction: column;
        gap: 0.05rem;
    }

    .detail-label {
        color: var(--text-muted);
        font-size: 0.6rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .detail-value {
        color: var(--text-secondary);
        font-weight: 500;
        font-size: 0.8rem;
        word-break: break-word;
    }

    .detail-value.highlight {
        color: var(--accent-orange);
        font-weight: 600;
    }

    .detail-value.missing {
        color: var(--accent-red);
        font-style: italic;
    }

    .site-actions {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 0.7rem;
    }

    .action-btn {
        flex: 1;
        min-width: 100px;
        padding: 0.5rem 0.8rem;
        border-radius: 40px;
        border: none;
        font-size: 0.75rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s;
        text-decoration: none;
        text-align: center;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 0.4rem;
    }

    .action-btn:active { transform: scale(0.95); }

    .btn-map {
        background: var(--accent-blue);
        color: white;
    }

    .btn-map:hover {
        background: var(--accent-blue-hover);
        color: white;
    }

    .btn-call {
        background: var(--accent-green);
        color: #0a0a0f;
    }

    .btn-call:hover {
        background: var(--accent-green-hover);
        color: #0a0a0f;
    }

    .btn-disabled {
        background: var(--bg-card);
        color: var(--text-muted);
        border: 1px solid var(--border-color);
        cursor: not-allowed;
    }

    /* ========================================
       WELCOME SCREEN
       ======================================== */
    .welcome-screen {
        text-align: center;
        padding: 2rem 1rem;
        background: var(--bg-secondary);
        border-radius: 16px;
        border: 1px solid var(--border-color);
        margin: 1rem 0;
    }

    .welcome-icon { font-size: 3.5rem; margin-bottom: 0.8rem; }
    .welcome-title {
        font-size: 1.4rem;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 0.3rem;
    }
    .welcome-subtitle {
        color: var(--text-secondary);
        font-size: 0.9rem;
        max-width: 400px;
        margin: 0 auto;
        line-height: 1.5;
    }
    .welcome-hint {
        color: var(--text-muted);
        font-size: 0.8rem;
        margin-top: 1.2rem;
        padding: 0.8rem;
        background: var(--bg-card);
        border-radius: 8px;
        border: 1px dashed var(--border-color);
        display: inline-block;
    }

    /* ========================================
       BOTTOM NAVIGATION
       ======================================== */
    .bottom-nav {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: var(--bg-secondary);
        border-top: 1px solid var(--border-color);
        display: flex;
        justify-content: space-around;
        padding: 0.4rem 0.5rem calc(0.4rem + var(--safe-bottom, 0px));
        z-index: 1000;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
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
        color: var(--text-muted);
        font-size: 0.55rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
        text-decoration: none;
        min-width: 50px;
    }

    .nav-item .nav-icon { font-size: 1.2rem; }
    .nav-item.active { color: var(--accent-blue); }
    .nav-item:active { transform: scale(0.9); }

    /* ========================================
       SEARCH HIGHLIGHT
       ======================================== */
    .search-highlight {
        background: var(--highlight-yellow);
        color: #0a0a0f;
        padding: 0.05rem 0.2rem;
        border-radius: 3px;
        font-weight: 600;
    }

    /* ========================================
       WEB APP - DESKTOP
       ======================================== */
    @media (min-width: 769px) {
        .main .block-container {
            padding: 1rem 2rem 6rem 2rem;
            max-width: 1200px !important;
            margin: 0 auto;
        }

        .app-header {
            padding: 0.8rem 2rem;
            margin: -0.5rem -2rem 1.5rem -2rem;
        }

        .app-logo-text { font-size: 1.3rem; }

        .stats-grid {
            grid-template-columns: repeat(4, 1fr);
            gap: 1rem;
        }

        .stat-number { font-size: 1.8rem; }
        .stat-card { padding: 1.2rem; }

        .site-card {
            padding: 1.5rem;
            margin-bottom: 1rem;
        }

        .site-card:hover {
            background: var(--bg-card-hover);
            border-color: var(--accent-purple);
            transform: translateY(-2px);
            box-shadow: 0 8px 30px var(--shadow-color);
        }

        .site-name { font-size: 1.2rem; }
        .site-details { grid-template-columns: repeat(3, 1fr); }
        .site-actions { gap: 0.8rem; }

        .action-btn {
            flex: 0 1 auto;
            min-width: 140px;
            padding: 0.6rem 1.2rem;
            font-size: 0.85rem;
        }

        .action-btn:hover { transform: translateY(-2px); }
        .btn-map:hover { box-shadow: 0 4px 15px rgba(79, 140, 247, 0.3); }
        .btn-call:hover { box-shadow: 0 4px 15px rgba(52, 211, 153, 0.3); }

        .welcome-screen { padding: 4rem 2rem; }
        .welcome-icon { font-size: 5rem; }
        .welcome-title { font-size: 2rem; }
        .welcome-subtitle { font-size: 1.1rem; }

        .bottom-nav { display: none; }
        .search-section { padding: 1.5rem; }

        .search-input-wrapper input {
            padding: 0.8rem 0.8rem 0.8rem 3rem;
            font-size: 1rem;
        }

        .search-btn, .clear-btn {
            padding: 0.8rem 1.5rem;
            font-size: 0.95rem;
            min-width: 80px;
        }

        .debug-container { max-height: 300px; }
    }

    /* ========================================
       TABLET
       ======================================== */
    @media (min-width: 481px) and (max-width: 768px) {
        .stats-grid { grid-template-columns: repeat(4, 1fr); }
        .site-details { grid-template-columns: repeat(2, 1fr); }
        .bottom-nav .nav-item { font-size: 0.6rem; }
        .bottom-nav .nav-item .nav-icon { font-size: 1.3rem; }
    }

    /* ========================================
       SMALL PHONE
       ======================================== */
    @media (max-width: 380px) {
        .app-logo-text { font-size: 0.9rem; }
        .app-logo-badge { font-size: 0.5rem; padding: 0.1rem 0.4rem; }
        .nav-btn { font-size: 0.65rem; padding: 0.3rem 0.6rem; }
        .search-btn, .clear-btn {
            font-size: 0.7rem;
            padding: 0.6rem 0.7rem;
            min-width: 50px;
        }
        .site-name { font-size: 0.9rem; }
        .site-details { grid-template-columns: 1fr 1fr; }
        .action-btn {
            min-width: 70px;
            font-size: 0.65rem;
            padding: 0.4rem 0.6rem;
        }
    }
    </style>
""", unsafe_allow_html=True)

# ------------------------------
# FUNCTIONS
# ------------------------------
@st.cache_data
def load_excel_data(file_path):
    """Load data from Excel file using the correct column mappings"""
    try:
        if not os.path.exists(file_path):
            return None
        df = pd.read_excel(file_path, engine='openpyxl')
        # Keep original column names
        return df
    except Exception as e:
        st.error(f"❌ Error loading file: {str(e)}")
        return None

def safe_str(val):
    if pd.isna(val):
        return ""
    return str(val)

def find_column(row_dict, possible_names):
    """
    Find a column in the row dictionary by trying multiple possible names.
    Returns the matched column name or None.
    """
    row_keys = list(row_dict.keys())
    
    for name in possible_names:
        # Exact match
        if name in row_dict:
            return name
        # Case-insensitive match
        for key in row_keys:
            if key.strip().upper() == name.strip().upper():
                return key
            # Contains match
            if name.strip().upper() in key.strip().upper():
                return key
    return None

def get_column_value(row_dict, possible_names, default=""):
    """
    Safely get value from a row dictionary using multiple possible column names.
    """
    if isinstance(possible_names, str):
        possible_names = [possible_names]
    
    # Try to find the column
    matched_col = find_column(row_dict, possible_names)
    
    if matched_col and matched_col in row_dict:
        val = row_dict[matched_col]
        return safe_str(val)
    
    return default

def highlight_text(text, search_term):
    if not search_term or not text:
        return text
    try:
        pattern = re.compile(re.escape(search_term), re.IGNORECASE)
        return pattern.sub(lambda m: f'<span class="search-highlight">{m.group()}</span>', str(text))
    except:
        return text

def perform_intelligent_search(df, search_input):
    if not search_input or search_input.strip() == '':
        return pd.DataFrame()
    search_terms = [term.strip() for term in search_input.split(',') if term.strip()]
    if not search_terms:
        return pd.DataFrame()
    final_mask = pd.Series([False] * len(df))
    for term in search_terms:
        term_mask = pd.Series([False] * len(df))
        term_found = False
        
        # Search in PLAID
        if 'PLAID' in df.columns:
            exact_mask_plaid = df['PLAID'].astype(str).str.strip().str.upper() == term.upper()
            term_mask |= exact_mask_plaid
            if exact_mask_plaid.any():
                term_found = True
        
        # Search in SITE
        if 'SITE' in df.columns:
            exact_mask_site = df['SITE'].astype(str).str.strip().str.upper() == term.upper()
            term_mask |= exact_mask_site
            if exact_mask_site.any():
                term_found = True
        
        # If no exact match, try contains
        if not term_found:
            if 'PLAID' in df.columns:
                term_mask |= df['PLAID'].astype(str).str.contains(term, case=False, na=False)
            if 'SITE' in df.columns:
                term_mask |= df['SITE'].astype(str).str.contains(term, case=False, na=False)
        
        final_mask |= term_mask
    return df[final_mask].copy()

def create_site_card_html(row_dict, search_term=""):
    """Create HTML for a site card with the correct column mappings"""
    
    # Get values using multiple possible column names
    plaid = get_column_value(row_dict, ['PLAID'])
    site = get_column_value(row_dict, ['SITE'])
    region = get_column_value(row_dict, ['REGION'])
    province = get_column_value(row_dict, ['PROVINCE'])
    municipality = get_column_value(row_dict, ['MUNICIPALITY'])
    barangay = get_column_value(row_dict, ['BARANGAY'])
    territory = get_column_value(row_dict, ['TERRITORY'])
    lat = get_column_value(row_dict, ['LATITUDE'])
    lon = get_column_value(row_dict, ['LONGITUDE'])
    site_add = get_column_value(row_dict, ['SITE_ADD', 'SITE ADD'])
    assigned_hub = get_column_value(row_dict, ['ASSIGN_HUB', 'ASSIGN HUB'])
    towerco = get_column_value(row_dict, ['TOWERCO'])
    
    # CRITICAL: These are the correctly mapped columns - try multiple variations
    new_assign_hub = get_column_value(row_dict, ['NEW ASSIGN_HUB', 'NEW ASSIGN HUB', 'NEW_ASSIGN_HUB'])
    fo_onsite = get_column_value(row_dict, ['NEW ENGINEER_ANM1', 'NEW ENGINEER_ANM1', 'NEW_ENGINEER_ANM1'])
    contact = get_column_value(row_dict, ['CONTACT NUMBER', 'CONTACT_NUMBER', 'CONTACT NO'])
    
    # Additional fields
    new_engineer_ah = get_column_value(row_dict, ['NEW ENGINEER_AH', 'NEW ENGINEER AH'])
    new_anm_head = get_column_value(row_dict, ['NEW ANM HEAD', 'NEW_ANM_HEAD'])
    new_roh = get_column_value(row_dict, ['NEW ROH', 'NEW_ROH'])
    
    # For display names
    hub_display = new_assign_hub if new_assign_hub else "Not assigned"
    fo_display = fo_onsite if fo_onsite else "No FO assigned"
    contact_display = contact if contact else "No contact"
    
    # Highlight search terms
    site_display = highlight_text(site, search_term)
    plaid_display = highlight_text(plaid, search_term)
    hub_display_highlighted = highlight_text(hub_display, search_term)
    fo_display_highlighted = highlight_text(fo_display, search_term)
    
    # Check if values are missing for styling
    fo_missing_class = "missing" if not fo_onsite else ""
    hub_missing_class = "missing" if not new_assign_hub else ""
    
    # Map button
    map_button = ''
    if lat and lon:
        try:
            float(lat); float(lon)
            maps_url = f"https://www.google.com/maps?q={lat},{lon}"
            map_button = f'<a href="{maps_url}" target="_blank" class="action-btn btn-map">🗺️ Navigate</a>'
        except:
            map_button = '<span class="action-btn btn-disabled">⚠️ Invalid</span>'
    else:
        map_button = '<span class="action-btn btn-disabled">⚠️ No coords</span>'
    
    # Call button
    call_button = ''
    if contact_display and contact_display != "No contact":
        clean_contact = ''.join(ch for ch in contact_display if ch.isdigit() or ch == '+')
        if clean_contact:
            call_button = f'<a href="tel:{clean_contact}" class="action-btn btn-call">📞 Call FO</a>'
        else:
            call_button = f'<span class="action-btn btn-disabled">📞 {contact_display}</span>'
    else:
        call_button = '<span class="action-btn btn-disabled">📞 No contact</span>'
    
    html = f"""
    <div class="site-card">
        <div class="site-header">
            <div>
                <span class="site-name">{site_display}</span>
                <span class="site-plaid">{plaid_display}</span>
            </div>
        </div>
        <div class="site-location">{region} · {province} · {municipality} · {barangay}</div>
        <div class="site-tags">
            <span class="tag tag-territory">{territory}</span>
            <span class="tag tag-towerco">{towerco}</span>
        </div>
        <div class="site-details">
            <div class="detail-item">
                <span class="detail-label">Address</span>
                <span class="detail-value">{site_add}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">👤 FO ONSITE</span>
                <span class="detail-value highlight {fo_missing_class}">{fo_display_highlighted}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">🌐 GLOBE HUB</span>
                <span class="detail-value highlight {hub_missing_class}">{hub_display_highlighted}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">📋 ASSIGN HUB</span>
                <span class="detail-value">{assigned_hub if assigned_hub else "Not assigned"}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">📞 FO NUMBER</span>
                <span class="detail-value">{contact_display}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">👤 AH</span>
                <span class="detail-value">{new_engineer_ah if new_engineer_ah else "N/A"}</span>
            </div>
        </div>
        <div class="site-actions">
            {map_button}
            {call_button}
        </div>
    </div>
    """
    return html

def create_map(df, selected_indices=None):
    map_df = df[df['LATITUDE'].notna() & df['LONGITUDE'].notna()].copy()
    if map_df.empty:
        return None
    fig = go.Figure()
    fig.add_trace(go.Scattermapbox(
        lat=map_df['LATITUDE'],
        lon=map_df['LONGITUDE'],
        mode='markers',
        marker=go.scattermapbox.Marker(size=10, color='#4f8cf7', opacity=0.6),
        text=map_df['SITE'] + '<br>' + map_df['SITE_ADD'],
        hoverinfo='text',
        name='All Sites',
        showlegend=False
    ))
    if selected_indices:
        selected_df = map_df.iloc[selected_indices]
        fig.add_trace(go.Scattermapbox(
            lat=selected_df['LATITUDE'],
            lon=selected_df['LONGITUDE'],
            mode='markers',
            marker=go.scattermapbox.Marker(size=15, color='#ef4444', opacity=0.9),
            text=selected_df['SITE'] + '<br>' + selected_df['SITE_ADD'],
            hoverinfo='text',
            name='Selected Sites',
            showlegend=False
        ))
        if len(selected_df) > 1:
            for i in range(len(selected_df) - 1):
                fig.add_trace(go.Scattermapbox(
                    lat=[selected_df.iloc[i]['LATITUDE'], selected_df.iloc[i+1]['LATITUDE']],
                    lon=[selected_df.iloc[i]['LONGITUDE'], selected_df.iloc[i+1]['LONGITUDE']],
                    mode='lines',
                    line=dict(width=2, color='#ef4444'),
                    showlegend=False,
                    hoverinfo='skip'
                ))
    fig.update_layout(
        mapbox=dict(
            style='dark',
            center=dict(
                lat=map_df['LATITUDE'].mean() if not map_df.empty else 14.5995,
                lon=map_df['LONGITUDE'].mean() if not map_df.empty else 121.0139
            ),
            zoom=8
        ),
        height=400,
        margin=dict(l=0, r=0, t=0, b=0),
        hovermode='closest',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )
    return fig

def create_pdf_export(df, selected_indices):
    try:
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        import tempfile
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.close()
        
        doc = SimpleDocTemplate(
            temp_file.name,
            pagesize=landscape(letter),
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#e8e8f0'),
            alignment=1,
            spaceAfter=30
        )
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#a0a0b8'),
            alignment=1,
            spaceAfter=20
        )
        
        content = []
        content.append(Paragraph("📍 GPS Extractor - Site Report", title_style))
        content.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", subtitle_style))
        content.append(Spacer(1, 20))
        content.append(Paragraph(f"<b>Total Sites:</b> {len(selected_indices)}", styles['Normal']))
        content.append(Spacer(1, 10))
        
        selected_df = df.iloc[selected_indices]
        
        # Header
        header = ['PLAID', 'SITE', 'REGION', 'FO ONSITE', 'GLOBE HUB', 'CONTACT', 'LATITUDE', 'LONGITUDE']
        table_data = [header]
        
        for idx, row in selected_df.iterrows():
            row_dict = row.to_dict()
            fo_onsite = get_column_value(row_dict, ['NEW ENGINEER_ANM1', 'NEW ENGINEER_ANM1', 'NEW_ENGINEER_ANM1'])
            globe_hub = get_column_value(row_dict, ['NEW ASSIGN_HUB', 'NEW ASSIGN HUB', 'NEW_ASSIGN_HUB'])
            contact = get_column_value(row_dict, ['CONTACT NUMBER', 'CONTACT_NUMBER', 'CONTACT NO'])
            lat_val = get_column_value(row_dict, ['LATITUDE'])
            lon_val = get_column_value(row_dict, ['LONGITUDE'])
            
            try:
                if lat_val and lon_val:
                    lat_val = f"{float(lat_val):.6f}"
                    lon_val = f"{float(lon_val):.6f}"
            except:
                pass
            
            table_data.append([
                get_column_value(row_dict, ['PLAID']),
                get_column_value(row_dict, ['SITE']),
                get_column_value(row_dict, ['REGION']),
                fo_onsite if fo_onsite else 'No FO assigned',
                globe_hub if globe_hub else 'Not assigned',
                contact if contact else 'No contact',
                lat_val,
                lon_val
            ])
        
        table = Table(table_data, colWidths=[0.8*inch, 1.2*inch, 1*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#e8e8f0')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#0a0a0f')),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#e8e8f0')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#2a2a44')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        content.append(table)
        doc.build(content)
        
        with open(temp_file.name, 'rb') as f:
            pdf_data = f.read()
        os.unlink(temp_file.name)
        return pdf_data
        
    except ImportError:
        st.error("PDF generation requires reportlab. Install with: pip install reportlab")
        return None
    except Exception as e:
        st.error(f"Error generating PDF: {str(e)}")
        return None

# ------------------------------
# APP HEADER
# ------------------------------
def app_header():
    st.markdown("""
    <div class="app-header">
        <div class="app-header-content">
            <div class="app-logo">
                <span class="app-logo-icon">📍</span>
                <span class="app-logo-text">GPS Extractor</span>
                <span class="app-logo-badge">FO Engr</span>
            </div>
            <div class="app-nav">
                <button class="nav-btn active" onclick="location.href='/'">🏠 Home</button>
                <button class="nav-btn" onclick="location.href='?page=about'">ℹ️ About</button>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ------------------------------
# BOTTOM NAVIGATION
# ------------------------------
def bottom_nav():
    st.markdown("""
    <div class="bottom-nav">
        <span class="nav-item active">
            <span class="nav-icon">📍</span>
            Sites
        </span>
        <span class="nav-item" style="color: var(--text-muted);">
            <span class="nav-icon">🔍</span>
            Search
        </span>
    </div>
    """, unsafe_allow_html=True)

# ------------------------------
# COLUMN DEBUGGER
# ------------------------------
def show_column_debug(df):
    """Show debug information about columns"""
    st.markdown("---")
    st.subheader("🔍 Column Debugger")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Available Columns in Your Excel:**")
        for col in df.columns:
            st.markdown(f"- `{col}`")
    
    with col2:
        st.markdown("**Column Mapping Status:**")
        
        # Check critical columns
        critical_columns = {
            'NEW ENGINEER_ANM1': ['NEW ENGINEER_ANM1', 'NEW ENGINEER_ANM1', 'NEW_ENGINEER_ANM1'],
            'NEW ASSIGN_HUB': ['NEW ASSIGN_HUB', 'NEW ASSIGN HUB', 'NEW_ASSIGN_HUB'],
            'CONTACT NUMBER': ['CONTACT NUMBER', 'CONTACT_NUMBER', 'CONTACT NO'],
            'ASSIGN_HUB': ['ASSIGN_HUB', 'ASSIGN HUB'],
        }
        
        for display_name, possible_names in critical_columns.items():
            found = False
            for name in possible_names:
                if name in df.columns:
                    found = True
                    break
                # Case-insensitive check
                for col in df.columns:
                    if col.strip().upper() == name.strip().upper():
                        found = True
                        break
                    if name.strip().upper() in col.strip().upper():
                        found = True
                        break
            
            if found:
                st.markdown(f"✅ **{display_name}** - Found")
            else:
                st.markdown(f"❌ **{display_name}** - Not Found")
    
    # Show sample data
    st.markdown("**Sample Data (First Row):**")
    if len(df) > 0:
        sample_row = df.iloc[0].to_dict()
        for key, value in sample_row.items():
            if pd.isna(value):
                val_display = "NULL"
            else:
                val_display = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
            st.markdown(f"- `{key}`: {val_display}")

# ------------------------------
# ABOUT PAGE
# ------------------------------
def show_about():
    app_header()
    
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0 1.5rem 0;">
        <h1 style="font-size: 1.8rem; font-weight: 700; color: #e8e8f0;">📍 GPS Extractor</h1>
        <p style="font-size: 0.95rem; color: #a0a0b8;">Globe FO Engineer Contact Management</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a1a2e 0%, #2a1a3e 100%); 
                border-radius: 16px; padding: 1.5rem; border: 1px solid #2a2a44; margin: 0.5rem 0;">
        <div style="display: flex; align-items: center; gap: 1rem; flex-wrap: wrap;">
            <div style="flex: 1;">
                <h2 style="color: #e8e8f0; margin: 0; font-size: 1.2rem;">👨‍💻 Developer</h2>
                <h3 style="color: #a0a0b8; margin: 0.3rem 0; font-size: 1rem;">Engr. John Carlo Rabanes, ECE</h3>
                <p style="margin: 0.2rem 0; color: #6b6b85; font-size: 0.85rem;">📧 rabanes.johncarlo4@gmail.com</p>
                <p style="margin: 0.2rem 0; color: #6b6b85; font-size: 0.85rem;">🏢 Nokia Shanghai Bell</p>
            </div>
            <div style="font-size: 3rem;">📡</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div style="background: #14141e; border-radius: 12px; padding: 1rem; height: 100%; border: 1px solid #2a2a44;">
            <h3 style="color: #4f8cf7; font-size: 1rem;">🎯 Mission</h3>
            <p style="color: #a0a0b8; font-size: 0.85rem; line-height: 1.5;">
                To empower field operations engineers with seamless access to site information, 
                enabling efficient navigation and communication for faster response times.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: #14141e; border-radius: 12px; padding: 1rem; height: 100%; border: 1px solid #2a2a44;">
            <h3 style="color: #fbbf24; font-size: 1rem;">👁️ Vision</h3>
            <p style="color: #a0a0b8; font-size: 0.85rem; line-height: 1.5;">
                To be the leading digital tool for telecommunications field operations, 
                setting the standard for efficiency and user experience.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.subheader("⚡ Features")
    
    features = [
        ("📍 GPS Navigation", "One-click Google Maps"),
        ("📞 Click-to-Call", "Direct contact dialing"),
        ("🔍 Smart Search", "Exact match first, then partial"),
        ("🗺️ Map View", "Interactive site visualization"),
        ("📄 PDF Export", "Multiple sites export"),
        ("📱 Mobile Ready", "Fully responsive design"),
        ("👤 FO Onsite Display", "Shows assigned Field Operations engineer"),
        ("🌐 Globe Hub Display", "Shows assigned Globe Hub"),
    ]
    
    for icon, name in features:
        st.markdown(f"**{icon} {name}**")
    
    st.markdown("---")
    st.caption("© 2026 GPS Extractor | Developed for Globe Telecom")
    
    bottom_nav()

# ------------------------------
# MAIN PAGE
# ------------------------------
def show_main():
    app_header()
    
    # Load data
    if st.session_state.df is None:
        df = load_excel_data("database.xlsx")
        if df is None:
            possible_paths = ["data/database.xlsx", "./data/database.xlsx", Path(__file__).parent / "database.xlsx", Path(__file__).parent / "data" / "database.xlsx"]
            for path in possible_paths:
                df = load_excel_data(path)
                if df is not None:
                    break
        if df is not None:
            st.session_state.df = df
            st.session_state.debug_info = df.columns.tolist()
    else:
        df = st.session_state.df
    
    if df is None or df.empty:
        st.warning("⚠️ No data available. Please check the database file.")
        bottom_nav()
        return
    
    # Show debug toggle
    if st.checkbox("🔧 Show Column Debugger", value=False):
        show_column_debug(df)
    
    # Search Section
    st.markdown('<div class="search-section">', unsafe_allow_html=True)
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input(
            "Search",
            value=st.session_state.search_term,
            placeholder="🔍 Search PLAID or Site Name...",
            label_visibility="collapsed",
            help="Search multiple sites with commas"
        )
    with col2:
        search_btn = st.button("🔍 Search", use_container_width=True)
        clear_btn = st.button("✖ Clear", use_container_width=True)
    
    st.markdown("""
    <div class="search-hint">
        🔍 <strong>Smart Search</strong> · Exact matches first, then partial · Separate with commas: 
        <code>Min97, SITE001</code>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    if clear_btn:
        st.session_state.search_term = ''
        st.session_state.has_searched = False
        st.session_state.search_results = None
        st.rerun()
    
    if search_btn and search_term:
        st.session_state.search_term = search_term
        st.session_state.has_searched = True
        st.session_state.search_results = perform_intelligent_search(df, search_term)
    
    if st.session_state.has_searched:
        search_results_df = st.session_state.search_results
        if search_results_df is None or len(search_results_df) == 0:
            terms = [term.strip() for term in search_term.split(',') if term.strip()]
            terms_display = ', '.join([f'"{t}"' for t in terms])
            st.markdown(f"""
            <div class="welcome-screen">
                <div class="welcome-icon">🔍</div>
                <div class="welcome-title">No Results Found</div>
                <div class="welcome-subtitle">No sites found matching: {terms_display}</div>
                <div class="welcome-hint">💡 Try checking the spelling or use partial matching</div>
            </div>
            """, unsafe_allow_html=True)
            bottom_nav()
            return
        
        terms = [term.strip() for term in search_term.split(',') if term.strip()]
        terms_display = ', '.join([f'"{t}"' for t in terms])
        st.markdown(f"**Found {len(search_results_df)} site(s)** matching: {terms_display}")
        
        # Count FO Onsite and Hub availability
        fo_count = 0
        hub_count = 0
        contact_count = 0
        for _, row in search_results_df.iterrows():
            row_dict = row.to_dict()
            if get_column_value(row_dict, ['NEW ENGINEER_ANM1', 'NEW ENGINEER_ANM1', 'NEW_ENGINEER_ANM1']):
                fo_count += 1
            if get_column_value(row_dict, ['NEW ASSIGN_HUB', 'NEW ASSIGN HUB', 'NEW_ASSIGN_HUB']):
                hub_count += 1
            if get_column_value(row_dict, ['CONTACT NUMBER', 'CONTACT_NUMBER', 'CONTACT NO']):
                contact_count += 1
        
        stats = {
            'total': len(search_results_df),
            'regions': search_results_df['REGION'].nunique() if 'REGION' in search_results_df.columns else 0,
            'coords': search_results_df['LATITUDE'].notna().sum() if 'LATITUDE' in search_results_df.columns else 0,
            'contacts': contact_count,
            'fo_onsite': fo_count,
            'globe_hub': hub_count,
        }
        
        st.markdown(f"""
        <div class="stats-grid">
            <div class="stat-card"><span class="stat-number">{stats['total']}</span><span class="stat-label">Results</span></div>
            <div class="stat-card"><span class="stat-number">{stats['regions']}</span><span class="stat-label">Regions</span></div>
            <div class="stat-card"><span class="stat-number">{stats['fo_onsite']}</span><span class="stat-label">👤 With FO Onsite</span></div>
            <div class="stat-card"><span class="stat-number">{stats['globe_hub']}</span><span class="stat-label">🌐 With Globe Hub</span></div>
        </div>
        """, unsafe_allow_html=True)
        
        # Filters
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            if 'REGION' in search_results_df.columns:
                regions = ['All'] + sorted(search_results_df['REGION'].dropna().unique().tolist())
                selected_region = st.selectbox('Region', regions)
                if selected_region != 'All':
                    search_results_df = search_results_df[search_results_df['REGION'] == selected_region]
        with col2:
            if 'TOWERCO' in search_results_df.columns:
                towercos = ['All'] + sorted(search_results_df['TOWERCO'].dropna().unique().tolist())
                selected_towerco = st.selectbox('TowerCo', towercos)
                if selected_towerco != 'All':
                    search_results_df = search_results_df[search_results_df['TOWERCO'] == selected_towerco]
        with col3:
            show_map = st.checkbox('🗺️ Map')
        
        # Map View
        if show_map and len(search_results_df) > 0:
            st.markdown("---")
            st.subheader("🗺️ Site Map Visualization")
            map_indices = search_results_df[search_results_df['LATITUDE'].notna() & search_results_df['LONGITUDE'].notna()].index.tolist()
            if map_indices:
                selected_map = st.multiselect("Highlight sites", options=map_indices, format_func=lambda x: f"{search_results_df.loc[x, 'SITE']}")
                fig = create_map(search_results_df, selected_map)
                if fig:
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                    if selected_map:
                        if st.button("📄 Export to PDF"):
                            pdf_data = create_pdf_export(search_results_df, selected_map)
                            if pdf_data:
                                b64 = base64.b64encode(pdf_data).decode()
                                href = f'<a href="data:application/pdf;base64,{b64}" download="site_report_{datetime.now().strftime("%Y%m%d")}.pdf" class="action-btn btn-map" style="text-decoration:none; text-align:center;">📥 Download PDF</a>'
                                st.markdown(href, unsafe_allow_html=True)
        
        # Site Cards
        st.markdown("---")
        records = search_results_df.to_dict(orient="records")
        for row in records:
            html = create_site_card_html(row, st.session_state.search_term)
            st.markdown(html, unsafe_allow_html=True)
        
        # Export
        col1, col2 = st.columns(2)
        with col1:
            csv = search_results_df.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ CSV Filtered", data=csv, file_name=f"sites_{datetime.now().strftime('%Y%m%d')}.csv", use_container_width=True)
        with col2:
            full_csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ CSV All", data=full_csv, file_name=f"all_sites_{datetime.now().strftime('%Y%m%d')}.csv", use_container_width=True)
    
    else:
        # Welcome Screen
        # Count FO Onsite and Hub availability
        fo_count = 0
        hub_count = 0
        contact_count = 0
        for _, row in df.iterrows():
            row_dict = row.to_dict()
            if get_column_value(row_dict, ['NEW ENGINEER_ANM1', 'NEW ENGINEER_ANM1', 'NEW_ENGINEER_ANM1']):
                fo_count += 1
            if get_column_value(row_dict, ['NEW ASSIGN_HUB', 'NEW ASSIGN HUB', 'NEW_ASSIGN_HUB']):
                hub_count += 1
            if get_column_value(row_dict, ['CONTACT NUMBER', 'CONTACT_NUMBER', 'CONTACT NO']):
                contact_count += 1
        
        stats = {
            'total': len(df),
            'regions': df['REGION'].nunique() if 'REGION' in df.columns else 0,
            'coords': df['LATITUDE'].notna().sum() if 'LATITUDE' in df.columns else 0,
            'contacts': contact_count,
            'fo_onsite': fo_count,
            'globe_hub': hub_count,
        }
        
        st.markdown("""
        <div class="welcome-screen">
            <div class="welcome-icon">📍</div>
            <div class="welcome-title">Welcome to GPS Extractor</div>
            <div class="welcome-subtitle">
                Search for sites using PLAID or Site Name.<br>
                Search multiple sites with commas.
            </div>
            <div class="welcome-hint">
                💡 Example: <code>Min97, SITE001, PLAID002</code>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="stats-grid">
            <div class="stat-card"><span class="stat-number">{stats['total']}</span><span class="stat-label">Available Sites</span></div>
            <div class="stat-card"><span class="stat-number">{stats['regions']}</span><span class="stat-label">Regions</span></div>
            <div class="stat-card"><span class="stat-number">{stats['fo_onsite']}</span><span class="stat-label">👤 With FO Onsite</span></div>
            <div class="stat-card"><span class="stat-number">{stats['globe_hub']}</span><span class="stat-label">🌐 With Globe Hub</span></div>
        </div>
        """, unsafe_allow_html=True)
    
    bottom_nav()

# ------------------------------
# ROUTING
# ------------------------------
query_params = st.query_params
if 'page' in query_params and query_params['page'] == 'about':
    st.session_state.page = 'about'
else:
    st.session_state.page = 'main'

if st.session_state.page == 'about':
    show_about()
else:
    show_main()
