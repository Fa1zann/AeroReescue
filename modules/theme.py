"""
modules/theme.py
Two-Color Obsidian & Tactical Amber Design System with Complete Typography,
Font-Scale Hierarchy, and Strictly Scoped 3D Tactile Buttons.
"""

import streamlit as st

def inject_command_center_theme():
    """Injects custom typography, strictly scoped 3D buttons, and tactical styling."""
    css = """
    <style>
        /* Import High-Precision Tactical Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700;800&display=swap');

        /* Color & Font Design System Tokens */
        :root {
            --bg-obsidian: #0B0E14;
            --bg-card: #161C28;
            --bg-elevated: #1F2738;
            --border-tactical: #2D3748;
            --text-main: #F9FAFB;
            --text-sub: #9CA3AF;
            --text-muted: #6B7280;
            --amber-main: #F59E0B;
            --amber-dark: #B45309;
            --amber-light: #FBBF24;
            --red-alert: #EF4444;
            --emerald-safe: #10B981;
            
            /* Typography Tokens */
            --font-primary: 'Outfit', -apple-system, sans-serif;
            --font-mono: 'JetBrains Mono', monospace;
        }

        /* Global Application Baseline */
        .stApp {
            background-color: var(--bg-obsidian) !important;
            color: var(--text-main) !important;
            font-family: var(--font-primary) !important;
            font-size: 0.92rem !important;
            line-height: 1.55 !important;
            -webkit-font-smoothing: antialiased;
        }

        /* Typography Hierarchy: Headings */
        h1 {
            font-family: var(--font-primary) !important;
            font-size: 1.85rem !important;
            font-weight: 800 !important;
            letter-spacing: -0.5px !important;
            color: var(--text-main) !important;
            line-height: 1.25 !important;
        }

        h2 {
            font-family: var(--font-primary) !important;
            font-size: 1.35rem !important;
            font-weight: 700 !important;
            letter-spacing: -0.3px !important;
            color: var(--text-main) !important;
            margin-top: 1rem !important;
            margin-bottom: 0.5rem !important;
        }

        h3 {
            font-family: var(--font-primary) !important;
            font-size: 1.1rem !important;
            font-weight: 700 !important;
            color: var(--amber-main) !important;
            letter-spacing: -0.2px !important;
        }

        h4, h5, h6 {
            font-family: var(--font-primary) !important;
            font-size: 0.95rem !important;
            font-weight: 600 !important;
            color: var(--text-main) !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
        }

        /* Paragraphs, Body Text & Captions (Excluded span to protect internal Streamlit Icons) */
        p, label {
            font-family: var(--font-primary) !important;
            font-size: 0.90rem !important;
            color: var(--text-main) !important;
        }

        .stCaption, [data-testid="stCaptionContainer"] {
            font-size: 0.80rem !important;
            color: var(--text-sub) !important;
            font-weight: 500 !important;
            line-height: 1.4 !important;
        }

        /* Monospaced Code & Coordinates Inline Tags */
        code {
            font-family: var(--font-mono) !important;
            font-size: 0.82rem !important;
            font-weight: 600 !important;
            color: var(--amber-main) !important;
            background-color: #11151F !important;
            border: 1px solid var(--border-tactical) !important;
            padding: 2px 6px !important;
            border-radius: 4px !important;
        }

        /* Header Bar Styling */
        header[data-testid="stHeader"] {
            background-color: var(--bg-obsidian) !important;
            border-bottom: 1px solid var(--border-tactical) !important;
        }

        /* Sidebar Styling & Font Calibration */
        section[data-testid="stSidebar"] {
            background-color: #11151F !important;
            border-right: 1px solid var(--border-tactical) !important;
        }

        section[data-testid="stSidebar"] h1, 
        section[data-testid="stSidebar"] h2, 
        section[data-testid="stSidebar"] h3 {
            font-size: 1.15rem !important;
            font-weight: 800 !important;
            letter-spacing: 0.5px !important;
        }

        section[data-testid="stSidebar"] label {
            font-size: 0.82rem !important;
            font-weight: 600 !important;
            color: var(--text-sub) !important;
            text-transform: uppercase !important;
            letter-spacing: 0.6px !important;
        }

        /* BRAND COMMAND BANNER */
        .brand-card {
            background: linear-gradient(135deg, #161C28 0%, #0B0E14 100%);
            border: 1px solid var(--border-tactical);
            border-left: 5px solid var(--amber-main);
            border-radius: 10px;
            padding: 16px 20px;
            margin-bottom: 18px;
            box-shadow: 0 8px 20px rgba(0,0,0,0.4);
        }

        /* 3D TACTILE METRIC CONTAINERS */
        div[data-testid="metric-container"] {
            background-color: var(--bg-card) !important;
            border: 1px solid var(--border-tactical) !important;
            border-bottom: 3px solid var(--amber-dark) !important;
            border-radius: 10px !important;
            padding: 14px 18px !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
        }
        
        div[data-testid="metric-container"] label {
            color: var(--text-sub) !important;
            font-size: 0.74rem !important;
            font-weight: 700 !important;
            letter-spacing: 1px !important;
            text-transform: uppercase !important;
        }

        div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
            color: var(--amber-main) !important;
            font-family: var(--font-mono) !important;
            font-size: 1.80rem !important;
            font-weight: 700 !important;
            letter-spacing: -0.5px !important;
            font-feature-settings: "tnum";
        }

        div[data-testid="metric-container"] [data-testid="stMetricDelta"] {
            font-family: var(--font-primary) !important;
            font-size: 0.80rem !important;
            font-weight: 600 !important;
        }

        /* 3D TACTILE BUTTONS (Strictly Scoped to st.button, ignores file uploader) */
        div[data-testid="stButton"] > button {
            background: linear-gradient(180deg, #252E3E 0%, #161C28 100%) !important;
            color: var(--text-main) !important;
            border: 1px solid #374151 !important;
            border-bottom: 4px solid #0F172A !important;
            border-radius: 8px !important;
            font-family: var(--font-primary) !important;
            font-weight: 700 !important;
            font-size: 0.88rem !important;
            letter-spacing: 0.3px !important;
            padding: 10px 18px !important;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.4) !important;
            transition: all 0.1s ease-in-out !important;
            cursor: pointer !important;
        }

        div[data-testid="stButton"] > button:hover {
            background: linear-gradient(180deg, #2D3748 0%, #1F2738 100%) !important;
            color: var(--amber-main) !important;
            border-color: var(--amber-main) !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 6px 12px rgba(245, 158, 11, 0.2) !important;
        }

        div[data-testid="stButton"] > button:active {
            transform: translateY(2px) !important;
            border-bottom: 1px solid #0F172A !important;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.4) !important;
        }

        /* PRIMARY ALERT BUTTONS */
        div[data-testid="stButton"] > button[kind="primary"] {
            background: linear-gradient(180deg, #DC2626 0%, #991B1B 100%) !important;
            border: 1px solid #EF4444 !important;
            border-bottom: 4px solid #7F1D1D !important;
            color: #FFFFFF !important;
            box-shadow: 0 4px 10px rgba(239, 68, 68, 0.35) !important;
        }

        div[data-testid="stButton"] > button[kind="primary"]:hover {
            background: linear-gradient(180deg, #EF4444 0%, #B91C1C 100%) !important;
            color: #FFFFFF !important;
            box-shadow: 0 6px 16px rgba(239, 68, 68, 0.5) !important;
        }

        /* TAB STYLING & FONT SIZE */
        button[data-baseweb="tab"] {
            background-color: #11151F !important;
            color: var(--text-sub) !important;
            border-radius: 8px 8px 0 0 !important;
            font-family: var(--font-primary) !important;
            font-size: 0.90rem !important;
            font-weight: 700 !important;
            letter-spacing: 0.2px !important;
            padding: 12px 20px !important;
            border: 1px solid var(--border-tactical) !important;
            border-bottom: none !important;
            margin-right: 6px !important;
        }

        button[data-baseweb="tab"][aria-selected="true"] {
            background-color: var(--bg-card) !important;
            color: var(--amber-main) !important;
            border-bottom: 3px solid var(--amber-main) !important;
        }

        /* INPUT CONTROLS & SELECT BOXES */
        div[data-baseweb="select"] > div, input, textarea {
            background-color: #11151F !important;
            color: var(--text-main) !important;
            font-family: var(--font-primary) !important;
            font-size: 0.88rem !important;
            border-color: var(--border-tactical) !important;
            border-radius: 8px !important;
        }

        /* DATAFRAMES & TABLES FONT CALIBRATION */
        div[data-testid="stDataFrame"] {
            font-family: var(--font-mono) !important;
            font-size: 0.84rem !important;
            background-color: var(--bg-card) !important;
            border: 1px solid var(--border-tactical) !important;
            border-radius: 8px !important;
        }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def apply_plotly_command_center_theme(fig):
    """Applies Two-Color Obsidian & Amber theme to Plotly charts with scaled typography."""
    fig.update_layout(
        paper_bgcolor="#161C28",
        plot_bgcolor="#0B0E14",
        font=dict(color="#F9FAFB", family="Outfit, sans-serif", size=12),
        title_font=dict(color="#F59E0B", size=15, family="Outfit, sans-serif"),
        xaxis=dict(gridcolor="#2D3748", zerolinecolor="#2D3748", tickfont=dict(color="#9CA3AF", size=11, family="JetBrains Mono")),
        yaxis=dict(gridcolor="#2D3748", zerolinecolor="#2D3748", tickfont=dict(color="#9CA3AF", size=11, family="JetBrains Mono")),
        legend=dict(bgcolor="#11151F", bordercolor="#2D3748", font=dict(color="#F9FAFB", size=11)),
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig

