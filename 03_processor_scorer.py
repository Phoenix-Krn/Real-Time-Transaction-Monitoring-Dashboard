import pandas as pd
import joblib
import numpy as np
from datetime import datetime
import os
import time

MODEL_FILE = "xgboost_fraud_model.joblib"
INPUT_FILE = "data/realtime_stream.csv"
OUTPUT_FILE = "data/scored_transactions.csv"
THRESHOLD = 0.75  # Increased to reduce fraud rate (less sensitive, fewer false positives)

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

print("🔍 Loading model...")
model = joblib.load(MODEL_FILE)
print("✅ Model loaded successfully.")

def score_new_transactions():
    if not os.path.exists(INPUT_FILE):
        print("⚠️ Input file not found.")
        return

    df_stream = pd.read_csv(INPUT_FILE)
    if df_stream.empty:
        print("⏳ No transactions found.")
        return

    df_stream["transaction_id"] = df_stream["transaction_id"].astype(str)
    
    # Debug: Check for fraud flags in input
    if 'is_fraud' in df_stream.columns:
        fraud_count_input = df_stream['is_fraud'].sum()
        print(f"🔍 Input file has {fraud_count_input} fraud transactions (is_fraud column)")
    elif 'fraud_prediction' in df_stream.columns:
        fraud_count_input = df_stream['fraud_prediction'].sum()
        print(f"🔍 Input file has {fraud_count_input} fraud transactions (fraud_prediction column)")

    if os.path.exists(OUTPUT_FILE):
        df_scored = pd.read_csv(OUTPUT_FILE)
        if "transaction_id" in df_scored.columns:
            df_scored["transaction_id"] = df_scored["transaction_id"].astype(str)
            scored_ids = set(df_scored["transaction_id"])
        else:
            print("⚠️ 'transaction_id' column missing. Resetting scored file.")
            df_scored = pd.DataFrame()
            scored_ids = set()
    else:
        df_scored = pd.DataFrame()
        scored_ids = set()

    df_new = df_stream[~df_stream["transaction_id"].isin(scored_ids)].copy()
    if df_new.empty:
        print("⏳ No new transactions to score.")
        return

    print(f"🆕 New transactions to score: {len(df_new)}")
    
    # Debug: Check for fraud flags in new transactions
    if 'is_fraud' in df_new.columns:
        fraud_count_new = df_new['is_fraud'].sum()
        print(f"🔍 New transactions include {fraud_count_new} fraud transactions (is_fraud column)")
    elif 'fraud_prediction' in df_new.columns:
        fraud_count_new = df_new['fraud_prediction'].sum()
        print(f"🔍 New transactions include {fraud_count_new} fraud transactions (fraud_prediction column)")

    required_cols = ["transaction_id", "timestamp", "sender_account", "receiver_account", "amount", "transaction_type", "location"]
    # Don't drop rows based on is_fraud or fraud_probability - they're optional
    df_new = df_new.dropna(subset=required_cols)
    
    # Preserve simulator fraud flags if they exist
    simulator_fraud_backup = None
    simulator_prob_backup = None
    if 'is_fraud' in df_new.columns:
        simulator_fraud_backup = df_new['is_fraud'].copy()
    elif 'fraud_prediction' in df_new.columns:
        simulator_fraud_backup = df_new['fraud_prediction'].copy()
    if 'fraud_probability' in df_new.columns:
        simulator_prob_backup = df_new['fraud_probability'].copy()

    df_new['amount'] = pd.to_numeric(df_new['amount'], errors='coerce')
    before = len(df_new)
    df_new = df_new.dropna(subset=['amount'])
    df_new = df_new[df_new['amount'] < 1e6]
    after = len(df_new)
    print(f"🧹 Dropped {before - after} rows with invalid or extreme amount values.")

    if df_new.empty:
        print("⚠️ No valid transactions to score after cleaning.")
        return

    df_new['timestamp'] = pd.to_datetime(df_new['timestamp'], errors='coerce')
    df_new['hour'] = df_new['timestamp'].dt.hour
    df_new['day_of_week'] = df_new['timestamp'].dt.dayofweek
    df_new['amount_log'] = np.log1p(df_new['amount'])

    df_new["transaction_type_raw"] = df_new["transaction_type"]
    df_new["location_raw"] = df_new["location"]

    df_model = pd.get_dummies(df_new, columns=['transaction_type', 'location'], drop_first=True)

    model_features = model.get_booster().feature_names
    for col in model_features:
        if col not in df_model.columns:
            df_model[col] = 0
    df_model = df_model[model_features]

    # 🔍 Predict fraud probability and label using ML model
    fraud_probs = model.predict_proba(df_model)[:, 1]
    
    # Check if simulator already marked transactions as fraud
    simulator_fraud_col = None
    if 'fraud_prediction' in df_new.columns:
        simulator_fraud_col = 'fraud_prediction'
    elif 'is_fraud' in df_new.columns:
        simulator_fraud_col = 'is_fraud'
    
    # Use simulator's fraud flag if available, otherwise use model prediction
    if simulator_fraud_col is not None:
        simulator_fraud = pd.to_numeric(df_new[simulator_fraud_col], errors='coerce').fillna(0).astype(int)
        
        # Get simulator's fraud probability if available (use backup if column was lost)
        if 'fraud_probability' in df_new.columns:
            simulator_prob = pd.to_numeric(df_new['fraud_probability'], errors='coerce').fillna(0).values
        elif simulator_prob_backup is not None:
            simulator_prob = pd.to_numeric(simulator_prob_backup, errors='coerce').fillna(0).values
        else:
            simulator_prob = np.zeros(len(df_new))
        
        fraud_count = int(simulator_fraud.sum())
        print(f"📊 Simulator fraud flags found: {fraud_count} frauds marked out of {len(df_new)} transactions")
        
        if fraud_count > 0:
            print(f"🔍 Sample fraud transactions: {simulator_fraud[simulator_fraud == 1].head(3).index.tolist()}")
        
        # Hybrid approach: Use simulator flag if it says fraud, otherwise use model
        # If simulator marked as fraud, use simulator's probability (usually high)
        # Otherwise, use model's prediction
        df_new["fraud_probability"] = np.where(
            simulator_fraud.values == 1,
            np.maximum(simulator_prob, fraud_probs),  # Use higher of simulator or model
            fraud_probs  # Use model prediction for non-fraud
        )
        df_new["fraud_prediction"] = np.where(
            simulator_fraud.values == 1,
            1,  # Trust simulator's fraud flag
            (fraud_probs >= THRESHOLD).astype(int)  # Use model for others
        )
    else:
        # No simulator flags, use model only
        print("⚠️ No simulator fraud flags found, using ML model only")
        df_new["fraud_probability"] = fraud_probs
        df_new["fraud_prediction"] = (fraud_probs >= THRESHOLD).astype(int)

    df_new["processed_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    df_output = df_new[[
        "transaction_id", "timestamp", "processed_time",
        "sender_account", "receiver_account", "amount",
        "transaction_type_raw", "location_raw",
        "fraud_prediction", "fraud_probability"
    ]].rename(columns={
        "transaction_type_raw": "transaction_type",
        "location_raw": "location"
    })

    df_output["fraud_prediction"] = df_output["fraud_prediction"].astype(int)
    df_output["fraud_probability"] = df_output["fraud_probability"].round(4)
    df_output = df_output.sort_values(by="timestamp")

    df_output.to_csv(OUTPUT_FILE, mode='a', header=not os.path.exists(OUTPUT_FILE), index=False)
    print(f"✅ Scored {len(df_output)} new transactions → {OUTPUT_FILE}")
    print(f"🚨 Detected {df_output['fraud_prediction'].sum()} frauds ({df_output['fraud_prediction'].mean() * 100:.2f}%)")

if __name__ == "__main__":
    while True:
        score_new_transactions()
        time.sleep(5)