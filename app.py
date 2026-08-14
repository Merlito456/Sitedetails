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
    initial_sidebar_state="expanded",
)

# ------------------------------
# DARK THEME CUSTOM CSS
# ------------------------------
st.markdown("""
    <style>
    /* Dark theme variables */
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
    }

    /* Main container */
    .main .block-container {
        padding: 1rem 1.5rem;
        background: var(--bg-primary);
    }
    
    /* Override Streamlit default background */
    .stApp {
        background: var(--bg-primary);
    }
    
    /* Card style */
    .site-card {
        background: var(--bg-card);
        border-radius: 16px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1.2rem;
        border: 1px solid var(--border-color);
        transition: all 0.3s ease;
        box-shadow: 0 4px 20px var(--shadow-color);
        animation: fadeIn 0.5s ease-in;
    }
    .site-card:hover {
        background: var(--bg-card-hover);
        border-color: var(--accent-purple);
        box-shadow: 0 8px 30px var(--shadow-color);
        transform: translateY(-2px);
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .site-title {
        font-weight: 600;
        font-size: 1.2rem;
        color: var(--text-primary);
        margin-bottom: 0.25rem;
    }
    .site-sub {
        font-size: 0.9rem;
        color: var(--text-secondary);
    }
    
    .badge {
        background: rgba(79, 140, 247, 0.15);
        color: var(--accent-blue);
        padding: 0.2rem 0.8rem;
        border-radius: 40px;
        font-size: 0.75rem;
        font-weight: 500;
        display: inline-block;
        margin-right: 0.4rem;
        border: 1px solid rgba(79, 140, 247, 0.2);
    }
    .badge-plaid {
        background: rgba(139, 92, 246, 0.2);
        color: var(--accent-purple);
        padding: 0.2rem 0.8rem;
        border-radius: 40px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
        margin-right: 0.4rem;
        border: 1px solid rgba(139, 92, 246, 0.2);
    }
    .badge-territory {
        background: rgba(52, 211, 153, 0.15);
        color: var(--accent-green);
        padding: 0.2rem 0.8rem;
        border-radius: 40px;
        font-size: 0.75rem;
        font-weight: 500;
        display: inline-block;
        margin-right: 0.4rem;
        border: 1px solid rgba(52, 211, 153, 0.2);
    }
    .badge-towerco {
        background: rgba(251, 191, 36, 0.15);
        color: var(--highlight-yellow);
        padding: 0.2rem 0.8rem;
        border-radius: 40px;
        font-size: 0.75rem;
        font-weight: 500;
        display: inline-block;
        margin-right: 0.4rem;
        border: 1px solid rgba(251, 191, 36, 0.2);
    }
    
    .btn-group {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 0.6rem;
    }
    .btn-map {
        background: var(--accent-blue);
        color: white !important;
        padding: 0.4rem 1.2rem;
        border-radius: 40px;
        font-size: 0.85rem;
        font-weight: 500;
        text-decoration: none;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        transition: all 0.2s;
        border: none;
        cursor: pointer;
    }
    .btn-map:hover {
        background: var(--accent-blue-hover);
        color: white !important;
        transform: scale(1.02);
        box-shadow: 0 4px 15px rgba(79, 140, 247, 0.3);
    }
    .btn-call {
        background: var(--accent-green);
        color: #0a0a0f !important;
        padding: 0.4rem 1.2rem;
        border-radius: 40px;
        font-size: 0.85rem;
        font-weight: 500;
        text-decoration: none;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        transition: all 0.2s;
        border: none;
        cursor: pointer;
    }
    .btn-call:hover {
        background: var(--accent-green-hover);
        color: #0a0a0f !important;
        transform: scale(1.02);
        box-shadow: 0 4px 15px rgba(52, 211, 153, 0.3);
    }
    
    .btn-back {
        background: var(--bg-card);
        color: var(--text-primary) !important;
        padding: 0.5rem 1.5rem;
        border-radius: 40px;
        font-size: 0.9rem;
        font-weight: 500;
        text-decoration: none;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        transition: all 0.2s;
        border: 1px solid var(--border-color);
        cursor: pointer;
    }
    .btn-back:hover {
        background: var(--bg-card-hover);
        border-color: var(--accent-blue);
        transform: translateX(-3px);
    }
    
    .detail-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 0.5rem 1.5rem;
        margin-top: 0.5rem;
        font-size: 0.9rem;
    }
    .detail-item {
        display: flex;
        flex-wrap: wrap;
        align-items: baseline;
        gap: 0.2rem;
    }
    .detail-label {
        color: var(--text-muted);
        font-weight: 400;
        min-width: 80px;
    }
    .detail-value {
        font-weight: 500;
        color: var(--text-primary);
    }
    
    .stats-container {
        background: var(--bg-secondary);
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin: 1rem 0;
        border: 1px solid var(--border-color);
        display: flex;
        flex-wrap: wrap;
        gap: 2rem;
    }
    .stat-item {
        display: flex;
        align-items: baseline;
        gap: 0.5rem;
    }
    .stat-number {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--text-primary);
    }
    .stat-label {
        color: var(--text-secondary);
        font-size: 0.9rem;
    }
    
    .search-highlight {
        background: var(--highlight-yellow);
        color: #0a0a0f;
        padding: 0.1rem 0.3rem;
        border-radius: 4px;
        font-weight: 600;
    }
    
    /* Search container */
    .search-container {
        background: var(--bg-secondary);
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid var(--border-color);
        margin: 1rem 0;
    }
    
    /* Welcome message */
    .welcome-container {
        text-align: center;
        padding: 3rem 1rem;
        background: var(--bg-secondary);
        border-radius: 16px;
        border: 1px solid var(--border-color);
        margin: 2rem 0;
    }
    .welcome-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
    }
    .welcome-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 0.5rem;
    }
    .welcome-subtitle {
        color: var(--text-secondary);
        font-size: 1.1rem;
        max-width: 600px;
        margin: 0 auto;
        line-height: 1.6;
    }
    .welcome-hint {
        color: var(--text-muted);
        font-size: 0.9rem;
        margin-top: 1.5rem;
        padding: 1rem;
        background: var(--bg-card);
        border-radius: 8px;
        border: 1px dashed var(--border-color);
        display: inline-block;
    }
    
    /* Navigation buttons */
    .nav-container {
        display: flex;
        justify-content: flex-end;
        gap: 0.5rem;
        margin-bottom: 1rem;
    }
    
    /* Headers */
    h1, h2, h3, h4 {
        color: var(--text-primary) !important;
    }
    
    /* Input fields */
    .stTextInput > div > div > input {
        background: var(--bg-input) !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-primary) !important;
        border-radius: 8px !important;
        font-size: 1rem !important;
        padding: 0.75rem 1rem !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: var(--accent-blue) !important;
        box-shadow: 0 0 0 3px rgba(79, 140, 247, 0.1) !important;
    }
    .stTextInput > div > div > input::placeholder {
        color: var(--text-muted) !important;
    }
    
    /* Select boxes */
    .stSelectbox > div > div {
        background: var(--bg-input) !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-primary) !important;
    }
    
    /* Checkbox */
    .stCheckbox > label {
        color: var(--text-secondary) !important;
    }
    
    /* Dataframe */
    .stDataFrame {
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        overflow: hidden !important;
    }
    .stDataFrame > div {
        background: var(--bg-secondary) !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-primary) !important;
        border-radius: 8px !important;
        transition: all 0.2s !important;
        padding: 0.5rem 1rem !important;
        font-weight: 500 !important;
    }
    .stButton > button:hover {
        background: var(--bg-card-hover) !important;
        border-color: var(--accent-blue) !important;
        color: var(--text-primary) !important;
        transform: translateY(-1px);
    }
    
    /* Download buttons */
    .stDownloadButton > button {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-primary) !important;
        border-radius: 8px !important;
        transition: all 0.2s !important;
    }
    .stDownloadButton > button:hover {
        background: var(--bg-card-hover) !important;
        border-color: var(--accent-blue) !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: var(--bg-secondary) !important;
        border-color: var(--border-color) !important;
        color: var(--text-primary) !important;
    }
    .streamlit-expanderContent {
        background: var(--bg-secondary) !important;
        border-color: var(--border-color) !important;
    }
    
    /* Info/Warning/Success messages */
    .stAlert {
        background: var(--bg-card) !important;
        border-color: var(--border-color) !important;
        color: var(--text-primary) !important;
    }
    
    /* Plotly charts */
    .js-plotly-plot .plotly .main-svg {
        background: var(--bg-secondary) !important;
    }
    
    /* Footer */
    hr {
        border-color: var(--border-color) !important;
    }
    
    /* About page specific */
    .about-back-container {
        margin-bottom: 1.5rem;
    }
    
    /* mobile adjustments */
    @media (max-width: 640px) {
        .site-card {
            padding: 1rem;
        }
        .btn-group {
            flex-direction: column;
            align-items: stretch;
        }
        .btn-map, .btn-call {
            justify-content: center;
        }
        .detail-grid {
            grid-template-columns: 1fr;
        }
        .stats-container {
            flex-direction: column;
            gap: 0.5rem;
        }
        .welcome-title {
            font-size: 1.4rem;
        }
        .nav-container {
            flex-direction: column;
            align-items: stretch;
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
        # Try multiple possible locations
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
        
        # Read the Excel file
        df = pd.read_excel(file_path, engine='openpyxl')
        
        # Clean column names
        df.columns = df.columns.str.strip().str.upper()
        
        # Check if we have data
        if df.empty:
            st.error("❌ The database file is empty!")
            return None
        
        return df
        
    except Exception as e:
        st.error(f"❌ Error loading database: {str(e)}")
        return None

def safe_str(val):
    """Convert value to string safely"""
    if pd.isna(val):
        return ""
    return str(val)

def highlight_text(text, search_term):
    """Highlight search term in text"""
    if not search_term or not text:
        return text
    try:
        pattern = re.compile(re.escape(search_term), re.IGNORECASE)
        return pattern.sub(lambda m: f'<span class="search-highlight">{m.group()}</span>', str(text))
    except:
        return text

def create_site_card(row, search_term=""):
    """Create HTML for a site card with search highlighting"""
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
    
    # Highlight search terms
    site_display = highlight_text(site, search_term)
    plaid_display = highlight_text(plaid, search_term)
    region_display = highlight_text(region, search_term)
    province_display = highlight_text(province, search_term)
    municipality_display = highlight_text(municipality, search_term)
    barangay_display = highlight_text(barangay, search_term)
    site_add_display = highlight_text(site_add, search_term)
    
    html = f"""
    <div class="site-card">
        <div style="display: flex; flex-wrap: wrap; justify-content: space-between; align-items: flex-start;">
            <div>
                <div class="site-title">{site_display} <span class="badge-plaid">{plaid_display}</span></div>
                <div class="site-sub">{region_display} · {province_display} · {municipality_display} · {barangay_display}</div>
            </div>
            <div style="display: flex; gap: 0.4rem; flex-wrap: wrap; margin-top: 0.2rem;">
                <span class="badge-territory">{territory}</span>
                <span class="badge-towerco">{towerco}</span>
            </div>
        </div>
        <div class="detail-grid">
            <div class="detail-item"><span class="detail-label">Address</span><span class="detail-value">{site_add_display}</span></div>
            <div class="detail-item"><span class="detail-label">Assigned Hub</span><span class="detail-value">{assigned_hub}</span></div>
            <div class="detail-item"><span class="detail-label">New Assign Hub</span><span class="detail-value">{new_assign_hub}</span></div>
            <div class="detail-item"><span class="detail-label">FO Onsite</span><span class="detail-value">{fo_onsite}</span></div>
            <div class="detail-item"><span class="detail-label">Lat/Lon</span><span class="detail-value">{lat}, {lon}</span></div>
        </div>
        <div class="btn-group">
    """
    
    # Map button
    if lat and lon:
        try:
            float(lat)
            float(lon)
            maps_url = f"https://www.google.com/maps?q={lat},{lon}"
            html += f'<a href="{maps_url}" target="_blank" class="btn-map"><span>🗺️</span> Navigate to Google Maps</a>'
        except:
            html += '<span style="background:#2a2a44; color:#6b6b85; padding:0.3rem 1rem; border-radius:40px; font-size:0.85rem;">⚠️ invalid coordinates</span>'
    else:
        html += '<span style="background:#2a2a44; color:#6b6b85; padding:0.3rem 1rem; border-radius:40px; font-size:0.85rem;">⚠️ no coordinates</span>'
    
    # Call button
    if contact:
        clean_contact = ''.join(ch for ch in contact if ch.isdigit() or ch == '+')
        if clean_contact:
            html += f'<a href="tel:{clean_contact}" class="btn-call"><span>📞</span> Call FO: {contact}</a>'
        else:
            html += f'<span style="background:#2a2a44; color:#6b6b85; padding:0.3rem 1rem; border-radius:40px; font-size:0.85rem;">📞 {contact}</span>'
    else:
        html += '<span style="background:#2a2a44; color:#6b6b85; padding:0.3rem 1rem; border-radius:40px; font-size:0.85rem;">📞 no contact</span>'
    
    html += "</div></div>"
    return html

def create_map(df, selected_indices=None):
    """Create interactive map with dark theme"""
    map_df = df[df['LATITUDE'].notna() & df['LONGITUDE'].notna()].copy()
    
    if map_df.empty:
        return None
    
    fig = go.Figure()
    
    # All sites
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
    
    # Selected sites
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
        
        # Add connecting lines between selected sites
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
    
    # Configure map layout with dark theme
    fig.update_layout(
        mapbox=dict(
            style='dark',
            center=dict(
                lat=map_df['LATITUDE'].mean() if not map_df.empty else 14.5995,
                lon=map_df['LONGITUDE'].mean() if not map_df.empty else 121.0139
            ),
            zoom=8
        ),
        height=500,
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
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.close()
        
        # Create PDF document
        doc = SimpleDocTemplate(
            temp_file.name,
            pagesize=landscape(letter),
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )
        
        # Prepare styles
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
        
        # Build content
        content = []
        
        # Title
        content.append(Paragraph("📍 GPS Extractor - Site Report", title_style))
        content.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", subtitle_style))
        content.append(Spacer(1, 20))
        
        # Statistics
        content.append(Paragraph(f"<b>Total Sites:</b> {len(selected_indices)}", styles['Normal']))
        content.append(Spacer(1, 10))
        
        # Table data
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
        
        # Create table
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
        
        # Build PDF
        doc.build(content)
        
        # Read the file
        with open(temp_file.name, 'rb') as f:
            pdf_data = f.read()
        
        # Clean up
        os.unlink(temp_file.name)
        
        return pdf_data
        
    except ImportError:
        st.error("PDF generation requires reportlab. Install with: pip install reportlab")
        return None
    except Exception as e:
        st.error(f"Error generating PDF: {str(e)}")
        return None

# ------------------------------
# NAVIGATION COMPONENT
# ------------------------------
def navigation_buttons():
    """Display navigation buttons in the top right"""
    col1, col2, col3 = st.columns([4, 1, 1])
    with col2:
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.page = 'main'
            st.session_state.has_searched = False
            st.session_state.search_results = None
            st.rerun()
    with col3:
        if st.button("ℹ️ About", use_container_width=True):
            st.session_state.page = 'about'
            st.rerun()

# ------------------------------
# ABOUT PAGE
# ------------------------------
def show_about():
    # Back button at top
    st.markdown('<div class="about-back-container">', unsafe_allow_html=True)
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("← Back", use_container_width=True):
            st.session_state.page = 'main'
            st.rerun()
    with col2:
        st.markdown("")  # Spacer
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0 2rem 0;">
        <h1 style="font-size: 2.5rem; font-weight: 700; color: #e8e8f0;">📍 GPS Extractor</h1>
        <p style="font-size: 1.2rem; color: #a0a0b8; margin-top: 0.5rem;">Globe FO Engineer Contact Management System</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Developer Info
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a1a2e 0%, #2a1a3e 100%); 
                border-radius: 16px; padding: 2rem; border: 1px solid #2a2a44; margin: 1rem 0;">
        <div style="display: flex; align-items: center; gap: 1rem; flex-wrap: wrap;">
            <div style="flex: 1;">
                <h2 style="color: #e8e8f0; margin: 0;">👨‍💻 Developer</h2>
                <h3 style="color: #a0a0b8; margin: 0.5rem 0;">Engr. John Carlo Rabanes, ECE</h3>
                <p style="margin: 0.3rem 0; color: #6b6b85;">📧 rabanes.johncarlo4@gmail.com</p>
                <p style="margin: 0.3rem 0; color: #6b6b85;">🏢 Nokia Shanghai Bell</p>
            </div>
            <div style="font-size: 4rem;">📡</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Mission & Vision
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div style="background: #14141e; border-radius: 12px; padding: 1.5rem; height: 100%; border: 1px solid #2a2a44;">
            <h3 style="color: #4f8cf7;">🎯 Mission</h3>
            <p style="color: #a0a0b8; line-height: 1.6;">
                To empower field operations engineers with seamless access to site information, 
                enabling efficient navigation and communication for faster response times and 
                improved network reliability across the Philippines.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: #14141e; border-radius: 12px; padding: 1.5rem; height: 100%; border: 1px solid #2a2a44;">
            <h3 style="color: #fbbf24;">👁️ Vision</h3>
            <p style="color: #a0a0b8; line-height: 1.6;">
                To be the leading digital tool for telecommunications field operations, 
                setting the standard for efficiency, accuracy, and user experience in 
                site management and engineer coordination.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Features Comparison
    st.markdown("---")
    st.subheader("⚡ Features & Comparison")
    
    comparison_data = {
        "Feature": [
            "📍 GPS Navigation",
            "📞 Click-to-Call",
            "🔍 Search by PLAID/Site",
            "📊 Data Visualization",
            "📱 Mobile Friendly",
            "🗺️ Map Visualization",
            "📄 PDF Export",
            "🔍 Smart Filtering",
            "⚡ Speed",
            "💰 Cost"
        ],
        "GPS Extractor": [
            "✅ One-click Google Maps",
            "✅ Direct contact dialing",
            "✅ Instant search results",
            "✅ Interactive charts",
            "✅ Fully responsive",
            "✅ Interactive maps",
            "✅ Multiple sites export",
            "✅ Multi-filter system",
            "🚀 Instant",
            "💵 Free (Open Source)"
        ],
        "Traditional Methods": [
            "❌ Manual copy-paste",
            "❌ Manual dialing",
            "❌ Manual CTRL+F search",
            "❌ Static spreadsheets",
            "❌ Desktop-only",
            "❌ No visualization",
            "❌ Manual screenshots",
            "❌ Limited filtering",
            "🐢 Slow",
            "💰 Expensive tools"
        ]
    }
    
    comparison_df = pd.DataFrame(comparison_data)
    st.dataframe(
        comparison_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Feature": st.column_config.TextColumn("Feature", width="small"),
            "GPS Extractor": st.column_config.TextColumn("GPS Extractor", width="medium"),
            "Traditional Methods": st.column_config.TextColumn("Traditional Methods", width="medium"),
        }
    )
    
    # Advantages & Disadvantages
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div style="background: rgba(52, 211, 153, 0.1); border-left: 4px solid #34d399; border-radius: 8px; padding: 1.5rem;">
            <h3 style="color: #34d399; margin-top: 0;">✅ Advantages</h3>
            <ul style="color: #a0a0b8; line-height: 2;">
                <li>🚀 Instant access to site data</li>
                <li>🗺️ Seamless Google Maps integration</li>
                <li>📞 Direct engineer contact</li>
                <li>🔍 Quick search by PLAID or Site Name</li>
                <li>📊 Visual data representation</li>
                <li>📱 Accessible anywhere, anytime</li>
                <li>💾 Built-in data export</li>
                <li>🔄 Real-time filtering</li>
                <li>💰 Zero licensing costs</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: rgba(239, 68, 68, 0.1); border-left: 4px solid #ef4444; border-radius: 8px; padding: 1.5rem;">
            <h3 style="color: #ef4444; margin-top: 0;">⚠️ Disadvantages</h3>
            <ul style="color: #a0a0b8; line-height: 2;">
                <li>🌐 Requires internet connection</li>
                <li>📊 Data format dependent</li>
                <li>🔧 Excel file management needed</li>
                <li>🖥️ Initial setup required</li>
                <li>📈 Performance on large datasets</li>
                <li>🔒 No built-in authentication</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.caption("© 2026 GPS Extractor | Developed for Globe Telecom Operations")
    
    # Back button at bottom
    st.markdown('<div style="text-align: center; margin-top: 2rem;">', unsafe_allow_html=True)
    if st.button("← Back to Home", use_container_width=False):
        st.session_state.page = 'main'
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------
# MAIN PAGE
# ------------------------------
def show_main():
    # Navigation
    navigation_buttons()
    
    # Title
    st.markdown("""
        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
            <span style="font-size: 2rem;">📍</span>
            <h1 style="display: inline-block; margin: 0; font-weight: 600; color: #e8e8f0;">GPS Extractor</h1>
            <span style="background: rgba(79, 140, 247, 0.2); color: #4f8cf7; padding: 0.2rem 1rem; border-radius: 40px; font-size: 0.8rem; font-weight: 500; margin-left: 0.5rem; border: 1px solid rgba(79, 140, 247, 0.2);">Globe FO Engr</span>
        </div>
        <p style="color: #a0a0b8; margin-top: -0.2rem; font-size: 1rem;">
            📊 Search <strong style="color: #e8e8f0;">database.xlsx</strong> · Click on any map button to navigate in Google Maps · Click to call FO directly.
        </p>
    """, unsafe_allow_html=True)
    
    # Load data (but don't display yet)
    if st.session_state.df is None:
        df = load_excel_data()
        if df is not None:
            st.session_state.df = df
    else:
        df = st.session_state.df
    
    if df is None or df.empty:
        st.warning("⚠️ No data available. Please check the database file.")
        return
    
    # ------------------------------
    # SEARCH SECTION (Always visible)
    # ------------------------------
    st.markdown("---")
    st.subheader("🔍 Search Sites")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input(
            "Search by PLAID or Site Name",
            value=st.session_state.search_term,
            placeholder="Enter PLAID or Site Name (e.g., SITE001 or Alpha)",
            help="Search will look for matches in both PLAID and Site Name columns",
            label_visibility="collapsed"
        )
    with col2:
        search_button = st.button("🔍 Search", use_container_width=True)
        clear_button = st.button("✖️ Clear", use_container_width=True)
    
    if clear_button:
        st.session_state.search_term = ''
        st.session_state.has_searched = False
        st.session_state.search_results = None
        st.rerun()
    
    # Perform search when button is clicked
    if search_button and search_term:
        st.session_state.search_term = search_term
        st.session_state.has_searched = True
        
        # Search in PLAID and SITE columns (case-insensitive)
        mask = pd.Series([False] * len(df))
        if 'PLAID' in df.columns:
            mask |= df['PLAID'].astype(str).str.contains(search_term, case=False, na=False)
        if 'SITE' in df.columns:
            mask |= df['SITE'].astype(str).str.contains(search_term, case=False, na=False)
        
        st.session_state.search_results = df[mask].copy()
    
    # ------------------------------
    # DISPLAY RESULTS (only if searched)
    # ------------------------------
    if st.session_state.has_searched:
        filtered_df = st.session_state.search_results
        
        if filtered_df is None or len(filtered_df) == 0:
            st.warning(f"No sites found matching '{st.session_state.search_term}'")
            # Show empty state with search hint
            st.markdown("""
            <div class="welcome-container" style="padding: 2rem;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">🔍</div>
                <div class="welcome-title">No Results Found</div>
                <div class="welcome-subtitle">
                    Try searching with a different PLAID or Site Name.
                </div>
                <div class="welcome-hint">
                    💡 Tip: Search is case-insensitive and matches partial terms
                </div>
            </div>
            """, unsafe_allow_html=True)
            return
        
        # Show search results count
        st.markdown(f"**Found {len(filtered_df)} site(s)** matching '{st.session_state.search_term}'")
        
        # Statistics for search results
        stats = {
            'total_sites': len(filtered_df),
            'total_regions': filtered_df['REGION'].nunique() if 'REGION' in filtered_df.columns else 0,
            'with_coords': filtered_df['LATITUDE'].notna().sum() if 'LATITUDE' in filtered_df.columns else 0,
            'with_contact': filtered_df['CONTACT NUMBER'].notna().sum() if 'CONTACT NUMBER' in filtered_df.columns else 0,
        }
        
        st.markdown(f"""
        <div class="stats-container">
            <div class="stat-item">
                <span class="stat-number">{stats['total_sites']}</span>
                <span class="stat-label">Results Found</span>
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
        # FILTERS (for search results)
        # ------------------------------
        col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
        
        with col1:
            if 'REGION' in filtered_df.columns:
                regions = ['All'] + sorted(filtered_df['REGION'].dropna().unique().tolist())
                selected_region = st.selectbox('Filter by Region', regions)
                if selected_region != 'All':
                    filtered_df = filtered_df[filtered_df['REGION'] == selected_region]
        
        with col2:
            if 'TOWERCO' in filtered_df.columns:
                towercos = ['All'] + sorted(filtered_df['TOWERCO'].dropna().unique().tolist())
                selected_towerco = st.selectbox('Filter by TowerCo', towercos)
                if selected_towerco != 'All':
                    filtered_df = filtered_df[filtered_df['TOWERCO'] == selected_towerco]
        
        with col3:
            show_with_coords = st.checkbox('Only with coords', value=False)
            if show_with_coords:
                filtered_df = filtered_df[filtered_df['LATITUDE'].notna() & filtered_df['LONGITUDE'].notna()]
        
        with col4:
            show_map = st.checkbox('Show Map View', value=False)
        
        # Update count after filters
        if len(filtered_df) > 0:
            st.markdown(f"**Showing {len(filtered_df)} site(s)**")
        
        # ------------------------------
        # MAP VIEW
        # ------------------------------
        if show_map and len(filtered_df) > 0:
            st.markdown("---")
            st.subheader("🗺️ Site Map Visualization")
            
            map_indices = filtered_df[filtered_df['LATITUDE'].notna() & filtered_df['LONGITUDE'].notna()].index.tolist()
            
            if map_indices:
                selected_map_indices = st.multiselect(
                    "Select sites to highlight on map (optional)",
                    options=map_indices,
                    format_func=lambda x: f"{filtered_df.loc[x, 'SITE']} - {filtered_df.loc[x, 'REGION']}"
                )
                
                fig = create_map(filtered_df, selected_map_indices)
                if fig:
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                    
                    if selected_map_indices:
                        col1, col2, col3 = st.columns([2, 1, 1])
                        with col2:
                            if st.button("📄 Export Selected to PDF", use_container_width=True):
                                with st.spinner("Generating PDF..."):
                                    pdf_data = create_pdf_export(filtered_df, selected_map_indices)
                                    if pdf_data:
                                        b64 = base64.b64encode(pdf_data).decode()
                                        href = f'<a href="data:application/pdf;base64,{b64}" download="site_report_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf" class="btn-map" style="text-align:center; text-decoration:none;">📥 Download PDF Report</a>'
                                        st.markdown(href, unsafe_allow_html=True)
                    else:
                        st.info("💡 Select sites above to generate a PDF report")
            else:
                st.warning("⚠️ No sites with coordinates found in the filtered data")
        
        # ------------------------------
        # SITE CARDS
        # ------------------------------
        if len(filtered_df) > 0:
            st.markdown("---")
            records = filtered_df.to_dict(orient="records")
            
            for row in records:
                html = create_site_card(row, st.session_state.search_term)
                st.markdown(html, unsafe_allow_html=True)
            
            # Data Table
            with st.expander("📊 View raw data table", expanded=False):
                st.dataframe(filtered_df, use_container_width=True, height=400)
            
            # Export Options
            col1, col2 = st.columns(2)
            
            with col1:
                csv = filtered_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="⬇️ Download Filtered Data as CSV",
                    data=csv,
                    file_name=f"globe_fo_extract_filtered_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            
            with col2:
                full_csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="⬇️ Download All Data as CSV",
                    data=full_csv,
                    file_name=f"globe_fo_extract_all_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
    
    else:
        # ------------------------------
        # WELCOME SCREEN (No search performed yet)
        # ------------------------------
        st.markdown("""
        <div class="welcome-container">
            <div class="welcome-icon">📍</div>
            <div class="welcome-title">Welcome to GPS Extractor</div>
            <div class="welcome-subtitle">
                Search for sites using PLAID or Site Name to get started.<br>
                Click on any search result to navigate or call the FO directly.
            </div>
            <div class="welcome-hint">
                💡 Enter a PLAID or Site Name in the search box above and click Search
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Show database stats
        stats = {
            'total_sites': len(df),
            'total_regions': df['REGION'].nunique() if 'REGION' in df.columns else 0,
            'with_coords': df['LATITUDE'].notna().sum() if 'LATITUDE' in df.columns else 0,
            'with_contact': df['CONTACT NUMBER'].notna().sum() if 'CONTACT NUMBER' in df.columns else 0,
        }
        
        st.markdown(f"""
        <div class="stats-container" style="margin-top: 1rem;">
            <div class="stat-item">
                <span class="stat-number">{stats['total_sites']}</span>
                <span class="stat-label">Total Sites in Database</span>
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
# ROUTING
# ------------------------------
if st.session_state.page == 'about':
    show_about()
else:
    show_main()

# ------------------------------
# FOOTER
# ------------------------------
st.markdown("""
    <hr style="margin-top: 2rem; opacity:0.3; border-color: #2a2a44;">
    <div style="text-align: center; color: #6b6b85; font-size: 0.8rem; padding: 0.5rem;">
        GPS Extractor · Globe FO Engr Contact · Developed by Engr. John Carlo Rabanes, ECE
    </div>
""", unsafe_allow_html=True)
