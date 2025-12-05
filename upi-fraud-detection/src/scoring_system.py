"""
Hybrid fraud scoring system
"""
import pickle
import numpy as np
import pandas as pd
import xgboost as xgb
from config import SCORE_WEIGHTS, RISK_LEVELS

class UPIFraudScorer:
    def __init__(self):
        """Initialize the hybrid fraud detection system"""
        self.rule_engine = None
        self.iso_forest = None
        self.xgb_model = None
        self.load_models()
        
    def load_models(self):
        """Load all trained models"""
        try:
            # Load Rule Engine
            with open('models/rule_engine.pkl', 'rb') as f:
                self.rule_engine = pickle.load(f)
                
            # Load Isolation Forest
            with open('models/isolation_forest.pkl', 'rb') as f:
                self.iso_forest = pickle.load(f)
                
            # Load XGBoost
            self.xgb_model = xgb.XGBClassifier()
            self.xgb_model.load_model('models/xgboost_model.json')
            
            print("✅ All models loaded successfully!")
            
        except Exception as e:
            print(f"❌ Error loading models: {e}")
            # Create dummy models for demo
            self.rule_engine = type('obj', (object,), {
                'calculate_score': lambda x: 0,
                'get_reasons': lambda x: []
            })()
    
    def calculate_final_score(self, transaction_features):
        """
        Calculate final fraud risk score using hybrid approach
        
        Args:
            transaction_features (dict or pd.Series): Transaction features
            
        Returns:
            dict: Risk assessment with score, level, and explanations
        """
        # Convert to dict if Series
        if isinstance(transaction_features, pd.Series):
            transaction_dict = transaction_features.to_dict()
        else:
            transaction_dict = transaction_features
        
        # 1. Rule Engine Score
        rule_score = self.rule_engine.calculate_score(transaction_dict)
        rule_reasons = self.rule_engine.get_reasons(transaction_dict)
        
        # 2. Prepare for ML models
        feature_names = list(transaction_dict.keys())
        feature_values = [transaction_dict[f] for f in feature_names]
        
        # Create DataFrame for model prediction
        X = pd.DataFrame([feature_values], columns=feature_names)
        
        # 3. Isolation Forest Anomaly Score
        try:
            iso_score = self.iso_forest.score_samples(X)[0]
            iso_normalized = 100 * (1 - (iso_score - (-0.5)) / 0.5)
            iso_normalized = max(0, min(100, iso_normalized))
        except:
            iso_normalized = 50
            iso_score = 0
        
        # 4. XGBoost Probability
        try:
            xgb_proba = self.xgb_model.predict_proba(X)[0][1]
            xgb_normalized = xgb_proba * 100
        except:
            xgb_normalized = 50
            xgb_proba = 0.5
        
        # 5. Weighted Ensemble Score
        weights = SCORE_WEIGHTS
        
        final_score = (
            weights['rule_engine'] * (rule_score / 100) +
            weights['xgboost'] * (xgb_normalized / 100) +
            weights['isolation_forest'] * (iso_normalized / 100)
        )
        
        # Convert to 0-100
        final_score_percent = final_score * 100
        
        # 6. Determine risk level
        risk_level = "LOW"
        for level, (low, high) in RISK_LEVELS.items():
            if low <= final_score_percent < high:
                risk_level = level
                break
        
        # 7. Compile explanations
        explanations = []
        if rule_reasons:
            explanations.extend(rule_reasons)
        
        if xgb_proba > 0.7:
            explanations.append(f"ML model predicts high fraud probability ({xgb_proba:.2f})")
        
        if iso_score < -0.3:
            explanations.append("Transaction shows anomalous behavior pattern")
        
        # 8. Get feature breakdown
        breakdown = {
            'rule_engine_score': round(rule_score, 2),
            'xgboost_probability': round(xgb_proba, 3),
            'anomaly_score': round(iso_score, 3),
            'anomaly_normalized': round(iso_normalized, 2)
        }
        
        # 9. Suggested action
        suggested_action = self.get_suggested_action(final_score_percent, risk_level, explanations)
        
        return {
            'risk_score': round(final_score_percent, 2),
            'risk_level': risk_level,
            'explanations': explanations[:5],
            'breakdown': breakdown,
            'suggested_action': suggested_action,
            'timestamp': pd.Timestamp.now().isoformat()
        }
    
    def get_suggested_action(self, score, level, explanations):
        """Get suggested action based on risk level"""
        if level == "HIGH":
            return "BLOCK - Require additional verification (SMS OTP + Security Questions)"
        elif level == "MEDIUM":
            if any('velocity' in exp.lower() for exp in explanations):
                return "CHALLENGE - Ask user to confirm this is not a velocity attack"
            elif any('new recipient' in exp.lower() for exp in explanations):
                return "WARN - Show warning about new recipient and require PIN confirmation"
            else:
                return "ALLOW WITH WARNING - Transaction appears suspicious"
        else:
            return "ALLOW - Transaction appears normal"
    
    def analyze_batch(self, transactions_df):
        """
        Analyze a batch of transactions
        
        Args:
            transactions_df (pd.DataFrame): DataFrame of transactions
            
        Returns:
            pd.DataFrame: Original dataframe with risk scores added
        """
        results = []
        
        print(f"Analyzing {len(transactions_df)} transactions...")
        
        for idx, row in transactions_df.iterrows():
            if idx % 100 == 0:
                print(f"  Processed {idx}/{len(transactions_df)} transactions...")
            
            # Calculate risk score
            risk_assessment = self.calculate_final_score(row)
            
            # Add to results
            results.append({
                'transaction_id': row.get('transaction_id', f'TXN_{idx}'),
                'risk_score': risk_assessment['risk_score'],
                'risk_level': risk_assessment['risk_level'],
                'suggested_action': risk_assessment['suggested_action'],
                'top_reason': risk_assessment['explanations'][0] if risk_assessment['explanations'] else 'No significant risk factors'
            })
        
        # Convert to DataFrame
        results_df = pd.DataFrame(results)
        
        # Merge with original data
        if 'transaction_id' in transactions_df.columns:
            merged_df = pd.merge(transactions_df, results_df, on='transaction_id', how='left')
        else:
            merged_df = pd.concat([transactions_df, results_df], axis=1)
        
        return merged_df

if __name__ == "__main__":
    # Test the scoring system
    from src.data_generator import generate_synthetic_transactions
    from src.feature_engineer import FeatureEngineer
    
    print("Testing scoring system...")
    
    # Create test data
    df = generate_synthetic_transactions(100)
    engineer = FeatureEngineer()
    df_features = engineer.create_features(df)
    
    # Initialize scorer
    scorer = UPIFraudScorer()
    
    # Test single transaction
    print("\n🔍 Testing single transaction...")
    sample = df_features.iloc[0]
    result = scorer.calculate_final_score(sample)
    
    print(f"\nTransaction ID: {sample.get('transaction_id', 'Unknown')}")
    print(f"Amount: ₹{sample.get('amount', 0):.2f}")
    print(f"Risk Score: {result['risk_score']}")
    print(f"Risk Level: {result['risk_level']}")
    print(f"Suggested Action: {result['suggested_action']}")
    print(f"\nReasons:")
    for reason in result['explanations']:
        print(f"  • {reason}")
    
    # Test batch analysis
    print("\n\n📊 Testing batch analysis...")
    batch_results = scorer.analyze_batch(df_features.head(10))
    
    print("\nResults summary:")
    print(batch_results[['transaction_id', 'amount', 'risk_score', 'risk_level']].head())