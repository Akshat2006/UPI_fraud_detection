#!/usr/bin/env python3
"""
Main CLI interface for UPI Fraud Detection System
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from src.scoring_system import UPIFraudScorer

def print_header():
    """Print application header"""
    print("="*70)
    print(" " * 20 + "🛡️ UPI FRAUD DETECTION SYSTEM")
    print("="*70)
    print()

def main():
    """Main function"""
    print_header()
    
    # Initialize the system
    print("🚀 Initializing fraud detection system...")
    scorer = UPIFraudScorer()
    
    # Interactive menu
    while True:
        print("\n" + "-"*40)
        print("MAIN MENU")
        print("-"*40)
        print("1. Test single transaction")
        print("2. Analyze batch of transactions")
        print("3. Run demo scenarios")
        print("4. Exit")
        print("-"*40)
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            test_single_transaction(scorer)
        elif choice == "2":
            analyze_batch(scorer)
        elif choice == "3":
            run_demo_scenarios(scorer)
        elif choice == "4":
            print("\n👋 Thank you for using UPI Fraud Detection System!")
            break
        else:
            print("\n❌ Invalid choice. Please enter 1-4.")

def test_single_transaction(scorer):
    """Test single transaction analysis"""
    print_header()
    print("🔍 SINGLE TRANSACTION ANALYSIS")
    print("-"*70)
    
    print("\nEnter transaction details (press Enter for defaults):")
    
    # Get user input with defaults
    amount = input("Amount (₹) [50000]: ").strip()
    amount = float(amount) if amount else 50000.0
    
    recipient = input("Recipient ID [RECIP_NEW123]: ").strip()
    recipient = recipient if recipient else "RECIP_NEW123"
    
    hour = input("Hour of day (0-23) [14]: ").strip()
    hour = int(hour) if hour else 14
    
    txns_last_1h = input("Transactions by user in last hour [1]: ").strip()
    txns_last_1h = int(txns_last_1h) if txns_last_1h else 1
    
    is_new_recipient = input("Is new recipient? (y/n) [y]: ").strip().lower()
    is_new_recipient = 1 if is_new_recipient in ['y', 'yes', ''] else 0
    
    # Create transaction dict
    transaction = {
        'amount': amount,
        'recipient_id': recipient,
        'hour': hour,
        'txns_last_1h': txns_last_1h,
        'is_new_recipient': is_new_recipient,
        'amount_gt_3x_avg': 1 if amount > 3000 else 0,
        'is_night': 1 if hour in [0, 1, 2, 3, 4, 5, 23] else 0,
        'time_since_last_txn': 60,
        'user_amount_mean': 1000,
        'amount_z_score': (amount - 1000) / 300
    }
    
    # Calculate risk
    print("\n🔍 Analyzing transaction...")
    result = scorer.calculate_final_score(transaction)
    
    print(f"\n📊 RISK ASSESSMENT")
    print(f"  Score: {result['risk_score']}/100")
    print(f"  Level: {result['risk_level']}")
    print(f"  Action: {result['suggested_action']}")
    
    if result['explanations']:
        print(f"\n  Reasons:")
        for reason in result['explanations']:
            print(f"    • {reason}")
    
    input("\nPress Enter to continue...")

def analyze_batch(scorer):
    """Analyze batch of transactions"""
    print_header()
    print("📊 BATCH TRANSACTION ANALYSIS")
    print("-"*70)
    
    # Load sample data
    try:
        sample_data = pd.read_csv('data/processed/demo_sample.csv')
        print(f"Loaded {len(sample_data)} sample transactions")
        
        # Create features
        from src.feature_engineer import FeatureEngineer
        engineer = FeatureEngineer()
        sample_features = engineer.create_features(sample_data)
        
        # Ask for number of transactions to analyze
        print(f"\nHow many transactions to analyze? (1-{len(sample_features)})")
        n_txns = input(f"Enter number [{min(50, len(sample_features))}]: ").strip()
        n_txns = int(n_txns) if n_txns else min(50, len(sample_features))
        n_txns = min(n_txns, len(sample_features))
        
        # Analyze batch
        print(f"\nAnalyzing {n_txns} transactions...")
        batch_results = scorer.analyze_batch(sample_features.head(n_txns))
        
        # Summary
        print(f"\n📈 SUMMARY")
        print(f"  Total analyzed: {len(batch_results)}")
        print(f"  🔴 High risk: {(batch_results['risk_level'] == 'HIGH').sum()}")
        print(f"  🟡 Medium risk: {(batch_results['risk_level'] == 'MEDIUM').sum()}")
        print(f"  🟢 Low risk: {(batch_results['risk_level'] == 'LOW').sum()}")
        
        # Show top risky
        if (batch_results['risk_level'] == 'HIGH').sum() > 0:
            print(f"\n🚨 TOP RISKY TRANSACTIONS:")
            high_risk = batch_results[batch_results['risk_level'] == 'HIGH']
            for idx, row in high_risk.head(3).iterrows():
                print(f"  {row['transaction_id']}: ₹{row['amount']:.2f} -> {row['risk_level']} ({row['risk_score']})")
        
        # Ask to save results
        save = input("\nSave results to CSV? (y/n) [n]: ").strip().lower()
        if save in ['y', 'yes']:
            filename = input("Filename [fraud_analysis_results.csv]: ").strip()
            filename = filename if filename else "fraud_analysis_results.csv"
            batch_results.to_csv(filename, index=False)
            print(f"✅ Results saved to {filename}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure you've run the data generation script first!")
    
    input("\nPress Enter to continue...")

def run_demo_scenarios(scorer):
    """Run pre-defined demo scenarios"""
    print_header()
    print("🎯 DEMO SCENARIOS")
    print("-"*70)
    
    scenarios = [
        ("🚨 MICROPAY SCAM", "₹1 verification → ₹50,000 theft", {
            "amount": 50000,
            "txns_last_1h": 2,
            "is_new_recipient": 1,
            "amount_gt_3x_avg": 1,
            "micropay_followed_by_large": 1,
            "hour": 14
        }),
        ("⚡ VELOCITY ATTACK", "9 transactions in 1 hour", {
            "amount": 20000,
            "txns_last_1h": 9,
            "is_new_recipient": 1,
            "amount_gt_3x_avg": 1,
            "hour": 3,
            "is_night": 1
        }),
        ("✅ NORMAL TRANSACTION", "Regular payment", {
            "amount": 1500,
            "txns_last_1h": 1,
            "is_new_recipient": 0,
            "amount_gt_3x_avg": 0,
            "hour": 15,
            "is_night": 0
        })
    ]
    
    for name, description, features in scenarios:
        print(f"\n{name}")
        print(f"Description: {description}")
        
        # Add default values for missing features
        default_features = {
            "time_since_last_txn": 60,
            "user_amount_mean": 1000,
            "amount_z_score": 0,
            "micropay_followed_by_large": 0,
            "high_velocity_new_recipient": 0
        }
        features.update(default_features)
        features['amount_z_score'] = (features['amount'] - 1000) / 300
        
        result = scorer.calculate_final_score(features)
        
        print(f"  Risk Score: {result['risk_score']}/100")
        print(f"  Risk Level: {result['risk_level']}")
        print(f"  Action: {result['suggested_action']}")
        
        if result['explanations']:
            print(f"  Reasons: {result['explanations'][0]}")
        
        print("-"*50)
    
    input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()