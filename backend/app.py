"""
Project S - TikTok Political Sentiment Dashboard
Restored "Ngrok" Design Style
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import SupabaseClient
from datetime import datetime, timedelta
import logging
import sys
from openai import OpenAI
import subprocess
import textwrap
import json
import os
import time
import requests
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Project S - Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# DEBUG: Expose Key Suffix
try:
    k = Config.OPENAI_API_KEY
    suffix = k[-8:] if k and len(k) > 10 else "MISSING/SHORT"
    st.sidebar.warning(f"🔑 Loaded Key Suffix: ...{suffix}")
    
    # SYSTEM UPGRADE BANNER
    st.success("✅ **SYSTEM UPDATED v3.2:** Unified Rendering Engine & Auto-Monitor Parity Online")

    if "Is6E" in suffix:
        st.error(f"🚨 ACTIVE KEY IS OLD! Suffix: ...{suffix}. Please Reboot App completely.")
    else:
        st.success(f"✅ ACTIVE KEY IS NEW. Suffix: ...{suffix}")
except:
    pass

# Initialize database
@st.cache_resource
def get_database():
    try:
        return SupabaseClient()
    except Exception as e:
        st.error(f"Detailed Connection Error: {str(e)}")
        return None

db = get_database()

if not db:
    st.error("⚠️ Application could not connect to the database. Please check your Secrets.")
    st.stop()

# Health check endpoint - responds to ?health=true query parameter
# Also works with Streamlit's built-in /_stcore/health endpoint
query_params = st.query_params
if query_params.get("health") == "true":
    health_status = {
        "status": "ok",
        "service": "streamlit-frontend",
        "database_connected": db is not None,
        "timestamp": datetime.now().isoformat()
    }
    st.json(health_status)
    st.stop()

# Helper Functions for UI
def fmt_num(n):
    if not n: return "0"
    try:
        ni = int(n)
        if ni >= 1_000_000: return f"{ni/1_000_000:.1f}M"
        if ni >= 1_000: return f"{ni/1_000:.1f}K"
        return str(ni)
    except:
        return str(n)

def render_video_card(v, compact=False, is_new=False):
    # Prepare Data
    sent = v.get('sentiment', 'Not Analyzed')
    sent_score = v.get('sentiment_score')
    if sent_score is None:
        sent_score = 5  # Default to 5 (neutral) if None

    # NEW badge HTML if video was just scraped
    new_badge_html = ""
    new_border_style = ""
    if is_new:
        new_badge_html = '<span style="background:linear-gradient(135deg, #00D4FF, #7B2FF7); color:white; padding:3px 8px; border-radius:4px; font-size:9px; font-weight:800; margin-left:8px; animation:pulse 2s infinite;">NEW</span>'
        new_border_style = "box-shadow: 0 0 15px rgba(0, 212, 255, 0.5); border: 2px solid #00D4FF;"
    
    # Styling
    border_color = "#F39C12" # Neutral
    icon = "😐"
    bg_light = "#FFF9E6"
    text_color = "#F39C12"
    sent_label = "NEUTRAL"
    cls = "badge-neutral"
    
    if "Positive" in str(sent) or sent_score >= 7:
        border_color = "#2ECC71"
        icon = "😃"
        bg_light = "#E8F8F5"
        text_color = "#2ECC71"
        sent_label = "POSITIVE"
        cls = "badge-positive"
    elif "Negative" in str(sent) or sent_score <= 3:
        border_color = "#E74C3C"
        icon = "☹️"
        bg_light = "#FDEDEC"
        text_color = "#E74C3C"
        sent_label = "NEGATIVE"
        cls = "badge-negative"
        
    desc = v.get('description', '')[:120] + "..." if len(v.get('description', '')) > 120 else v.get('description', '')
    summary = v.get('summary', "No AI summary available.")
    
    # Prepare Keyword Tags
    keywords_html = ""
    raw_points = v.get('discussion_points', [])
    points_list = []
    if isinstance(raw_points, list):
        points_list = raw_points
    elif isinstance(raw_points, str):
        points_list = [x.strip() for x in raw_points.split(',') if x.strip()]
    
    for k in points_list[:7]:
        keywords_html += f'<span style="background:#2C3E50; color:#BDC3C7; padding:2px 6px; border-radius:3px; font-size:9px;">{k}</span>'

    # Prepare Insight Tags
    pk_issue = v.get('key_issues', [])
    insight_html = ""
    if pk_issue and isinstance(pk_issue, list):
        for issue in pk_issue[:3]:
             insight_html += f'<span style="background:#FFF3E0; color:#E67E22; padding:3px 8px; border-radius:4px; font-size:10px; font-weight:600; margin-right:4px;">{issue}</span>'
    else:
        insight_html = '<span style="background:#f0f0f0; color:#999; padding:3px 8px; border-radius:4px; font-size:10px;">General</span>'

    tiktok_url = f"https://www.tiktok.com/@{v.get('author_username', 'user')}/video/{v.get('tiktok_id', '')}"
    
    # Determine card class based on is_new
    card_class = "video-card video-card-new" if is_new else "video-card"
    extra_style = new_border_style if is_new else ""

    if compact:
        # Mini card
        html = f"""
        <div class="{card_class}" style="padding:15px; margin-bottom:10px; border:1px solid #444; background:#262730; border-radius:12px; {extra_style}">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <div style="font-weight:700; font-size:12px; color:#FAFAFA;">
                    <a href="{tiktok_url}" target="_blank" style="text-decoration:none; color:#FAFAFA; display:flex; align-items:center; gap:4px;">
                        @{v.get('author_username')} 🔗 {new_badge_html}
                    </a>
                </div>
                <div style="font-size:10px; color:#999;">{sent_score}</div>
            </div>
            <div class="badge {cls}" style="font-size:9px;">{sent_label}</div>
            <div style="width:100%; height:4px; background:#1A1A1A; border-radius:2px; margin-top:8px; overflow:hidden;">
                <div style="width:{int(sent_score)*10}%; height:100%; background:{border_color};"></div>
            </div>
        </div>
        """
    else:
        # Full detailed card
        html = f"""
        <div class="{card_class}" style="background:#262730; border:1px solid #444; border-radius:12px; padding:20px; margin-bottom:20px; box-shadow:0 2px 5px rgba(0,0,0,0.2); height:510px; display:flex; flex-direction:column; position:relative; {extra_style}">
            <div style="position:absolute; left:0; top:0; bottom:0; width:6px; background:{border_color};"></div>

            <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:15px;">
                <div style="font-weight:700; font-size:14px; color:#FAFAFA;">
                     <a href="{tiktok_url}" target="_blank" style="text-decoration:none; color:#FAFAFA; display:flex; align-items:center; gap:6px;">
                        @{v.get('author_username')}
                        <span style="font-size:12px; opacity:0.7;">🔗</span>
                        {new_badge_html}
                    </a>
                </div>
                <div class="badge {cls}">{sent_label}</div>
            </div>
            
            <div style="font-size:13px; color:#CCC; margin-bottom:15px; height:60px; overflow:hidden; line-height:1.4;">
                {desc}
            </div>
            
            <div style="background:#1A1A1A; border:1px solid #333; padding:10px; border-radius:8px; margin-bottom:10px; flex-grow:1; overflow-y:auto;">
                <div style="font-size:10px; font-weight:700; color:#888; margin-bottom:4px;">PUBLIC REACTION & TOP COMMENTS SUMMARY:</div>
                <div style="font-size:11px; color:#DDD; line-height:1.4; margin-bottom:8px;">{summary}</div>
                
                <div style="border-top:1px solid #333; padding-top:8px;">
                    <div style="font-size:9px; font-weight:700; color:#666; margin-bottom:4px;">KEYWORDS & SLANG:</div>
                    <div style="display:flex; flex-wrap:wrap; gap:4px;">
                        {keywords_html}
                    </div>
                </div>
            </div>
            
            <div style="margin-bottom:15px;">
                 <div style="font-size:10px; font-weight:700; color:#888; margin-bottom:4px;">MAIN TOPICS:</div>
                 <div style="display:flex; flex-wrap:wrap; gap:4px;">
                    {insight_html}
                 </div>
            </div>
            
            <div style="border-top:1px solid #333; padding-top:12px; display:flex; justify-content:space-between; color:#999; font-size:12px;">
                <span title="Views">👁️ {fmt_num(v.get('views_count',0))}</span>
                <span title="Likes">❤️ {fmt_num(v.get('likes_count',0))}</span>
                <span title="Comments">💬 {fmt_num(v.get('comments_count',0))}</span>
                <span title="Shares">↗️ {fmt_num(v.get('shares_count',0))}</span>
            </div>
        </div>
        """
    # Process HTML to remove extra whitespace and newlines that can break rendering
    html = "".join(line.strip() for line in html.split("\n"))
    st.markdown(html, unsafe_allow_html=True)

# ============================================
# CSS STYLING (Single Block, No Indentation Issues)
# ============================================
css_styles = """
<style>
    /* VARIABLES (DARK MODE) */
    :root {
        --bg-color: #0E1117;
        --sidebar-bg: #1E1E1E;
        --card-bg: #262730;
        --gold: #F1C40F;
        --text-dark: #FFFFFF;
        --text-light: #A0A0A0;
        --positive: #2ECC71;
        --neutral: #F39C12;
        --negative: #E74C3C;
    }
    /* Force main background to dark */
    .stApp { background-color: var(--bg-color); color: var(--text-dark); }
    header, footer, #MainMenu { visibility: hidden; }
    [data-testid="stSidebar"] { display: none; } 

    /* CUSTOM SIDEBAR */
    .custom-sidebar {
        position: fixed; left: 0; top: 0; bottom: 0; width: 80px;
        background-color: #222; z-index: 99999;
        display: flex; flex-direction: column; align-items: center; padding-top: 30px;
    }
    
    /* LOGO AREA */
    .sidebar-logo {
        margin-bottom: 15px;
        width: 40px; height: 40px;
        display: flex; justify-content: center; align-items: center;
    }

    .sidebar-ribbon::after {
        content: ''; position: absolute; bottom: -15px; left: 0;
        border-left: 18px solid transparent; border-right: 18px solid transparent;
        border-top: 15px solid #FFD700; /* Match bottom color */
    }
    /* Since gradient ends in Yellow, the bottom triangle should be Yellow. 
       However, the gradient is diagonal. The bottom cut might look weird if solid.
       A simpler approach for the "V" cut is a clip-path. */
    .sidebar-ribbon {
        width: 36px; height: 140px;
        clip-path: polygon(0 0, 100% 0, 100% 100%, 50% 88%, 0 100%);
        margin-bottom: 30px;
    }
    
    .sidebar-btn {
        width: 40px; height: 40px; margin-bottom: 20px;
        border-radius: 8px; background-color: #333;
        display: flex; justify-content: center; align-items: center;
        cursor: pointer; transition: all 0.3s ease;
        text-decoration: none; color: white !important;
    }
    .sidebar-btn:hover { background-color: var(--gold); transform: scale(1.1); }
    .sidebar-btn svg { width: 22px; height: 22px; fill: white; }
    .sidebar-btn:hover svg { fill: #222; }
    
    /* TOOLTIP */
    .sidebar-btn:hover::after {
        content: attr(data-title);
        position: absolute; left: 50px; 
        background-color: #333; color: #fff; padding: 5px 10px;
        border-radius: 4px; white-space: nowrap; font-size: 12px;
        z-index: 999999; pointer-events: none;
    }

    .sidebar-icon.active { color: var(--gold); border-left: 3px solid var(--gold); }
    .sidebar-label {
        font-size: 9px; color: #666; margin-top: -10px; margin-bottom: 20px;
        text-align: center; letter-spacing: 1px; font-weight: 700;
    }

    /* MAIN CONTENT OFFSET */
    .block-container {
        padding-left: 100px !important; padding-top: 2rem !important;
        padding-right: 2rem !important; max-width: 100% !important;
        padding-bottom: 5rem !important; /* Space for chatting widget */
    }

    /* TOP FILTER BAR */
    .filter-bar {
        background-color: #2C2C2C; padding: 15px 20px; border-radius: 8px;
        color: white; display: flex; align-items: center; margin-bottom: 20px;
    }
    .filter-label {
        color: var(--gold); font-weight: bold; margin-right: 20px;
        font-size: 12px; letter-spacing: 1px;
    }
    .filter-btn {
        font-size: 11px; padding: 6px 16px; border-radius: 4px;
        margin-right: 10px; cursor: pointer; font-weight: 600;
    }
    .filter-btn.active { background-color: var(--gold); color: #2C2C2C; }
    .filter-btn.inactive { color: #999; }

    /* CARDS */
    .dashboard-card {
        background-color: var(--card-bg); border-radius: 12px; padding: 24px;
        margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        border: 1px solid #333;
    }
    h3 {
        color: var(--text-dark); font-size: 18px; font-weight: 800;
        margin-bottom: 20px; padding: 0;
    }

    /* SENTIMENT METER */
    .meter-bar {
        height: 8px; width: 100%;
        background: linear-gradient(90deg, #E74C3C 0%, #F39C12 50%, #2ECC71 100%);
        border-radius: 4px; position: relative;
    }
    .meter-thumb {
        width: 20px; height: 20px; background: white;
        border: 4px solid #555; border-radius: 50%;
        position: absolute; top: -6px; box-shadow: 0 2px 4px rgba(0,0,0,0.5);
        transform: translateX(-50%);
    }

    /* STAT BOXES */
    .stat-box {
        border: 1px solid #444; border-radius: 8px; padding: 15px 10px;
        text-align: center; background: var(--card-bg); height: 100%;
    }
    .stat-value { font-size: 24px; font-weight: 800; color: var(--text-dark); }
    .stat-label { font-size: 10px; font-weight: 700; text-transform: uppercase; margin-top: 5px; }
    .stat-label.pos { color: #2ECC71; }
    .stat-label.neu { color: #F39C12; }
    .stat-label.neg { color: #E74C3C; }
    .stat-label.vneg { color: #C0392B; }

    /* LIST TOPICS */
    .topic-row {
        display: flex; justify-content: space-between; padding: 12px 15px;
        background: #Fcfcfc; margin-bottom: 8px; border-radius: 6px;
        border: 1px solid #F0F0F0; align-items: center;
    }
    .topic-name { font-weight: 600; color: #444; font-size: 13px; }
    .topic-count { font-size: 11px; color: #888; background: #EEE; padding: 2px 8px; border-radius: 10px; }

    /* VIDEO CARD */
    .video-card {
        background: white; border: 1px solid #EEE; border-radius: 12px;
        padding: 20px; margin-bottom: 20px; transition: transform 0.2s;
    }
    .video-card:hover { transform: translateY(-3px); box-shadow: 0 5px 15px rgba(0,0,0,0.08); }
    .badge {
        padding: 4px 10px; border-radius: 20px; font-size: 10px;
        font-weight: 800; letter-spacing: 0.5px; text-transform: uppercase;
        display: inline-block;
    }
    .badge-positive { background: rgba(46, 204, 113, 0.15); color: #2ECC71; }
    .badge-neutral { background: rgba(243, 156, 18, 0.15); color: #F39C12; }
    .badge-negative { background: rgba(231, 76, 60, 0.15); color: #E74C3C; }
    .badge-none { border: 1px solid #EEE; color: #999; }

    /* NEW video highlight animation */
    @keyframes pulse {
        0% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.8; transform: scale(1.05); }
        100% { opacity: 1; transform: scale(1); }
    }
    @keyframes glow {
        0% { box-shadow: 0 0 5px rgba(0, 212, 255, 0.5); }
        50% { box-shadow: 0 0 20px rgba(0, 212, 255, 0.8); }
        100% { box-shadow: 0 0 5px rgba(0, 212, 255, 0.5); }
    }
    .video-card-new {
        animation: glow 2s ease-in-out infinite;
        border: 2px solid #00D4FF !important;
    }
</style>
"""
st.markdown(css_styles, unsafe_allow_html=True)

# RESET DATABASE (Maintenance) & LOGS moved to main area for visibility
# ...

# ============================================
# SIDEBAR (HTML)
# ============================================
sidebar_html = """
<div class="custom-sidebar">
    <!-- LOGO -->
    <div class="sidebar-logo">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#F1C40F" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            <path d="M7 12l2.5 2.5 2.5-5 2.5 5 2.5-2.5" stroke="#E74C3C"/>
        </svg>
    </div>

    <!-- RIBBON -->
    <div class="sidebar-ribbon">
        <svg class="ribbon-star" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <!-- 9 pointed star approximation -->
            <polygon points="12,2 14.5,8.5 21.5,8.5 16,13 18.5,19.5 12,16 5.5,19.5 8,13 2.5,8.5 9.5,8.5"/>
        </svg>
    </div>

    <!-- MENU -->
    <div class="sidebar-icon active">
         <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
            <polyline points="9 22 9 12 15 12 15 22"></polyline>
        </svg>
    </div>
    <div class="sidebar-label">ANALYTICS</div>

    <div class="sidebar-icon">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="11" width="18" height="10" rx="2"></rect>
            <circle cx="12" cy="5" r="2"></circle>
            <path d="M12 7v4"></path>
            <line x1="8" y1="16" x2="8" y2="16"></line>
            <line x1="16" y1="16" x2="16" y2="16"></line>
        </svg>
    </div>
    <div class="sidebar-label">ASSISTANT</div>

    <div style="flex-grow:1"></div>
    
    <div class="sidebar-icon">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
        </svg>
    </div>
    <div class="sidebar-label">Ver 1.2</div>
</div>
"""
sidebar_html = "".join(line.strip() for line in sidebar_html.split("\n"))
st.markdown(sidebar_html, unsafe_allow_html=True)

# ============================================
# REPORT NAVIGATION
# ============================================

selected_report = "AGGREGATED OVERVIEW"
report_filter = None

if db:
    # Fetch available reports (keywords)
    try:
        available_reports = db.get_unique_keywords()
    except AttributeError:
        # Cache is stale (old db object without new method)
        st.warning("🔄 Updating system... (Clearing cache)")
        st.cache_resource.clear()
        st.rerun()
    
    # Add navigation to sidebar (using st.sidebar native or custom)
    # ============================================
    # HEADER & REPORT SELECTOR (MOVED UP)
    # ============================================

    # Main Report Selector (Top of Page)
    if available_reports:
        col_sel, col_info = st.columns([2, 3])
        with col_sel:
            options = ["AGGREGATED OVERVIEW"] + available_reports
            selected_report = st.selectbox("📑 SELECT REPORT (Topic):", options, index=0, key="report_selector_main")
            
        with col_info:
            if selected_report != "AGGREGATED OVERVIEW":
                report_filter = selected_report
                st.success(f"Viewing: **{selected_report}**")
            else:
                st.info("Viewing: **AGGREGATED OVERVIEW** (All Data)")
    else:
        st.info("💡 **Welcome!** No reports found in database. Start a scrape below to create your first analysis.")

    # ============================================
    # SCRAPER INPUT WIDGET (MOVED TO TOP)
    # ============================================
    with st.expander("🚀 Start New Analysis (Scrape Videos)", expanded=False):
            
        tab_keyword, tab_url = st.tabs(["Keyword Search", "Single Video"])
        
        mode = "keyword"
        target_input = ""
        max_vids = 5
        show_browser = False
        submitted = False
            
        # TAB 1: KEYWORD
        with tab_keyword:
            with st.form("scrape_form_keyword"):
                col_k, col_n, col_btn = st.columns([3, 1, 1])
                with col_k:
                    k_input = st.text_input("Keyword / Hashtag", placeholder="e.g. #sarawak")
                with col_n:
                    count = st.number_input("Max Videos", min_value=1, max_value=50, value=5)
                with col_btn:
                    st.markdown("<br>", unsafe_allow_html=True) 
                    submitted_k = st.form_submit_button("Start Analysis")
                
                show_browser_k = st.checkbox("Show Browser (Solve Captchas)", value=False, key="chk_k")
                
                if submitted_k:
                    mode = "keyword"
                    target_input = k_input
                    max_vids = count
                    show_browser = show_browser_k
                    submitted = True

        # TAB 2: SINGLE VIDEO
        with tab_url:
             with st.form("scrape_form_url"):
                col_u, col_btn_u = st.columns([4, 1])
                with col_u:
                    u_input = st.text_input("TikTok Video URL", placeholder="https://www.tiktok.com/@user/video/1234567890")
                with col_btn_u:
                    st.markdown("<br>", unsafe_allow_html=True) 
                    submitted_u = st.form_submit_button("Scrape Video")
                
                show_browser_u = st.checkbox("Show Browser (Solve Captchas)", value=False, key="chk_u")
                
                if submitted_u:
                    mode = "url"
                    target_input = u_input
                    max_vids = 1 # Single video
                    show_browser = show_browser_u
                    submitted = True

        if submitted and target_input:
            status_box = st.empty()

            if mode == "keyword":
                # ============================================
                # KEYWORD MODE: Subprocess (unchanged)
                # ============================================
                status_box.info(f"⏳ Scraping {max_vids} videos for '{target_input}'... Please wait.")
                cmd_args = ["--keywords", target_input, "--max", str(max_vids)]

                try:
                    import os
                    from pathlib import Path
                    import pathlib
                    current_file_path = Path(__file__).resolve()
                    if current_file_path.parent.name == "backend":
                         repo_root = current_file_path.parent.parent
                    else:
                         repo_root = current_file_path.parent

                    backend_dir = repo_root / "backend"
                    scraper_script = backend_dir / "run_scraper_job.py"

                    provider = Config.LLM_PROVIDER
                    if provider == "mistral":
                        api_key = Config.MISTRAL_API_KEY or ""
                    else:
                        api_key = Config.OPENAI_API_KEY or ""

                    base_cmd = [
                        sys.executable,
                        str(scraper_script)
                    ] + cmd_args + [
                        "--api_key", api_key,
                        "--provider", provider
                    ]

                    if show_browser:
                        base_cmd.append("--visible")

                    cmd = base_cmd

                    env = os.environ.copy()
                    env["SUPABASE_URL"] = Config.SUPABASE_URL or ""
                    env["SUPABASE_SERVICE_ROLE_KEY"] = Config.SUPABASE_SERVICE_ROLE_KEY or ""
                    env["SUPABASE_ANON_KEY"] = Config.SUPABASE_ANON_KEY or ""
                    env["OPENAI_API_KEY"] = Config.OPENAI_API_KEY or ""
                    env["PYTHONPATH"] = str(backend_dir)

                    with st.spinner(f"Running analysis for '{target_input}'... This may take a minute."):
                        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(backend_dir), env=env)

                        debug_img_path = backend_dir / "search_debug.png"
                        found_videos = "0 scraped" not in result.stdout and "found: 0" not in result.stdout.lower()

                        with st.expander("View Analysis Logs", expanded=not found_videos or result.returncode != 0):
                            st.code(result.stdout + "\n" + result.stderr)

                            if debug_img_path.exists():
                                st.error("📸 Scraper reached TikTok but may be blocked. Check the screenshot below.")
                                st.image(str(debug_img_path), caption="What the scraper saw", use_container_width=True)
                                st.info("💡 TIP: If you see a puzzle captcha, try running with 'Show Browser' checked and solve it manually.")

                        combined_output = result.stdout + "\n" + result.stderr
                        st.session_state["last_logs"] = combined_output

                        if result.returncode == 0:
                            if found_videos:
                                try:
                                    import re
                                    json_matches = re.findall(r'\{[^{}]*"status"[^{}]*\}', result.stdout, re.DOTALL)
                                    if json_matches:
                                        last_json = json_matches[-1]
                                        result_data = json.loads(last_json)
                                        newly_scraped = result_data.get('video_ids', [])
                                        if newly_scraped:
                                            st.session_state["newly_scraped_ids"] = newly_scraped
                                            st.session_state["scrape_timestamp"] = time.time()
                                except:
                                    pass

                                status_box.success("✅ Analysis Complete! Refreshing dashboard...")
                                st.cache_data.clear()
                                st.cache_resource.clear()
                                time.sleep(1)
                                st.rerun()
                            else:
                                status_box.warning("⚠️ Scraper finished but found 0 videos. See logs/screenshot above.")
                        else:
                            status_box.error(f"❌ Error during scrape: Check logs below.")
                except Exception as e:
                    st.error(f"❌ Execution failed: {e}")

            else:
                # ============================================
                # SINGLE VIDEO MODE: Flask API call
                # ============================================
                status_box.info(f"⏳ Analyzing Single Video via API... Please wait (this may take up to 2 minutes).")

                try:
                    # Determine Flask API URL
                    api_port = int(os.getenv("PORT", os.getenv("API_PORT", "5000")))
                    api_host = os.getenv("API_HOST", "127.0.0.1")
                    # 0.0.0.0 is a server bind address, not a client connect address
                    if api_host == "0.0.0.0":
                        api_host = "127.0.0.1"
                    # For Railway/production, use BACKEND_URL if set
                    backend_url = os.getenv("BACKEND_URL", f"http://{api_host}:{api_port}")
                    api_endpoint = f"{backend_url}/api/scrape/single-video"

                    # Step progress display
                    step_container = st.container()

                    with st.spinner(f"Scraping and analyzing video... This may take a minute."):
                        response = requests.post(
                            api_endpoint,
                            json={"url": target_input},
                            timeout=150  # 2.5 min timeout for scrape+analyze
                        )

                        result_data = response.json()

                        # Display step-by-step progress log
                        steps = result_data.get("steps", [])
                        if steps:
                            with step_container:
                                st.markdown("#### 📋 Processing Steps")
                                for step_info in steps:
                                    step_num = step_info.get("step", "?")
                                    step_name = step_info.get("name", "Unknown")
                                    step_status = step_info.get("status", "unknown")
                                    step_detail = step_info.get("detail", "")
                                    step_dur = step_info.get("duration", 0)

                                    # Status icon
                                    if step_status in ("success", "completed", "updated"):
                                        icon = "✅"
                                    elif step_status in ("failed", "error"):
                                        icon = "❌"
                                    elif step_status == "skipped":
                                        icon = "⏭️"
                                    elif step_status in ("exists", "not_found", "no_data"):
                                        icon = "ℹ️"
                                    else:
                                        icon = "⏳"

                                    st.markdown(
                                        f"`Step {step_num}` {icon} **{step_name}** — {step_detail} "
                                        f"<span style='color:#666; font-size:11px;'>({step_dur}s)</span>",
                                        unsafe_allow_html=True
                                    )

                        # Store logs
                        st.session_state["last_logs"] = json.dumps(result_data, indent=2, default=str)

                        if response.status_code == 200 and result_data.get("status") == "completed":
                            video_id = result_data.get("video_id")
                            video_data = result_data.get("video", {})
                            total_dur = result_data.get("total_duration", 0)

                            # Store newly scraped ID for highlighting
                            if video_id:
                                st.session_state["newly_scraped_ids"] = [video_id]
                                st.session_state["scrape_timestamp"] = time.time()

                            # Show result card
                            st.success(f"✅ Analysis Complete in {total_dur}s! Video saved to database.")

                            # Display video result card
                            sent_data = video_data.get("sentiment", {})
                            sentiment_label = sent_data.get("sentiment", "N/A") if sent_data else "N/A"
                            sentiment_score = sent_data.get("sentimentScore", 5) if sent_data else 5
                            summary = sent_data.get("summary", "No summary available.") if sent_data else "No summary available."

                            # Sentiment color
                            if "Positive" in str(sentiment_label):
                                sent_color = "#2ECC71"
                            elif "Negative" in str(sentiment_label):
                                sent_color = "#E74C3C"
                            else:
                                sent_color = "#F39C12"

                            score_pct = min(max((int(sentiment_score) if sentiment_score else 5) * 10, 5), 95)

                            author = video_data.get("authorUsername", "Unknown")
                            desc = video_data.get("description", "No description")
                            views = video_data.get("viewsCount", 0)
                            likes = video_data.get("likesCount", 0)
                            comments_ct = video_data.get("commentsCount", 0)
                            shares = video_data.get("sharesCount", 0)

                            key_issues = sent_data.get("keyIssues", []) if sent_data else []
                            issues_html = ""
                            if isinstance(key_issues, list):
                                for ki in key_issues[:5]:
                                    issues_html += f'<span style="background:#FFF3E0; color:#E67E22; padding:3px 8px; border-radius:4px; font-size:10px; font-weight:600; margin-right:4px;">{ki}</span>'

                            result_card_html = f"""
                            <div style="background:#262730; border:2px solid {sent_color}; border-radius:12px; padding:20px; margin:15px 0; box-shadow:0 0 15px {sent_color}40;">
                                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
                                    <div style="font-weight:700; font-size:16px; color:#FAFAFA;">@{author}</div>
                                    <span style="background:{sent_color}25; color:{sent_color}; padding:5px 12px; border-radius:20px; font-weight:800; font-size:11px; letter-spacing:0.5px;">{str(sentiment_label).upper()}</span>
                                </div>
                                <div style="font-size:13px; color:#CCC; margin-bottom:12px; line-height:1.4;">{str(desc)[:200]}</div>
                                <div style="background:#1A1A1A; padding:12px; border-radius:8px; margin-bottom:12px;">
                                    <div style="font-size:10px; font-weight:700; color:#888; margin-bottom:6px;">SENTIMENT SCORE</div>
                                    <div style="width:100%; height:8px; background:#333; border-radius:4px; overflow:hidden;">
                                        <div style="width:{score_pct}%; height:100%; background:linear-gradient(90deg, #E74C3C 0%, #F39C12 50%, #2ECC71 100%); border-radius:4px;"></div>
                                    </div>
                                    <div style="font-size:11px; color:#AAA; margin-top:4px;">{sentiment_score}/10</div>
                                </div>
                                <div style="background:#1A1A1A; padding:12px; border-radius:8px; margin-bottom:12px;">
                                    <div style="font-size:10px; font-weight:700; color:#888; margin-bottom:6px;">AI SUMMARY</div>
                                    <div style="font-size:12px; color:#DDD; line-height:1.5;">{summary}</div>
                                </div>
                                <div style="margin-bottom:12px;">
                                    <div style="font-size:10px; font-weight:700; color:#888; margin-bottom:6px;">KEY ISSUES</div>
                                    <div style="display:flex; flex-wrap:wrap; gap:4px;">{issues_html}</div>
                                </div>
                                <div style="display:flex; justify-content:space-between; color:#999; font-size:12px; border-top:1px solid #333; padding-top:10px;">
                                    <span>👁️ {fmt_num(views)}</span>
                                    <span>❤️ {fmt_num(likes)}</span>
                                    <span>💬 {fmt_num(comments_ct)}</span>
                                    <span>↗️ {fmt_num(shares)}</span>
                                </div>
                            </div>
                            """
                            result_card_html = "".join(line.strip() for line in result_card_html.split("\n"))
                            st.markdown(result_card_html, unsafe_allow_html=True)

                            # Refresh button
                            if st.button("🔄 Refresh Dashboard to See New Video"):
                                st.cache_data.clear()
                                st.cache_resource.clear()
                                st.rerun()

                        elif result_data.get("status") == "partial":
                            status_box.warning(f"⚠️ Partial result: Video scraped but some steps failed. Check steps above.")

                        else:
                            error_msg = result_data.get("error", "Unknown error")
                            status_box.error(f"❌ Analysis failed: {error_msg}")

                except requests.exceptions.ConnectionError:
                    status_box.error("❌ Cannot connect to Flask API backend. Make sure it's running on the expected port.")
                    st.info(f"💡 Expected backend at: {api_endpoint if 'api_endpoint' in dir() else 'http://127.0.0.1:5000'}")
                except requests.exceptions.Timeout:
                    status_box.error("❌ Request timed out. The video may be taking too long to scrape.")
                except Exception as e:
                    status_box.error(f"❌ Error: {e}")
                    st.session_state["last_logs"] = str(e)



# ============================================
# DATA LOADING
# ============================================
overview = None
videos = []
if db:
    # Pass report_filter to analytics methods
    overview = db.get_sentiment_overview(days=365, keyword=report_filter)
    
    # get_recent_videos supports keyword filter
    videos = db.get_recent_videos(days=365, include_sentiment=True, limit=50, keyword=report_filter)
    
    # -----------------------------------------------
    # DOUBLE FAILSAFE: App-Level Filtering
    # -----------------------------------------------
    if report_filter and videos:
        # Strict check: Remove any video that doesn't match the report filter exactly
        initial_count = len(videos)
        videos = [v for v in videos if v.get('search_keyword') == report_filter]
        final_count = len(videos)
        
        # DEBUG SENSOR
        if initial_count != final_count:
            st.toast(f"🛡️ Security System: Blocked {initial_count - final_count} leaking videos.", icon="🛡️")

    # Debug Data Panel (Hidden by default)
    with st.expander("🛠️ Debug Data (Filter Status)", expanded=False):
        st.write(f"Active Report Filter: **{report_filter}**")
        st.write(f"Videos Loaded: {len(videos)}")
        if videos:
            st.write(f"Sample Source: {videos[0].get('search_keyword')}")


if not overview:
    overview = {"total_videos": 0, "total_analyzed": 0, "avg_sentiment": 5, "total_views": 0, "sentiment_breakdown": {}}

# Helper to check if video is newly scraped (within last 5 minutes)
def is_video_new(video_id):
    """Check if a video was just scraped based on session state"""
    newly_scraped = st.session_state.get("newly_scraped_ids", [])
    scrape_time = st.session_state.get("scrape_timestamp", 0)
    # Only highlight if scraped within last 5 minutes
    if time.time() - scrape_time > 300:
        return False
    return video_id in newly_scraped

# Show notification if there are newly scraped videos
newly_scraped_ids = st.session_state.get("newly_scraped_ids", [])
scrape_timestamp = st.session_state.get("scrape_timestamp", 0)
if newly_scraped_ids and (time.time() - scrape_timestamp < 300):
    # Count how many newly scraped videos are in the current view
    new_in_view = sum(1 for v in videos if v.get('id') in newly_scraped_ids)
    if new_in_view > 0:
        st.toast(f"[NEW] {new_in_view} newly scraped video(s) highlighted below!", icon="✨")

total_views = overview.get('total_views', 0)
total_likes = sum(v.get('likes_count', 0) for v in videos)
analyzed_videos = overview.get('total_analyzed', 0)
avg_sentiment = overview.get('avg_sentiment', 5)

# ============================================
# HEADER
# ============================================
# Helper placeholder
# Header moved up to line 300


filter_html = """
<div class="filter-bar">
    <span class="filter-label">TIME PERIOD:</span>
    <span class="filter-btn active">ALL TIME</span>
    <span class="filter-btn inactive">TODAY</span>
    <span class="filter-btn inactive">7 DAYS</span>
    <span class="filter-btn inactive">30 DAYS</span>
</div>
"""
st.markdown(filter_html, unsafe_allow_html=True)

# ============================================
# MAIN LAYOUT
# ============================================

# SETTINGS & MAINTENANCE (Collapsible)
with st.expander("⚙️ Settings & Maintenance (Reset Database)", expanded=False):
    col_m1, col_m2 = st.columns([1, 1])
    with col_m1:
        st.markdown('<div style="font-size:12px; font-weight:700; color:#555; margin-bottom:10px;">DESTRUCTIVE ACTIONS</div>', unsafe_allow_html=True)
        
        # 1. Selective Delete
        if available_reports:
            del_option = st.selectbox("Delete Specific Report", ["Select..."] + available_reports, label_visibility="collapsed")
            if del_option != "Select...":
                 if st.button(f"🗑️ Delete '{del_option}' Data", type="primary"):
                    st.cache_resource.clear()
                    db = get_database() # Refresh client
                    if db:
                         with st.spinner(f"Deleting '{del_option}'..."):
                            if db.delete_report_data(del_option):
                                st.success(f"Deleted '{del_option}'!")
                                time.sleep(1)
                                st.cache_data.clear()
                                st.cache_resource.clear()
                                st.rerun()
                            else:
                                st.error("Deletion failed.")

        st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)
        
        # 2. Full Reset
        st.warning("⚠️ **Reset All Data**")
        if st.button("☣️ ERASE ENTIRE DATABASE", type="primary", help="Permanently delete ALL videos and analysis."):
             # Force reload DB client to ensure 'clear_all_data' method exists (busting cache)
             st.cache_resource.clear()
             db = get_database()
             
             if db:
                with st.spinner("Clearing database..."):
                    success = db.clear_all_data()
                    if success:
                        st.success("✅ Database cleared!")
                        time.sleep(1)
                        st.cache_data.clear()
                        st.cache_resource.clear()
                        st.rerun()
                    else:
                        st.error("Failed to clear database.")
             else:
                st.error("Database not connected.")
    with col_m2:
        st.info("ℹ️ **Debug Logs**")
        if "last_logs" in st.session_state:
            st.code(st.session_state["last_logs"][-1000:], language="text")
        else:
            st.write("No logs available.")

col_left, col_right = st.columns([6, 4])

# --- LEFT COLUMN ---
with col_left:

    # AUTOMATED MONITOR CONFIG WIDGET
    with st.expander("🤖 Automated Monitoring Settings", expanded=False):
        MONITOR_CONFIG_FILE = "monitor_config.json"
        
        def load_monitor_config():
            if not os.path.exists(MONITOR_CONFIG_FILE):
                return {"keywords": [], "interval_hours": 24, "start_time": "09:00"}
            try:
                with open(MONITOR_CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except:
                return {}

        def save_monitor_config(cfg):
            with open(MONITOR_CONFIG_FILE, 'w') as f:
                json.dump(cfg, f, indent=4)

        current_config = load_monitor_config()
        current_keywords = ", ".join(current_config.get("keywords", []))
        
        with st.form("monitor_settings"):
            st.markdown('<div style="font-size:12px; font-weight:700; color:#555; margin-bottom:5px;">Daily Keywords (Comma Separated)</div>', unsafe_allow_html=True)
            new_keywords_str = st.text_area("Keywords", value=current_keywords, height=100, label_visibility="collapsed")
            
            c_time, c_int = st.columns(2)
            with c_time:
                new_start_time = st.text_input("Start Time (24h)", value=current_config.get("start_time", "09:00"))
            with c_int:
                st.markdown('<div style="font-size:12px; color:#999; margin-top:35px;">Runs daily at this time</div>', unsafe_allow_html=True)
                
            submitted_cfg = st.form_submit_button("💾 Save Settings")
            
            if submitted_cfg:
                # Parse keywords
                k_list = [k.strip() for k in new_keywords_str.split(",") if k.strip()]
                current_config["keywords"] = k_list
                current_config["start_time"] = new_start_time
                save_monitor_config(current_config)
                st.success(f"✅ Settings Saved! Monitor will check {len(k_list)} keywords daily at {new_start_time}.")
                st.info("Note: If the monitor script is running, restart it to apply schedule changes immediately.")

    st.markdown('<div style="font-size:11px; font-weight:700; color:#999; margin-bottom:10px; letter-spacing:1px;">OVERVIEW OF PUBLIC SENTIMENT</div>', unsafe_allow_html=True)
    
    sentiment_label = "Neutral"
    if avg_sentiment > 6: sentiment_label = "Positive"
    elif avg_sentiment < 4: sentiment_label = "Negative"
    
    meter_percent = min(max((avg_sentiment / 10) * 100, 5), 95)
    
    
    # Get Key Issues
    key_issues = db.get_top_issues(days=365, limit=5, keyword=report_filter)
    issues_html = ""
    if key_issues:
        for issue in key_issues:
            issues_html += f'<div style="color:#7F8C8D; font-size:13px; margin-bottom:12px; border-bottom:1px solid #F0F0F0; padding-bottom:8px;">{issue["issue"]}</div>'
    else:
        issues_html = '<div style="color:#BDC3C7; font-size:13px; font-style:italic;">No key issues identified yet.</div>'

    report_title = "Briefing Summary"
    if report_filter:
        report_title = f"Report: {report_filter}"

    briefing_html = f"""<div class="dashboard-card">
    <div style="font-size:11px; font-weight:800; color:#F39C12; text-transform:uppercase; letter-spacing:1px; margin-bottom:15px;">
        <span style="border-left:3px solid #F39C12; padding-left:8px;">{sentiment_label}</span>
    </div>
    <h3 style="margin-top:0;">{report_title}</h3>
    <p style="color:#777; font-size:14px; line-height:1.6; margin-bottom:30px;">
        Analysis based on <b>{analyzed_videos} analyzed videos</b> from <b>{overview.get('total_videos')} total videos</b> over the past period.
        <br>Public sentiment is currently leaning <b>{sentiment_label.lower()}</b>.
    </p>
    <div style="background:#F9F9F9; padding:20px; border-radius:12px; margin-bottom: 25px;">
        <div style="font-size:10px; font-weight:800; color:#AAA; margin-bottom:5px; text-transform:uppercase;">OVERALL SENTIMENT</div>
        <div style="font-size:16px; font-weight:800; color:#333; margin-bottom:15px;">{sentiment_label}</div>
        <div class="meter-bar">
            <div class="meter-thumb" style="left: {meter_percent}%;"></div>
        </div>
    </div>
    <h4 style="font-size:14px; font-weight:800; color:#2C3E50; margin-bottom:15px;">Key Issues</h4>
    <div style="padding-left: 5px;">
        {issues_html}
    </div>
</div>"""
    st.markdown(briefing_html, unsafe_allow_html=True)
    
    st.markdown("<h3>Detailed Sentiment Breakdown</h3>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    bd = overview.get('sentiment_breakdown', {})
    
    with c1: st.markdown(f'<div class="stat-box"><div class="stat-value">{bd.get("Positive", 0)}</div><div class="stat-label pos">Positive</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="stat-box"><div class="stat-value">{bd.get("Neutral", 0) + bd.get("Mixed", 0)}</div><div class="stat-label neu">Neutral</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="stat-box"><div class="stat-value">{bd.get("Negative", 0)}</div><div class="stat-label neg">Negative</div></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="stat-box"><div class="stat-value">{bd.get("Very Negative", 0)}</div><div class="stat-label vneg">Very Negative</div></div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("<h3>MOST DISCUSSED TOPICS</h3>", unsafe_allow_html=True)
    st.markdown('<div class="dashboard-card" style="padding:10px;">', unsafe_allow_html=True)
    topics = db.get_top_hashtags(30, 5, keyword=report_filter) if db else []
    if topics:
        for t in topics:
            st.markdown(f'<div class="topic-row"><div class="topic-name">{t["hashtag"]}</div><div class="topic-count">{t["video_count"]} videos</div></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="padding:20px; text-align:center; color:#AAA;">No topics data</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # RECENT VIDEOS (Moved to Left Column)
    st.markdown("<h3>Recent Analyzed Videos</h3>", unsafe_allow_html=True)
    
    def fmt_num(n):
        if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
        if n >= 1_000: return f"{n/1_000:.1f}K"
        return str(n)

    for v in videos[:3]:
        render_video_card(v, compact=True, is_new=is_video_new(v.get('id')))

    # METRICS ROW
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Calculate Metrics
    m_total = analyzed_videos
    
    bd = overview.get('sentiment_breakdown', {})
    m_pos_count = bd.get('Positive', 0)
    m_pos_pct = int((m_pos_count / m_total * 100)) if m_total > 0 else 0
    
    m_trending = len(topics) if topics else 0
    m_issues = len(key_issues) if key_issues else 0
    
    metrics_html = f"""
    <div style="display:flex; justify-content:space-between; gap:10px;">
        <div style="flex:1; background:white; border-radius:12px; padding:15px; border:1px solid #EEE; display:flex; align-items:center;">
            <div style="width:40px; height:40px; background:#E8F8F5; border-radius:8px; display:flex; justify-content:center; align-items:center; margin-right:12px; font-size:20px; color:#2ECC71;">👍</div>
            <div>
                <div style="font-size:18px; font-weight:800; color:#333; line-height:1;">{m_total}</div>
                <div style="font-size:10px; color:#999; margin-top:2px;">Total Videos Analyzed</div>
            </div>
        </div>
        
        <div style="flex:1; background:white; border-radius:12px; padding:15px; border:1px solid #EEE; display:flex; align-items:center;">
            <div style="width:40px; height:40px; background:#FFF9E6; border-radius:8px; display:flex; justify-content:center; align-items:center; margin-right:12px; font-size:20px; color:#F39C12;">📊</div>
            <div>
                <div style="font-size:18px; font-weight:800; color:#333; line-height:1;">{m_pos_pct}%</div>
                <div style="font-size:10px; color:#999; margin-top:2px;">Positive Sentiment</div>
            </div>
        </div>
        
        <div style="flex:1; background:white; border-radius:12px; padding:15px; border:1px solid #EEE; display:flex; align-items:center;">
            <div style="width:40px; height:40px; background:#FFF0E6; border-radius:8px; display:flex; justify-content:center; align-items:center; margin-right:12px; font-size:20px; color:#E67E22;">🔥</div>
            <div>
                <div style="font-size:18px; font-weight:800; color:#333; line-height:1;">{m_trending}</div>
                <div style="font-size:10px; color:#999; margin-top:2px;">Trending Topics</div>
            </div>
        </div>
        
        <div style="flex:1; background:white; border-radius:12px; padding:15px; border:1px solid #EEE; display:flex; align-items:center;">
            <div style="width:40px; height:40px; background:#FDEDEC; border-radius:8px; display:flex; justify-content:center; align-items:center; margin-right:12px; font-size:20px; color:#E74C3C;">⚠️</div>
            <div>
                <div style="font-size:18px; font-weight:800; color:#333; line-height:1;">{m_issues}</div>
                <div style="font-size:10px; color:#999; margin-top:2px;">Critical Issues</div>
            </div>
        </div>
    </div>
    """
    metrics_html = "".join(line.strip() for line in metrics_html.split("\n"))
    st.markdown(metrics_html, unsafe_allow_html=True)

# --- RIGHT ---
with col_right:
    st.markdown('<div style="font-size:11px; font-weight:700; color:#999; margin-bottom:10px; letter-spacing:1px;">NEWS AND SOCIAL MEDIA</div>', unsafe_allow_html=True)
    
    def fmt_num(n):
        if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
        if n >= 1_000: return f"{n/1_000:.1f}K"
        return str(n)

    reach_html = f"""
    <div class="dashboard-card" style="display:flex; align-items:center;">
        <div style="width:60px; height:60px; background:#FFEAA7; border-radius:12px; display:flex; justify-content:center; align-items:center; margin-right:20px; font-size:24px;">📹</div>
        <div>
            <div style="font-size:18px; font-weight:800; color:#333;">Reach</div>
            <div style="font-size:13px; color:#888;">{fmt_num(total_views)} Views <span style="margin:0 5px;">|</span> {fmt_num(total_likes)} Likes</div>
        </div>
    </div>
    """
    reach_html = "".join(line.strip() for line in reach_html.split("\n"))
    st.markdown(reach_html, unsafe_allow_html=True)
    
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    if analyzed_videos > 0:
        labels = ['Positive', 'Negative', 'Neutral']
        bd = overview.get('sentiment_breakdown', {})
        v_pos = bd.get('Positive', 0)
        v_neg = bd.get('Negative', 0) + bd.get('Very Negative', 0)
        v_neu = bd.get('Neutral', 0) + bd.get('Mixed', 0)
        
        fig = go.Figure(data=[go.Pie(labels=labels, values=[v_pos, v_neg, v_neu], hole=.65, marker_colors=['#2ECC71', '#E74C3C', '#F39C12'], textinfo='none')])
        fig.update_layout(showlegend=True, height=180, margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(f'<div style="margin-top:20px;"><div style="font-weight:700; font-size:14px; margin-bottom:5px;">Social Media Summary</div><div style="font-size:12px; color:#777;">Analyzed {analyzed_videos} videos.<br><a href="#" style="color:#3498DB; text-decoration:none;">Read More</a></div></div>', unsafe_allow_html=True)
    else:
        st.info("No scraped data to visualize.")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div style="font-size:11px; font-weight:700; color:#999; margin-bottom:10px; letter-spacing:1px;">DETAILED ANALYSIS FEED</div>', unsafe_allow_html=True)
    
    # Render detailed cards
    if videos:
        for v in videos[:5]:
            render_video_card(v, is_new=is_video_new(v.get('id')))
    else:
        st.info("No analysis data available yet. Run a scrape to populate!")


# ============================================
# FOOTER EXPLORER SECTION
# ============================================
st.markdown("<br><br><hr style='border-top: 1px solid #EEE;'><br>", unsafe_allow_html=True)

# 1. HEADER & SEARCH
st.markdown(f"<h3>🎥 Recent Videos <span style='font-size:14px; color:#999; font-weight:400; margin-left:10px;'>{len(videos)} videos total</span></h3>", unsafe_allow_html=True)

search_term = st.text_input("", placeholder="🔍 Search videos, authors, hashtags...", label_visibility="collapsed")

# 2. FILTERS
f_col1, f_col2, f_col3 = st.columns([2, 5, 2])
with f_col1:
    filter_sentiment = st.selectbox("🙂 Sentiment:", ["All Sentiments", "Positive", "Neutral", "Negative", "Very Negative", "Not Analyzed"])
with f_col3:
    sort_option = st.selectbox("🔃 Sort by:", ["Most Recent", "Most Views", "Most Likes", "Highest Engagement"])

# 3. FILTERING LOGIC
filtered_videos = videos.copy()

# Search
if search_term:
    term = search_term.lower()
    filtered_videos = [v for v in filtered_videos if term in v.get('description', '').lower() or term in v.get('author_username', '').lower() or term in v.get('search_keyword', '').lower()]

# Sentiment
if filter_sentiment != "All Sentiments":
    filtered_videos = [v for v in filtered_videos if filter_sentiment.lower() in str(v.get('sentiment', '')).lower()]

# Sort
if sort_option == "Most Recent":
    pass # Already sorted by default
elif sort_option == "Most Views":
    filtered_videos.sort(key=lambda x: x.get('views_count', 0), reverse=True)
elif sort_option == "Most Likes":
    filtered_videos.sort(key=lambda x: x.get('likes_count', 0), reverse=True)
elif sort_option == "Highest Engagement":
    filtered_videos.sort(key=lambda x: x.get('stats_digg_count', 0) + x.get('stats_comment_count', 0) + x.get('stats_share_count', 0), reverse=True)

# 4. VIDEO GRID
st.markdown("<br>", unsafe_allow_html=True)

if not filtered_videos:
    st.warning("No videos found matching your criteria.")
else:
    # chunk into rows of 3
    cols = st.columns(3)
    for idx, v in enumerate(filtered_videos):
        col = cols[idx % 3]
        with col:
            render_video_card(v, is_new=is_video_new(v.get('id')))

# 5. FLOATING CHAT WIDGET
# ============================================
# BUMI AI ASSISTANT
# ============================================

# Initialize Session State
if "chat_messages" not in st.session_state:
    st.session_state["chat_messages"] = [
        {"role": "assistant", "content": "Hello! I am Bumi, your Sarawak Sentiment AI. Ask me anything about the latest trends!"}
    ]

# We will use st.popover (Streamlit 1.33+) or a simple expander in the sidebar for the chat interface
# Given the user wants a "Floating Assistant", we can use `st.popover` if available, or just a bottom container.
# Let's try to mimic the design in the screenshot - a popup.
# Since Custom CSS floating elements are hard to interact with in Streamlit (event loop),
# We will use a dedicated "Assistant" tab in the sidebar OR a bottom expander.
# The user's screenshot showed a popup. The best native way is `st.popover("Chat", help="Open Assistant")`.

st.markdown("""
<style>
/* Floating Chat Button Style */
div[data-testid="stPopover"] {
    position: fixed;
    bottom: 30px;
    right: 30px;
    z-index: 1000;
}
div[data-testid="stPopover"] button {
    background-color: #F1C40F;
    color: #333;
    border: none;
    border-radius: 50%;
    width: 60px;
    height: 60px;
    font-size: 24px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    transition: transform 0.2s;
}
div[data-testid="stPopover"] button:hover {
    transform: scale(1.1);
    background-color: #F9E79F;
}
</style>
""", unsafe_allow_html=True)

# Context Retrieval Function
def get_rag_context(local_videos, local_issues, local_filter):
    """Generates RICH context from filtered dashboard data"""
    
    # Defaults
    if not local_videos: local_videos = []
    if not local_issues: local_issues = []
    current_topic = local_filter or "General/All Data"
    
    # Calculate Stats
    total_vids = len(local_videos)
    total_views = sum(v.get('views_count', 0) for v in local_videos)
    avg_score = sum(v.get('sentiment_score', 0) for v in local_videos) / total_vids if total_vids > 0 else 0
    
    # Format Issues
    issues_text = "\n".join([f"- {i['issue']} (Trend: {i.get('trend','stable')})" for i in local_issues[:5]])
    
    # Format Video Summaries (Rich Data)
    # We take top 15 videos to fit in context window (approx 200 tokens each = 3000 tokens)
    video_summaries = []
    for i, v in enumerate(local_videos[:15]):
        summ = v.get('summary', 'N/A')
        if not summ or summ == "N/A": 
             summ = v.get('description', '')
        
        video_summaries.append(
            f"Video {i+1}: '{v.get('topic', 'Unknown')}' | Sentiment: {v.get('sentiment')} | Views: {v.get('views_count')} | Summary: {summ[:200]}..."
        )
    
    videos_block = "\n".join(video_summaries)
    
    context = f"""
    CURRENT REPORT: {current_topic}
    
    METRICS:
    - Analyzed Videos: {total_vids}
    - Total Engagement: {total_views} views
    - Average Sentiment: {avg_score:.1f}/10
    
    KEY ISSUES IDENTIFIED:
    {issues_text}
    
    DETAILED VIDEO ANALYSIS (Top 15):
    {videos_block}
    """
    return context

# Floating Chat Widget implementation using Popover
with st.popover("💬", help="Bumi AI Assistant"):
    st.markdown("### 🤖 BUMI AI Assistant")
    st.markdown("Ask me about the sentiment data!")
    
    # Message Container
    messages = st.container(height=300)
    for msg in st.session_state["chat_messages"]:
        messages.chat_message(msg["role"]).write(msg["content"])
        
    # Chat Input
    if prompt := st.chat_input("Ask Bumi...", key="chat_input_popover"):
        st.session_state["chat_messages"].append({"role": "user", "content": prompt})
        messages.chat_message("user").write(prompt)
        
        # Generate Response
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            response_text = "⚠️ OpenAI API Key missing. Please check .env file."
            st.session_state["chat_messages"].append({"role": "assistant", "content": response_text})
            messages.chat_message("assistant").write(response_text)
        else:
            try:
                client = OpenAI(api_key=api_key)
                
                # PASS LOCAL VARIABLES DIRECTLY (No Globals)
                context_data = get_rag_context(videos, key_issues, report_filter)
                
                full_prompt = [
                   {"role": "system", "content": f"You are Bumi, an expert AI analyst. Use the provided Context Data to answer questions about: {report_filter or 'the data'}. \n\nRULES:\n1. Use specific video examples from the context.\n2. Cite view counts to justify trends.\n3. Be concise but insightful.\n\nCONTEXT:\n{context_data}"},
                   {"role": "user", "content": prompt}
                ]
                
                stream = client.chat.completions.create(
                    model="gpt-4o",
                    messages=full_prompt,
                    stream=True,
                )
                response = messages.chat_message("assistant").write_stream(stream)
                st.session_state["chat_messages"].append({"role": "assistant", "content": response})
                
            except Exception as e:
                err_msg = f"Error: {e}"
                st.session_state["chat_messages"].append({"role": "assistant", "content": err_msg})
                messages.chat_message("assistant").write(err_msg)


