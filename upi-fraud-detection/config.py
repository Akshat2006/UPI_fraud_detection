# Configuration file for UPI Fraud Detection System

# Paths
DATA_PATH = "data/raw/synthetic_upi_transactions.csv"
SAMPLE_PATH = "data/processed/demo_sample.csv"
MODEL_PATH = "models/"

# Model parameters
RANDOM_STATE = 42
TEST_SIZE = 0.2
FRAUD_RATE = 0.2

# Feature Engineering parameters
VELOCITY_WINDOWS = ['1h', '6h', '24h', '7d']

# Rule Engine thresholds
RULE_THRESHOLDS = {
    'velocity_1h': 5,
    'velocity_24h': 20,
    'new_recipient_amount_multiplier': 3,
    'micropay_threshold': 10,
    'time_suspicious_hours': [0, 1, 2, 3, 4, 5, 23],
}

# Scoring weights
SCORE_WEIGHTS = {
    'rule_engine': 0.3,
    'xgboost': 0.4,
    'isolation_forest': 0.3,
}

# Risk levels
RISK_LEVELS = {
    'LOW': (0, 40),
    'MEDIUM': (40, 70),
    'HIGH': (70, 100)
}