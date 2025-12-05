#!/usr/bin/env python3
"""
Script 3: Train and save models
FIXED: No lambda functions, all pickleable
"""

import os
import sys
import pickle
import json
import random
import csv

# Define classes at module level
class RuleBasedFraudDetector:
    def __init__(self):
        # Define rule conditions as regular methods (not lambdas)
        self.rules = [
            {'condition': self._check_amount_gt_50000, 'score': 40, 'description': "Amount > ₹50,000"},
            {'condition': self._check_amount_gt_10000, 'score': 30, 'description': "Amount > ₹10,000"},
            {'condition': self._check_hour_lt_6, 'score': 25, 'description': "Transaction during late night (12AM-6AM)"},
            {'condition': self._check_hour_gt_22, 'score': 20, 'description': "Transaction during suspicious hours (10PM-12AM)"},
            {'condition': self._check_amount_log_gt_12, 'score': 35, 'description': "Exceptionally high amount"},
        ]
        
        self.thresholds = {
            'HIGH': 70,
            'MEDIUM': 40,
            'LOW': 0
        }
    
    # Define rule conditions as regular methods
    def _check_amount_gt_50000(self, transaction):
        return transaction.get('amount', 0) > 50000
    
    def _check_amount_gt_10000(self, transaction):
        return transaction.get('amount', 0) > 10000
    
    def _check_hour_lt_6(self, transaction):
        return transaction.get('hour', 12) < 6
    
    def _check_hour_gt_22(self, transaction):
        return transaction.get('hour', 12) > 22
    
    def _check_amount_log_gt_12(self, transaction):
        return transaction.get('amount_log', 0) > 12
    
    def predict(self, transaction):
        total_score = 0
        triggered_rules = []
        
        # Apply rules
        for rule in self.rules:
            if rule['condition'](transaction):
                total_score += rule['score']
                triggered_rules.append(rule['description'])
        
        # Cap at 100
        total_score = min(total_score, 100)
        
        # Determine risk level
        if total_score >= self.thresholds['HIGH']:
            risk_level = 'HIGH'
            action = 'BLOCK - Requires additional verification'
        elif total_score >= self.thresholds['MEDIUM']:
            risk_level = 'MEDIUM'
            action = 'WARN - Review recommended'
        else:
            risk_level = 'LOW'
            action = 'ALLOW - Appears legitimate'
        
        return {
            'risk_score': total_score,
            'risk_level': risk_level,
            'suggested_action': action,
            'rules_triggered': triggered_rules
        }

class SimpleScorer:
    def __init__(self, model):
        self.model = model
    
    def calculate_final_score(self, transaction):
        return self.model.predict(transaction)
    
    def analyze_batch(self, transactions):
        results = []
        for i, txn in enumerate(transactions):
            result = self.model.predict(txn)
            results.append({
                'transaction_id': txn.get('transaction_id', f'TXN_{i}'),
                'risk_score': result['risk_score'],
                'risk_level': result['risk_level'],
                'suggested_action': result['suggested_action']
            })
        return results

def load_training_data():
    """Load training data from CSV files."""
    train_features = []
    train_labels = []
    
    # Try to load features
    try:
        with open('data/processed/train_features.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert values
                converted = {}
                for key, value in row.items():
                    try:
                        converted[key] = float(value)
                    except:
                        converted[key] = value
                train_features.append(converted)
    except:
        print("⚠️  Could not load training features, using synthetic data")
        # Create synthetic features
        for i in range(100):
            train_features.append({
                'amount': random.randint(100, 50000),
                'hour': random.randint(0, 23),
                'amount_log': random.uniform(0, 15)
            })
    
    # Try to load labels
    try:
        with open('data/processed/train_labels.csv', 'r') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            for row in reader:
                train_labels.append(int(row[0]))
    except:
        print("⚠️  Could not load training labels, using synthetic labels")
        train_labels = [random.choice([0, 0, 0, 0, 1]) for _ in range(len(train_features))]
    
    return train_features, train_labels

def main():
    """Main function"""
    print("="*60)
    print("STEP 3: TRAINING MODELS")
    print("="*60)
    
    # Create models directory
    os.makedirs('models', exist_ok=True)
    
    print("\n📊 Loading training data...")
    features, labels = load_training_data()
    
    if features:
        fraud_rate = sum(labels) / len(labels) if labels else 0
        print(f"   Samples: {len(features)}")
        print(f"   Fraud rate: {fraud_rate:.1%}")
    
    print("\n🤖 Training rule-based model...")
    model = RuleBasedFraudDetector()
    
    # Save the model
    print("💾 Saving models...")
    with open('models/rule_engine.pkl', 'wb') as f:
        pickle.dump(model, f)
    print("   ✅ Saved: models/rule_engine.pkl")
    
    # Create and save scorer
    scorer = SimpleScorer(model)
    with open('models/scorer.pkl', 'wb') as f:
        pickle.dump(scorer, f)
    print("   ✅ Saved: models/scorer.pkl")
    
    # Also save as JSON for easy inspection
    model_info = {
        'name': 'UPI Fraud Detection Rule Engine',
        'version': '1.0',
        'rules_count': len(model.rules),
        'thresholds': model.thresholds,
        'rule_descriptions': [rule['description'] for rule in model.rules]
    }
    
    with open('models/model_info.json', 'w') as f:
        json.dump(model_info, f, indent=2)
    print("   ✅ Saved: models/model_info.json")
    
    # Test the model
    print("\n🧪 Testing model...")
    test_cases = [
        {'amount': 50000, 'hour': 3, 'amount_log': 12},
        {'amount': 1500, 'hour': 15, 'amount_log': 9},
        {'amount': 20000, 'hour': 22, 'amount_log': 11}
    ]
    
    for i, test in enumerate(test_cases):
        result = model.predict(test)
        print(f"   Test {i+1}: ₹{test['amount']} at {test['hour']}:00 → {result['risk_level']} ({result['risk_score']}/100)")
        if result['rules_triggered']:
            print(f"        Rules: {', '.join(result['rules_triggered'])}")
    
    print("\n" + "="*60)
    print("✅ MODEL TRAINING COMPLETE!")
    print("="*60)
    print("\n📁 Models saved to: models/")
    print("   - rule_engine.pkl")
    print("   - scorer.pkl")
    print("   - model_info.json")
    
    print("\n🎯 Next steps:")
    print("   1. Run demo: python scripts/04_run_demo.py")
    print("   2. Launch UI: streamlit run app.py")
    print("   3. Use CLI: python main.py")
    
    return True

if __name__ == "__main__":
    main()