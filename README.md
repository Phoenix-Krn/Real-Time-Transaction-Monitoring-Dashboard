# 🏦 Real-Time Transaction Monitoring Dashboard

A sophisticated fraud detection and transaction monitoring system built with Streamlit, featuring real-time data processing, interactive visualizations, and comprehensive analytics.

## 🌟 Features

### 📊 Real-Time Monitoring
- **Live Transaction Stream**: Monitor transactions as they occur
- **Auto-Refresh Dashboard**: Configurable refresh intervals (1-60 seconds)
- **Fraud Detection**: AI-powered fraud prediction with probability scores
- **Transaction Timeline**: 7-day historical view with interactive charts

### 🎯 Advanced Analytics
- **Fraud Risk Gauge**: Real-time fraud rate visualization
- **KPI Dashboard**: Total transactions, fraud count, fraud rate, and volume
- **Risk Analysis**: Fraud score distribution and hourly trends
- **Location Analysis**: Geographic fraud patterns and hotspots

### 🎨 Professional UI/UX
- **Theme Support**: Light and dark themes with persistent settings
- **Responsive Design**: Optimized for desktop and tablet viewing
- **Interactive Filters**: Dynamic transaction filtering by type, location, and risk level
- **Export Functionality**: Download filtered data in CSV format

### 🔍 Fraud Management
- **Manual Review**: Suspicious transaction verification interface
- **Fraud Confirmation**: Mark transactions as confirmed fraud or not fraud
- **Session Persistence**: Maintains review state across sessions
- **High-Risk Alerts**: Automatic notifications for high-probability fraud

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


## 🛠️ Technology Stack

- **Frontend**: Streamlit 1.28+
- **Backend**: Python 3.8+
- **Data Processing**: Pandas, NumPy
- **Visualization**: Plotly, Streamlit Charts
- **Real-Time**: CSV-based data streaming
- **Styling**: Custom CSS with theme support

## 📁 Project Structure

```
Phoenix-Krn/Real-Time-Transaction-Monitoring-Dashboard/
├── dashboard_app.py              # Main Streamlit application
├── data/                         # Data directory
│   ├── scored_transactions.csv    # Real-time transaction data
│   └── historical_data.csv       # Historical transaction data
├── README.md                     # This file
└── requirements.txt              # Python dependencies
```

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- Git

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/Real-Time-Transaction-Monitoring-Dashboard.git
   cd Real-Time-Transaction-Monitoring-Dashboard
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create data directory**
   ```bash
   mkdir data
   ```

5. **Run the application**
   ```bash
   streamlit run dashboard_app.py
   ```

## 📊 Data Requirements

### Data Format

The dashboard expects CSV files with the following columns:

#### scored_transactions.csv (Real-time data)
```csv
transaction_id,amount,timestamp,processed_time,transaction_type,location,fraud_prediction,fraud_probability
```

#### historical_data.csv (Historical data)
```csv
transaction_id,amount,timestamp,processed_time,transaction_type,location,fraud_prediction,fraud_probability
```

### Sample Data Generation

To generate sample data for testing:

```python
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Generate sample transactions
def generate_sample_data(num_records=1000):
    np.random.seed(42)
    
    data = {
        'transaction_id': [f'TXN{i:06d}' for i in range(num_records)],
        'amount': np.random.uniform(10, 10000, num_records),
        'timestamp': [datetime.now() - timedelta(minutes=np.random.randint(0, 4320)) for _ in range(num_records)],
        'processed_time': [datetime.now() - timedelta(minutes=np.random.randint(0, 4320)) for _ in range(num_records)],
        'transaction_type': np.random.choice(['TRANSFER', 'PAYMENT', 'WITHDRAWAL', 'DEPOSIT'], num_records),
        'location': np.random.choice(['MUMBAI', 'DELHI', 'BANGALORE', 'CHENNAI', 'KOLKATA'], num_records),
        'fraud_prediction': np.random.choice([0, 1], num_records, p=[0.95, 0.05]),
        'fraud_probability': np.random.uniform(0, 1, num_records)
    }
    
    df = pd.DataFrame(data)
    return df

# Save sample data
sample_data = generate_sample_data()
sample_data.to_csv('data/scored_transactions.csv', index=False)
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file for configuration:

```env
# Refresh rate in seconds (default: 5)
REFRESH_RATE=5

