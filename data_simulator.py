import pandas as pd
import numpy as np
import uuid
import random
from datetime import datetime
import time
import os

STREAM_FILE = "data/realtime_stream.csv"
os.makedirs(os.path.dirname(STREAM_FILE), exist_ok=True)

columns = [
    "transaction_id", "timestamp", "processed_time",
    "sender_account", "receiver_account", "amount",
    "transaction_type", "location", "is_fraud", "fraud_probability"
]

transaction_types = ["PURCHASE", "WITHDRAWAL", "DEPOSIT", "TRANSFER", "UPI", "IMPS", "NEFT", "RTGS"]
locations = ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Kolkata", "Pune", "Ahmedabad","Andra Pradesh","Tamil Nadu","Kerala"]

def get_dynamic_fraud_rate(transaction_type, location):
    hour = datetime.now().hour
    minute = datetime.now().minute
    
    # Add time-based fluctuation using sine wave for natural variation
    # Creates fluctuation between 0.3x and 1.7x of base rate
    time_factor = 0.7 + 0.3 * np.sin((hour * 60 + minute) / 30.0)  # Oscillates every ~30 minutes
    
    # REDUCED base rate by time of day (decreased from original values)
    if 0 <= hour < 6:
        base_rate = 0.03 * time_factor  # Reduced from 0.08
    elif 6 <= hour < 12:
        base_rate = 0.01 * time_factor  # Reduced from 0.03
    elif 12 <= hour < 18:
        base_rate = 0.015 * time_factor  # Reduced from 0.04
    else:
        base_rate = 0.02 * time_factor  # Reduced from 0.06

    # Pattern-based adjustments (reduced)
    if transaction_type == "UPI" and location == "Mumbai":
        base_rate += 0.02  # Reduced from 0.05
    elif transaction_type == "WITHDRAWAL" and location == "Delhi":
        base_rate += 0.01  # Reduced from 0.03
    elif location == "Kolkata":
        base_rate += 0.008  # Reduced from 0.02

    return min(base_rate, 0.10)  # Cap at 10% (reduced from 20%)

def generate_transaction(force_fraud=False):
    now = datetime.now()
    transaction_type = random.choice(transaction_types)
    location = random.choice(locations)
    fraud_rate = get_dynamic_fraud_rate(transaction_type, location)

    # REDUCED FRAUD RATE with fluctuation - base 0.5-1% chance of fraud
    # Add random fluctuation to create variation
    fluctuation = random.uniform(0.8, 1.2)  # ±20% variation
    base_fraud_chance = 0.007 * fluctuation  # Base ~0.7% with fluctuation
    
    if force_fraud or random.random() < base_fraud_chance:
        is_fraud = True
        # High-risk fraud transactions with high probability
        fraud_prob = round(random.uniform(0.85, 0.99), 4)
        # Fraud transactions often have unusual amounts
        amount = round(np.random.exponential(scale=15000) + 1000, 2)  # Higher amounts for fraud
    else:
        is_fraud = random.random() < fraud_rate
        fraud_prob = round(random.uniform(0.7, 0.99), 4) if is_fraud else round(random.uniform(0.01, 0.3), 4)
        amount = round(np.random.exponential(scale=8000) + 500, 2)

    return {
        "transaction_id": str(uuid.uuid4()),
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
        "processed_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "sender_account": f"AC{random.randint(100000, 999999)}",
        "receiver_account": f"AC{random.randint(100000, 999999)}",
        "amount": amount,
        "transaction_type": transaction_type,
        "location": location,
        "is_fraud": int(is_fraud),
        "fraud_probability": fraud_prob
    }

print("🚀 Starting real-time transaction simulator...")
fraud_counter = 0
while True:
    batch_size = random.randint(3, 10)  # Increased batch size for faster generation
    transactions = []
    
    # Occasionally force fraud to maintain lower rate with fluctuation (every 40-60 batches)
    fraud_counter += 1
    # Add fluctuation: sometimes skip more batches, sometimes fewer
    batch_interval = random.randint(40, 80)  # Increased from 20-30 to decrease rate
    force_fraud_batch = (fraud_counter % batch_interval) == 0
    
    for i in range(batch_size):
        # Force fraud in some batches, or random chance
        force_fraud = force_fraud_batch and (i == 0)  # First transaction in fraud batch
        tx = generate_transaction(force_fraud=force_fraud)
        transactions.append(tx)
    
    df = pd.DataFrame(transactions, columns=columns)
    df.to_csv(STREAM_FILE, mode='a', header=not os.path.exists(STREAM_FILE), index=False)
    
    for tx in transactions:
        # Safely check for fraud flag (handle both is_fraud and fraud_prediction)
        is_fraud_flag = tx.get('is_fraud', tx.get('fraud_prediction', 0))
        fraud_indicator = "🚨 FRAUD" if is_fraud_flag == 1 else "✅ LEGIT"
        print(f"{fraud_indicator} | ₹{tx['amount']:,.2f} | {tx['transaction_type']} | {tx['location']} | Prob: {tx['fraud_probability']:.2%} → {tx['transaction_id'][:8]}")
    
    time.sleep(random.uniform(0.5, 2))  # Faster generation: 0.5 to 2 seconds delay