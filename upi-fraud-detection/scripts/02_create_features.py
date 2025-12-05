#!/usr/bin/env python3
"""
Script 2: Create features from raw data
Simplified robust version
"""

import os
import sys
import csv
import math
import random
from datetime import datetime

# Try imports
try:
    import pandas as pd
except Exception:
    pd = None

try:
    import numpy as np
except Exception:
    np = None

def create_simple_features_from_csv(input_path):
    """Create basic features from CSV without pandas dependency."""
    
    # Read CSV
    data = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    
    if not data:
        return [], []
    
    # Process each record
    features = []
    labels = []
    
    for i, row in enumerate(data):
        try:
            amount = float(row.get('amount', 0))
            timestamp = row.get('timestamp', '')
            user_id = row.get('user_id', '')
            is_fraud = int(row.get('is_fraud', 0))
            
            # Parse timestamp
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                hour = dt.hour
                day_of_week = dt.weekday()
            except:
                hour = random.randint(0, 23)
                day_of_week = random.randint(0, 6)
            
            # Simple features
            feat = {
                'amount': amount,
                'hour': hour,
                'day_of_week': day_of_week,
                'is_weekend': 1 if day_of_week in [5, 6] else 0,
                'is_night': 1 if hour in [0, 1, 2, 3, 4, 5, 23] else 0,
                'amount_log': math.log1p(amount),
                'high_amount': 1 if amount > 10000 else 0,
                'suspicious_time': 1 if hour < 6 else 0,
                'user_hash': hash(user_id) % 100  # simple user feature
            }
            
            features.append(feat)
            labels.append(is_fraud)
            
        except Exception as e:
            # Skip bad records
            continue
    
    return features, labels

def save_features_csv(features, labels, output_prefix):
    """Save features and labels to CSV files."""
    if not features:
        return
    
    # Save features
    feature_keys = features[0].keys()
    with open(f'{output_prefix}_features.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=feature_keys)
        writer.writeheader()
        writer.writerows(features)
    
    # Save labels
    with open(f'{output_prefix}_labels.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['is_fraud'])
        for label in labels:
            writer.writerow([label])

def main():
    """Main function"""
    print("="*60)
    print("STEP 2: FEATURE ENGINEERING")
    print("="*60)
    
    # Create directories
    os.makedirs('data/processed', exist_ok=True)
    
    # Check input file
    input_path = 'data/raw/synthetic_upi_transactions.csv'
    if not os.path.exists(input_path):
        print(f"❌ Data file not found: {input_path}")
        print("Please run script 01_generate_data.py first")
        
        # Create minimal data
        print("Creating minimal data for demo...")
        with open('data/raw/dummy.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['amount', 'timestamp', 'user_id', 'is_fraud'])
            for i in range(100):
                writer.writerow([random.randint(100, 50000), 
                               datetime.now().isoformat(), 
                               f'USER_{i%10}', 
                               random.choice([0, 0, 0, 0, 1])])
        input_path = 'data/raw/dummy.csv'
    
    print(f"\nProcessing data from {input_path}...")
    
    # Create features
    features, labels = create_simple_features_from_csv(input_path)
    
    if not features:
        print("❌ No features created!")
        return False
    
    print(f"Created {len(features)} feature vectors with {len(features[0])} features each")
    
    # Split into train/test (80/20)
    split_idx = int(0.8 * len(features))
    train_features = features[:split_idx]
    train_labels = labels[:split_idx]
    test_features = features[split_idx:]
    test_labels = labels[split_idx:]
    
    # Save processed data
    print("\n💾 Saving processed data...")
    save_features_csv(train_features, train_labels, 'data/processed/train')
    save_features_csv(test_features, test_labels, 'data/processed/test')
    
    # Statistics
    fraud_rate = sum(labels) / len(labels) if labels else 0
    print(f"\n✅ Feature engineering complete!")
    print(f"   Training samples: {len(train_features)}")
    print(f"   Test samples: {len(test_features)}")
    print(f"   Fraud rate: {fraud_rate:.1%}")
    
    return True

if __name__ == "__main__":
    main()