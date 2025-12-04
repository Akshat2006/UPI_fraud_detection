import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import json

class UPITransactionGenerator:
    def __init__(self, seed=42):
        np.random.seed(seed)
        random.seed(seed)

        self.user_profiles = {
            'low_income': {'avg_amount': 500, 'freq': 2, 'balance': 10000},
            'medium_income': {'avg_amount': 2000, 'freq': 5, 'balance': 50000},
            'high_income': {'avg_amount': 10000, 'freq': 10, 'balance': 200000}
        }

        self.recipient_categories = ['family', 'friend', 'merchant', 'utility', 'unknown']

        self.merchant_risk = {
            'ecommerce': 0.3,
            'food_delivery': 0.2,
            'bill_payment': 0.1,
            'travel': 0.4,
            'investment': 0.6,
            'gaming': 0.7,
            'loan_app': 0.8
        }

        self.fraud_patterns = {
            'micropay_scam': {
                'description': 'Small verification payment followed by large withdrawal',
                'pattern': [('amount', 'small'), ('time_gap', 'short'), ('amount', 'large')]
            },
            'velocity_attack': {
                'description': 'Multiple rapid transactions',
                'pattern': [('count_10min', 'high'), ('recipient', 'varied')]
            },
            'fake_refund': {
                'description': 'Fake refund request',
                'pattern': [('is_refund', True), ('amount', 'high')]
            },
            'new_recipient_scam': {
                'description': 'High amount to new recipient',
                'pattern': [('is_new_recipient', True), ('amount', 'high')]
            },
            'odd_hour_fraud': {
                'description': 'Transaction at suspicious hours',
                'pattern': [('hour', 'odd'), ('amount', 'medium')]
            }
        }
    
    def generate_user(self, user_id):
        """Generate a user profile"""
        profile_type = random.choice(list(self.user_profiles.keys()))
        profile = self.user_profiles[profile_type].copy()
        
        return {
            'user_id': f"USER_{user_id:06d}",
            'profile_type': profile_type,
            'avg_transaction_amount': profile['avg_amount'],
            'daily_frequency': profile['freq'],
            'account_balance': profile['balance'],
            'device_age_days': np.random.randint(30, 365),
            'trust_score': np.random.beta(3, 1),  # Most users are trustworthy
            'frequent_recipients': self._generate_frequent_recipients()
        }
    
    def _generate_frequent_recipients(self):
        """Generate frequent recipients for a user"""
        n_recipients = np.random.poisson(5)
        recipients = []
        
        for i in range(max(1, n_recipients)):
            recipients.append({
                'recipient_id': f"REC_{np.random.randint(1000, 9999)}",
                'category': random.choice(self.recipient_categories),
                'transaction_count': np.random.poisson(3),
                'total_amount': np.random.exponential(5000)
            })
        
        return recipients

    