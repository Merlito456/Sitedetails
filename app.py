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
# CUSTOM CSS
# ------------------------------
st.markdown("""
    <style>
    /* main container */
    .main .block-container {
        padding: 1rem 1.5rem;
    }
    
    /* card style for each row */
    .site-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.04);
        border: 1px solid #f0f2f6;
        transition: 0.2s;
    }
    .site-card:hover {
        border-color: #d0d5dd;
        box-shadow: 0 8px 20px rgba(0,0,0,0.06);
    }
    .site-title {
        font-weight: 600;
        font-size: 1.2rem;
        color: #1f2937;
        margin-bottom: 0.25rem;
    }
    .site-sub {
        font-size: 0.9rem;
        color: #6b7280;
    }
    .badge {
        background: #eef2ff;
        color: #4f46e5;
        padding: 0.2rem 0.8rem;
        border-radius: 40px;
        font-size: 0.75rem;
        font-weight: 500;
        display: inline-block;
        margin-right: 0.4rem;
    }
    .badge-plaid {
        background: #dbeafe;
        color: #1e40af;
        padding: 0.2rem 0.8rem;
        border-radius: 40px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
        margin-right: 0.4rem;
    }
    .btn-group {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 0.6rem;
    }
    .btn-map {
        background: #1a73e8;
        color: white !important;
        padding: 0.4rem 1.2rem;
        border-radius: 40px;
        font-size: 0.85rem;
        font-weight: 500;
        text-decoration: none;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        transition: 0.2s;
        border: none;
        cursor: pointer;
    }
    .btn-map:hover {
        background: #1557b0;
        color: white !important;
    }
    .btn-call {
        background: #16a34a;
        color: white !important;
        padding: 0.4rem 1.2rem;
        border-radius: 40px;
        font-size: 0.85rem;
        font-weight: 500;
        text-decoration: none;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        transition: 0.2s;
        border: none;
        cursor: pointer;
    }
    .btn-call:hover {
        background: #15803d;
        color: white !important;
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
        color: #6b7280;
        font-weight: 400;
        min-width: 80px;
    }
    .detail-value {
        font-weight: 500;
        color: #1f2937;
    }
    .stats-container {
        background: #f8fafc;
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin: 1rem 0;
        border: 1px solid #e5e7eb;
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
        color: #1f2937;
    }
    .stat-label {
        color: #6b7280;
        font-size: 0.9rem;
    }
    .search-highlight {
        background: #fef08a;
        padding: 0.1rem 0.3rem;
        border-radius: 4px;
    }
    .stDataFrame {
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        overflow: hidden;
    }
    
    /* Search box styling */
    .search-container {
        background: white;
        border-radius: 12px;
        padding: 1rem;
        border: 1px solid #e5e7eb;
        margin: 1rem 0;
    }
    .search-input {
        width: 100%;
        padding: 0.75rem 1rem;
        border: 2px solid #e5e7eb;
        border-radius: 8px;
        font-size: 1rem;
        transition: 0.2s;
    }
    .search-input:focus {
        border-color: #1a73e8;
        outline: none;
        box-shadow: 0 0 0 3px rgba(26, 115, 232, 0.1);
    }
    .search-icon {
        position: relative;
        left: 30px;
        top: 2px;
        color: #9ca3af;
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

# ------------------------------
# FUNCTIONS
# ------------------------------
@st.cache_data
def load_excel_data():
    """Load data from Excel file"""
    try:
        # Try multiple possible locations
        possible_paths = [
            "data/Globe FO Engr Conctat_Vendor.xlsx",
            "Globe FO Engr Conctat_Vendor.xlsx",
            "./data/Globe FO Engr Conctat_Vendor.xlsx",
            "./Globe FO Engr Conctat_Vendor.xlsx",
            Path(__file__).parent / "data" / "Globe FO Engr Conctat_Vendor.xlsx",
            Path(__file__).parent / "Globe FO Engr Conctat_Vendor.xlsx",
        ]
        
        file_path = None
        for path in possible_paths:
            if os.path.exists(path):
                file_path = path
                break
        
        if file_path is None:
            st.error("""
            ❌ **Excel file not found!**
            
            Please place `Globe FO Engr Conctat_Vendor.xlsx` in one of these locations:
            - `data/Globe FO Engr Conctat_Vendor.xlsx`
            - `Globe FO Engr Conctat_Vendor.xlsx` (root folder)
            """)
            return None
        
        # Read the Excel file
        df = pd.read_excel(file_path, engine='openpyxl')
        
        # Clean column names
        df.columns = df.columns.str.strip().str.upper()
        
        # Check if we have data
        if df.empty:
            st.error("❌ The Excel file is empty!")
            return None
        
        st.success(f"✅ Successfully loaded {len(df)} records from '{Path(file_path).name}'")
        return df
        
    except Exception as e:
        st.error(f"❌ Error loading file: {str(e)}")
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
                <span class="badge" style="background:#f3f4f6; color:#374151;">{territory}</span>
                <span class="badge" style="background:#fef3c7; color:#92400e;">{towerco}</span>
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
            html += '<span style="background:#f3f4f6; color:#6b7280; padding:0.3rem 1rem; border-radius:40px; font-size:0.85rem;">⚠️ invalid coordinates</span>'
    else:
        html += '<span style="background:#f3f4f6; color:#6b7280; padding:0.3rem 1rem; border-radius:40px; font-size:0.85rem;">⚠️ no coordinates</span>'
    
    # Call button
    if contact:
        clean_contact = ''.join(ch for ch in contact if ch.isdigit() or ch == '+')
        if clean_contact:
            html += f'<a href="tel:{clean_contact}" class="btn-call"><span>📞</span> Call FO: {contact}</a>'
        else:
            html += f'<span style="background:#f3f4f6; color:#6b7280; padding:0.3rem 1rem; border-radius:40px; font-size:0.85rem;">📞 {contact}</span>'
    else:
        html += '<span style="background:#f3f4f6; color:#6b7280; padding:0.3rem 1rem; border-radius:40px; font-size:0.85rem;">📞 no contact</span>'
    
    html += "</div></div>"
    return html

def create_map(df, selected_indices=None):
    """Create interactive map"""
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
            color='#9ca3af',
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
    
    # Configure map layout
    fig.update_layout(
        mapbox=dict(
            style='open-street-map',
            center=dict(
                lat=map_df['LATITUDE'].mean() if not map_df.empty else 14.5995,
                lon=map_df['LONGITUDE'].mean() if not map_df.empty else 121.0139
            ),
            zoom=8
        ),
        height=500,
        margin=dict(l=0, r=0, t=0, b=0),
        hovermode='closest'
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
            textColor=colors.HexColor('#1f2937'),
            alignment=1,
            spaceAfter=30
        )
        
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#6b7280'),
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
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1f2937')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#374151')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
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
# ABOUT PAGE
# ------------------------------
def show_about():
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1 style="font-size: 2.5rem; font-weight: 700; color: #1f2937;">📍 GPS Extractor</h1>
        <p style="font-size: 1.2rem; color: #6b7280; margin-top: 0.5rem;">Globe FO Engineer Contact Management System</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Developer Info
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                border-radius: 16px; padding: 2rem; color: white; margin: 1rem 0;">
        <div style="display: flex; align-items: center; gap: 1rem; flex-wrap: wrap;">
            <div style="flex: 1;">
                <h2 style="color: white; margin: 0;">👨‍💻 Developer</h2>
                <h3 style="color: white; margin: 0.5rem 0;">Engr. John Carlo Rabanes, ECE</h3>
                <p style="margin: 0.3rem 0;">📧 rabanes.johncarlo4@gmail.com</p>
                <p style="margin: 0.3rem 0;">🏢 Nokia Shanghai Bell</p>
            </div>
            <div style="font-size: 4rem;">📡</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Mission & Vision
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div style="background: #f0f4ff; border-radius: 12px; padding: 1.5rem; height: 100%;">
            <h3 style="color: #4f46e5;">🎯 Mission</h3>
            <p style="color: #374151; line-height: 1.6;">
                To empower field operations engineers with seamless access to site information, 
                enabling efficient navigation and communication for faster response times and 
                improved network reliability across the Philippines.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: #fef3c7; border-radius: 12px; padding: 1.5rem; height: 100%;">
            <h3 style="color: #92400e;">👁️ Vision</h3>
            <p style="color: #374151; line-height: 1.6;">
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
        <div style="background: #ecfdf5; border-left: 4px solid #10b981; border-radius: 8px; padding: 1.5rem;">
            <h3 style="color: #065f46; margin-top: 0;">✅ Advantages</h3>
            <ul style="color: #374151; line-height: 2;">
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
        <div style="background: #fef2f2; border-left: 4px solid #ef4444; border-radius: 8px; padding: 1.5rem;">
            <h3 style="color: #991b1b; margin-top: 0;">⚠️ Disadvantages</h3>
            <ul style="color: #374151; line-height: 2;">
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

# ------------------------------
# MAIN PAGE
# ------------------------------
def show_main():
    # Navigation
    col1, col2, col3 = st.columns([3, 1, 1])
    with col2:
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.page = 'main'
            st.rerun()
    with col3:
        if st.button("ℹ️ About", use_container_width=True):
            st.session_state.page = 'about'
            st.rerun()
    
    # Title
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
    
    # Load data
    if st.session_state.df is None:
        df = load_excel_data()
        if df is not None:
            st.session_state.df = df
    else:
        df = st.session_state.df
    
    if df is None or df.empty:
        st.warning("⚠️ No data available. Please check the Excel file.")
        return
    
    # Statistics
    stats = {
        'total_sites': len(df),
        'total_regions': df['REGION'].nunique() if 'REGION' in df.columns else 0,
        'with_coords': df['LATITUDE'].notna().sum() if 'LATITUDE' in df.columns else 0,
        'with_contact': df['CONTACT NUMBER'].notna().sum() if 'CONTACT NUMBER' in df.columns else 0,
    }
    
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
    # SEARCH SECTION
    # ------------------------------
    st.markdown("---")
    st.subheader("🔍 Search Sites")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input(
            "Search by PLAID or Site Name",
            value=st.session_state.search_term,
            placeholder="Enter PLAID or Site Name (e.g., SITE001 or Alpha)",
            help="Search will look for matches in both PLAID and Site Name columns"
        )
    with col2:
        search_button = st.button("🔍 Search", use_container_width=True)
        clear_button = st.button("✖️ Clear", use_container_width=True)
    
    if clear_button:
        st.session_state.search_term = ''
        st.rerun()
    
    if search_button and search_term:
        st.session_state.search_term = search_term
    
    # Apply search filter
    filtered_df = df.copy()
    search_term = st.session_state.search_term
    
    if search_term:
        # Search in PLAID and SITE columns (case-insensitive)
        mask = pd.Series([False] * len(filtered_df))
        if 'PLAID' in filtered_df.columns:
            mask |= filtered_df['PLAID'].astype(str).str.contains(search_term, case=False, na=False)
        if 'SITE' in filtered_df.columns:
            mask |= filtered_df['SITE'].astype(str).str.contains(search_term, case=False, na=False)
        filtered_df = filtered_df[mask]
        
        if len(filtered_df) == 0:
            st.warning(f"No sites found matching '{search_term}'")
    
    # ------------------------------
    # FILTERS
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
    
    # Display count
    st.markdown(f"**Showing {len(filtered_df)} site(s)**" + (f" matching '{search_term}'" if search_term else ""))
    
    # ------------------------------
    # MAP VIEW
    # ------------------------------
    if show_map:
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
                st.plotly_chart(fig, use_container_width=True)
                
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
    st.markdown("---")
    
    if len(filtered_df) == 0:
        st.info("No records match the selected filters.")
    else:
        records = filtered_df.to_dict(orient="records")
        
        for row in records:
            html = create_site_card(row, search_term)
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
    <hr style="margin-top: 2rem; opacity:0.3;">
    <div style="text-align: center; color: #9ca3af; font-size: 0.8rem; padding: 0.5rem;">
        GPS Extractor · Globe FO Engr Contact · Developed by Engr. John Carlo Rabanes, ECE
    </div>
""", unsafe_allow_html=True)
