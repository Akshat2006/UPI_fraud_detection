#!/usr/bin/env python3
"""
Script 1: Generate synthetic UPI transaction data
Robust version that works whether or not numpy/pandas are installed.
"""

import os
import sys
import csv
import random
from datetime import datetime, timedelta

# Try to handle import errors gracefully
try:
    import numpy as np  # optional
except Exception:
    np = None

try:
    import pandas as pd
except Exception:
    pd = None

HAS_IMPORTS = pd is not None and np is not None

def generate_simple_data(n_samples=50000, fraud_rate=0.2, use_pandas=False):
    """Generate transaction data as list of dicts; return DataFrame only if use_pandas=True and pandas is available."""
    data = []
    for i in range(n_samples):
        # Basic transaction info
        timestamp = datetime.now() - timedelta(
            days=random.randint(0, 90),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )

        # User's average amount (simulated)
        # Use exponential via random.expovariate to avoid numpy dependency
        user_avg = 1000 + random.expovariate(1/9000)

        # Decide if fraud
        is_fraud = random.random() < fraud_rate

        if is_fraud:
            fraud_type = random.choice(['micropay_scam', 'velocity_attack', 'new_recipient', 'fake_refund'])

            if fraud_type == 'micropay_scam':
                amount = random.choice([1, 2, 5, 10])
            elif fraud_type == 'velocity_attack':
                amount = random.uniform(5000, 50000)
            elif fraud_type == 'new_recipient':
                amount = user_avg * random.uniform(3, 10)
            else:
                amount = random.uniform(1000, 20000)
        else:
            # normal user amount - use random.normalvariate (stdlib) instead of numpy
            amount = max(10, random.normalvariate(user_avg, user_avg/3))
            amount = min(amount, 100000)

        transaction = {
            'transaction_id': f'TXN_{i:08d}',
            'user_id': f'USER_{random.randint(1, 1000):04d}',
            'timestamp': timestamp.isoformat(sep=' '),  # store as ISO string for CSV compatibility
            'amount': round(amount, 2),
            'recipient_id': f'RECIP_{random.randint(1, 500):04d}',
            'transaction_type': random.choice(['P2P', 'P2M', 'Recharge', 'Bill Payment']),
            'device_id': f'DEV_{random.randint(1, 100):03d}',
            'location': random.choice(['Delhi', 'Mumbai', 'Bangalore', 'Chennai', 'Kolkata', 'Hyderabad']),
            'is_fraud': int(is_fraud),
            'fraud_type': fraud_type if is_fraud else 'legitimate'
        }

        data.append(transaction)

    if use_pandas and pd is not None:
        return pd.DataFrame(data)
    return data

def add_simple_patterns(data):
    """
    Add sequential fraud patterns.
    Accepts either a pandas DataFrame or list of dicts and returns same type.
    """
    if pd is not None and isinstance(data, pd.DataFrame):
        df = data
        users = df['user_id'].unique()[:100]
        for user in users:
            user_indices = df[df['user_id'] == user].index.tolist()
            if len(user_indices) > 10:
                fraud_count = max(1, len(user_indices) // 10)
                fraud_indices = random.sample(user_indices, fraud_count)
                df.loc[fraud_indices, 'is_fraud'] = 1
                df.loc[fraud_indices, 'fraud_type'] = 'velocity_attack'
        return df

    # Otherwise operate on list of dicts
    # Build mapping user_id -> list of indices
    if isinstance(data, list):
        user_map = {}
        for idx, rec in enumerate(data):
            user_map.setdefault(rec['user_id'], []).append(idx)

        # pick up to 100 users
        for user, indices in list(user_map.items())[:100]:
            if len(indices) > 10:
                fraud_count = max(1, len(indices) // 10)
                fraud_indices = random.sample(indices, fraud_count)
                for fi in fraud_indices:
                    data[fi]['is_fraud'] = 1
                    data[fi]['fraud_type'] = 'velocity_attack'
        return data

    # If unknown type, just return as-is
    return data

def save_to_csv(data, output_path):
    """
    Save data (DataFrame or list of dicts) to CSV safely.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if pd is not None and isinstance(data, pd.DataFrame):
        data.to_csv(output_path, index=False)
        return

    # list of dicts fallback
    if isinstance(data, list) and len(data) > 0:
        # ensure consistent field order
        fieldnames = list(data[0].keys())
        with open(output_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                writer.writerow(row)
        return

    # If empty or unknown structure, write an empty CSV
    with open(output_path, mode='w', newline='', encoding='utf-8') as f:
        f.write('')

def sample_data(data, sample_size=1000, random_state=42):
    """Return a sample of the data in same type (DataFrame or list)."""
    if pd is not None and isinstance(data, pd.DataFrame):
        n = min(sample_size, len(data))
        return data.sample(n, random_state=random_state)
    if isinstance(data, list):
        n = min(sample_size, len(data))
        return random.Random(random_state).sample(data, n)
    return data

def compute_stats(data):
    """Compute total transactions and fraud rate. Accepts DataFrame or list."""
    if pd is not None and isinstance(data, pd.DataFrame):
        total = len(data)
        fraud_rate = data['is_fraud'].mean() if total > 0 else 0.0
        return total, fraud_rate
    if isinstance(data, list):
        total = len(data)
        fraud_rate = sum(int(rec.get('is_fraud', 0)) for rec in data) / total if total > 0 else 0.0
        return total, fraud_rate
    return 0, 0.0

def main():
    """Main function"""
    print("="*60)
    print("STEP 1: GENERATING SYNTHETIC UPI TRANSACTION DATA")
    print("="*60)

    # Create directories if they don't exist
    os.makedirs('data/raw', exist_ok=True)
    os.makedirs('data/processed', exist_ok=True)

    # Generate data
    print("\nGenerating 50,000 synthetic transactions...")

    if pd is not None:
        df = generate_simple_data(50000, 0.2, use_pandas=True)
        df = add_simple_patterns(df)
        # Save using pandas for performance
        output_path = 'data/raw/synthetic_upi_transactions.csv'
        save_to_csv(df, output_path)
    else:
        print("⚠️  Missing pandas (or numpy). Using fallback data generation...")
        data = generate_simple_data(1000, 0.2, use_pandas=False)
        data = add_simple_patterns(data)
        output_path = 'data/raw/synthetic_upi_transactions.csv'
        save_to_csv(data, output_path)
        # To keep downstream code readable, we can also convert to DataFrame-like summary if needed

    # Statistics
    if pd is not None:
        total, fraud_rate = compute_stats(df)
    else:
        total, fraud_rate = compute_stats(data)

    print(f"\n✅ Data generation complete!")
    print(f"Saved to: {output_path}")
    print(f"Total transactions: {total:,}")
    print(f"Fraud rate: {fraud_rate:.2%}")

    # Create a smaller sample for demo
    if pd is not None:
        sample_df = sample_data(df, sample_size=1000, random_state=42)
        sample_path = 'data/processed/demo_sample.csv'
        save_to_csv(sample_df, sample_path)
        print(f"\nCreated demo sample: {sample_path} ({len(sample_df)} transactions)")
    else:
        sample_list = sample_data(data, sample_size=1000, random_state=42)
        sample_path = 'data/processed/demo_sample.csv'
        save_to_csv(sample_list, sample_path)
        print(f"\nCreated demo sample: {sample_path} ({len(sample_list)} transactions)")

    return True

if __name__ == "__main__":
    main()