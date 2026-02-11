import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import time
import os
import warnings
from datetime import datetime

# Suppress pandas date parsing warnings
warnings.filterwarnings('ignore', category=UserWarning, message='.*Could not infer format.*')

# ---------------------------
# CONFIGURATION
# ---------------------------
st.set_page_config(
    page_title="💳 Real-Time Fraud Monitoring Dashboard (INR)",
    layout="wide",
    page_icon="💳"
)

# ---------------------------------
# THEME & AESTHETICS
# ---------------------------------
if 'theme' not in st.session_state:
    st.session_state.theme = 'Dark'

st.sidebar.header("🎨 Appearance")
theme_toggle = st.sidebar.radio("Theme Mode", ["Dark", "Light"], index=0 if st.session_state.theme == 'Dark' else 1, horizontal=True)

if theme_toggle != st.session_state.theme:
    st.session_state.theme = theme_toggle
    st.rerun()

# Define CSS based on theme
if st.session_state.theme == 'Dark':
    chart_template = "plotly_dark"
    custom_css = """
    <style>
        /* Dark Theme Overrides */
        .stApp {
            background-color: #0E1117;
            color: #FAFAFA;
        }
        [data-testid="stSidebar"] {
            background-color: #262730;
            color: #FAFAFA;
        }
        /* Sidebar text fixes */
        [data-testid="stSidebar"] .css-1d391kg,
        [data-testid="stSidebar"] .css-1lcbmhc,
        [data-testid="stSidebar"] .css-17eqqhr,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] span {
            color: #FAFAFA !important;
        }
        /* Main text elements */
        h1, h2, h3, h4, h5, h6 { color: #FFFFFF !important; }
        p, span, div { color: #E5E7EB !important; }
        a { color: #60A5FA !important; }
        /* Captions and subtle text */
        .stCaption { color: #A0AEC0 !important; }
        /* Card-like containers for metrics */
        div[data-testid="metric-container"] {
            background-color: #1E1E1E;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            border: 1px solid #0a0a0a;
        }
        div[data-testid="stMetricValue"] {
            color: #4CAF50 !important; /* Green for numbers */
        }
        div[data-testid="stMetricLabel"] {
            color: #D1D5DB !important; /* lighter gray for labels */
            font-weight: 600;
        }
        /* Custom KPI cards for dark theme */
        .kpi-card {
            background-color: #1E1E1E !important;
            color: #FFFFFF !important;
        }
        .kpi-value {
            color: #FFFFFF !important;
        }
        .kpi-label {
            color: #D1D5DB !important;
        }
        .kpi-delta {
            color: #A0AEC0 !important;
        }
        /* Tables and data editor */
        .stDataFrame { color: #E5E7EB !important; }
        .css-1cpxqw2 { color: #E5E7EB !important; }
        /* Expanders */
        .streamlit-expanderHeader { color: #FFFFFF !important; }
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] { color: #FFFFFF !important; }
        .stTabs [data-baseweb="tab"] { color: #A0AEC0 !important; }
        /* Buttons */
        .stButton > button { color: #FFFFFF !important; background-color: #2563EB !important; }
        .stDownloadButton > button { color: #FFFFFF !important; background-color: #2563EB !important; }
        /* Form controls */
        .css-1lcbmhc { color: #E5E7EB !important; }
        .css-17eqqhr { color: #E5E7EB !important; }
        /* Live Transaction Stream Styling - Dark */
        .live-tx-box {
            background-color: #1E1E1E;
            color: #FAFAFA;
            padding: 12px;
            border-radius: 8px;
            margin: 8px 0;
            border: 1px solid #333;
            font-size: 14px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .fraud-tx {
            border-left: 5px solid #f21111;
            background-color: rgba(255, 68, 68, 0.1);
        }
        .legit-tx {
            border-left: 5px solid #05ed63;
            background-color: rgba(0, 200, 81, 0.1);
        }
        .tx-id { font-weight: bold; color: #FAFAFA; }
        .tx-amount { font-family: monospace; font-weight: 600; color: #fca212; }
        .tx-details { color: #B0B0B0; font-size: 0.9em; }
        .tx-prob-high { color: #ff4444; font-weight: bold; }
        .tx-prob-low { color: #00C851; font-weight: bold; }
        /* Section containers */
        .streamlit-section {
            background-color: #161A22;
            padding: 20px;
            border-radius: 12px;
            margin: 15px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.4);
            border: 1px solid #222631;
        }
    </style>
    """
else:
    chart_template = "plotly_white"
    custom_css = """
    <style>
        /* Light Theme Overrides - Enhanced Visibility */
        .stApp {
            background-color: #FFFFFF; /* Pure white for better contrast */
            color: #1A1A1A; /* Very dark text for maximum visibility */
        }
        [data-testid="stSidebar"] {
            background-color: #F8F9FA;
            color: #1A1A1A;
        }
        /* Fix sidebar text - Enhanced visibility */
        [data-testid="stSidebar"] .css-1d391kg, 
        [data-testid="stSidebar"] .css-1lcbmhc,
        [data-testid="stSidebar"] .css-17eqqhr,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] span {
            color: #1A1A1A !important; /* Very dark for maximum visibility */
        }
        /* Fix sidebar headers - Enhanced visibility */
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            color: #0D0D0D !important; /* Even darker for headers */
        }
        /* Make sidebar tabs more visible - Enhanced */
        [data-testid="stSidebar"] .stTabs,
        [data-testid="stSidebar"] .stTabs [data-baseweb="tab-list"],
        [data-testid="stSidebar"] .stTabs [data-baseweb="tab"],
        [data-testid="stSidebar"] .stTabs [data-baseweb="tab"] span {
            color: #1A1A1A !important; /* Dark for visibility */
            background-color: #FFFFFF !important;
            font-weight: 700 !important;
        }
        /* Active tab styling - Enhanced */
        [data-testid="stSidebar"] .stTabs [data-baseweb="tab"][aria-selected="true"] {
            color: #0D0D0D !important; /* Very dark for active tab */
            background-color: #E9ECEF !important;
        }
        /* Fix main text elements - Enhanced visibility */
        h1, h2, h3, h4, h5, h6 {
            color: #0D0D0D !important; /* Very dark for headings */
        }
        h1 {
            font-size: 2.5rem !important;
            font-weight: 800 !important;
        }
        h2 {
            font-size: 2rem !important;
            font-weight: 700 !important;
        }
        h3 {
            font-size: 1.75rem !important;
            font-weight: 700 !important;
        }
        h4 {
            font-size: 1.5rem !important;
            font-weight: 600 !important;
        }
        h5 {
            font-size: 1.25rem !important;
            font-weight: 600 !important;
        }
        h6 {
            font-size: 1.1rem !important;
            font-weight: 600 !important;
        }
        p, span, div {
            color: #1A1A1A !important; /* Dark for all text */
        }
        /* Fix captions - Enhanced */
        .stCaption {
            color: #495057 !important; /* Darker gray for better contrast */
            font-weight: 500;
        }
        /* Fix data editor text - Enhanced */
        .stDataFrame {
            color: #1A1A1A !important;
        }
        /* Fix expander text - Enhanced */
        .streamlit-expanderHeader {
            color: #1A1A1A !important;
        }
        /* Fix Streamlit header tabs - Enhanced visibility */
        .stTabs [data-baseweb="tab-list"] {
            color: #1A1A1A !important;
            background-color: #FFFFFF !important;
        }
        .stTabs [data-baseweb="tab"] {
            color: #343A40 !important; /* Darker for better visibility */
            font-weight: 600;
            background-color: #F8F9FA !important;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            color: #0D0D0D !important;
            background-color: #E9ECEF !important;
        }
        /* Fix main header navigation */
        .stApp header {
            background-color: #FFFFFF !important;
        }
        .stApp header a {
            color: #1A1A1A !important;
        }
        /* Card-like containers for metrics - Enhanced */
        div[data-testid="metric-container"] {
            background-color: #FFFFFF;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            border: 1px solid #DEE2E6;
        }
        div[data-testid="stMetricValue"] {
            color: #0A6C3D !important; /* Dark green for numbers */
            font-weight: 700;
        }
        div[data-testid="stMetricLabel"] {
            color: #343A40 !important; /* Darker for labels */
            font-weight: 600;
        }
        /* Custom KPI cards - Enhanced light theme */
        .kpi-card {
            background-color: #FFFFFF !important;
            color: #1A1A1A !important;
            border: 1px solid #DEE2E6 !important;
        }
        .kpi-value {
            color: #1A1A1A !important;
        }
        .kpi-label {
            color: #495057 !important;
        }
        .kpi-delta {
            color: #6C757D !important;
        }
        /* Live Transaction Stream Styling - Enhanced Light */
        .live-tx-box {
            background-color: #FFFFFF;
            color: #1A1A1A;
            padding: 16px;
            border-radius: 10px;
            margin: 10px 0;
            border: 1px solid #DEE2E6;
            font-size: 14px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .fraud-tx {
            border-left: 5px solid #DC3545;
            background-color: #F8D7DA;
        }
        .legit-tx {
            border-left: 5px solid #28A745;
            background-color: #D4EDDA;
        }
        .tx-id { font-weight: bold; color: #1A1A1A; }
        .tx-amount { font-family: monospace; font-weight: 600; color: #0056B3; }
        .tx-details { color: #495057; font-size: 0.9em; }
        .tx-prob-high { color: #DC3545; font-weight: bold; }
        .tx-prob-low { color: #28A745; font-weight: bold; }
        /* Section styling - Enhanced */
        .streamlit-section {
            background-color: #FFFFFF;
            padding: 20px;
            border-radius: 12px;
            margin: 15px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border: 1px solid #DEE2E6;
        }
        /* Fix button text - Enhanced */
        .stButton > button {
            color: #0056B3 !important;
            background-color: #ffffff !important; /* Darker blue for better contrast */
            font-weight: 600;
        }
        /* Fix download button - Enhanced */
        .stDownloadButton > button {
            color: #FFFFFF !important;
            background-color: #A0AEC0 !important;
            font-weight: 600;
        }
        /* Fix data editor - Enhanced */
        .css-1cpxqw2 {
            color: #1A1A1A !important;
        }
        /* Fix selectbox and slider - Enhanced */
        .css-1lcbmhc {
            color: #1A1A1A !important;
        }
        .css-17eqqhr {
            color: #1A1A1A !important;
        }
        /* Fix filter buttons and interactive elements - Enhanced */
        .stSelectbox > div > div {
            color: #1A1A1A !important;
            background-color: #FFFFFF !important;
            border: 1px solid #DEE2E6 !important;
        }
        .stSelectbox > div > div:hover {
            background-color: #F8F9FA !important;
            border-color: #ADB5BD !important;
        }
        .stSelectbox option {
            color: #1A1A1A !important;
            background-color: #FFFFFF !important;
        }
        .stSelectbox svg {
            fill: #1A1A1A !important;
        }
        .stSelectbox[data-testid="stSelectbox"] > div > div {
            color: #1A1A1A !important;
            background-color: #FFFFFF !important;
        }
        .stSelectbox[data-testid="stSelectbox"] > div > div::after {
            color: #1A1A1A !important;
            border-color: #1A1A1A transparent transparent transparent !important;
        }
        .stMultiSelect > div > div {
            color: #1A1A1A !important;
            background-color: #FFFFFF !important;
            border: 1px solid #DEE2E6 !important;
        }
        .stMultiSelect > div > div:hover {
            background-color: #F8F9FA !important;
            border-color: #ADB5BD !important;
        }
        .stMultiSelect option {
            color: #1A1A1A !important;
            background-color: #FFFFFF !important;
        }
        .stMultiSelect svg {
            fill: #1A1A1A !important;
        }
        /* Fix all dropdown arrows */
        .css-1c7bg2y {
            color: #1A1A1A !important;
        }
        .css-1lcbmhc {
            color: #1A1A1A !important;
            background-color: #FFFFFF !important;
        }
        .css-17eqqhr {
            color: #1A1A1A !important;
            background-color: #FFFFFF !important;
        }
        /* Fix dropdown containers */
        [data-testid="stSelectbox"] {
            color: #1A1A1A !important;
            background-color: #FFFFFF !important;
        }
        [data-testid="stMultiSelect"] {
            color: #1A1A1A !important;
            background-color: #FFFFFF !important;
        }
        /* Fix dropdown option list - CRITICAL for clicked dropdowns */
        .stSelectbox ul {
            background-color: #FFFFFF !important;
            border: 1px solid #DEE2E6 !important;
        }
        .stSelectbox ul li {
            color: #1A1A1A !important;
            background-color: #FFFFFF !important;
        }
        .stSelectbox ul li:hover {
            background-color: #F8F9FA !important;
        }
        .stSelectbox ul li[aria-selected="true"] {
            background-color: #E9ECEF !important;
            color: #0D0D0D !important;
        }
        .stMultiSelect ul {
            background-color: #FFFFFF !important;
            border: 1px solid #DEE2E6 !important;
        }
        .stMultiSelect ul li {
            color: #1A1A1A !important;
            background-color: #FFFFFF !important;
        }
        .stMultiSelect ul li:hover {
            background-color: #F8F9FA !important;
        }
        .stMultiSelect ul li[aria-selected="true"] {
            background-color: #E9ECEF !important;
            color: #0D0D0D !important;
        }
        /* Fix baseweb dropdown components */
        [data-baseweb="select"] {
            color: #1A1A1A !important;
            background-color: #FFFFFF !important;
        }
        [data-baseweb="select"] option {
            color: #1A1A1A !important;
            background-color: #FFFFFF !important;
        }
        [data-baseweb="select"] ul {
            background-color: #FFFFFF !important;
            border: 1px solid #DEE2E6 !important;
        }
        [data-baseweb="select"] ul li {
            color: #1A1A1A !important;
            background-color: #FFFFFF !important;
        }
        /* Fix any remaining dropdown elements */
        div[role="listbox"] {
            background-color: #FFFFFF !important;
            border: 1px solid #DEE2E6 !important;
        }
        div[role="listbox"] div[role="option"] {
            color: #1A1A1A !important;
            background-color: #FFFFFF !important;
        }
        div[role="listbox"] div[role="option"]:hover {
            background-color: #F8F9FA !important;
        }
        /* Fix dropdown popups and overlays */
        .stSelectbox div[role="listbox"] {
            background-color: #FFFFFF !important;
            border: 1px solid #DEE2E6 !important;
            color: #1A1A1A !important;
        }
        .stSelectbox div[role="listbox"] div[role="option"] {
            background-color: #FFFFFF !important;
            color: #1A1A1A !important;
        }
        .stMultiSelect div[role="listbox"] {
            background-color: #FFFFFF !important;
            border: 1px solid #DEE2E6 !important;
            color: #1A1A1A !important;
        }
        .stMultiSelect div[role="listbox"] div[role="option"] {
            background-color: #FFFFFF !important;
            color: #1A1A1A !important;
        }
        /* Fix dropdown menu containers */
        .css-1c7bg2y {
            background-color: #FFFFFF !important;
            color: #1A1A1A !important;
        }
        .css-1lcbmhc {
            background-color: #FFFFFF !important;
            color: #1A1A1A !important;
        }
        .css-17eqqhr {
            background-color: #FFFFFF !important;
            color: #1A1A1A !important;
        }
        /* Fix dropdown menu items */
        .css-1c7bg2y div {
            background-color: #FFFFFF !important;
            color: #1A1A1A !important;
        }
        .css-1lcbmhc div {
            background-color: #FFFFFF !important;
            color: #1A1A1A !important;
        }
        .css-17eqqhr div {
            background-color: #FFFFFF !important;
            color: #1A1A1A !important;
        }
        /* Fix session statistics and JSON display - WHITE TEXT */
        .stJson {
            color: #FFFFFF !important;
            background-color: #1A1A1A !important;
        }
        .stJson pre {
            color: #FFFFFF !important;
        }
        .stJson code {
            color: #FFFFFF !important;
        }
        .stJson span {
            color: #FFFFFF !important;
        }
        .stJson div {
            color: #FFFFFF !important;
        }
        /* Fix all JSON and code display elements */
        .stCode {
            color: #FFFFFF !important;
            background-color: #1A1A1A !important;
        }
        .stCode pre {
            color: #FFFFFF !important;
        }
        .stCode code {
            color: #FFFFFF !important;
        }
        /* Fix filter buttons and interactive elements - TRANSPARENT */
        .stSelectbox > div > div {
            color: #1A1A1A !important;
            background-color: transparent !important;
            border: 1px solid #DEE2E6 !important;
        }
        .stSelectbox > div > div:hover {
            background-color: rgba(248, 249, 250, 0.8) !important;
            border-color: #ADB5BD !important;
        }
        .stSelectbox option {
            color: #1A1A1A !important;
            background-color: #FFFFFF !important;
        }
        .stSelectbox svg {
            fill: #1A1A1A !important;
        }
        .stSelectbox[data-testid="stSelectbox"] > div > div {
            color: #1A1A1A !important;
            background-color: transparent !important;
        }
        .stSelectbox[data-testid="stSelectbox"] > div > div::after {
            color: #1A1A1A !important;
            border-color: #1A1A1A transparent transparent transparent !important;
        }
        .stMultiSelect > div > div {
            color: #1A1A1A !important;
            background-color: transparent !important;
            border: 1px solid #DEE2E6 !important;
        }
        .stMultiSelect > div > div:hover {
            background-color: rgba(248, 249, 250, 0.8) !important;
            border-color: #ADB5BD !important;
        }
        .stMultiSelect option {
            color: #1A1A1A !important;
            background-color: #FFFFFF !important;
        }
        .stMultiSelect svg {
            fill: #1A1A1A !important;
        }
        /* Fix dropdown containers - TRANSPARENT */
        [data-testid="stSelectbox"] {
            color: #1A1A1A !important;
            background-color: transparent !important;
        }
        [data-testid="stMultiSelect"] {
            color: #1A1A1A !important;
            background-color: transparent !important;
        }
        /* Fix dropdown option list - WHITE TEXT ON DARK */
        .stSelectbox ul {
            background-color: #1A1A1A !important;
            border: 1px solid #DEE2E6 !important;
        }
        .stSelectbox ul li {
            color: #FFFFFF !important;
            background-color: #1A1A1A !important;
        }
        .stSelectbox ul li:hover {
            background-color: #343A40 !important;
        }
        .stSelectbox ul li[aria-selected="true"] {
            background-color: #495057 !important;
            color: #FFFFFF !important;
        }
        .stMultiSelect ul {
            background-color: #1A1A1A !important;
            border: 1px solid #DEE2E6 !important;
        }
        .stMultiSelect ul li {
            color: #FFFFFF !important;
            background-color: #1A1A1A !important;
        }
        .stMultiSelect ul li:hover {
            background-color: #343A40 !important;
        }
        .stMultiSelect ul li[aria-selected="true"] {
            background-color: #495057 !important;
            color: #FFFFFF !important;
        }
        /* Fix info/warning/error messages - Enhanced */
        .stInfo {
            color: #1A1A1A !important;
        }
        .stWarning {
            color: #856404 !important;
        }
        .stError {
            color: #721C24 !important;
        }
        .stSuccess {
            color: #155724 !important;
        }
        /* Custom KPI cards - Enhanced light theme */
        .kpi-card {
            background-color: #FFFFFF !important;
            color: #1A1A1A !important;
        }
        .kpi-value {
            color: #1A1A1A !important;
        }
        .kpi-label {
            color: #495057 !important;
        }
        .kpi-delta {
            color: #6C757D !important;
        }
        /* Custom section titles and chart titles for light theme */
        .section-title-large {
            color: #0D0D0D !important;
        }
        .chart-title {
            color: #0D0D0D !important;
        }
        /* Additional dropdown fixes for light theme - Enhanced visibility */
        .stSelectbox div[role="listbox"],
        .stSelectbox [data-baseweb="menu"],
        .stSelectbox ul,
        .stMultiSelect div[role="listbox"],
        .stMultiSelect [data-baseweb="menu"],
        .stMultiSelect ul,
        [data-baseweb="select"] div[role="listbox"],
        [data-baseweb="select"] [data-baseweb="menu"],
        [data-baseweb="select"] ul {
            background-color: #FFFFFF !important;
            border: 1px solid #DEE2E6 !important;
        }
        .stSelectbox div[role="option"],
        .stSelectbox li,
        .stSelectbox [data-baseweb="menu"] li,
        .stMultiSelect div[role="option"],
        .stMultiSelect li,
        .stMultiSelect [data-baseweb="menu"] li,
        [data-baseweb="select"] div[role="option"],
        [data-baseweb="select"] li,
        [data-baseweb="select"] [data-baseweb="menu"] li {
            color: #ffffff !important;
            background-color: #FFFFFF !important;
        }
        .stSelectbox div[role="option"]:hover,
        .stSelectbox li:hover,
        .stSelectbox [data-baseweb="menu"] li:hover,
        .stMultiSelect div[role="option"]:hover,
        .stMultiSelect li:hover,
        .stMultiSelect [data-baseweb="menu"] li:hover,
        [data-baseweb="select"] div[role="option"]:hover,
        [data-baseweb="select"] li:hover,
        [data-baseweb="select"] [data-baseweb="menu"] li:hover {
            background-color: #F8F9FA !important;
            color: #000000 !important;
        }
        /* Specific rules for dropdown options */
        div[role="listbox"] div[role="option"],
        div[role="listbox"] li,
        ul[role="listbox"] li {
            color: #000000 !important;
            background-color: #FFFFFF !important;
        }
        div[role="listbox"] div[role="option"]:hover,
        div[role="listbox"] li:hover,
        ul[role="listbox"] li:hover {
            background-color: #343A40 !important;
            color: #FFFFFF !important;
        }
        /* Critical fix for dropdown menu items */
        .stSelectbox [data-baseweb="popover"] div[role="option"],
        .stMultiSelect [data-baseweb="popover"] div[role="option"],
        [data-baseweb="select"] [data-baseweb="popover"] div[role="option"] {
            color: #FFFFFF !important;
            background-color: #1A1A1A !important;
        }
        .stSelectbox [data-baseweb="popover"] div[role="option"]:hover,
        .stMultiSelect [data-baseweb="popover"] div[role="option"]:hover,
        [data-baseweb="select"] [data-baseweb="popover"] div[role="option"]:hover {
            background-color: #343A40 !important;
            color: #FFFFFF !important;
        }
        /* Fix for all dropdown menu containers */
        [data-baseweb="popover"] {
            background-color: #1A1A1A !important;
            border: 1px solid #DEE2E6 !important;
        }
        [data-baseweb="popover"] div[role="option"] {
            color: #FFFFFF !important;
            background-color: #1A1A1A !important;
        }
        [data-baseweb="popover"] div[role="option"]:hover {
            background-color: #343A40 !important;
            color: #FFFFFF !important;
        }
        /* Fix dropdown popup menus - WHITE TEXT ON DARK FOR POPUPS */
        .stSelectbox [data-baseweb="popover"],
        .stMultiSelect [data-baseweb="popover"],
        [data-baseweb="select"] [data-baseweb="popover"] {
            background-color: #1A1A1A !important;
            border: 1px solid #DEE2E6 !important;
        }
        .stSelectbox [data-baseweb="popover"] div[role="option"],
        .stMultiSelect [data-baseweb="popover"] div[role="option"],
        [data-baseweb="select"] [data-baseweb="popover"] div[role="option"] {
            color: #FFFFFF !important;
            background-color: #1A1A1A !important;
        }
        .stSelectbox [data-baseweb="popover"] div[role="option"]:hover,
        .stMultiSelect [data-baseweb="popover"] div[role="option"]:hover,
        [data-baseweb="select"] [data-baseweb="popover"] div[role="option"]:hover {
            background-color: #343A40 !important;
            color: #FFFFFF !important;
        }
        /* Fix all popover content - WHITE TEXT */
        [data-baseweb="popover"] * {
            color: #FFFFFF !important;
        }
        [data-baseweb="popover"] div {
            color: #FFFFFF !important;
            background-color: #1A1A1A !important;
        }
        [data-baseweb="popover"] span {
            color: #FFFFFF !important;
        }
        [data-baseweb="popover"] li {
            color: #FFFFFF !important;
            background-color: #1A1A1A !important;
        }
        [data-baseweb="popover"] ul {
            background-color: #1A1A1A !important;
        }
        /* Fix menu items specifically */
        [data-baseweb="menu"] {
            background-color: #1A1A1A !important;
        }
        [data-baseweb="menu"] div {
            color: #FFFFFF !important;
            background-color: #1A1A1A !important;
        }
        [data-baseweb="menu"] li {
            color: #FFFFFF !important;
            background-color: #1A1A1A !important;
        }
        [data-baseweb="menu"] span {
            color: #FFFFFF !important;
        }
        /* Additional fix for select span elements */
        div[data-baseweb="select"] span {
            color: white !important;
        }
    </style>
    """
st.markdown(custom_css, unsafe_allow_html=True)

# Additional CSS for larger section headings and chart titles
heading_css = """
<style>
.section-title-large {
    font-size: 34px;
    font-weight: 800;
    line-height: 1.25;
    margin: 6px 0 14px 0;
}
.chart-title {
    font-size: 20px;
    font-weight: 700;
}
</style>
"""
st.markdown(heading_css, unsafe_allow_html=True)

REALTIME_FILE = "data/scored_transactions.csv"
HISTORICAL_FILE = "data/historical_data.csv"

# ---------------------------
# INITIALIZE SESSION STATE
# ---------------------------
if 'last_seen_ids' not in st.session_state:
    st.session_state.last_seen_ids = set()
if 'transaction_history' not in st.session_state:
    st.session_state.transaction_history = []
if 'last_refresh_time' not in st.session_state:
    st.session_state.last_refresh_time = datetime.now()
if 'checked_fraud_transactions' not in st.session_state:
    st.session_state.checked_fraud_transactions = set()
if 'confirmed_fraud_transactions' not in st.session_state:
    st.session_state.confirmed_fraud_transactions = set()  # Transactions manually confirmed as fraud
if 'confirmed_not_fraud_transactions' not in st.session_state:
    st.session_state.confirmed_not_fraud_transactions = set()  # Transactions manually confirmed as NOT fraud

# ---------------------------
# SIDEBAR SETTINGS
# ---------------------------
st.sidebar.header("⚙️ Dashboard Settings")
refresh_rate = st.sidebar.slider("Auto-refresh interval (seconds)", 1, 60, 5)

# Use st_autorefresh with a key that doesn't interfere with theme
st_autorefresh(interval=refresh_rate * 1000, key="auto_refresh_key")

# Real-time mode toggle
realtime_mode = st.sidebar.checkbox("🔴 Real-Time Mode (Fast Updates)", value=True)
if realtime_mode:
    st.sidebar.info(f"🔄 Updating every {refresh_rate} seconds")

