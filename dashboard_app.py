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
st_autorefresh(interval=refresh_rate * 1000, key="datarefresh")

# Real-time mode toggle
realtime_mode = st.sidebar.checkbox("🔴 Real-Time Mode (Fast Updates)", value=True)
if realtime_mode:
    st.sidebar.info(f"🔄 Updating every {refresh_rate} seconds")

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
                            <div style='background-color:{"#ffebee" if tx["fraud_prediction"] == 1 else "#e8f5e9"};color:#1f1f1f;padding:10px;border-radius:5px;margin:5px 0;border-left:4px solid {"red" if tx["fraud_prediction"] == 1 else "green"};font-size:14px;font-weight:500;'>
                                <strong style='color:#000000;'>{fraud_indicator} {str(tx["transaction_id"])[:8]}...</strong> | 
                                <span style='color:#1a1a1a;'>₹{tx["amount"]:,.2f}</span> | 
                                <span style='color:#1a1a1a;'>{tx_type}</span> | 
                                <span style='color:#1a1a1a;'>{tx_location}</span> | 
                                <span style='color:{"#d32f2f" if tx["fraud_prediction"] == 1 else "#2e7d32"};font-weight:600;'>Fraud Prob: {fraud_prob:.2%}</span> | 
                                <span style='color:#666666;'>{tx_time}</span>
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

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Transactions", f"{total_tx:,}", delta=f"+{new_transactions_count}" if new_transactions_count > 0 else None)
    col2.metric("Fraudulent Transactions", f"{fraud_tx:,}", delta=f"{fraud_rate:.2f}%", delta_color="inverse")
    col3.metric("Fraud Rate (%)", f"{fraud_rate:.2f}%", delta="⚠️ High" if fraud_rate > 5 else "✅ Normal" if fraud_rate < 2 else "⚠️ Elevated")
    col4.metric("Average Amount (₹)", f"₹{avg_amount:,.2f}" if not pd.isna(avg_amount) and avg_amount > 0 else "N/A")
    col5.metric("Total Volume (₹)", f"₹{total_amount:,.2f}" if not pd.isna(total_amount) and total_amount > 0 else "N/A")
