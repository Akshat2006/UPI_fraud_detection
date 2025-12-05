"""
Train and save machine learning models
"""
import pandas as pd
import numpy as np
import pickle
import xgboost as xgb
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import SMOTE
from sklearn.metrics import classification_report, roc_auc_score
from config import RANDOM_STATE, TEST_SIZE

class ModelTrainer:
    def __init__(self):
        self.feature_columns = None
        self.iso_forest = None
        self.xgb_model = None
        self.rf_model = None
        self.rule_engine = None
    
    def prepare_data(self, df, feature_columns, target_column='is_fraud'):
        """Prepare data for training"""
        X = df[feature_columns].copy()
        y = df[target_column].copy()
        
        # Handle NaN values
        X = X.fillna(X.mean())
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
        )
        
        # Handle class imbalance with SMOTE
        smote = SMOTE(random_state=RANDOM_STATE)
        X_train_balanced, y_train_balanced = smote.fit_resample(X_train, y_train)
        
        return {
            'X_train': X_train,
            'X_test': X_test,
            'y_train': y_train,
            'y_test': y_test,
            'X_train_balanced': X_train_balanced,
            'y_train_balanced': y_train_balanced
        }
    
    def train_isolation_forest(self, X_train):
        """Train Isolation Forest for anomaly detection"""
        print("Training Isolation Forest...")
        
        iso_forest = IsolationForest(
            n_estimators=100,
            max_samples='auto',
            contamination=0.2,
            random_state=RANDOM_STATE,
            verbose=0
        )
        
        iso_forest.fit(X_train)
        self.iso_forest = iso_forest
        
        print("Isolation Forest trained!")
        return iso_forest
    
    def train_xgboost(self, X_train, y_train):
        """Train XGBoost classifier"""
        print("Training XGBoost...")
        
        xgb_model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            scale_pos_weight=4,
            random_state=RANDOM_STATE,
            eval_metric='auc',
            use_label_encoder=False
        )
        
        xgb_model.fit(X_train, y_train)
        self.xgb_model = xgb_model
        
        print("XGBoost trained!")
        return xgb_model
    
    def train_random_forest(self, X_train, y_train):
        """Train Random Forest classifier"""
        print("Training Random Forest...")
        
        rf_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=RANDOM_STATE,
            class_weight='balanced',
            n_jobs=-1
        )
        
        rf_model.fit(X_train, y_train)
        self.rf_model = rf_model
        
        print("Random Forest trained!")
        return rf_model
    
    def create_rule_engine(self):
        """Create rule-based fraud detection engine"""
        print("Creating Rule Engine...")
        
        class RuleEngine:
            def __init__(self):
                from config import RULE_THRESHOLDS
                self.thresholds = RULE_THRESHOLDS
            
            def calculate_score(self, transaction):
                score = 0
                
                # Velocity attack
                txns_last_1h = transaction.get('txns_last_1h', 0)
                if txns_last_1h > self.thresholds['velocity_1h']:
                    score += min(txns_last_1h * 5, 30)
                
                # New recipient with high amount
                if (transaction.get('is_new_recipient', 0) == 1 and 
                    transaction.get('amount_gt_3x_avg', 0) == 1):
                    score += 25
                
                # Micropayment followed by large amount
                if transaction.get('micropay_followed_by_large', 0) == 1:
                    score += 40
                
                # Suspicious timing
                if transaction.get('is_night', 0) == 1:
                    score += 15
                
                # High amount z-score
                amount_z = abs(transaction.get('amount_z_score', 0))
                if amount_z > 3:
                    score += min(amount_z * 5, 20)
                
                # High velocity with new recipient
                if transaction.get('high_velocity_new_recipient', 0) == 1:
                    score += 35
                
                return min(score, 100)
            
            def get_reasons(self, transaction):
                reasons = []
                
                if transaction.get('txns_last_1h', 0) > self.thresholds['velocity_1h']:
                    reasons.append(f"High velocity: {transaction['txns_last_1h']} transactions in last hour")
                
                if (transaction.get('is_new_recipient', 0) == 1 and 
                    transaction.get('amount_gt_3x_avg', 0) == 1):
                    reasons.append("New recipient with amount > 3x average")
                
                if transaction.get('micropay_followed_by_large', 0) == 1:
                    reasons.append("Micropayment followed by large transaction")
                
                if transaction.get('is_night', 0) == 1:
                    reasons.append("Transaction during suspicious hours")
                
                if abs(transaction.get('amount_z_score', 0)) > 3:
                    reasons.append(f"Amount significantly different from average")
                
                if transaction.get('high_velocity_new_recipient', 0) == 1:
                    reasons.append("High transaction velocity with new recipient")
                
                return reasons
        
        self.rule_engine = RuleEngine()
        print("Rule Engine created!")
        return self.rule_engine
    
    def evaluate_models(self, X_test, y_test):
        """Evaluate all trained models"""
        print("\n" + "="*50)
        print("MODEL EVALUATION")
        print("="*50)
        
        results = {}
        
        # Evaluate Isolation Forest
        if self.iso_forest:
            iso_scores = self.iso_forest.score_samples(X_test)
            iso_predictions = (iso_scores < np.percentile(iso_scores, 20)).astype(int)
            results['isolation_forest'] = {
                'predictions': iso_predictions,
                'scores': iso_scores,
                'roc_auc': roc_auc_score(y_test, -iso_scores)
            }
            print(f"Isolation Forest ROC-AUC: {results['isolation_forest']['roc_auc']:.4f}")
        
        # Evaluate XGBoost
        if self.xgb_model:
            xgb_predictions = self.xgb_model.predict(X_test)
            xgb_probabilities = self.xgb_model.predict_proba(X_test)[:, 1]
            results['xgboost'] = {
                'predictions': xgb_predictions,
                'probabilities': xgb_probabilities,
                'roc_auc': roc_auc_score(y_test, xgb_probabilities)
            }
            print(f"XGBoost ROC-AUC: {results['xgboost']['roc_auc']:.4f}")
            print("\nXGBoost Classification Report:")
            print(classification_report(y_test, xgb_predictions))
        
        # Evaluate Random Forest
        if self.rf_model:
            rf_predictions = self.rf_model.predict(X_test)
            rf_probabilities = self.rf_model.predict_proba(X_test)[:, 1]
            results['random_forest'] = {
                'predictions': rf_predictions,
                'probabilities': rf_probabilities,
                'roc_auc': roc_auc_score(y_test, rf_probabilities)
            }
            print(f"Random Forest ROC-AUC: {results['random_forest']['roc_auc']:.4f}")
        
        return results
    
    def save_models(self):
        """Save all trained models"""
        print("\nSaving models...")
        
        # Save Isolation Forest
        if self.iso_forest:
            with open('models/isolation_forest.pkl', 'wb') as f:
                pickle.dump(self.iso_forest, f)
        
        # Save XGBoost
        if self.xgb_model:
            self.xgb_model.save_model('models/xgboost_model.json')
        
        # Save Random Forest
        if self.rf_model:
            with open('models/random_forest.pkl', 'wb') as f:
                pickle.dump(self.rf_model, f)
        
        # Save Rule Engine
        if self.rule_engine:
            with open('models/rule_engine.pkl', 'wb') as f:
                pickle.dump(self.rule_engine, f)
        
        print("All models saved to models/ directory!")

if __name__ == "__main__":
    # Test the model trainer
    from src.data_generator import generate_synthetic_transactions, add_sequential_patterns
    from src.feature_engineer import FeatureEngineer
    
    print("Testing model training pipeline...")
    
    # Generate data
    df = generate_synthetic_transactions(10000)
    df = add_sequential_patterns(df)
    
    # Create features
    engineer = FeatureEngineer()
    df_features = engineer.create_features(df)
    
    # Train models
    trainer = ModelTrainer()
    data = trainer.prepare_data(df_features, engineer.get_feature_columns())
    
    trainer.train_isolation_forest(data['X_train'])
    trainer.train_xgboost(data['X_train_balanced'], data['y_train_balanced'])
    trainer.train_random_forest(data['X_train_balanced'], data['y_train_balanced'])
    trainer.create_rule_engine()
    
    # Evaluate
    results = trainer.evaluate_models(data['X_test'], data['y_test'])
    
    # Save models
    trainer.save_models()