# Review table size
review_limit = st.sidebar.slider("Review table size", 10, 200, 50, step=10,
    help="How many suspicious transactions to show for manual review")

# ---------------------------
# HELPER FUNCTIONS
# ---------------------------
def extract_transaction_type(row):
    """Extract transaction type from one-hot encoded columns or direct column"""
    if 'transaction_type' in row.index and pd.notna(row.get('transaction_type')):
        return str(row['transaction_type'])
    
    # Try to extract from one-hot encoded columns
    tx_type_cols = [col for col in row.index if col.startswith('transaction_type_')]
    for col in tx_type_cols:
        if row.get(col) == True or row.get(col) == 1:
            return col.replace('transaction_type_', '')
    return 'UNKNOWN'

def extract_location(row):
    """Extract location from one-hot encoded columns or direct column"""
    if 'location' in row.index and pd.notna(row.get('location')):
        return str(row['location'])
    
    # Try to extract from one-hot encoded columns
    loc_cols = [col for col in row.index if col.startswith('location_')]
    for col in loc_cols:
        if row.get(col) == True or row.get(col) == 1:
            return col.replace('location_', '')
    return 'UNKNOWN'

# ---------------------------
# LOAD DATA FUNCTION
# ---------------------------
def load_realtime_data():
    """Load and process real-time transaction data"""
    if not os.path.exists(REALTIME_FILE):
        return pd.DataFrame()
    
    try:
        # Read CSV
        df_rt = pd.read_csv(REALTIME_FILE, low_memory=False)
        if df_rt.empty:
            return pd.DataFrame()
        
        # Convert transaction_id to string
        if 'transaction_id' in df_rt.columns:
            df_rt['transaction_id'] = df_rt['transaction_id'].astype(str)
        else:
            return pd.DataFrame()
        
        # Handle numeric columns
        if 'amount' in df_rt.columns:
            df_rt['amount'] = pd.to_numeric(df_rt['amount'], errors='coerce')
        if 'fraud_probability' in df_rt.columns:
            df_rt['fraud_probability'] = pd.to_numeric(df_rt['fraud_probability'], errors='coerce')
        
        # Handle fraud_prediction - check if it exists, otherwise use is_fraud
        if 'fraud_prediction' in df_rt.columns:
            df_rt['fraud_prediction'] = pd.to_numeric(df_rt['fraud_prediction'], errors='coerce').fillna(0).astype(int)
        elif 'is_fraud' in df_rt.columns:
            df_rt['fraud_prediction'] = pd.to_numeric(df_rt['is_fraud'], errors='coerce').fillna(0).astype(int)
        else:
            df_rt['fraud_prediction'] = 0
        
        # Handle timestamps - specify format to avoid warnings
        if 'timestamp' in df_rt.columns:
            df_rt['timestamp'] = pd.to_datetime(df_rt['timestamp'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
        if 'processed_time' in df_rt.columns:
            df_rt['processed_time'] = pd.to_datetime(df_rt['processed_time'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
        else:
            if 'timestamp' in df_rt.columns:
                df_rt['processed_time'] = df_rt['timestamp']
            else:
                df_rt['processed_time'] = pd.Timestamp.now()
        
        # Extract transaction_type and location if not present
        if 'transaction_type' not in df_rt.columns:
            df_rt['transaction_type'] = df_rt.apply(extract_transaction_type, axis=1)
        if 'location' not in df_rt.columns:
            df_rt['location'] = df_rt.apply(extract_location, axis=1)
        
        # Remove duplicates
        df_rt.drop_duplicates(subset="transaction_id", inplace=True)
        df_rt["source"] = "Real-Time"
        
        # Sort by processed_time, handling NaT values
        if 'processed_time' in df_rt.columns:
            df_rt = df_rt.sort_values(by="processed_time", ascending=False, na_position='last')
        
        return df_rt
    except Exception as e:
        # Don't show error in function - let caller handle it
        return pd.DataFrame()

def load_historical_data():
    """Load historical data"""
    if not os.path.exists(HISTORICAL_FILE):
        return pd.DataFrame()
    
    try:
        df_hist = pd.read_csv(HISTORICAL_FILE, low_memory=False)
        if df_hist.empty:
            return pd.DataFrame()
        
        df_hist['amount'] = pd.to_numeric(df_hist['amount'], errors='coerce')
        # Specify format to avoid warnings and improve performance
        df_hist['timestamp'] = pd.to_datetime(df_hist['timestamp'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
        if 'processed_time' in df_hist.columns:
            df_hist['processed_time'] = pd.to_datetime(df_hist['processed_time'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
        else:
            df_hist['processed_time'] = df_hist['timestamp']
        
        # Handle fraud prediction
        if 'fraud_prediction' in df_hist.columns:
            df_hist["fraud_prediction"] = pd.to_numeric(df_hist["fraud_prediction"], errors='coerce').fillna(0).astype(int)
        elif 'is_fraud' in df_hist.columns:
            df_hist["fraud_prediction"] = pd.to_numeric(df_hist["is_fraud"], errors='coerce').fillna(0).astype(int)
        else:
            df_hist["fraud_prediction"] = 0
        
        df_hist["source"] = "Historical"
        return df_hist
    except Exception as e:
        return pd.DataFrame()

# ---------------------------
# LOAD DATA
# ---------------------------
# Show loading status
with st.spinner("Loading transaction data..."):
    df_rt = load_realtime_data()

# Debug info at top
if df_rt.empty:
    st.error("❌ No data loaded!")
    st.warning("⏳ Waiting for real-time transactions to appear...")
    st.info("💡 Make sure the streaming script and processor are running!")
    st.info(f"📁 Looking for file: {REALTIME_FILE}")
    if os.path.exists(REALTIME_FILE):
        file_size = os.path.getsize(REALTIME_FILE)
        st.info(f"✅ File exists! Size: {file_size:,} bytes")
        # Try to read a sample
        try:
            sample_df = pd.read_csv(REALTIME_FILE, nrows=5)
            st.success(f"✅ File is readable! Sample rows: {len(sample_df)}")
            st.dataframe(sample_df.head())
        except Exception as e:
            st.error(f"❌ Error reading file: {e}")
    else:
        st.error(f"❌ File not found: {REALTIME_FILE}")
    st.stop()

# Show data loaded successfully
st.success(f"✅ Loaded {len(df_rt):,} transactions")

# Detect new transactions
try:
    current_ids = set(df_rt['transaction_id'].astype(str))
    new_ids = current_ids - st.session_state.last_seen_ids
    new_transactions_count = len(new_ids)

    # Update session state
    if new_ids:
        new_transactions = df_rt[df_rt['transaction_id'].astype(str).isin(new_ids)]
        for _, tx in new_transactions.iterrows():
            try:
                st.session_state.transaction_history.insert(0, {
                    'id': str(tx['transaction_id']),
                    'time': tx['processed_time'] if pd.notna(tx['processed_time']) else tx['timestamp'],
                    'amount': tx['amount'],
                    'fraud': tx['fraud_prediction'],
                    'prob': tx['fraud_probability'],
                    'type': tx.get('transaction_type', 'N/A'),
                    'location': tx.get('location', 'N/A')
                })
            except:
                pass
        # Keep only last 100 transactions in history
        st.session_state.transaction_history = st.session_state.transaction_history[:100]
        st.session_state.last_seen_ids = current_ids
except Exception as e:
    new_transactions_count = 0
    # Initialize if not set
    if 'last_seen_ids' not in st.session_state:
        st.session_state.last_seen_ids = set()
    if len(st.session_state.last_seen_ids) == 0:
        st.session_state.last_seen_ids = set(df_rt['transaction_id'].astype(str))

try:
    df_hist = load_historical_data()
    if not df_hist.empty:
        df = pd.concat([df_rt, df_hist], ignore_index=True)
    else:
        df = df_rt.copy()
except Exception as e:
    df = df_rt.copy()

# ---------------------------
# FILTERS
# ---------------------------
st.sidebar.markdown("---")
st.sidebar.header("🔍 Filters")

try:
    # Get unique values safely
    sender_accounts = df['sender_account'].dropna().unique().tolist() if 'sender_account' in df.columns else []
    receiver_accounts = df['receiver_account'].dropna().unique().tolist() if 'receiver_account' in df.columns else []
    hours = df['timestamp'].dt.hour.dropna().unique().tolist() if 'timestamp' in df.columns and not df['timestamp'].isna().all() else []

    sender_filter = st.sidebar.selectbox("Sender Account", ["All"] + sorted(sender_accounts))
    receiver_filter = st.sidebar.selectbox("Receiver Account", ["All"] + sorted(receiver_accounts))
    hour_filter = st.sidebar.selectbox("Hour of Day", ["All"] + sorted(hours))

    if sender_filter != "All" and 'sender_account' in df.columns:
        df = df[df["sender_account"] == sender_filter]
    if receiver_filter != "All" and 'receiver_account' in df.columns:
        df = df[df["receiver_account"] == receiver_filter]
    if hour_filter != "All" and 'timestamp' in df.columns and not df['timestamp'].isna().all():
        df = df[df["timestamp"].dt.hour == int(hour_filter)]
except Exception as e:
    st.sidebar.error(f"Filter error: {e}")

df_rt_filtered = df[df["source"] == "Real-Time"] if 'source' in df.columns else df_rt

# ---------------------------
# HEADER WITH LIVE STATUS
# ---------------------------
st.title("💳 Real-Time Fraud Monitoring Dashboard (INR)")
st.caption("Live transaction monitoring with instant fraud detection and alerts")

col_header1, col_header2 = st.columns([3, 1])
with col_header1:
    pass  # Title already shown above
with col_header2:
    try:
        if new_transactions_count > 0:
            st.success(f"🆕 {new_transactions_count} new transaction(s)")
        status_color = "🟢" if realtime_mode else "⚪"
        st.caption(f"{status_color} Real-Time: {'ON' if realtime_mode else 'OFF'}")
    except:
        pass

# ---------------------------
# LIVE TRANSACTION STREAM
# ---------------------------
try:
    if new_transactions_count > 0 and realtime_mode:
        st.markdown("### 🔴 Live Transaction Stream")
        stream_container = st.container()
        with stream_container:
            try:
                recent_new = df_rt[df_rt['transaction_id'].astype(str).isin(new_ids)].head(10)
                for _, tx in recent_new.iterrows():
                    try:
                        fraud_indicator = "🚨" if tx['fraud_prediction'] == 1 else "✅"
                        tx_type = tx.get('transaction_type', 'N/A')
                        tx_location = tx.get('location', 'N/A')
                        tx_time = tx['processed_time'].strftime("%H:%M:%S") if pd.notna(tx['processed_time']) else (tx['timestamp'].strftime("%H:%M:%S") if pd.notna(tx['timestamp']) else "N/A")
                        fraud_prob = tx['fraud_probability'] if pd.notna(tx['fraud_probability']) else 0
                        
                        st.markdown(
                            f"""
                            <div class="live-tx-box {'fraud-tx' if tx['fraud_prediction'] == 1 else 'legit-tx'}">
                                <div>
                                    <span class="tx-id">{fraud_indicator} {str(tx["transaction_id"])[:8]}...</span>
                                    <span class="tx-details"> | {tx_type} | {tx_location}</span>
                                </div>
                                <div>
                                    <span class="tx-amount">₹{tx["amount"]:,.2f}</span>
                                    <span class="{'tx-prob-high' if tx['fraud_prediction'] == 1 else 'tx-prob-low'}">
                                        ({fraud_prob:.1%})
                                    </span>
                                    <span class="tx-details" style="margin-left: 8px;">{tx_time}</span>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    except:
                        pass
            except:
                pass
except:
    pass

# ---------------------------
# KPIs WITH DELTA INDICATORS
# ---------------------------
# Initialize variables
total_tx = len(df_rt_filtered)
fraud_tx = 0
fraud_rate = 0
avg_amount = 0
total_amount = 0

try:
    # Calculate fraud transactions: All transactions in review table are fraud by default
    # Only checked transactions (in confirmed_not_fraud) are NOT fraud
    # Get all suspicious transactions (fraud_prediction = 1) that are in review
    if 'fraud_prediction' in df_rt_filtered.columns:
        all_suspicious = df_rt_filtered[df_rt_filtered["fraud_prediction"] == 1].copy()
        if not all_suspicious.empty:
            all_suspicious["transaction_id"] = all_suspicious["transaction_id"].astype(str)
            # All suspicious transactions are fraud, except those checked as "not fraud"
            fraud_tx = len(all_suspicious) - len(st.session_state.confirmed_not_fraud_transactions.intersection(set(all_suspicious["transaction_id"])))
            fraud_rate = (fraud_tx / total_tx * 100) if total_tx > 0 else 0
        else:
            fraud_tx = 0
            fraud_rate = 0
    else:
        fraud_tx = 0
        fraud_rate = 0
    
    avg_amount = df_rt_filtered['amount'].mean() if 'amount' in df_rt_filtered.columns else 0
    total_amount = df_rt_filtered['amount'].sum() if 'amount' in df_rt_filtered.columns else 0

    # KPI Section with better styling
    st.markdown("### 📊 Key Performance Indicators")
    
    # Add custom CSS for KPI highlighting
    kpi_css = """
    <style>
    .kpi-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2px;
        border-radius: 15px;
        margin: 10px 0;
    }
    .kpi-card {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 13px;
        margin: 0 2px;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        border: 1px solid rgba(255,255,255,0.18);
        backdrop-filter: blur(4px);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .kpi-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.15);
    }
    .kpi-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1C1C1C;
        margin: 10px 0;
    }
    .kpi-label {
        font-size: 0.9rem;
        font-weight: 600;
        color: #6C757D;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .kpi-delta {
        font-size: 0.8rem;
        font-weight: 500;
        margin-top: 5px;
    }
    </style>
    """
    st.markdown(kpi_css, unsafe_allow_html=True)
    
    # Create enhanced KPI cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-label">Total Transactions</div>
            <div class="kpi-value">{:,}</div>
            <div class="kpi-delta">{}</div>
        </div>
        """.format(total_tx, f"+{new_transactions_count}" if new_transactions_count > 0 else "No new"), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-label">Fraudulent Transactions</div>
            <div class="kpi-value">{:,}</div>
            <div class="kpi-delta">{:.2f}%</div>
        </div>
        """.format(fraud_tx, fraud_rate), unsafe_allow_html=True)
    
    with col3:
        status_emoji = "🚨" if fraud_rate > 5 else "⚠️" if fraud_rate > 2 else "✅"
        status_color = "#dc3545" if fraud_rate > 5 else "#ffc107" if fraud_rate > 2 else "#28a745"
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-label">Fraud Rate</div>
            <div class="kpi-value" style="color: {}">{:.2f}%</div>
            <div class="kpi-delta">{} {}</div>
        </div>
        """.format(status_color, fraud_rate, status_emoji, 'High' if fraud_rate > 5 else 'Elevated' if fraud_rate > 2 else 'Normal'), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-label">Total Volume</div>
            <div class="kpi-value">{}</div>
            <div class="kpi-delta">INR</div>
        </div>
        """.format(f"₹{total_amount:,.2f}" if not pd.isna(total_amount) and total_amount > 0 else "N/A"), unsafe_allow_html=True)
    
    # Add some spacing
    st.markdown("<br>", unsafe_allow_html=True)
    
except Exception as e:
    st.error(f"Error displaying KPIs: {e}")
    # Still show basic info
    st.write(f"Total Transactions: {total_tx:,}")
    st.write(f"Data shape: {df_rt_filtered.shape}")
    st.write(f"Columns: {list(df_rt_filtered.columns)}")

# ---------------------------
# FRAUD RATE GAUGE (Moved after table to reflect checked transactions)
# ---------------------------
# Gauge will be rendered after the fraud transactions table

# ---------------------------
# HIGH-RISK FRAUD ALERT BANNER
# ---------------------------
try:
    if 'fraud_probability' in df_rt_filtered.columns:
        high_risk_frauds = df_rt_filtered[df_rt_filtered["fraud_probability"] >= 0.9]
        
        if not high_risk_frauds.empty:
            st.error(f"🚨 HIGH-RISK FRAUD DETECTED: {len(high_risk_frauds)} transactions with fraud probability ≥ 90%.")
except:
    pass

# ---------------------------
# ALERT BANNER
# ---------------------------
try:
    if fraud_rate > 5:
        st.error("🚨 High fraud rate detected! Investigate immediately.")
    elif fraud_rate > 2:
        st.warning("⚠️ Elevated fraud activity. Monitor closely.")
    else:
        st.success("✅ Fraud rate within normal range.")
except:
    pass

# ---------------------------
# REAL-TIME TRANSACTION TIMELINE
# ---------------------------
try:
    st.markdown("""
    <div class="section-title-large">📈 Real-Time Transaction Timeline (Past 7 Days)</div>
    """, unsafe_allow_html=True)
    if not df_rt_filtered.empty and 'processed_time' in df_rt_filtered.columns:
        df_rt_filtered_copy = df_rt_filtered.copy()
        # Filter to only last 7 days
        seven_days_ago = datetime.now() - pd.Timedelta(days=7)
        df_rt_filtered_copy = df_rt_filtered_copy[df_rt_filtered_copy['processed_time'] >= seven_days_ago]
        
        if not df_rt_filtered_copy.empty:
            df_rt_filtered_copy['time_bucket'] = df_rt_filtered_copy['processed_time'].dt.floor('1min')
            timeline = df_rt_filtered_copy.groupby('time_bucket').agg({
                'transaction_id': 'count',
                'fraud_prediction': 'sum',
                'amount': 'sum'
            }).reset_index()
            timeline.columns = ['time', 'count', 'frauds', 'volume']
            
            if not timeline.empty:
                fig_timeline = go.Figure()
                fig_timeline.add_trace(go.Scatter(
                    x=timeline['time'],
                    y=timeline['count'],
                    mode='lines+markers',
                    name='Total Transactions',
                    line=dict(color='#007bff', width=3)
                ))
                fig_timeline.add_trace(go.Scatter(
                    x=timeline['time'],
                    y=timeline['frauds'],
                    mode='lines+markers',
                    name='Fraudulent Transactions',
                    line=dict(color='#dc3545', width=3)
                ))
                fig_timeline.update_layout(
                    title=dict(
                        text="<b>Transaction Volume Over Time (Past 7 Days)</b>",
                        font=dict(size=18, color="#FAFAFA" if st.session_state.theme == 'Dark' else '#0D0D0D')
                        font=dict(size=18, color="#FFFFFF" if st.session_state.theme == 'Light' else '#FAFAFA')
                    ),
                    xaxis_title="Time",
                    yaxis_title="Count",
                    hovermode='x unified',
                    template=chart_template,
                    height=400,
                    xaxis=dict(
                        range=[seven_days_ago, datetime.now()],
                        tickformat='%m-%d %H:%M'
                    )
                )
                st.plotly_chart(fig_timeline, use_container_width=True)
            else:
                st.info("No transactions in the past 7 days.")
        else:
            st.info("No transactions in the last 30 minutes.")
except Exception as e:
    st.error(f"Error displaying timeline: {e}")

# ---------------------------
# FRAUD ANALYSIS DASHBOARD
# ---------------------------
try:
    st.markdown("""
    <div class="section-title-large">📊 Fraud Analysis Dashboard</div>
    """, unsafe_allow_html=True)
    
    # Create tabs for better organization
    tab1, tab2, tab3 = st.tabs(["📈 Overview", "🎯 Risk Analysis", "🌍 Location Analysis"])
    
    with tab1:
        # Create two columns for side-by-side charts
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            # Fraud Amount Distribution
            st.markdown("#### 💰 Fraud Amount Distribution")
            if 'fraud_prediction' in df_rt_filtered.columns and 'amount' in df_rt_filtered.columns:
                fraud_df = df_rt_filtered[df_rt_filtered['fraud_prediction'] == 1].copy()
                if not fraud_df.empty and len(fraud_df) > 0:
                    fig_amount = px.histogram(
                        fraud_df, 
                        x='amount', 
                        nbins=20,
                        title="<b>Distribution of Fraudulent Transaction Amounts</b>",
                        labels={'amount': 'Amount (₹)', 'count': 'Number of Transactions'},
                        color_discrete_sequence=['#dc3545'],
                        template=chart_template
                    )
                    fig_amount.update_layout(
                        showlegend=False,
                        height=350,
                        title=dict(
                            text=fig_amount.layout.title.text,
                            font=dict(size=16, color="#FAFAFA" if st.session_state.theme == 'Dark' else '#0D0D0D')
                        )
                    )
                    st.plotly_chart(fig_amount, use_container_width=True)
                    
                    # Show statistics
                    fraud_total = fraud_df['amount'].sum()
                    fraud_avg = fraud_df['amount'].mean()
                    fraud_max = fraud_df['amount'].max()
                    st.metric("Total Fraud Amount", f"₹{fraud_total:,.2f}")
                    st.caption(f"Avg: ₹{fraud_avg:,.2f} | Max: ₹{fraud_max:,.2f}")
                else:
                    st.info("No fraudulent transactions to display")
            else:
                st.info("Data not available")
        
        with col_chart2:
            # Fraud by Transaction Type
            st.markdown("#### 🔄 Fraud by Transaction Type")
            if 'fraud_prediction' in df_rt_filtered.columns and 'transaction_type' in df_rt_filtered.columns:
                type_fraud = df_rt_filtered.groupby('transaction_type').agg({
                    'fraud_prediction': ['sum', 'count']
                }).reset_index()
                type_fraud.columns = ['transaction_type', 'fraud_count', 'total_count']
                type_fraud['fraud_rate'] = (type_fraud['fraud_count'] / type_fraud['total_count'] * 100).round(2)
                type_fraud = type_fraud.sort_values('fraud_count', ascending=False)
                
                if not type_fraud.empty:
                    fig_type = px.bar(
                        type_fraud.head(8),
                        x='transaction_type',
                        y='fraud_count',
                        title="<b>Fraud Count by Transaction Type</b>",
                        labels={'fraud_count': 'Fraud Count', 'transaction_type': 'Transaction Type'},
                        color='fraud_rate',
                        color_continuous_scale='Reds',
                        text='fraud_rate',
                        template=chart_template
                    )
                    fig_type.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                    fig_type.update_layout(
                        showlegend=False,
                        height=350,
                        xaxis_tickangle=-45,
                        title=dict(
                            text=fig_type.layout.title.text,
                            font=dict(size=16, color="#FAFAFA" if st.session_state.theme == 'Dark' else '#0D0D0D')
                        )
                    )
                    st.plotly_chart(fig_type, use_container_width=True)
                else:
                    st.info("No transaction type data available")
            else:
                st.info("Data not available")
    
    with tab2:
        col_chart3, col_chart4 = st.columns(2)
        
        with col_chart3:
            # Fraud Risk Score Distribution
            st.markdown("#### 🎯 Fraud Risk Score Distribution")
            if 'fraud_probability' in df_rt_filtered.columns:
                fig_risk = px.histogram(
                    df_rt_filtered,
                    x='fraud_probability',
                    nbins=30,
                    title="<b>Distribution of Fraud Risk Scores</b>",
                    labels={'fraud_probability': 'Fraud Probability', 'count': 'Number of Transactions'},
                    color_discrete_sequence=['#dc3545'],
                    marginal="box",
                    template=chart_template
                )
                fig_risk.add_vline(x=0.75, line_dash="dash", line_color="red", 
                                 annotation_text="Threshold (0.75)", annotation_position="top")
                fig_risk.update_layout(
                    showlegend=False,
                    height=350,
                    title=dict(
                        text=fig_risk.layout.title.text,
                        font=dict(size=16, color="#FAFAFA" if st.session_state.theme == 'Dark' else '#0D0D0D')
                    )
                )
                st.plotly_chart(fig_risk, use_container_width=True)
                
                # Risk categories
                if len(df_rt_filtered) > 0:
                    high_risk = len(df_rt_filtered[df_rt_filtered['fraud_probability'] >= 0.9])
                    medium_risk = len(df_rt_filtered[(df_rt_filtered['fraud_probability'] >= 0.75) & 
                                                      (df_rt_filtered['fraud_probability'] < 0.9)])
                    low_risk = len(df_rt_filtered[df_rt_filtered['fraud_probability'] < 0.75])
                    st.caption(f"🔴 High Risk (≥90%): {high_risk} | 🟡 Medium (75-90%): {medium_risk} | 🟢 Low (<75%): {low_risk}")
            else:
                st.info("Risk score data not available")
        
        with col_chart4:
            # Fraud Trend by Hour
            st.markdown("#### 📈 Fraud Trend by Hour")
            if 'timestamp' in df_rt_filtered.columns and 'fraud_prediction' in df_rt_filtered.columns:
                df_rt_filtered_copy = df_rt_filtered.copy()
                df_rt_filtered_copy['hour'] = df_rt_filtered_copy['timestamp'].dt.hour
                hourly_fraud = df_rt_filtered_copy.groupby('hour').agg({
                    'fraud_prediction': ['sum', 'count']
                }).reset_index()
                hourly_fraud.columns = ['hour', 'fraud_count', 'total_count']
                hourly_fraud['fraud_rate'] = (hourly_fraud['fraud_count'] / hourly_fraud['total_count'] * 100).round(2)
                
                if not hourly_fraud.empty:
                    fig_hourly = go.Figure()
                    fig_hourly.add_trace(go.Bar(
                        x=hourly_fraud['hour'],
                        y=hourly_fraud['fraud_count'],
                        name='Fraud Count',
                        marker_color='#dc3545',
                        yaxis='y'
                    ))
                    fig_hourly.add_trace(go.Scatter(
                        x=hourly_fraud['hour'],
                        y=hourly_fraud['fraud_rate'],
                        name='Fraud Rate %',
                        mode='lines+markers',
                        line=dict(color='#ffc107', width=3),
                        yaxis='y2'
                    ))
                    fig_hourly.update_layout(
                        title=dict(
                            text="<b>Fraud Activity by Hour of Day</b>",
                            font=dict(size=16, color="#FAFAFA" if st.session_state.theme == 'Dark' else '#0D0D0D')
                        ),
                        xaxis_title="Hour of Day",
                        yaxis=dict(title="Fraud Count", side="left"),
                        yaxis2=dict(title="Fraud Rate (%)", overlaying="y", side="right"),
                        hovermode='x unified',
                        height=350,
                        template=chart_template
                    )
                    st.plotly_chart(fig_hourly, use_container_width=True)
                    st.caption("📊 Shows both fraud count (bars) and fraud rate percentage (line) by hour")
            else:
                st.info("Hourly trend data not available")
    
    with tab3:
        # Top Fraud Locations
        st.markdown("#### 🌍 Top Fraud Locations")
        if 'fraud_prediction' in df_rt_filtered.columns and 'location' in df_rt_filtered.columns:
            loc_fraud = df_rt_filtered[df_rt_filtered['fraud_prediction'] == 1].groupby('location').agg({
                'fraud_prediction': 'count',
                'amount': 'sum'
            }).reset_index()
            loc_fraud.columns = ['location', 'fraud_count', 'total_amount']
            loc_fraud = loc_fraud.sort_values('fraud_count', ascending=False).head(10)
            
            if not loc_fraud.empty:
                fig_loc = px.bar(
                    loc_fraud,
                    x='location',
                    y='fraud_count',
                    title="<b>Fraud Count by Location</b>",
                    labels={'fraud_count': 'Fraud Count', 'location': 'Location'},
                    color='total_amount',
                    color_continuous_scale='Oranges',
                    text='fraud_count',
                    template=chart_template
                )
                fig_loc.update_traces(texttemplate='%{text}', textposition='outside')
                fig_loc.update_layout(
                    showlegend=False, 
                    height=400, 
                    xaxis_tickangle=-45,
                    title=dict(
                        text=fig_loc.layout.title.text,
                        font=dict(size=16, color="#FFFFFF" if st.session_state.theme == 'Light' else '#FAFAFA')
                    )
                )
                st.plotly_chart(fig_loc, use_container_width=True)
                
                # Show top location
                top_loc = loc_fraud.iloc[0]
                st.caption(f"📍 Highest: {top_loc['location']} ({top_loc['fraud_count']} frauds, ₹{top_loc['total_amount']:,.2f})")
            else:
                st.info("No location data available")
        else:
            st.info("Location data not available")
    
except Exception as e:
    st.error(f"Error displaying fraud analysis: {e}")

# ---------------------------
# FRAUD TREND BY HOUR
# ---------------------------
# FRAUD TREND BY HOUR (Removed - now part of Fraud Analysis Dashboard)
# ---------------------------

# ---------------------------
# FRAUD HEATMAP BY LOCATION
# ---------------------------
# Location heatmap removed - now part of Fraud Analysis Dashboard above

# ---------------------------
# TRANSACTION REVIEW TABLE (Manual Fraud Verification)
# ---------------------------
st.markdown(
    """
    <div class="section-title-large">🧾 Suspicious Transactions Review</div>
    """,
    unsafe_allow_html=True
)
st.caption("Review suspicious transactions and mark them as fraud or not fraud. Only confirmed fraud transactions will appear in the Fraud Transactions Table below.")

if 'fraud_prediction' in df_rt_filtered.columns:
    # Get suspicious transactions (fraud_prediction = 1) that haven't been reviewed yet
    suspicious_tx = df_rt_filtered[df_rt_filtered["fraud_prediction"] == 1].copy()
    
    # Filter out only transactions confirmed as NOT fraud (keep fraud ones visible so they can be unchecked if needed)
    if not suspicious_tx.empty:
        suspicious_tx["transaction_id"] = suspicious_tx["transaction_id"].astype(str)
        # Only filter out transactions confirmed as NOT fraud
        suspicious_tx = suspicious_tx[~suspicious_tx["transaction_id"].isin(st.session_state.confirmed_not_fraud_transactions)]
    
    # Sort by processed_time and limit to user-configured review size
    if not suspicious_tx.empty and 'processed_time' in suspicious_tx.columns:
        suspicious_tx = suspicious_tx.sort_values(by="processed_time", ascending=False).head(review_limit)
    elif not suspicious_tx.empty:
        suspicious_tx = suspicious_tx.head(review_limit)
    
    if not suspicious_tx.empty:
        # Create display dataframe with checkbox column
        display_cols = ["transaction_id", "timestamp", "sender_account", "receiver_account", "amount", "fraud_probability"]
        if 'transaction_type' in suspicious_tx.columns:
            display_cols.append("transaction_type")
        if 'location' in suspicious_tx.columns:
            display_cols.append("location")
        
        review_df = suspicious_tx[display_cols].copy()
        
        # Convert transaction_id to string for consistent matching
        review_df["transaction_id"] = review_df["transaction_id"].astype(str)
        
        # Initialize "Not Fraud" column - checked means NOT fraud, unchecked means IS fraud (default)
        # If transaction is in confirmed_not_fraud, it should be checked (meaning it's NOT fraud)
        review_df["Not Fraud"] = review_df["transaction_id"].isin(st.session_state.confirmed_not_fraud_transactions)
        
        # Create a copy for editing with formatted values
        review_df_edit = review_df.copy()
        review_df_edit["amount"] = review_df_edit["amount"].apply(lambda x: f"₹{x:,.2f}")
        review_df_edit["fraud_probability"] = review_df_edit["fraud_probability"].apply(lambda x: f"{x:.2%}" if pd.notna(x) else "N/A")
        
        # Reorder columns to put "Not Fraud" first
        cols_order = ["Not Fraud"] + [col for col in review_df_edit.columns if col != "Not Fraud"]
        review_df_edit = review_df_edit[cols_order]
        
        # Use data_editor for interactive checkboxes
        edited_review_df = st.data_editor(
            review_df_edit,
            use_container_width=True,
            height=300,
            hide_index=True,
            column_config={
                "Not Fraud": st.column_config.CheckboxColumn(
                    "Not Fraud",
                    help="Check this box if the transaction is NOT fraud. Leave unchecked if it IS fraud.",
                    default=False,
                ),
                "transaction_id": st.column_config.TextColumn("Transaction ID"),
                "timestamp": st.column_config.DatetimeColumn("Timestamp"),
                "amount": st.column_config.TextColumn("Amount"),
                "fraud_probability": st.column_config.TextColumn("Fraud Probability"),
            },
            disabled=([col for col in review_df_edit.columns if col != "Not Fraud"]),
        )
        
        # Update session state with confirmed fraud/not fraud transactions
        if "Not Fraud" in edited_review_df.columns and "transaction_id" in edited_review_df.columns:
            # Convert transaction_id to string for consistent matching
            edited_review_df["transaction_id"] = edited_review_df["transaction_id"].astype(str)
            
            # INVERTED LOGIC: Checked = NOT fraud, Unchecked = IS fraud
            not_fraud_series = edited_review_df["Not Fraud"].astype(bool)
            confirmed_not_fraud_ids = set(edited_review_df[not_fraud_series]["transaction_id"].tolist())
            
            # All transactions in review table that are NOT checked are considered fraud
            all_review_ids = set(edited_review_df["transaction_id"].tolist())
            confirmed_fraud_ids = all_review_ids - confirmed_not_fraud_ids
            
            # Keep previous state for delta messages
            prev_fraud = set(st.session_state.confirmed_fraud_transactions)
            prev_not_fraud = set(st.session_state.confirmed_not_fraud_transactions)

            # Update session state
            # First, remove transactions from opposite sets to avoid conflicts
            st.session_state.confirmed_not_fraud_transactions -= confirmed_fraud_ids
            st.session_state.confirmed_fraud_transactions -= confirmed_not_fraud_ids
            
            # Then add to appropriate sets
            if confirmed_fraud_ids:
                st.session_state.confirmed_fraud_transactions.update(confirmed_fraud_ids)
            if confirmed_not_fraud_ids:
                st.session_state.confirmed_not_fraud_transactions.update(confirmed_not_fraud_ids)

            # Compute deltas (newly marked in this interaction)
            newly_marked_fraud = st.session_state.confirmed_fraud_transactions - prev_fraud
            newly_marked_not_fraud = st.session_state.confirmed_not_fraud_transactions - prev_not_fraud
        
        # Show counts and debug info
        confirmed_fraud_count = len(st.session_state.confirmed_fraud_transactions)
        confirmed_not_fraud_count = len(st.session_state.confirmed_not_fraud_transactions)
        
        # Status messages (show only changes), plus an in-view summary to avoid confusion
        if 'newly_marked_fraud' in locals() and len(newly_marked_fraud) > 0:
            st.success(f"✅ {len(newly_marked_fraud)} transaction(s) marked as FRAUD")
        if 'newly_marked_not_fraud' in locals() and len(newly_marked_not_fraud) > 0:
            st.info(f"ℹ️ {len(newly_marked_not_fraud)} transaction(s) marked as NOT fraud")
        # Always show current view summary
        if 'all_review_ids' in locals():
            st.caption(f"In view: {len(confirmed_fraud_ids)} fraud (unchecked) | {len(confirmed_not_fraud_ids)} not fraud (checked) out of {len(all_review_ids)} displayed")
        
        if confirmed_fraud_count > 0 or confirmed_not_fraud_count > 0:
            st.info(f"📊 Review Status: {confirmed_fraud_count} confirmed as fraud | {confirmed_not_fraud_count} confirmed as not fraud")
    else:
        st.success("✅ No suspicious transactions pending review.")
else:
    st.info("ℹ️ No fraud prediction data available for review.")

# ---------------------------
# CONFIRMED FRAUD TRANSACTIONS TABLE
# ---------------------------
st.markdown("""
<div class="section-title-large">🚨 Confirmed Fraud Transactions</div>
""", unsafe_allow_html=True)
st.caption("This table shows all suspicious transactions that are fraud (unchecked in review table). Checked transactions are NOT fraud and won't appear here.")

# Get all suspicious transactions that are NOT checked (i.e., are fraud)
if 'fraud_prediction' in df_rt_filtered.columns:
    all_suspicious = df_rt_filtered[df_rt_filtered["fraud_prediction"] == 1].copy()
    
    if not all_suspicious.empty:
        all_suspicious["transaction_id"] = all_suspicious["transaction_id"].astype(str)
        # All suspicious transactions are fraud, except those checked as "not fraud"
        fraud_transaction_ids = set(all_suspicious["transaction_id"]) - st.session_state.confirmed_not_fraud_transactions
        
        if fraud_transaction_ids:
            # Get fraud transactions from the unfiltered dataframe to ensure we find all transactions
            # Try df_rt first, then df (which includes historical data) if needed
            confirmed_fraud_df = pd.DataFrame()
            
            # Convert transaction_id to string for matching in df_rt
            if not df_rt.empty and 'transaction_id' in df_rt.columns:
                df_rt_for_lookup = df_rt.copy()
                df_rt_for_lookup["transaction_id"] = df_rt_for_lookup["transaction_id"].astype(str)
                confirmed_fraud_df = df_rt_for_lookup[df_rt_for_lookup["transaction_id"].isin(fraud_transaction_ids)].copy()
            
            # If not found in df_rt, try the combined df (includes historical)
            if confirmed_fraud_df.empty and 'transaction_id' in df.columns:
                df_for_lookup = df.copy()
                df_for_lookup["transaction_id"] = df_for_lookup["transaction_id"].astype(str)
                confirmed_fraud_df = df_for_lookup[df_for_lookup["transaction_id"].isin(fraud_transaction_ids)].copy()
            
            if not confirmed_fraud_df.empty:
                # Sort by processed_time
                if 'processed_time' in confirmed_fraud_df.columns:
                    confirmed_fraud_df = confirmed_fraud_df.sort_values(by="processed_time", ascending=False)
                
                # Create display columns
                display_cols = ["transaction_id", "timestamp", "sender_account", "receiver_account", "amount", "fraud_probability"]
                if 'transaction_type' in confirmed_fraud_df.columns:
                    display_cols.append("transaction_type")
                if 'location' in confirmed_fraud_df.columns:
                    display_cols.append("location")
                
                display_confirmed = confirmed_fraud_df[display_cols].copy()
                display_confirmed["amount"] = display_confirmed["amount"].apply(lambda x: f"₹{x:,.2f}")
                display_confirmed["fraud_probability"] = display_confirmed["fraud_probability"].apply(lambda x: f"{x:.2%}" if pd.notna(x) else "N/A")
                
                st.dataframe(display_confirmed, use_container_width=True, height=300)
                
                # Show summary
                total_fraud_amount = confirmed_fraud_df["amount"].sum() if 'amount' in confirmed_fraud_df.columns else 0
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Confirmed Fraud Transactions", len(confirmed_fraud_df))
                with col2:
                    st.metric("Total Fraud Amount", f"₹{total_fraud_amount:,.2f}")
            else:
                st.warning(f"⚠️ {len(fraud_transaction_ids)} fraud transaction(s) identified, but not found in current data.")
        else:
            st.info("ℹ️ All suspicious transactions have been checked as NOT fraud, or no suspicious transactions found.")
    else:
        st.info("ℹ️ No suspicious transactions found.")
else:
    st.info("ℹ️ No fraud prediction data available.")

# ---------------------------
# FRAUD RATE GAUGE (Based on manually confirmed fraud transactions)
# ---------------------------
try:
    st.markdown("""
    <div class="section-title-large">🎯 Fraud Risk Gauge</div>
    """, unsafe_allow_html=True)
    
    # Calculate fraud rate: All transactions in review table are fraud by default
    # Only checked transactions (confirmed_not_fraud) are NOT fraud
    fraud_rate_for_gauge = 0
    if 'fraud_prediction' in df_rt_filtered.columns:
        all_suspicious = df_rt_filtered[df_rt_filtered["fraud_prediction"] == 1].copy()
        if not all_suspicious.empty:
            all_suspicious["transaction_id"] = all_suspicious["transaction_id"].astype(str)
            # All suspicious transactions are fraud, except those checked as "not fraud"
            confirmed_fraud_count = len(all_suspicious) - len(st.session_state.confirmed_not_fraud_transactions.intersection(set(all_suspicious["transaction_id"])))
            fraud_rate_for_gauge = (confirmed_fraud_count / total_tx * 100) if total_tx > 0 else 0
        else:
            fraud_rate_for_gauge = 0
    else:
        fraud_rate_for_gauge = 0

    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=fraud_rate_for_gauge,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "<b>Fraud Rate (%)</b>", 'font': {'size': 26}},
        delta={'reference': 2.0, 'position': "top"},
        gauge={
        'axis': {'range': [0, 10], 'tickwidth': 1, 'tickcolor': "#1C1C1C"},
        'bar': {'color': "#dc3545", 'thickness': 0.3},
        'steps': [
            {'range': [0, 1], 'color': "#00ff3c"},
            {'range': [1, 3], 'color': "#ffc400"},
            {'range': [3, 5], 'color': "#ff7300"},
            {'range': [5, 10], 'color': "#ff0019"}
        ],
        'threshold': {
            'line': {'color': "#dc3545", 'width': 6},
            'thickness': 0.9,
            'value': fraud_rate_for_gauge
            }
        }
    ))
    fig_gauge.update_layout(
        template=chart_template,
        height=500,
        margin=dict(l=20, r=20, t=60, b=20),
        font=dict(color="#FFFFFF" if st.session_state.theme == 'Light' else '#FAFAFA', size=14)
    )
    st.plotly_chart(fig_gauge, use_container_width=True)
    
    # Show indicator
    if 'fraud_prediction' in df_rt_filtered.columns:
        all_suspicious = df_rt_filtered[df_rt_filtered["fraud_prediction"] == 1]
        if not all_suspicious.empty:
            checked_count = len(st.session_state.confirmed_not_fraud_transactions)
            fraud_count = len(all_suspicious) - checked_count
            st.caption(f"📊 Gauge showing fraud rate: {fraud_count} fraud transactions (all suspicious minus {checked_count} checked as not fraud)")
        else:
            st.caption("📊 Gauge showing fraud rate based on suspicious transactions. Check transactions in review table if they're NOT fraud.")
    else:
        st.caption("📊 Gauge showing fraud rate based on suspicious transactions.")
except Exception as e:
    st.error(f"Error displaying gauge: {e}")

# ---------------------------
# EXPORT BUTTON
# ---------------------------
st.markdown("""
<div class="section-title-large">📥 Data Export</div>
""", unsafe_allow_html=True)
col1, col2 = st.columns([1, 3])
with col1:
    st.download_button(
        label="📥 Export Filtered Dataset as CSV",
        data=df.to_csv(index=False).encode('utf-8'),
        file_name=f"fraud_transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )
with col2:
    st.caption("Download the current filtered dataset for further analysis or record-keeping.")

# ---------------------------
# FOOTER WITH STATUS
# ---------------------------
st.markdown("---")
st.markdown("""
<div class="section-title-large">📋 Dashboard Status</div>
""", unsafe_allow_html=True)
col_footer1, col_footer2, col_footer3 = st.columns(3)
with col_footer1:
    if not df_rt_filtered.empty:
        tx_id = str(df_rt_filtered['transaction_id'].iloc[0]) if 'transaction_id' in df_rt_filtered.columns else "N/A"
        st.metric("Last Transaction ID", f"{tx_id[:20]}...")
with col_footer2:
    st.metric("Auto-Refresh", f"Every {refresh_rate} seconds")
with col_footer3:
    st.metric("Last Update", datetime.now().strftime("%H:%M:%S"))

# ---------------------------
# DEBUG PANEL
# ---------------------------
with st.expander("🧪 Debug: Real-Time Statistics"):
    col_debug1, col_debug2 = st.columns(2)
    with col_debug1:
        st.write("**Last 5 Transactions:**")
        debug_cols = ["transaction_id", "timestamp", "amount"]
        if 'fraud_prediction' in df_rt_filtered.columns:
            debug_cols.append("fraud_prediction")
        if 'fraud_probability' in df_rt_filtered.columns:
            debug_cols.append("fraud_probability")
        
        available_cols = [col for col in debug_cols if col in df_rt_filtered.columns]
        if available_cols:
            st.dataframe(
                df_rt_filtered.head(5)[available_cols],
                use_container_width=True
            )
        else:
            st.write("No data available")
    with col_debug2:
        st.write("**Session Statistics:**")
        st.json({
            "Total transactions seen": len(st.session_state.last_seen_ids),
            "New transactions this refresh": new_transactions_count,
            "Transaction history size": len(st.session_state.transaction_history),
            "Last refresh time": st.session_state.last_refresh_time.strftime("%H:%M:%S"),
            "Data shape": f"{df_rt.shape[0]} rows, {df_rt.shape[1]} columns",
            "Columns": list(df_rt.columns)[:10]  # First 10 columns
        })
    st.session_state.last_refresh_time = datetime.now()