except Exception as e:
    st.error(f"Error displaying KPIs: {e}")
    import traceback
    st.code(traceback.format_exc())
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
            st.markdown(
        f"""
        <div style='background-color:#ff4d4d;padding:20px;border-radius:10px;animation: blinker 1s linear infinite;'>
            <h3 style='color:white;margin:0;'>🚨 HIGH-RISK FRAUD DETECTED</h3>
            <p style='color:white;margin:0;'>Detected <strong>{len(high_risk_frauds)}</strong> transactions with fraud probability ≥ 90%.</p>
        </div>
        <style>
        @keyframes blinker {{
            50% {{ opacity: 0.5; }}
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
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
    st.markdown("### 📈 Real-Time Transaction Timeline (Last 30 Minutes)")
    if not df_rt_filtered.empty and 'processed_time' in df_rt_filtered.columns:
        df_rt_filtered_copy = df_rt_filtered.copy()
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
                line=dict(color='blue', width=2)
            ))
            fig_timeline.add_trace(go.Scatter(
                x=timeline['time'],
                y=timeline['frauds'],
                mode='lines+markers',
                name='Fraudulent Transactions',
                line=dict(color='red', width=2)
            ))
            fig_timeline.update_layout(
                title="Transaction Volume Over Time",
                xaxis_title="Time",
                yaxis_title="Count",
                hovermode='x unified'
            )
            st.plotly_chart(fig_timeline, use_container_width=True)
except Exception as e:
    st.error(f"Error displaying timeline: {e}")

# ---------------------------
# FRAUD ANALYSIS DASHBOARD
# ---------------------------
try:
    st.markdown("### 📊 Fraud Analysis Dashboard")
    
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
                    title="Distribution of Fraudulent Transaction Amounts",
                    labels={'amount': 'Amount (₹)', 'count': 'Number of Transactions'},
                    color_discrete_sequence=['#ff4444']
                )
                fig_amount.update_layout(showlegend=False, height=350)
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
                    title="Fraud Count by Transaction Type",
                    labels={'fraud_count': 'Fraud Count', 'transaction_type': 'Transaction Type'},
                    color='fraud_rate',
                    color_continuous_scale='Reds',
                    text='fraud_rate'
                )
                fig_type.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                fig_type.update_layout(showlegend=False, height=350, xaxis_tickangle=-45)
                st.plotly_chart(fig_type, use_container_width=True)
            else:
                st.info("No transaction type data available")
        else:
            st.info("Data not available")
    
    # Second row of charts
    col_chart3, col_chart4 = st.columns(2)
    
    with col_chart3:
        # Fraud Risk Score Distribution
        st.markdown("#### 🎯 Fraud Risk Score Distribution")
        if 'fraud_probability' in df_rt_filtered.columns:
            fig_risk = px.histogram(
                df_rt_filtered,
                x='fraud_probability',
                nbins=30,
                title="Distribution of Fraud Risk Scores",
                labels={'fraud_probability': 'Fraud Probability', 'count': 'Number of Transactions'},
                color_discrete_sequence=['#ff6b6b'],
                marginal="box"
            )
            fig_risk.add_vline(x=0.75, line_dash="dash", line_color="red", 
                             annotation_text="Threshold (0.75)", annotation_position="top")
            fig_risk.update_layout(showlegend=False, height=350)
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
                    title="Fraud Count by Location",
                    labels={'fraud_count': 'Fraud Count', 'location': 'Location'},
                    color='total_amount',
                    color_continuous_scale='Oranges',
                    text='fraud_count'
                )
                fig_loc.update_traces(texttemplate='%{text}', textposition='outside')
                fig_loc.update_layout(showlegend=False, height=350, xaxis_tickangle=-45)
                st.plotly_chart(fig_loc, use_container_width=True)
                
                # Show top location
                top_loc = loc_fraud.iloc[0]
                st.caption(f"📍 Highest: {top_loc['location']} ({top_loc['fraud_count']} frauds, ₹{top_loc['total_amount']:,.2f})")
            else:
                st.info("No location data available")
        else:
            st.info("Data not available")
    
    # Third row - Combined analysis
    st.markdown("#### 📈 Fraud Trend Analysis")
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
                marker_color='#ff4444',
                yaxis='y'
            ))
            fig_hourly.add_trace(go.Scatter(
                x=hourly_fraud['hour'],
                y=hourly_fraud['fraud_rate'],
                name='Fraud Rate %',
                mode='lines+markers',
                line=dict(color='#ffaa00', width=3),
                yaxis='y2'
            ))
            fig_hourly.update_layout(
                title="Fraud Activity by Hour of Day",
                xaxis_title="Hour of Day",
                yaxis=dict(title="Fraud Count", side="left"),
                yaxis2=dict(title="Fraud Rate (%)", overlaying="y", side="right"),
                hovermode='x unified',
                height=400
            )
            st.plotly_chart(fig_hourly, use_container_width=True)
            st.caption("📊 Shows both fraud count (bars) and fraud rate percentage (line) by hour")
    
except Exception as e:
    st.error(f"Error displaying fraud analysis: {e}")
    import traceback
    st.code(traceback.format_exc())

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
st.markdown("### 🔍 Transaction Review - Manual Fraud Verification")
st.caption("Review suspicious transactions and mark them as fraud or not fraud. Only confirmed fraud transactions will appear in the Fraud Transactions Table below.")

if 'fraud_prediction' in df_rt_filtered.columns:
    # Get suspicious transactions (fraud_prediction = 1) that haven't been reviewed yet
    suspicious_tx = df_rt_filtered[df_rt_filtered["fraud_prediction"] == 1].copy()
    
    # Filter out only transactions confirmed as NOT fraud (keep fraud ones visible so they can be unchecked if needed)
    if not suspicious_tx.empty:
        suspicious_tx["transaction_id"] = suspicious_tx["transaction_id"].astype(str)
        # Only filter out transactions confirmed as NOT fraud
        suspicious_tx = suspicious_tx[~suspicious_tx["transaction_id"].isin(st.session_state.confirmed_not_fraud_transactions)]
    
    # Sort by processed_time and limit to 50 for review
    if not suspicious_tx.empty and 'processed_time' in suspicious_tx.columns:
        suspicious_tx = suspicious_tx.sort_values(by="processed_time", ascending=False).head(50)
    elif not suspicious_tx.empty:
        suspicious_tx = suspicious_tx.head(50)
    
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
            height=400,
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
            
            # Update session state
            # First, remove transactions from opposite sets to avoid conflicts
            st.session_state.confirmed_not_fraud_transactions -= confirmed_fraud_ids
            st.session_state.confirmed_fraud_transactions -= confirmed_not_fraud_ids
            
            # Then add to appropriate sets
            if confirmed_fraud_ids:
                st.session_state.confirmed_fraud_transactions.update(confirmed_fraud_ids)
            if confirmed_not_fraud_ids:
                st.session_state.confirmed_not_fraud_transactions.update(confirmed_not_fraud_ids)
        
        # Show counts and debug info
        confirmed_fraud_count = len(st.session_state.confirmed_fraud_transactions)
        confirmed_not_fraud_count = len(st.session_state.confirmed_not_fraud_transactions)
        
        # Debug: Show what was just processed
        if confirmed_fraud_ids:
            st.success(f"✅ {len(confirmed_fraud_ids)} transaction(s) marked as FRAUD (unchecked)")
        if confirmed_not_fraud_ids:
            st.info(f"ℹ️ {len(confirmed_not_fraud_ids)} transaction(s) marked as NOT fraud (checked)")
        
        if confirmed_fraud_count > 0 or confirmed_not_fraud_count > 0:
            st.info(f"📊 Review Status: {confirmed_fraud_count} confirmed as fraud | {confirmed_not_fraud_count} confirmed as not fraud")
    else:
        st.success("✅ No suspicious transactions pending review.")
else:
    st.info("ℹ️ No fraud prediction data available for review.")

# ---------------------------
# CONFIRMED FRAUD TRANSACTIONS TABLE
# ---------------------------
st.markdown("### 🚨 Confirmed Fraud Transactions")
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
                
                st.dataframe(display_confirmed, use_container_width=True, height=400)
                
                # Show summary
                total_fraud_amount = confirmed_fraud_df["amount"].sum() if 'amount' in confirmed_fraud_df.columns else 0
                st.metric("Total Confirmed Fraud Transactions", len(confirmed_fraud_df))
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
    st.markdown("### 🎯 Fraud Risk Gauge")
    
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
        title={'text': "Fraud Rate (%)"},
        delta={'reference': 2.0, 'position': "top"},
        gauge={
        'axis': {'range': [0, 10]},
        'bar': {'color': "darkred"},
        'steps': [
            {'range': [0, 1], 'color': "lightgreen"},
            {'range': [1, 3], 'color': "yellow"},
            {'range': [3, 5], 'color': "orange"},
            {'range': [5, 10], 'color': "red"}
        ],
        'threshold': {
            'line': {'color': "black", 'width': 4},
            'thickness': 0.75,
            'value': fraud_rate_for_gauge
            }
        }
    ))
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
st.download_button(
    label="📥 Export Filtered Dataset as CSV",
    data=df.to_csv(index=False).encode('utf-8'),
    file_name=f"fraud_transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
    mime="text/csv"
)

# ---------------------------
# FOOTER WITH STATUS
# ---------------------------
st.markdown("---")
col_footer1, col_footer2, col_footer3 = st.columns(3)
with col_footer1:
    if not df_rt_filtered.empty:
        tx_id = str(df_rt_filtered['transaction_id'].iloc[0]) if 'transaction_id' in df_rt_filtered.columns else "N/A"
        st.caption(f"🧾 Last transaction ID: {tx_id[:20]}...")
with col_footer2:
    st.caption(f"🔄 Auto-refresh: Every {refresh_rate} seconds")
with col_footer3:
    st.caption(f"⏱️ Last refresh: {datetime.now().strftime('%H:%M:%S')}")

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
