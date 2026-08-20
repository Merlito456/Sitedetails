import streamlit as st
import pandas as pd
from pathlib import Path
import os

# ------------------------------
# PAGE CONFIG
# ------------------------------
st.set_page_config(
    page_title="GPS Extractor • Data Mapper",
    page_icon="📍",
    layout="wide",
)

# ------------------------------
# DARK THEME
# ------------------------------
st.markdown("""
    <style>
    .main .block-container {
        padding: 1rem 1.5rem;
        background: #0a0a0f;
    }
    .stApp {
        background: #0a0a0f;
    }
    h1, h2, h3 {
        color: #e8e8f0 !important;
    }
    p, li {
        color: #a0a0b8 !important;
    }
    .stDataFrame {
        background: #14141e !important;
        border: 1px solid #2a2a44 !important;
        border-radius: 12px !important;
    }
    .column-card {
        background: #1a1a2e;
        border-radius: 12px;
        padding: 0.8rem 1rem;
        margin: 0.3rem 0;
        border: 1px solid #2a2a44;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .column-name {
        color: #e8e8f0;
        font-weight: 600;
    }
    .column-sample {
        color: #4f8cf7;
        font-size: 0.85rem;
        background: #1e1e32;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
    }
    .mapped-badge {
        background: #34d399;
        color: #0a0a0f;
        padding: 0.15rem 0.6rem;
        border-radius: 40px;
        font-size: 0.65rem;
        font-weight: 600;
    }
    .unmapped-badge {
        background: #ef4444;
        color: white;
        padding: 0.15rem 0.6rem;
        border-radius: 40px;
        font-size: 0.65rem;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

# ------------------------------
# FUNCTIONS
# ------------------------------
@st.cache_data
def load_excel_file(file):
    """Load Excel file and show columns"""
    try:
        df = pd.read_excel(file, engine='openpyxl')
        return df
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")
        return None

def detect_column_mappings(df):
    """Detect which columns contain what data"""
    mappings = {
        'PLAID': {'keywords': ['PLAID', 'PLID', 'SITE ID', 'ID'], 'found': None},
        'SITE': {'keywords': ['SITE', 'SITE NAME', 'SITENAME', 'SITE_NAME'], 'found': None},
        'REGION': {'keywords': ['REGION', 'REG'], 'found': None},
        'PROVINCE': {'keywords': ['PROVINCE', 'PROV'], 'found': None},
        'MUNICIPALITY': {'keywords': ['MUNICIPALITY', 'MUN', 'CITY', 'MUNICIPAL'], 'found': None},
        'BARANGAY': {'keywords': ['BARANGAY', 'BRGY', 'BAR'], 'found': None},
        'TERRITORY': {'keywords': ['TERRITORY', 'TERR'], 'found': None},
        'LATITUDE': {'keywords': ['LATITUDE', 'LAT', 'LAT'], 'found': None},
        'LONGITUDE': {'keywords': ['LONGITUDE', 'LONG', 'LON', 'LNG'], 'found': None},
        'SITE_ADD': {'keywords': ['SITE_ADD', 'ADDRESS', 'SITE ADDRESS', 'LOCATION'], 'found': None},
        'ASSIGNED_HUB': {'keywords': ['ASSIGNED HUB', 'ASSIGNED_HUB', 'HUB', 'CURRENT HUB'], 'found': None},
        'TOWERCO': {'keywords': ['TOWERCO', 'TOWER CO', 'TOWER', 'TOWER COMPANY'], 'found': None},
        'NEW_ASSIGN_HUB': {'keywords': ['NEW ASSIGN HUB', 'NEW_ASSIGN_HUB', 'NEW HUB', 'NEW HUB'], 'found': None},
        'FO_ONSITE': {'keywords': ['FO ONSITE', 'NEW ENGINEER_ANM1', 'ONSITE', 'ENGINEER', 'FO', 'FIELD OPERATIONS'], 'found': None},
        'CONTACT_NUMBER': {'keywords': ['CONTACT NUMBER', 'CONTACT', 'PHONE', 'MOBILE', 'CELL', 'CONTACT NO'], 'found': None},
    }
    
    # Search for each column
    for col in df.columns:
        col_upper = col.upper().strip()
        for mapping_key, mapping_value in mappings.items():
            if any(keyword.upper() in col_upper for keyword in mapping_value['keywords']):
                mapping_value['found'] = col
                break
    
    return mappings

def show_data_preview(df, selected_columns=None):
    """Show preview of data"""
    if selected_columns:
        preview_df = df[selected_columns].head(10)
    else:
        preview_df = df.head(10)
    return preview_df

# ------------------------------
# HEADER
# ------------------------------
st.markdown("""
    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;">
        <span style="font-size: 2rem;">🔍</span>
        <h1 style="display: inline-block; margin: 0; font-weight: 700; color: #e8e8f0;">Data Column Mapper</h1>
        <span style="background: rgba(79, 140, 247, 0.2); color: #4f8cf7; padding: 0.2rem 1rem; border-radius: 40px; font-size: 0.8rem; font-weight: 500; border: 1px solid rgba(79, 140, 247, 0.2);">Globe FO Engr</span>
    </div>
    <p style="color: #a0a0b8; margin-bottom: 1.5rem;">
        Upload your Excel file to detect and map columns automatically. 
        This will help identify where your FO Onsite and Hub data is located.
    </p>
""", unsafe_allow_html=True)

# ------------------------------
# FILE UPLOAD
# ------------------------------
uploaded_file = st.file_uploader(
    "Upload your Excel file (.xlsx)",
    type=["xlsx"],
    help="Upload the Globe FO Engr Contact Vendor Excel file"
)

if uploaded_file is not None:
    # Load the file
    df = load_excel_file(uploaded_file)
    
    if df is not None:
        st.success(f"✅ Successfully loaded {len(df)} rows with {len(df.columns)} columns")
        
        # Show column detection results
        st.markdown("---")
        st.subheader("📋 Column Detection Results")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("**Detected Columns:**")
            
            # Detect mappings
            mappings = detect_column_mappings(df)
            
            # Display each column with its mapping status
            for col in df.columns:
                col_upper = col.upper().strip()
                mapped_to = None
                for key, value in mappings.items():
                    if value['found'] == col:
                        mapped_to = key
                        break
                
                # Get sample data
                sample_value = str(df[col].iloc[0]) if len(df) > 0 else ""
                if len(sample_value) > 50:
                    sample_value = sample_value[:50] + "..."
                
                status_badge = f'<span class="mapped-badge">✓ {mapped_to}</span>' if mapped_to else '<span class="unmapped-badge">⚠ Unmapped</span>'
                
                st.markdown(f"""
                <div class="column-card">
                    <div>
                        <span class="column-name">{col}</span>
                        <span class="column-sample">{sample_value}</span>
                    </div>
                    <div>
                        {status_badge}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("**Summary:**")
            st.markdown(f"• **Total Columns:** {len(df.columns)}")
            st.markdown(f"• **Mapped Columns:** {sum(1 for v in mappings.values() if v['found'] is not None)}")
            st.markdown(f"• **Unmapped Columns:** {len(df.columns) - sum(1 for v in mappings.values() if v['found'] is not None)}")
            
            st.markdown("---")
            st.markdown("**🚨 Critical Fields:**")
            
            critical_fields = ['FO_ONSITE', 'ASSIGNED_HUB', 'NEW_ASSIGN_HUB']
            for field in critical_fields:
                found = mappings[field]['found'] if field in mappings else None
                status = "✅" if found else "❌"
                st.markdown(f"{status} **{field}**: {found if found else 'Not found'}")
        
        # Data Preview
        st.markdown("---")
        st.subheader("📊 Data Preview")
        
        # Allow user to select columns for preview
        all_cols = df.columns.tolist()
        selected_cols = st.multiselect(
            "Select columns to preview (or leave empty for all)",
            options=all_cols,
            default=all_cols[:10] if len(all_cols) > 10 else all_cols
        )
        
        if selected_cols:
            preview_df = show_data_preview(df, selected_cols)
        else:
            preview_df = show_data_preview(df)
        
        st.dataframe(preview_df, use_container_width=True, height=300)
        
        # Help identify missing data
        st.markdown("---")
        st.subheader("🔍 Looking for FO Onsite and Hub Data?")
        
        # Check specifically for FO Onsite and Hub columns
        fo_onsite_col = None
        assigned_hub_col = None
        new_hub_col = None
        
        for col in df.columns:
            col_upper = col.upper().strip()
            if 'FO ONSITE' in col_upper or 'NEW ENGINEER_ANM1' in col_upper or 'ONSITE' in col_upper:
                fo_onsite_col = col
            if 'ASSIGNED HUB' in col_upper or 'ASSIGNED_HUB' in col_upper or 'CURRENT HUB' in col_upper:
                assigned_hub_col = col
            if 'NEW ASSIGN HUB' in col_upper or 'NEW_ASSIGN_HUB' in col_upper or 'NEW HUB' in col_upper:
                new_hub_col = col
        
        if fo_onsite_col:
            st.success(f"✅ Found FO Onsite column: **{fo_onsite_col}**")
            st.markdown(f"Sample data: {df[fo_onsite_col].iloc[0] if len(df) > 0 else 'No data'}")
        else:
            st.warning("⚠️ FO Onsite column not found. Looking for variations like: 'FO ONSITE', 'NEW ENGINEER_ANM1', 'ONSITE'")
            st.info("💡 Check if your column might have a different name. Look for columns containing: FO, Engineer, Onsite, Field Operations")
        
        st.markdown("---")
        
        if assigned_hub_col:
            st.success(f"✅ Found Assigned Hub column: **{assigned_hub_col}**")
            st.markdown(f"Sample data: {df[assigned_hub_col].iloc[0] if len(df) > 0 else 'No data'}")
        else:
            st.warning("⚠️ Assigned Hub column not found. Looking for variations like: 'ASSIGNED HUB', 'HUB', 'CURRENT HUB'")
        
        if new_hub_col:
            st.success(f"✅ Found New Assign Hub column: **{new_hub_col}**")
            st.markdown(f"Sample data: {df[new_hub_col].iloc[0] if len(df) > 0 else 'No data'}")
        else:
            st.warning("⚠️ New Assign Hub column not found. Looking for variations like: 'NEW ASSIGN HUB', 'NEW HUB'")
        
        # Export mapping configuration
        st.markdown("---")
        st.subheader("📝 Column Mapping Configuration")
        
        # Show current mapping
        mapping_config = {}
        for key, value in mappings.items():
            if value['found']:
                mapping_config[key] = value['found']
        
        st.json(mapping_config)
        
        # Allow manual mapping
        st.markdown("**Manual Column Mapping:**")
        st.info("If automatic detection missed a column, you can manually map it below:")
        
        # Create mapping interface for critical fields
        critical_mappings = {
            'FO_ONSITE': 'FO Onsite (Engineer Name)',
            'ASSIGNED_HUB': 'Assigned Hub',
            'NEW_ASSIGN_HUB': 'New Assign Hub',
            'CONTACT_NUMBER': 'Contact Number',
            'LATITUDE': 'Latitude',
            'LONGITUDE': 'Longitude'
        }
        
        for field_key, field_label in critical_mappings.items():
            current_value = mappings[field_key]['found'] if field_key in mappings else None
            options = ['Not Set'] + df.columns.tolist()
            default_index = 0 if current_value not in df.columns else options.index(current_value)
            
            selected = st.selectbox(
                f"Map **{field_label}** to column:",
                options=options,
                index=default_index
            )
            
            if selected != 'Not Set':
                st.caption(f"Sample: {df[selected].iloc[0] if len(df) > 0 else 'No data'}")
        
        # Download mapping
        st.markdown("---")
        if st.button("📥 Download Column Mapping", use_container_width=True):
            import json
            json_data = json.dumps(mapping_config, indent=2)
            st.download_button(
                label="Download JSON Mapping",
                data=json_data,
                file_name="column_mapping.json",
                mime="application/json"
            )

else:
    st.info("👆 Please upload your Excel file to start the column mapping analysis.")

# ------------------------------
# FOOTER
# ------------------------------
st.markdown("""
    <hr style="margin-top: 2rem; opacity:0.3; border-color: #2a2a44;">
    <div style="text-align: center; color: #6b6b85; font-size: 0.8rem; padding: 0.5rem;">
        GPS Extractor · Column Mapper · Helps identify FO Onsite and Hub data
    </div>
""", unsafe_allow_html=True)
