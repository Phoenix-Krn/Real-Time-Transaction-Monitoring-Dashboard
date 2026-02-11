# Real-Time Fraud Detection System

This project simulates a **real-time fraud detection pipeline** for banking transactions. It combines synthetic data generation, machine learning (XGBoost), and a live **Streamlit dashboard** to mimic how banks monitor and flag suspicious activity.

---

## 🔄 Workflow Overview

1. **Start**  
   - System initialization begins the transaction monitoring cycle.  
   - Loads required modules: data simulator, fraud detection model, and dashboard interface.

2. **Generate Transaction Data**  
   - Synthetic transaction records are generated using Python to simulate real-time banking activity.  
   - Each transaction includes:  
     - Transaction ID  
     - Amount  
     - Location  
     - Fraud Probability  
     - Processing Time  
     - Status  

3. **Train Fraud Detection Model**  
   - Historical synthetic data is used to train an **XGBoost Classifier**.  
   - Fraud is flagged if:  
     - `is_fraud = 1` (simulator label), OR  
     - Fraud probability ≥ 75% (when simulator flag = 0).  
   - The model learns transaction patterns to identify suspicious behavior.

4. **Predict Fraud on Live Stream**  
   - Incoming transactions are scored in real time.  
   - Each record is assigned a **risk score** and classified as normal or fraudulent.  
   - Mimics predictive checks used in real-world banking systems.

5. **Update Dashboard**  
   - Built with **Streamlit**, the dashboard provides live monitoring.  
   - Displays:  
     - Total transactions  
     - Successful vs. failed counts  
     - Fraud count  
     - Processing time trends  
   - Auto-refresh ensures continuous updates.

6. **Display Alerts & Fraud Trends**  
   - Suspicious transactions trigger **visual alerts** (e.g., red highlights, warning icons).  
   - Fraud trend graphs show risky transaction patterns over time.  
   - Helps operations teams take quick action (manual review or account flagging).

7. **End (Looping System)**  
   - One cycle completes when all transactions in a stream are analyzed.  
   - The system runs continuously, repeating the cycle for real-time monitoring.

---

## 🏗️ Architecture

The system has **three layers**:

1. **Data Simulator Layer**  
   - `create_historical_data()` → Generates synthetic historical data (`Historical data.csv`).  
   - `simulate_realtime_stream()` → Simulates continuous live transaction flow.  

2. **Processing Layer (AI Engine)**  
   - `train_and_save_model()` → Trains XGBoost model on historical data, saves as `xgboost_fraud_model.joblib`.  
   - `score_realtime_transactions()` → Scores live transactions, outputs `scored_transactions.csv`.  

3. **Visualization Layer (Dashboard)**  
   - `key_matrices()` → Shows performance metrics (fraud detection rate, accuracy, precision).  
   - `visualize_graph()` → Real-time charts for fraud vs. normal trends.  
   - `view_table()` → Displays live table of scored transactions.  
   - `autorefresh_setup()` → Ensures dashboard updates continuously.  

---

## ⚡ Features

- Real-time transaction simulation  
- Fraud detection using **XGBoost**  
- Continuous scoring of live streams  
- Interactive **Streamlit dashboard**  
- Auto-refresh with fraud alerts and trend visualization  

---
