"""
Feature Pipeline — ported from rtoguard-data/src/features/feature_pipeline.py

Transforms raw order + customer + pincode records into the ML-ready feature matrix
that Riya's trained model pipeline expects as input.

Used by app/core/scoring.py to build the correct DataFrame before calling predict_proba().
"""

from typing import Tuple
import numpy as np
import pandas as pd


class FeaturePipeline:
    """
    Feature engineering transformer for checkout risk evaluation.
    Applies Bayesian smoothing on customer RTO history and pincode risk rates.
    """

    def __init__(self, prior_m_weight: float = 10.0, prior_global_rto: float = 0.20):
        self.prior_m_weight = prior_m_weight
        self.prior_global_rto = prior_global_rto

    def compute_customer_history(self, df_orders: pd.DataFrame) -> pd.DataFrame:
        """
        Computes historical order counts and Bayesian smoothed RTO rates per customer ID.
        Uses expanding window to prevent data leakage.
        """
        df_sorted = df_orders.sort_values("order_ts").copy()
        df_sorted["is_rto"] = (df_sorted["outcome"] == "RTO").astype(int)

        cust_group = df_sorted.groupby("customer_id")
        df_sorted["cust_order_count_hist"] = cust_group.cumcount()
        df_sorted["cust_rto_count_hist"] = cust_group["is_rto"].cumsum() - df_sorted["is_rto"]

        # Bayesian smoothed historical customer RTO rate
        df_sorted["cust_historical_rto_rate"] = (
            (df_sorted["cust_rto_count_hist"] + self.prior_m_weight * self.prior_global_rto)
            / (df_sorted["cust_order_count_hist"] + self.prior_m_weight)
        )
        return df_sorted

    def transform(
        self,
        df_customers: pd.DataFrame,
        df_orders: pd.DataFrame,
        df_pincodes: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Merges customer profile and pincode risk data into orders DataFrame,
        generating explicit model input features.
        """
        # 1. Add customer historical features (expanding window, no leakage)
        df_feat = self.compute_customer_history(df_orders)

        # 2. Merge customer pincode
        df_cust_slim = df_customers[["customer_id", "pincode"]].rename(
            columns={"pincode": "customer_pincode"}
        )
        df_feat = df_feat.merge(df_cust_slim, on="customer_id", how="left")

        # 3. Merge pincode risk statistics
        df_feat = df_feat.merge(df_pincodes, left_on="customer_pincode", right_on="pincode", how="left")

        # Fill defaults for unknown pincodes
        df_feat["tier"] = df_feat["tier"].fillna(2).astype(int)
        df_feat["smoothed_rto_rate"] = df_feat["smoothed_rto_rate"].fillna(self.prior_global_rto)
        df_feat["order_count"] = df_feat["order_count"].fillna(0).astype(int)

        # 4. Feature transformations
        df_feat["is_cod"] = (df_feat["payment_mode"] == "COD").astype(int)
        df_feat["is_night_order"] = df_feat["hour_of_day"].isin([0, 1, 2, 3, 4, 5]).astype(int)
        df_feat["incomplete_address_flag"] = (df_feat["address_completeness"] < 0.60).astype(int)
        df_feat["high_discount_flag"] = (df_feat["discount_pct"] >= 30.0).astype(int)

        # Target label encoding (1 = RTO, 0 = delivered)
        df_feat["target_rto"] = (df_feat["outcome"] == "RTO").astype(int)

        return df_feat

    def get_feature_matrix(self, df_transformed: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Extracts the final numerical feature matrix X and target label series y.
        These are the exact 14 columns Riya's model was trained on.
        """
        feature_cols = [
            "value", "is_cod", "discount_pct", "hour_of_day",
            "address_completeness", "cart_pattern", "is_festive",
            "tier", "smoothed_rto_rate", "cust_order_count_hist",
            "cust_historical_rto_rate", "is_night_order",
            "incomplete_address_flag", "high_discount_flag"
        ]

        X = df_transformed[feature_cols].copy()
        y = df_transformed["target_rto"].copy()
        return X, y
