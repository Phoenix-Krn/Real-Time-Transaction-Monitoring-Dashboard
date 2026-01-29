# Fraud Detection Criteria

This document explains how transactions are classified as fraudulent in the system.

## Overview

The system uses a **hybrid approach** combining:
1. **Simulator-based fraud flags** (for testing/demo)
2. **Machine Learning (XGBoost) model predictions** (for real-world detection)

## Final Fraud Classification

A transaction is marked as **FRAUD** (`fraud_prediction = 1`) if:

### Primary Criteria (Priority 1):
- **Simulator Flag**: If the data simulator marked `is_fraud = 1`, the transaction is **automatically classified as fraud**, regardless of ML model prediction.

### Secondary Criteria (Priority 2):
- **ML Model Prediction**: If simulator flag is `0` or not present, the transaction is classified as fraud if:
  - **Fraud Probability ≥ 0.5** (THRESHOLD in `03_processor_scorer.py`)
  - The ML model's predicted probability of fraud is 50% or higher

## Fraud Probability Calculation

The final `fraud_probability` is determined as:
- **If simulator marked as fraud**: Uses the **maximum** of:
  - Simulator's fraud probability (usually 0.85-0.99)
  - ML model's predicted probability
- **If simulator marked as legitimate**: Uses only the ML model's predicted probability

## ML Model Features

The XGBoost model uses the following features to predict fraud:

### 1. **Transaction Amount**
   - Raw amount value
   - Log-transformed amount (`amount_log = log(1 + amount)`)

### 2. **Transaction Type** (One-hot encoded)
   - PURCHASE
   - WITHDRAWAL
   - DEPOSIT
   - WIRE_TRANSFER
   - UPI
   - IMPS
   - NEFT
   - RTGS

### 3. **Location** (One-hot encoded)
   - Mumbai, Delhi, Bangalore, Hyderabad, Chennai, Kolkata, Pune, Ahmedabad, Andhra Pradesh
   - (Model was trained on: NYC, BOS, DAL, PHI, CHIC, MIA, NY, LA, UK, CHINA)

### 4. **Time Features**
   - **Hour of day** (0-23)
   - **Day of week** (0-6, Monday=0)

## Simulator Fraud Generation Criteria

For testing/demo purposes, the simulator marks transactions as fraud based on:

### 1. **Random Chance (30%)**
   - 20% of all transactions are randomly marked as fraud
   - These have high fraud probability (0.85-0.99)

### 2. **Dynamic Fraud Rate**
   - Base rate varies by time of day:
     - **Night (0-6 AM)**: 8% base rate
     - **Morning (6-12 PM)**: 3% base rate
     - **Afternoon (12-6 PM)**: 4% base rate
     - **Evening (6-12 PM)**: 6% base rate

### 3. **Pattern-Based Adjustments**
   - **UPI + Mumbai**: +5% fraud rate
   - **WITHDRAWAL + Delhi**: +3% fraud rate
   - **Kolkata location**: +2% fraud rate
   - Maximum cap: 20% fraud rate

### 4. **Fraud Transaction Characteristics**
   - Higher transaction amounts (exponential scale=15000 vs 8000 for legitimate)
   - High fraud probability (0.85-0.99)

## Configuration

### Threshold Settings
- **Fraud Detection Threshold**: `THRESHOLD = 0.5` in `03_processor_scorer.py`
  - Transactions with probability ≥ 0.5 are classified as fraud
  - You can adjust this threshold:
    - **Lower (e.g., 0.3)**: More sensitive, catches more frauds but more false positives
    - **Higher (e.g., 0.7)**: Less sensitive, fewer false positives but might miss some frauds

### Model Training
- Model was trained on 10,000 synthetic transactions
- Training data had 4% fraud rate (96% legitimate, 4% fraud)
- Features: amount, transaction_type, location, hour, day_of_week

## Summary

**A transaction is counted as FRAUD if:**
1. ✅ Simulator marked it as fraud (`is_fraud = 1`), OR
2. ✅ ML model predicted fraud probability ≥ 50% (when simulator flag is 0)

**Fraud Probability** is the higher value between:
- Simulator's probability (if marked as fraud)
- ML model's predicted probability

## Example Scenarios

<<<<<<< HEAD
___________________________________________________________________________________________
| Simulator Flag | ML Model Prob | Final Fraud Prediction | Reason                        |
|----------------|---------------|------------------------|-------------------------------|
| 1 (Fraud)      | 0.3           | **1 (Fraud)**          | Simulator flag takes priority |
| 0 (Legit)      | 0.7           | **1 (Fraud)**          | ML model probability > 0.5    |
| 0 (Legit)      | 0.3           | **0 (Legit)**          | ML model probability < 0.5    |
| 1 (Fraud)      | 0.8           | **1 (Fraud)**          | Simulator flag + high ML prob |
|________________|_______________|________________________|_______________________________|
=======
| Simulator Flag | ML Model Prob | Final Fraud Prediction | Reason |
|---------------|---------------|------------------------|--------|
| 1 (Fraud) | 0.3 | **1 (Fraud)** | Simulator flag takes priority |
| 0 (Legit) | 0.7 | **1 (Fraud)** | ML model probability > 0.5 |
| 0 (Legit) | 0.3 | **0 (Legit)** | ML model probability < 0.5 |
| 1 (Fraud) | 0.8 | **1 (Fraud)** | Simulator flag + high ML prob |


## Adjusting Fraud Detection

To change fraud detection sensitivity:

1. **Modify Threshold** in `03_processor_scorer.py`:
   ```python
   THRESHOLD = 0.5  # Change to 0.3 (more sensitive) or 0.7 (less sensitive)
   ```

2. **Modify Simulator Fraud Rate** in `data_simulator.py`:
   ```python
   if force_fraud or random.random() < 0.3:  # Change 0.3 to desired rate
   ```

3. **Retrain Model** with different training data in `02_model_trainer.py`

