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
    st.success("✅ **SYSTEM UPDATED v3.1:** Detailed Summarization & Insights Engine Online")

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

# ============================================
# CSS STYLING (Single Block, No Indentation Issues)
# ============================================
css_styles = """
<style>
    /* VARIABLES */
    :root {
        --bg-color: #F8F5F2;
        --sidebar-bg: #1E1E1E;
        --card-bg: #FFFFFF;
        --gold: #F1C40F;
        --text-dark: #2C3E50;
        --text-light: #7F8C8D;
        --positive: #2ECC71;
        --neutral: #F39C12;
        --negative: #E74C3C;
    }
    .stApp { background-color: var(--bg-color); }
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
        margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        border: 1px solid #EAEAEA;
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
        border: 4px solid #BDC3C7; border-radius: 50%;
        position: absolute; top: -6px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        transform: translateX(-50%);
    }

    /* STAT BOXES */
    .stat-box {
        border: 1px solid #EEE; border-radius: 8px; padding: 15px 10px;
        text-align: center; background: white; height: 100%;
    }
    .stat-value { font-size: 24px; font-weight: 800; color: #333; }
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
    if db and available_reports:
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
        st.warning("Database not connected or no reports available.")



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

# --- LEFT ---
with col_left:
    # SCRAPER INPUT WIDGET
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
                status_box.info(f"⏳ Scraping {max_vids} videos for '{target_input}'... Please wait.")
                cmd_args = ["--keywords", target_input, "--max", str(max_vids)]
            else:
                status_box.info(f"⏳ Scraping Single Video... Please wait.")
                cmd_args = ["--urls", target_input]

            try:
                # Run the scraper script as a subprocess
                # Fix: Use absolute path relative to this file to find run_scraper_job.py in root
                import os
                from pathlib import Path
                
                # Get repo root (parent of backend/)
                repo_root = Path(__file__).resolve().parent.parent
                backend_dir = repo_root / "backend"
                scraper_script = backend_dir / "run_scraper_job.py"
                
                base_cmd = [
                    sys.executable, 
                    str(scraper_script)
                ] + cmd_args + [
                    "--openai_key", Config.OPENAI_API_KEY or ""  # Force explicit key pass
                ]
                
                if show_browser:
                    base_cmd.append("--visible")
                
                cmd = base_cmd # Alias for clarity
                
                # Prepare environment for subprocess (Critical for Cloud)
                # Pass explicit secrets because standalone script can't read st.secrets
                env = os.environ.copy()
                env["SUPABASE_URL"] = Config.SUPABASE_URL or ""
                env["SUPABASE_SERVICE_ROLE_KEY"] = Config.SUPABASE_SERVICE_ROLE_KEY or ""
                env["SUPABASE_ANON_KEY"] = Config.SUPABASE_ANON_KEY or ""
                env["OPENAI_API_KEY"] = Config.OPENAI_API_KEY or ""
                # Also ensure PYTHONPATH includes backend for imports if needed
                env["PYTHONPATH"] = str(backend_dir)
                
                with st.spinner(f"Running analysis for '{target_input}'... This may take a minute."):
                    # Run in backend dir so imports work
                    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(backend_dir), env=env)
                
                # Check for debug screenshot from scraper
                debug_img_path = backend_dir / "search_debug.png"
                found_videos = "0 scraped" not in result.stdout and "found: 0" not in result.stdout.lower()
                
                # Auto-expand logs if issue detected
                with st.expander("View Analysis Logs", expanded=not found_videos or result.returncode != 0):
                    st.code(result.stdout + "\n" + result.stderr)
                    
                    if debug_img_path.exists():
                        st.error("📸 Debug Screenshot Captured (Scraper blocked or empty results):")
                        st.image(str(debug_img_path), caption="What the scraper saw", use_container_width=True)

                # DEBUG: Extract OpenAI Key info from logs to show user
                combined_output = result.stdout + "\n" + result.stderr
                st.session_state["last_logs"] = combined_output # PERSIST LOGS

                if "os.environ OPENAI_KEY" in combined_output:
                    for line in combined_output.split('\n'):
                        if "DEBUG: os.environ OPENAI_KEY" in line:
                            st.warning(f"🕵️ Key Check: {line.strip()}")

                if result.returncode == 0:
                    if found_videos:
                        status_box.success("✅ Analysis Complete! Refreshing dashboard...")
                        # Clear cache to ensure new data is fetched
                        st.cache_data.clear() 
                        st.cache_resource.clear()
                        import time
                        time.sleep(1) # Give DB a moment to settle
                        st.rerun() 
                    else:
                        status_box.warning("⚠️ Scraper finished but found 0 videos. See logs/screenshot above.")
                    # Filter junk from stderr
                    cleaned_err = "\n".join([line for line in result.stderr.split('\n') 
                                           if "[DEP" not in line 
                                           and "DeprecationWarning" not in line 
                                           and "(node:" not in line
                                           and "trace-deprecation" not in line])
                    
                    # Logic Check: If the job printed "Job completed", it finished.
                    # Warnings in stderr should not mask a success.
                    job_success = "Job completed" in result.stdout
                    
                    if job_success:
                         if found_videos:
                             status_box.success("✅ Analysis Complete! Refreshing...")
                         else:
                             status_box.warning("⚠️ Scraper finished but found 0 videos (Likely blocked). See debug screenshot below.")
                             
                         st.cache_data.clear()
                         st.cache_resource.clear()
                         import time
                         time.sleep(1)
                         if found_videos:
                             st.rerun()
                    else:
                        # Only show error if job actually CRASHED (no completion message)
                        err_msg = cleaned_err if cleaned_err.strip() else 'Unknown Error (Check Logs)'
                        status_box.error(f"❌ Error during scrape: {err_msg}")
            except Exception as e:
                status_box.error(f"❌ Execution failed: {e}")

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
        sent = v.get('sentiment', 'Not Analyzed')
        cls = "badge-neutral"
        if "Positive" in str(sent): cls = "badge-positive"
        elif "Negative" in str(sent): cls = "badge-negative"
        
        desc = v.get('description', '')[:80] + "..." if len(v.get('description', '')) > 80 else v.get('description', '')
        # summary not needed here since we are compacting it to match screenshot? 
        # Actually screenshot shows author, score, and desc. No summary box.
        
        tiktok_url = f"https://www.tiktok.com/@{v.get('author_username', 'user')}/video/{v.get('tiktok_id', '')}"
        
        video_html = f"""
        <div class="video-card" style="padding:15px; margin-bottom:10px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <div style="font-weight:700; font-size:12px; color:#333;">
                    <a href="{tiktok_url}" target="_blank" style="text-decoration:none; color:#333; display:flex; align-items:center; gap:4px;">
                        @{v.get('author_username')}
                        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#2980B9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                            <polyline points="15 3 21 3 21 9"></polyline>
                            <line x1="10" y1="14" x2="21" y2="3"></line>
                        </svg>
                    </a>
                </div>
                <div style="font-size:10px; color:#999;">{v.get('sentiment_score', 'N/A')}</div>
            </div>
            <div style="font-size:11px; color:#444; margin-bottom:8px;">{cls.replace('badge-','').upper()}</div>
             <div style="width:100%; height:4px; background:#EEE; border-radius:2px; overflow:hidden;">
                <div style="width:{int(v.get('sentiment_score', 0))*10}%; height:100%; background:{'#2ECC71' if 'Positive' in str(sent) else '#E74C3C' if 'Negative' in str(sent) else '#F39C12'};"></div>
            </div>
        </div>
        """
        video_html = "".join(line.strip() for line in video_html.split("\n"))
        st.markdown(video_html, unsafe_allow_html=True)

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
            sent_score = v.get('sentiment_score', 5)
            # Determine style
            border_color = "#F39C12" # Neutral
            icon = "😐"
            bg_light = "#FFF9E6"
            text_color = "#F39C12"
            sent_label = "NEUTRAL"
            
            if sent_score >= 7:
                border_color = "#2ECC71"
                icon = "😃"
                bg_light = "#E8F8F5"
                text_color = "#2ECC71"
                sent_label = "POSITIVE"
            elif sent_score <= 3:
                border_color = "#E74C3C"
                icon = "☹️"
                bg_light = "#FDEDEC"
                text_color = "#E74C3C"
                sent_label = "NEGATIVE"
                
            # If summary is missing, fallback to description
            body_text = v.get('summary')
            if not body_text or body_text == "N/A":
                body_text = v.get('description', "No content available.")
            
            # Use Topic if available, else username or keyword
            topic_title = v.get('topic', 'General Topic')
            if not topic_title or topic_title == "N/A": 
                topic_title = v.get('search_keyword') or "unknown topic"

            tiktok_url = f"https://www.tiktok.com/@{v.get('author_username', 'user')}/video/{v.get('tiktok_id', '')}"
            viral_pot = v.get('viral_potential', 'Low')
            trend_ctx = v.get('trend_context', '')
            issues_list = v.get('key_issues', [])
            
            # Formatting for Viral Badge
            viral_color = "#95A5A6"
            if "High" in viral_pot: viral_color = "#E74C3C"
            elif "Medium" in viral_pot: viral_color = "#F39C12"
            
            # Format Issues List
            issues_html = ""
            if issues_list and isinstance(issues_list, list):
                for issue in issues_list[:3]:
                    issues_html += f'<li style="margin-bottom:4px;">{issue}</li>'
            
            card_html = f"""
            <div style="background:white; border:1px solid {border_color}; border-radius:12px; padding:20px; margin-bottom:20px; position:relative; overflow:hidden;">
                <!-- Left Border Stripe -->
                <div style="position:absolute; left:0; top:0; bottom:0; width:6px; background:{border_color};"></div>
                
                <div style="display:flex; align-items:flex-start; margin-bottom:15px;">
                    <div style="font-size:24px; margin-right:15px; width:30px; text-align:center;">{icon}</div>
                    <div style="flex-grow:1;">
                        <div style="display:flex; justify-content:space-between; align-items:start;">
                            <div style="font-size:16px; font-weight:800; color:#333; margin-bottom:4px; text-transform:capitalize; display:flex; align-items:center; gap:8px;">
                                {topic_title}
                                <a href="{tiktok_url}" target="_blank" style="font-size:12px; font-weight:400; color:#3498DB; text-decoration:none; background:#F0F8FF; padding:2px 8px; border-radius:10px;">View ↗</a>
                            </div>
                            <div style="background:{viral_color}; color:white; padding:2px 8px; border-radius:4px; font-size:9px; font-weight:700; text-transform:uppercase;">
                                {viral_pot} VIRAL POTENTIAL
                            </div>
                        </div>
                        
                        <div style="font-size:13px; color:#555; line-height:1.5; margin-bottom:10px;">
                            <b>Summary:</b> {body_text}
                        </div>
                        
                        {f'<div style="background:#F9F9F9; padding:10px; border-radius:8px; font-size:12px; margin-bottom:10px; border-left:3px solid #DDD;"><b style="color:#555;">Trend Context:</b> {trend_ctx}</div>' if trend_ctx and trend_ctx != "N/A" else ''}
                        
                        {f'<div style="font-size:12px; color:#C0392B;"><b>⚠️ Key Issues:</b><ul style="margin:5px 0 0 0; padding-left:20px;">{issues_html}</ul></div>' if issues_html else ''}
                    </div>
                </div>
                
                <div style="display:flex; justify-content:flex-end; margin-top:10px;">
                     <div style="background:{bg_light}; color:{text_color}; padding:4px 12px; border-radius:20px; font-size:10px; font-weight:800; text-transform:uppercase; letter-spacing:1px;">
                        {sent_label}
                     </div>
                </div>
            </div>
            """
            card_html = "".join(line.strip() for line in card_html.split("\n"))
            st.markdown(card_html, unsafe_allow_html=True)
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
            # Prepare Data
            sent = v.get('sentiment', 'Not Analyzed')
            cls = "badge-neutral"
            if "Positive" in str(sent): cls = "badge-positive"
            elif "Negative" in str(sent): cls = "badge-negative"
            
            desc = v.get('description', '')[:120] + "..." if len(v.get('description', '')) > 120 else v.get('description', '')
            summary = v.get('summary', "No AI summary available.")
            pk_issue = v.get('key_issues', [])
            
            # Prepare Insight Tags
            insight_html = ""
            if pk_issue and isinstance(pk_issue, list):
                for issue in pk_issue[:3]: # Show top 3
                     insight_html += f'<span style="background:#FFF3E0; color:#E67E22; padding:3px 8px; border-radius:4px; font-size:10px; font-weight:600; margin-right:4px;">{issue}</span>'
            else:
                insight_html = '<span style="background:#f0f0f0; color:#999; padding:3px 8px; border-radius:4px; font-size:10px;">General</span>'
            
            tiktok_url = f"https://www.tiktok.com/@{v.get('author_username', 'user')}/video/{v.get('tiktok_id', '')}"
            
            grid_html = f"""
            <div style="background:white; border:1px solid #EEE; border-radius:12px; padding:20px; margin-bottom:20px; box-shadow:0 2px 5px rgba(0,0,0,0.02); height:500px; display:flex; flex-direction:column;">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:15px;">
                    <div style="font-weight:700; font-size:14px; color:#333;">
                         <a href="{tiktok_url}" target="_blank" style="text-decoration:none; color:#333; display:flex; align-items:center; gap:6px;">
                            @{v.get('author_username')}
                            <span style="font-size:12px; opacity:0.7;">🔗</span>
                        </a>
                    </div>
                    <div class="badge {cls}">{sent.upper()}</div>
                </div>
                
                <div style="font-size:13px; color:#555; margin-bottom:15px; flex-grow:0; height:60px; overflow:hidden; line-height:1.4;">
                    {desc}
                </div>
                
                <div style="background:#Fcfcfc; border:1px solid #F0F0F0; padding:10px; border-radius:8px; margin-bottom:10px; flex-grow:1; overflow-y:auto;">
                    <div style="font-size:10px; font-weight:700; color:#999; margin-bottom:4px;">VIDEO SUMMARY & INSIGHTS:</div>
                    <div style="font-size:11px; color:#444; line-height:1.4;">{summary[:500]}</div>
                    <div style="font-size:9px; color:#AAA; margin-top:5px; font-style:italic;">Source Report: {v.get('search_keyword', 'N/A')}</div>
                </div>
                
                <div style="margin-bottom:15px;">
                     <div style="font-size:10px; font-weight:700; color:#999; margin-bottom:4px;">MAIN TOPICS:</div>
                     <div style="display:flex; flex-wrap:wrap; gap:4px;">
                        {insight_html}
                     </div>
                </div>
                
                <div style="border-top:1px solid #F5F5F5; padding-top:12px; display:flex; justify-content:space-between; color:#AAA; font-size:12px;">
                    <span title="Views">👁️ {fmt_num(v.get('views_count',0))}</span>
                    <span title="Likes">❤️ {fmt_num(v.get('likes_count',0))}</span>
                    <span title="Comments">💬 {fmt_num(v.get('stats_comment_count',0))}</span>
                    <span title="Shares">↗️ {fmt_num(v.get('stats_share_count',0))}</span>
                </div>
            </div>
            """
            grid_html = "".join(line.strip() for line in grid_html.split("\n"))
            st.markdown(grid_html, unsafe_allow_html=True)

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