# Theme preference (light/dark)
DEFAULT_THEME=light

# Data file paths
REALTIME_FILE=data/scored_transactions.csv
HISTORICAL_FILE=data/historical_data.csv
```

### Dashboard Settings

The dashboard includes configurable settings:

- **Auto-refresh interval**: 1-60 seconds
- **Real-time mode**: Toggle for live updates
- **Review table size**: 10-200 transactions
- **Theme selection**: Light/Dark mode

## 🎯 Usage Guide

### Monitoring Transactions

1. **Live Stream**: View real-time transactions as they're processed
2. **Fraud Alerts**: Monitor high-risk transactions (≥90% probability)
3. **KPI Overview**: Track key metrics and trends
4. **Timeline Analysis**: Examine 7-day transaction patterns

### Managing Fraud

1. **Review Suspicious Transactions**: Access the review table
2. **Verify Transactions**: Mark as fraud or not fraud
3. **Track Confirmations**: View confirmed fraud statistics
4. **Export Data**: Download filtered results

### Filtering and Analysis

1. **Apply Filters**: Filter by transaction type, location, or risk level
2. **View Analytics**: Access fraud analysis dashboard
3. **Examine Trends**: Analyze hourly and location patterns
4. **Export Insights**: Download analysis results

## 🔧 Customization

### Adding New Features

1. **New Metrics**: Add KPIs in the metrics section
2. **Custom Charts**: Implement new visualizations
3. **Additional Filters**: Extend filtering capabilities
4. **Alert Rules**: Configure custom fraud detection rules

### Styling Customization

Modify the CSS in `dashboard_app.py`:

```python
# Light theme colors
LIGHT_BACKGROUND = "#FFFFFF"
LIGHT_TEXT = "#1A1A1A"
LIGHT_PRIMARY = "#007bff"

# Dark theme colors
DARK_BACKGROUND = "#0E1117"
DARK_TEXT = "#FAFAFA"
DARK_PRIMARY = "#0056B3"
```

## 🚀 Deployment

### Streamlit Cloud

1. Push code to GitHub
2. Connect to Streamlit Cloud
3. Configure environment variables
4. Deploy

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "dashboard_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Local Production

```bash
# Install production dependencies
pip install -r requirements.txt

# Run with production settings
streamlit run dashboard_app.py --server.port=8501 --server.address=0.0.0.0
```

## 📈 Performance Optimization

### Data Processing
- Use efficient pandas operations
- Implement data caching
- Optimize CSV reading with chunking

### Dashboard Performance
- Limit displayed records
- Use lazy loading for large datasets
- Implement data pagination

### Memory Management
- Clear session state regularly
- Use garbage collection
- Optimize data types

## 🛡️ Security Considerations

- **Data Privacy**: No sensitive data logging
- **Input Validation**: Sanitize all user inputs
- **Access Control**: Implement authentication if needed
- **Secure Deployment**: Use HTTPS in production

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 Python style guide
- Add comments for complex logic
- Test with sample data
- Update documentation

## 📝 Changelog

### Version 1.0.0
- Initial release
- Real-time transaction monitoring
- Fraud detection dashboard
- Theme support (light/dark)
- Export functionality
- Manual review system

## 🐛 Troubleshooting

### Common Issues

**Dashboard not loading data**
- Check file paths in configuration
- Verify CSV format and column names
- Ensure data files exist

**Theme not persisting**
- Clear browser cache
- Check session state initialization
- Verify theme toggle functionality

**Performance issues**
- Reduce data size for testing
- Optimize refresh intervals
- Check memory usage

### Getting Help

1. Check the [Issues](https://github.com/yourusername/Real-Time-Transaction-Monitoring-Dashboard/issues) page
2. Review existing documentation
3. Create a new issue with detailed information

## 🙏 Acknowledgments

- Streamlit team for the amazing framework
- Plotly for interactive visualizations
- Open-source community for inspiration and tools

## 📞 Support

For support and questions:
- 📧 Email: kavyaravinaik2003@gmail.com
- 💬 GitHub Issues: [Create an issue](https://github.com/Phoenix-Krn/Real-Time-Transaction-Monitoring-Dashboard/issues)
- 📖 Documentation: Check this README and inline comments

---

**⭐ If this project helped you, please give it a star!**
