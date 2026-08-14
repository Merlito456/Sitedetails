import pandas as pd
import streamlit as st

def safe_str(val):
    """Convert value to string, handling NaN/None"""
    if pd.isna(val):
        return ""
    return str(val)

def create_card_html(row):
    """Create HTML for a site card"""
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
    
    html = f"""
    <div class="site-card">
        <div style="display: flex; flex-wrap: wrap; justify-content: space-between; align-items: flex-start;">
            <div>
                <div class="site-title">{site} <span class="badge">{plaid}</span></div>
                <div class="site-sub">{region} · {province} · {municipality} · {barangay}</div>
            </div>
            <div style="display: flex; gap: 0.4rem; flex-wrap: wrap; margin-top: 0.2rem;">
                <span class="badge" style="background:#f3f4f6; color:#374151;">{territory}</span>
                <span class="badge" style="background:#fef3c7; color:#92400e;">{towerco}</span>
            </div>
        </div>
        <div class="detail-grid">
            <div class="detail-item"><span class="detail-label">Address</span><span class="detail-value">{site_add}</span></div>
            <div class="detail-item"><span class="detail-label">Assigned Hub</span><span class="detail-value">{assigned_hub}</span></div>
            <div class="detail-item"><span class="detail-label">New Assign Hub</span><span class="detail-value">{new_assign_hub}</span></div>
            <div class="detail-item"><span class="detail-label">FO Onsite</span><span class="detail-value">{fo_onsite}</span></div>
            <div class="detail-item"><span class="detail-label">Lat/Lon</span><span class="detail-value">{lat}, {lon}</span></div>
        </div>
        <div class="btn-group">
    """
    
    # Add map button
    if lat and lon:
        try:
            float(lat); float(lon)
            maps_url = f"https://www.google.com/maps?q={lat},{lon}"
            html += f'''
                <a href="{maps_url}" target="_blank" class="btn-map">
                    <span>🗺️</span> Navigate to Google Maps
                </a>
            '''
        except:
            html += f'''
                <span style="background:#f3f4f6; color:#6b7280; padding:0.3rem 1rem; border-radius:40px; font-size:0.85rem;">
                    ⚠️ invalid coordinates
                </span>
            '''
    else:
        html += f'''
            <span style="background:#f3f4f6; color:#6b7280; padding:0.3rem 1rem; border-radius:40px; font-size:0.85rem;">
                ⚠️ no coordinates
            </span>
        '''
    
    # Add call button
    if contact:
        clean_contact = ''.join(ch for ch in contact if ch.isdigit() or ch == '+')
        if clean_contact:
            html += f'''
                <a href="tel:{clean_contact}" class="btn-call">
                    <span>📞</span> Call FO: {contact}
                </a>
            '''
        else:
            html += f'''
                <span style="background:#f3f4f6; color:#6b7280; padding:0.3rem 1rem; border-radius:40px; font-size:0.85rem;">
                    📞 {contact}
                </span>
            '''
    else:
        html += f'''
            <span style="background:#f3f4f6; color:#6b7280; padding:0.3rem 1rem; border-radius:40px; font-size:0.85rem;">
                📞 no contact
            </span>
        '''
    
    html += "</div></div>"
    return html
