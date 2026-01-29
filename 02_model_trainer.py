import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
import joblib
import os

def generate_training_data(n=10000):
    np.random.seed(42)
    data = []
    for _ in range(n):
        amount = np.random.lognormal(mean=7, sigma=1)
        is_fraud = np.random.choice([0, 1], p=[0.96, 0.04])
        tx_type = np.random.choice(['PURCHASE', 'WITHDRAWAL', 'DEPOSIT', 'WIRE_TRANSFER'])
        location = np.random.choice(['NYC', 'BOS', 'DAL', 'PHI', 'CHIC', 'MIA', 'NY', 'LA', 'UK', 'CHINA'])
        hour = np.random.randint(0, 24)
        day_of_week = np.random.randint(0, 7)

        data.append({
            'amount': amount,
            'transaction_type': tx_type,
            'location': location,
            'hour': hour,
            'day_of_week': day_of_week,
            'is_fraud': is_fraud
        })

    return pd.DataFrame(data)

df = generate_training_data()
df['amount_log'] = np.log1p(df['amount'])
df = pd.get_dummies(df, columns=['transaction_type', 'location'], drop_first=True)

X = df.drop('is_fraud', axis=1)
y = df['is_fraud']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = XGBClassifier(use_label_encoder=False, eval_metric='logloss')
model.fit(X_train, y_train)

os.makedirs("data", exist_ok=True)
joblib.dump(model, "xgboost_fraud_model.joblib")
print("✅ Model trained and saved as xgboost_fraud_model.joblib")