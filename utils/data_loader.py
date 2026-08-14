import pandas as pd
import os
from pathlib import Path
import streamlit as st

@st.cache_data
def load_data():
    """Load data from the Excel file that's part of the system"""
    # Try multiple possible locations for the file
    possible_paths = [
        Path(__file__).parent.parent / "data" / "Globe FO Engr Conctat_Vendor.xlsx",
        Path(__file__).parent.parent / "Globe FO Engr Conctat_Vendor.xlsx",
        "Globe FO Engr Conctat_Vendor.xlsx",
        "data/Globe FO Engr Conctat_Vendor.xlsx",
    ]
    
    file_path = None
    for path in possible_paths:
        if os.path.exists(path):
            file_path = path
            break
    
    if file_path is None:
        # If file doesn't exist, create sample data
        return create_sample_data()
    
    try:
        df = pd.read_excel(file_path, engine="openpyxl")
        # Normalize column names
        df.columns = df.columns.str.strip().str.upper()
        return df
    except Exception as e:
        st.warning(f"⚠️ Could not load file: {e}. Using sample data instead.")
        return create_sample_data()

def create_sample_data():
    """Create sample data for demonstration"""
    sample_data = {
        'PLAID': ['PLAID001', 'PLAID002', 'PLAID003', 'PLAID004', 'PLAID005',
                  'PLAID006', 'PLAID007', 'PLAID008', 'PLAID009', 'PLAID010'],
        'SITE': ['Site Alpha', 'Site Beta', 'Site Gamma', 'Site Delta', 'Site Epsilon',
                 'Site Zeta', 'Site Eta', 'Site Theta', 'Site Iota', 'Site Kappa'],
        'REGION': ['NCR', 'NCR', 'Region IV-A', 'Region IV-A', 'Region III',
                   'Region VII', 'Region XI', 'NCR', 'Region IV-A', 'Region I'],
        'PROVINCE': ['Metro Manila', 'Metro Manila', 'Laguna', 'Cavite', 'Pampanga',
                     'Cebu', 'Davao', 'Metro Manila', 'Rizal', 'Pangasinan'],
        'MUNICIPALITY': ['Quezon City', 'Makati', 'Santa Rosa', 'Dasmariñas', 'San Fernando',
                         'Cebu City', 'Davao City', 'Mandaluyong', 'Antipolo', 'Dagupan'],
        'BARANGAY': ['Barangay 1', 'Barangay 2', 'Barangay 3', 'Barangay 4', 'Barangay 5',
                     'Barangay 6', 'Barangay 7', 'Barangay 8', 'Barangay 9', 'Barangay 10'],
        'TERRITORY': ['North', 'South', 'East', 'West', 'Central',
                      'North', 'South', 'East', 'West', 'Central'],
        'LATITUDE': [14.5995, 14.5547, 14.3123, 14.3294, 15.0287,
                     10.3157, 7.1907, 14.5794, 14.5864, 16.0422],
        'LONGITUDE': [121.0139, 121.0244, 121.1115, 120.9589, 120.6889,
                      123.8854, 125.4553, 121.0337, 121.1759, 120.3410],
        'SITE_ADD': ['123 Main St, QC', '456 Makati Ave', '789 Laguna Blvd', 
                     '321 Cavite Rd', '654 Pampanga St', '789 Cebu Rd',
                     '456 Davao St', '789 Mandaluyong', '321 Antipolo', '654 Dagupan'],
        'ASSIGNED_HUB': ['Hub 1', 'Hub 2', 'Hub 3', 'Hub 4', 'Hub 5',
                         'Hub 6', 'Hub 7', 'Hub 8', 'Hub 9', 'Hub 10'],
        'TOWERCO': ['TowerCo A', 'TowerCo B', 'TowerCo A', 'TowerCo C', 'TowerCo B',
                    'TowerCo A', 'TowerCo C', 'TowerCo B', 'TowerCo A', 'TowerCo C'],
        'NEW ASSIGN_HUB': ['New Hub 1', 'New Hub 2', 'New Hub 3', 'New Hub 4', 'New Hub 5',
                           'New Hub 6', 'New Hub 7', 'New Hub 8', 'New Hub 9', 'New Hub 10'],
        'NEW ENGINEER_ANM1': ['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Brown', 
                              'Charlie Wilson', 'David Lee', 'Emma Garcia', 
                              'Frank Martinez', 'Grace Taylor', 'Henry Anderson'],
        'CONTACT NUMBER': ['+639171234567', '+639188765432', '+639155554444', 
                           '+639176663333', '+639198882222', '+639177771111',
                           '+639199990000', '+639166665555', '+639188883333', '+639177774444']
    }
    return pd.DataFrame(sample_data)

def get_data_stats(df):
    """Get statistics about the dataset"""
    stats = {
        'total_sites': len(df),
        'total_regions': df['REGION'].nunique() if 'REGION' in df.columns else 0,
        'with_coords': df['LATITUDE'].notna().sum() if 'LATITUDE' in df.columns else 0,
        'with_contact': df['CONTACT NUMBER'].notna().sum() if 'CONTACT NUMBER' in df.columns else 0,
    }
    return stats
