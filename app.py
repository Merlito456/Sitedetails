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
# DARK THEME CUSTOM CSS - MOBILE APP + WEB APP
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
        --shadow-color: rgba(0, 0, 0, 0.5);
        --highlight-yellow: #fbbf24;
        --safe-top: env(safe-area-inset-top, 0px);
        --safe-bottom: env(safe-area-inset-bottom, 0px);
    }

    /* ========================================
       GLOBAL RESET & BASE
       ======================================== */
    * {
        box-sizing: border-box;
        -webkit-tap-highlight-color: transparent;
    }

    .main .block-container {
        padding: 0.5rem 0.8rem 5rem 0.8rem;
        background: var(--bg-primary);
        max-width: 100% !important;
    }

    .stApp {
        background: var(--bg-primary);
    }

    /* Hide Streamlit branding */
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

    .app-logo-icon {
        font-size: 1.5rem;
    }

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

    .site-card:active {
        transform: scale(0.98);
    }

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

    .action-btn:active {
        transform: scale(0.95);
    }

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

    .welcome-icon {
        font-size: 3.5rem;
        margin-bottom: 0.8rem;
    }

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

    .nav-item .nav-icon {
        font-size: 1.2rem;
    }

    .nav-item.active {
        color: var(--accent-blue);
    }

    .nav-item:active {
        transform: scale(0.9);
    }

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
       EMPTY STATE
       ======================================== */
    .empty-state {
        text-align: center;
        padding: 2rem 1rem;
        color: var(--text-muted);
    }

    .empty-state .empty-icon {
        font-size: 3rem;
        margin-bottom: 0.5rem;
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

        .app-logo-text {
            font-size: 1.3rem;
        }

        .stats-grid {
            grid-template-columns: repeat(4, 1fr);
            gap: 1rem;
        }

        .stat-number {
            font-size: 1.8rem;
        }

        .stat-card {
            padding: 1.2rem;
        }

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

        .site-name {
            font-size: 1.2rem;
        }

        .site-details {
            grid-template-columns: repeat(3, 1fr);
        }

        .site-actions {
            gap: 0.8rem;
        }

        .action-btn {
            flex: 0 1 auto;
            min-width: 140px;
            padding: 0.6rem 1.2rem;
            font-size: 0.85rem;
        }

        .action-btn:hover {
            transform: translateY(-2px);
        }

        .btn-map:hover {
            box-shadow: 0 4px 15px rgba(79, 140, 247, 0.3);
        }

        .btn-call:hover {
            box-shadow: 0 4px 15px rgba(52, 211, 153, 0.3);
        }

        .welcome-screen {
            padding: 4rem 2rem;
        }

        .welcome-icon {
            font-size: 5rem;
        }
        .welcome-title {
            font-size: 2rem;
        }
        .welcome-subtitle {
            font-size: 1.1rem;
        }

        .bottom-nav {
            display: none;
        }

        .search-section {
            padding: 1.5rem;
        }

        .search-input-wrapper input {
            padding: 0.8rem 0.8rem 0.8rem 3rem;
            font-size: 1rem;
        }

        .search-btn, .clear-btn {
            padding: 0.8rem 1.5rem;
            font-size: 0.95rem;
            min-width: 80px;
        }
    }

    /* ========================================
       TABLET
       ======================================== */
    @media (min-width: 481px) and (max-width: 768px) {
        .stats-grid {
            grid-template-columns: repeat(4, 1fr);
        }

        .site-details {
            grid-template-columns: repeat(2, 1fr);
        }

        .bottom-nav .nav-item {
            font-size: 0.6rem;
        }
        .bottom-nav .nav-item .nav-icon {
            font-size: 1.3rem;
        }
    }

    /* ========================================
       SMALL PHONE
       ======================================== */
    @media (max-width: 380px) {
        .app-logo-text {
            font-size: 0.9rem;
        }
        .app-logo-badge {
            font-size: 0.5rem;
            padding: 0.1rem 0.4rem;
        }
        .nav-btn {
            font-size: 0.65rem;
            padding: 0.3rem 0.6rem;
        }
        .search-btn, .clear-btn {
            font-size: 0.7rem;
            padding: 0.6rem 0.7rem;
            min-width: 50px;
        }
        .site-name {
            font-size: 0.9rem;
        }
        .site-details {
            grid-template-columns: 1fr 1fr;
        }
        .action-btn {
            min-width: 70px;
            font-size: 0.65rem;
            padding: 0.4rem 0.6rem;
        }
    }
    </style>
""", unsafe_allow_html=True)

# ------------------------------
# SESSION STATE INIT
# ------------------------------
if 'page' not in st.session_state:
    st.session_state.page = 'main'
if 'df' not in st.session_state:
    st.session_state.df = None
if 'search_term' not in st.session_state:
    st.session_state.search_term = ''
if 'has_searched' not in st.session_state:
    st.session_state.has_searched = False
if 'search_results' not in st.session_state:
    st.session_state.search_results = None

# ------------------------------
# FUNCTIONS
# ------------------------------
@st.cache_data
def load_excel_data():
    """Load data from Excel file (database.xlsx)"""
    try:
        possible_paths = [
            "data/database.xlsx",
            "database.xlsx",
            "./data/database.xlsx",
            "./database.xlsx",
            Path(__file__).parent / "data" / "database.xlsx",
            Path(__file__).parent / "database.xlsx",
        ]
        
        file_path = None
        for path in possible_paths:
            if os.path.exists(path):
                file_path = path
                break
        
        if file_path is None:
            st.error("""
            ❌ **Database file not found!**
            
            Please place `database.xlsx` in one of these locations:
            - `data/database.xlsx`
            - `database.xlsx` (root folder)
            """)
            return None
        
        df = pd.read_excel(file_path, engine='openpyxl')
        df.columns = df.columns.str.strip().str.upper()
        
        if df.empty:
            st.error("❌ The database file is empty!")
            return None
        
        return df
        
    except Exception as e:
        st.error(f"❌ Error loading database: {str(e)}")
        return None

def safe_str(val):
    if pd.isna(val):
        return ""
    return str(val)

def highlight_text(text, search_term):
    if not search_term or not text:
        return text
    try:
        pattern = re.compile(re.escape(search_term), re.IGNORECASE)
        return pattern.sub(lambda m: f'<span class="search-highlight">{m.group()}</span>', str(text))
    except:
        return text

def perform_intelligent_search(df, search_input):
    """
    Perform intelligent search on PLAID and SITE columns.
    - First tries exact match (case-insensitive)
    - Then tries contains match (for partial searches)
    Supports multiple terms separated by commas.
    """
    if not search_input or search_input.strip() == '':
        return pd.DataFrame()
    
    # Split by comma and clean each term
    search_terms = [term.strip() for term in search_input.split(',') if term.strip()]
    
    if not search_terms:
        return pd.DataFrame()
    
    # Create mask for each term
    final_mask = pd.Series([False] * len(df))
    matched_terms = []
    
    for term in search_terms:
        term_mask = pd.Series([False] * len(df))
        term_found = False
        
        # 1. Try EXACT match first (case-insensitive, trimmed)
        if 'PLAID' in df.columns:
            exact_mask_plaid = df['PLAID'].astype(str).str.strip().str.upper() == term.upper()
            term_mask |= exact_mask_plaid
            if exact_mask_plaid.any():
                term_found = True
        
        if 'SITE' in df.columns:
            exact_mask_site = df['SITE'].astype(str).str.strip().str.upper() == term.upper()
            term_mask |= exact_mask_site
            if exact_mask_site.any():
                term_found = True
        
        # 2. If no exact match, try CONTAINS match (for partial searching)
        if not term_found:
            if 'PLAID' in df.columns:
                contains_mask_plaid = df['PLAID'].astype(str).str.contains(term, case=False, na=False)
                term_mask |= contains_mask_plaid
            
            if 'SITE' in df.columns:
                contains_mask_site = df['SITE'].astype(str).str.contains(term, case=False, na=False)
                term_mask |= contains_mask_site
        
        final_mask |= term_mask
        matched_terms.append(term)
    
    return df[final_mask].copy()

def create_site_card_html(row, search_term=""):
    """Create HTML for a site card optimized for mobile"""
    plaid = safe_str(row.get("PLAID", ""))
    site = safe_str(row.get("SITE", ""))
    region = safe_str(row.get("REGION", ""))
    province = safe_str(row.get("PROVINCE", ""))
    municipality = safe_str(row.get("MUNICIPALITY", ""))
    barangay = safe_str(row.get("BARANGAY", ""))
    territory = safe_str(row.get("TERRITORY", ""))
    lat = safe_str(row.get("LATITUDE", ""))
    lon = safe_str(row.get("LONGITUDE", ""))
    site_add = safe_str(row.get("SITE_ADD", ""))
    assigned_hub = safe_str(row.get("ASSIGNED_HUB", ""))
    towerco = safe_str(row.get("TOWERCO", ""))
    new_assign_hub = safe_str(row.get("NEW ASSIGN HUB", ""))
    fo_onsite = safe_str(row.get("NEW ENGINEER_ANM1", ""))
    contact = safe_str(row.get("CONTACT NUMBER", ""))
    
    # Highlight
    site_display = highlight_text(site, search_term)
    plaid_display = highlight_text(plaid, search_term)
    
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
    if contact:
        clean_contact = ''.join(ch for ch in contact if ch.isdigit() or ch == '+')
        if clean_contact:
            call_button = f'<a href="tel:{clean_contact}" class="action-btn btn-call">📞 Call FO</a>'
        else:
            call_button = f'<span class="action-btn btn-disabled">📞 {contact}</span>'
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
                <span class="detail-label">FO Onsite</span>
                <span class="detail-value">{fo_onsite}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Assigned Hub</span>
                <span class="detail-value">{assigned_hub}</span>
            </div>
            <div class="detail-item">
                <span class="detail-label">New Assign Hub</span>
                <span class="detail-value">{new_assign_hub}</span>
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
    """Create interactive map with dark theme"""
    map_df = df[df['LATITUDE'].notna() & df['LONGITUDE'].notna()].copy()
    
    if map_df.empty:
        return None
    
    fig = go.Figure()
    
    fig.add_trace(go.Scattermapbox(
        lat=map_df['LATITUDE'],
        lon=map_df['LONGITUDE'],
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=10,
            color='#4f8cf7',
            opacity=0.6,
        ),
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
            marker=go.scattermapbox.Marker(
                size=15,
                color='#ef4444',
                opacity=0.9,
            ),
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
    """Create a PDF report with selected sites"""
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
        table_data = [['PLAID', 'Site', 'Region', 'FO Onsite', 'Contact', 'Latitude', 'Longitude']]
        
        for idx, row in selected_df.iterrows():
            lat_val = safe_str(row.get('LATITUDE', ''))
            lon_val = safe_str(row.get('LONGITUDE', ''))
            try:
                if lat_val and lon_val:
                    lat_val = f"{float(lat_val):.6f}"
                    lon_val = f"{float(lon_val):.6f}"
            except:
                pass
                
            table_data.append([
                safe_str(row.get('PLAID', '')),
                safe_str(row.get('SITE', '')),
                safe_str(row.get('REGION', '')),
                safe_str(row.get('NEW ENGINEER_ANM1', '')),
                safe_str(row.get('CONTACT NUMBER', '')),
                lat_val,
                lon_val
            ])
        
        table = Table(table_data, colWidths=[0.8*inch, 1.2*inch, 1*inch, 1.2*inch, 1.2*inch, 1*inch, 1*inch])
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
# BOTTOM NAVIGATION (Mobile)
# ------------------------------
def bottom_nav():
    current_page = st.session_state.page
    home_active = 'active' if current_page == 'main' else ''
    about_active = 'active' if current_page == 'about' else ''
    
    st.markdown(f"""
    <div class="bottom-nav">
        <button class="nav-item {home_active}" onclick="location.href='/'">
            <span class="nav-icon">🏠</span>
            Home
        </button>
        <button class="nav-item {about_active}" onclick="location.href='?page=about'">
            <span class="nav-icon">ℹ️</span>
            About
        </button>
    </div>
    """, unsafe_allow_html=True)

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
        df = load_excel_data()
        if df is not None:
            st.session_state.df = df
    else:
        df = st.session_state.df
    
    if df is None or df.empty:
        st.warning("⚠️ No data available. Please check the database file.")
        bottom_nav()
        return
    
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
    
    # Search hint
    st.markdown("""
    <div class="search-hint">
        🔍 <strong>Smart Search</strong> · Exact matches first, then partial · Separate multiple with commas: 
        <code>Min97, SITE001, PLAID002</code>
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
    
    # Display Results or Welcome
    if st.session_state.has_searched:
        filtered_df = st.session_state.search_results
        
        if filtered_df is None or len(filtered_df) == 0:
            # Show which terms were searched
            terms = [term.strip() for term in search_term.split(',') if term.strip()]
            terms_display = ', '.join([f'"{t}"' for t in terms])
            
            st.markdown(f"""
            <div class="welcome-screen">
                <div class="welcome-icon">🔍</div>
                <div class="welcome-title">No Results Found</div>
                <div class="welcome-subtitle">
                    No sites found matching: {terms_display}
                </div>
                <div class="welcome-hint">
                    💡 Try checking the spelling or use partial matching
                </div>
            </div>
            """, unsafe_allow_html=True)
            bottom_nav()
            return
        
        # Show what was searched
        terms = [term.strip() for term in search_term.split(',') if term.strip()]
        terms_display = ', '.join([f'"{t}"' for t in terms])
        st.markdown(f"**Found {len(filtered_df)} site(s)** matching: {terms_display}")
        
        # Stats
        stats = {
            'total': len(filtered_df),
            'regions': filtered_df['REGION'].nunique() if 'REGION' in filtered_df.columns else 0,
            'coords': filtered_df['LATITUDE'].notna().sum() if 'LATITUDE' in filtered_df.columns else 0,
            'contacts': filtered_df['CONTACT NUMBER'].notna().sum() if 'CONTACT NUMBER' in filtered_df.columns else 0,
        }
        
        st.markdown(f"""
        <div class="stats-grid">
            <div class="stat-card">
                <span class="stat-number">{stats['total']}</span>
                <span class="stat-label">Results</span>
            </div>
            <div class="stat-card">
                <span class="stat-number">{stats['regions']}</span>
                <span class="stat-label">Regions</span>
            </div>
            <div class="stat-card">
                <span class="stat-number">{stats['coords']}</span>
                <span class="stat-label">With Coords</span>
            </div>
            <div class="stat-card">
                <span class="stat-number">{stats['contacts']}</span>
                <span class="stat-label">With Contact</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Filters
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            if 'REGION' in filtered_df.columns:
                regions = ['All'] + sorted(filtered_df['REGION'].dropna().unique().tolist())
                selected_region = st.selectbox('Region', regions)
                if selected_region != 'All':
                    filtered_df = filtered_df[filtered_df['REGION'] == selected_region]
        with col2:
            if 'TOWERCO' in filtered_df.columns:
                towercos = ['All'] + sorted(filtered_df['TOWERCO'].dropna().unique().tolist())
                selected_towerco = st.selectbox('TowerCo', towercos)
                if selected_towerco != 'All':
                    filtered_df = filtered_df[filtered_df['TOWERCO'] == selected_towerco]
        with col3:
            show_map = st.checkbox('🗺️ Map')
        
        # Map View
        if show_map and len(filtered_df) > 0:
            map_indices = filtered_df[filtered_df['LATITUDE'].notna() & filtered_df['LONGITUDE'].notna()].index.tolist()
            if map_indices:
                selected_map = st.multiselect(
                    "Highlight sites",
                    options=map_indices,
                    format_func=lambda x: f"{filtered_df.loc[x, 'SITE']}"
                )
                fig = create_map(filtered_df, selected_map)
                if fig:
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                    
                    if selected_map:
                        if st.button("📄 Export to PDF"):
                            pdf_data = create_pdf_export(filtered_df, selected_map)
                            if pdf_data:
                                b64 = base64.b64encode(pdf_data).decode()
                                href = f'<a href="data:application/pdf;base64,{b64}" download="site_report_{datetime.now().strftime("%Y%m%d")}.pdf" class="action-btn btn-map" style="text-decoration:none; text-align:center;">📥 Download PDF</a>'
                                st.markdown(href, unsafe_allow_html=True)
        
        # Site Cards
        st.markdown("---")
        records = filtered_df.to_dict(orient="records")
        for row in records:
            html = create_site_card_html(row, st.session_state.search_term)
            st.markdown(html, unsafe_allow_html=True)
        
        # Export
        col1, col2 = st.columns(2)
        with col1:
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ CSV Filtered", data=csv, file_name=f"sites_{datetime.now().strftime('%Y%m%d')}.csv", use_container_width=True)
        with col2:
            full_csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ CSV All", data=full_csv, file_name=f"all_sites_{datetime.now().strftime('%Y%m%d')}.csv", use_container_width=True)
    
    else:
        # Welcome Screen
        stats = {
            'total': len(df),
            'regions': df['REGION'].nunique() if 'REGION' in df.columns else 0,
            'coords': df['LATITUDE'].notna().sum() if 'LATITUDE' in df.columns else 0,
            'contacts': df['CONTACT NUMBER'].notna().sum() if 'CONTACT NUMBER' in df.columns else 0,
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
            <div class="stat-card">
                <span class="stat-number">{stats['total']}</span>
                <span class="stat-label">Total Sites</span>
            </div>
            <div class="stat-card">
                <span class="stat-number">{stats['regions']}</span>
                <span class="stat-label">Regions</span>
            </div>
            <div class="stat-card">
                <span class="stat-number">{stats['coords']}</span>
                <span class="stat-label">With Coords</span>
            </div>
            <div class="stat-card">
                <span class="stat-number">{stats['contacts']}</span>
                <span class="stat-label">With Contact</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    bottom_nav()

# ------------------------------
# ROUTING
# ------------------------------
# Handle URL query params for navigation
query_params = st.query_params
if 'page' in query_params and query_params['page'] == 'about':
    st.session_state.page = 'about'
elif st.session_state.page == 'about' and 'page' not in query_params:
    st.session_state.page = 'main'

if st.session_state.page == 'about':
    show_about()
else:
    show_main()
