import streamlit as st
import sys
from pathlib import Path

# Add utils to path
sys.path.append(str(Path(__file__).parent))

from utils.data_loader import load_data, get_data_stats
from utils.helpers import safe_str, create_card_html
import pandas as pd

# ------------------------------
# PAGE CONFIG
# ------------------------------
st.set_page_config(
    page_title="GPS Extractor • Globe FO",
    page_icon="📍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------
# LOAD CUSTOM CSS
# ------------------------------
def load_css():
    css_file = Path(__file__).parent / "styles" / "custom.css"
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# ------------------------------
# HEADER
# ------------------------------
st.markdown("""
    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
        <span style="font-size: 2rem;">📍</span>
        <h1 style="display: inline-block; margin: 0; font-weight: 600;">GPS Extractor</h1>
        <span style="background: #eef2ff; color: #4f46e5; padding: 0.2rem 1rem; border-radius: 40px; font-size: 0.8rem; font-weight: 500; margin-left: 0.5rem;">Globe FO Engr</span>
    </div>
    <p style="color: #4b5563; margin-top: -0.2rem; font-size: 1rem;">
        📊 Accessing <strong>Globe FO Engr Contact_Vendor.xlsx</strong> from system · Click on any map button to navigate in Google Maps · Click to call FO directly.
    </p>
""", unsafe_allow_html=True)

# ------------------------------
# LOAD DATA
# ------------------------------
df = load_data()

if df is not None and not df.empty:
    # ------------------------------
    # STATISTICS
    # ------------------------------
    stats = get_data_stats(df)
    st.markdown(f"""
    <div class="stats-container">
        <div class="stat-item">
            <span class="stat-number">{stats['total_sites']}</span>
            <span class="stat-label">Total Sites</span>
        </div>
        <div class="stat-item">
            <span class="stat-number">{stats['total_regions']}</span>
            <span class="stat-label">Regions</span>
        </div>
        <div class="stat-item">
            <span class="stat-number">{stats['with_coords']}</span>
            <span class="stat-label">With Coordinates</span>
        </div>
        <div class="stat-item">
            <span class="stat-number">{stats['with_contact']}</span>
            <span class="stat-label">With Contact</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ------------------------------
    # FILTERS
    # ------------------------------
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        if 'REGION' in df.columns:
            regions = ['All'] + sorted(df['REGION'].dropna().unique().tolist())
            selected_region = st.selectbox('Filter by Region', regions)
    
    with col2:
        if 'TOWERCO' in df.columns:
            towercos = ['All'] + sorted(df['TOWERCO'].dropna().unique().tolist())
            selected_towerco = st.selectbox('Filter by TowerCo', towercos)
    
    with col3:
        show_with_coords = st.checkbox('Only with coords', value=False)
    
    # Apply filters
    filtered_df = df.copy()
    if 'REGION' in df.columns and selected_region != 'All':
        filtered_df = filtered_df[filtered_df['REGION'] == selected_region]
    if 'TOWERCO' in df.columns and selected_towerco != 'All':
        filtered_df = filtered_df[filtered_df['TOWERCO'] == selected_towerco]
    if show_with_coords:
        filtered_df = filtered_df[filtered_df['LATITUDE'].notna() & filtered_df['LONGITUDE'].notna()]

    # ------------------------------
    # DISPLAY CARDS
    # ------------------------------
    st.markdown("---")
    st.subheader(f"📍 Site Records ({len(filtered_df)} shown)")
    
    if len(filtered_df) == 0:
        st.info("No records match the selected filters.")
    else:
        records = filtered_df.to_dict(orient="records")
        
        for row in records:
            html = create_card_html(row)
            st.markdown(html, unsafe_allow_html=True)

        # ------------------------------
        # DATA TABLE
        # ------------------------------
        with st.expander("📊 View raw data table", expanded=False):
            st.dataframe(filtered_df, use_container_width=True, height=400)

        # ------------------------------
        # EXPORT OPTIONS
        # ------------------------------
        col1, col2 = st.columns(2)
        
        with col1:
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⬇️ Download Filtered Data as CSV",
                data=csv,
                file_name="globe_fo_extract_filtered.csv",
                mime="text/csv",
                use_container_width=True,
            )
        
        with col2:
            full_csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⬇️ Download All Data as CSV",
                data=full_csv,
                file_name="globe_fo_extract_all.csv",
                mime="text/csv",
                use_container_width=True,
            )

# ------------------------------
# FOOTER
# ------------------------------
st.markdown("""
    <hr style="margin-top: 2rem; opacity:0.3;">
    <div style="text-align: center; color: #9ca3af; font-size: 0.8rem; padding: 0.5rem;">
        GPS Extractor · Globe FO Engr Contact · Data loaded from system
    </div>
""", unsafe_allow_html=True)
