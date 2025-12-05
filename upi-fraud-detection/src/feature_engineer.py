"""
Feature engineering for UPI transactions
"""
import pandas as pd
import numpy as np
from datetime import timedelta
from config import RULE_THRESHOLDS

class FeatureEngineer:
    def __init__(self):
        pass
    
    def create_features(self, df):
        """Create all features from raw transaction data"""
        df = df.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values(['user_id', 'timestamp'])
        
        # Velocity features
        df = self._create_velocity_features(df)
        
        # Amount features
        df = self._create_amount_features(df)
        
        # Temporal features
        df = self._create_temporal_features(df)
        
        # Recipient features
        df = self._create_recipient_features(df)
        
        # Interaction features
        df = self._create_interaction_features(df)
        
        return df
    
    def _create_velocity_features(self, df):
        """Create transaction velocity features"""
        df = df.copy()
        
        windows = {
            '1h': pd.Timedelta(hours=1),
            '6h': pd.Timedelta(hours=6),
            '24h': pd.Timedelta(hours=24),
            '7d': pd.Timedelta(days=7)
        }
        
        for window_name, window_size in windows.items():
            feature_name = f'txns_last_{window_name}'
            df[feature_name] = 0
        
        for user in df['user_id'].unique():
            user_mask = df['user_id'] == user
            user_times = df.loc[user_mask, 'timestamp']
            user_indices = df[user_mask].index
            
            for idx, time in zip(user_indices, user_times):
                for window_name, window_size in windows.items():
                    window_start = time - window_size
                    count = ((user_times > window_start) & (user_times < time)).sum()
                    df.at[idx, f'txns_last_{window_name}'] = count
        
        return df
    
    def _create_amount_features(self, df):
        """Create amount-based features"""
        # User-level statistics
        user_stats = df.groupby('user_id')['amount'].agg(['mean', 'std', 'min', 'max']).reset_index()
        user_stats.columns = ['user_id', 'user_amount_mean', 'user_amount_std', 'user_amount_min', 'user_amount_max']
        
        df = pd.merge(df, user_stats, on='user_id', how='left')
        
        # Z-score
        df['amount_z_score'] = (df['amount'] - df['user_amount_mean']) / df['user_amount_std'].replace(0, 1)
        
        # Boolean flags
        df['amount_gt_3x_avg'] = (df['amount'] > 3 * df['user_amount_mean']).astype(int)
        df['amount_gt_5x_avg'] = (df['amount'] > 5 * df['user_amount_mean']).astype(int)
        df['is_micropayment'] = (df['amount'] <= RULE_THRESHOLDS['micropay_threshold']).astype(int)
        
        return df
    
    def _create_temporal_features(self, df):
        """Create time-based features"""
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        df['is_night'] = df['hour'].isin(RULE_THRESHOLDS['time_suspicious_hours']).astype(int)
        
        # Time since last transaction
        df['time_since_last_txn'] = df.groupby('user_id')['timestamp'].diff().dt.total_seconds() / 60
        df['time_since_last_txn'].fillna(24*60, inplace=True)
        
        return df
    
    def _create_recipient_features(self, df):
        """Create recipient-based features"""
        df['is_new_recipient'] = 0
        
        for idx, row in df.iterrows():
            user = row['user_id']
            recipient = row['recipient_id']
            
            prior_txns = df[(df['user_id'] == user) & 
                           (df['recipient_id'] == recipient) & 
                           (df.index < idx)]
            
            if len(prior_txns) == 0:
                df.at[idx, 'is_new_recipient'] = 1
        
        # Count unique recipients
        df['user_unique_recipients'] = 0
        
        for user in df['user_id'].unique():
            user_mask = df['user_id'] == user
            for idx in df[user_mask].index:
                prior_mask = (df['user_id'] == user) & (df.index < idx)
                unique_count = df.loc[prior_mask, 'recipient_id'].nunique()
                df.at[idx, 'user_unique_recipients'] = unique_count
        
        return df
    
    def _create_interaction_features(self, df):
        """Create interaction features"""
        # Micropay followed by large transaction
        df['micropay_followed_by_large'] = 0
        
        for user in df['user_id'].unique():
            user_mask = df['user_id'] == user
            user_df = df[user_mask].copy().sort_values('timestamp')
            
            for i in range(1, len(user_df)):
                prev_amount = user_df.iloc[i-1]['amount']
                curr_amount = user_df.iloc[i]['amount']
                time_diff = user_df.iloc[i]['timestamp'] - user_df.iloc[i-1]['timestamp']
                
                if (prev_amount <= 10 and 
                    curr_amount > 10000 and 
                    time_diff.total_seconds() <= 300):
                    df.loc[user_df.iloc[i].name, 'micropay_followed_by_large'] = 1
        
        # High velocity with new recipient
        df['high_velocity_new_recipient'] = (
            (df['txns_last_1h'] > 3) & 
            (df['is_new_recipient'] == 1)
        ).astype(int)
        
        return df
    
    def get_feature_columns(self):
        """Return list of feature columns for modeling"""
        return [
            # Velocity features
            'txns_last_1h', 'txns_last_6h', 'txns_last_24h', 'txns_last_7d',
            
            # Amount features
            'amount', 'amount_z_score', 'amount_gt_3x_avg', 'amount_gt_5x_avg', 'is_micropayment',
            'user_amount_mean', 'user_amount_std',
            
            # Temporal features
            'hour', 'day_of_week', 'is_weekend', 'is_night', 'time_since_last_txn',
            
            # Recipient features
            'is_new_recipient', 'user_unique_recipients',
            
            # Interaction features
            'micropay_followed_by_large', 'high_velocity_new_recipient'
        ]

if __name__ == "__main__":
    # Test the feature engineering
    from src.data_generator import generate_synthetic_transactions
    
    print("Testing feature engineering...")
    df = generate_synthetic_transactions(1000)
    engineer = FeatureEngineer()
    df_features = engineer.create_features(df)
    
    print(f"Original columns: {df.columns.tolist()}")
    print(f"Feature columns created: {engineer.get_feature_columns()}")
    print(f"Final shape: {df_features.shape}")