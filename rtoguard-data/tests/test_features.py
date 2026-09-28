"""
Unit tests for feature engineering pipeline.
"""

from src.features import FeaturePipeline
from src.generator import SyntheticDataGenerator


def test_feature_pipeline_transformation():
    gen = SyntheticDataGenerator(seed=99)
    pincodes = gen.generate_pincode_stats()
    customers = gen.generate_customers(num_customers=30)
    orders = gen.generate_orders(customers, pincodes, num_orders=100)

    # Export to dataframes
    import pandas as pd
    df_p = pd.DataFrame([p.model_dump() for p in pincodes])
    df_c = pd.DataFrame([c.model_dump() for c in customers])
    df_o = pd.DataFrame([o.model_dump() for o in orders])

    df_o["payment_mode"] = df_o["payment_mode"].astype(str)
    df_o["outcome"] = df_o["outcome"].astype(str)

    pipeline = FeaturePipeline()
    df_transformed = pipeline.transform(df_c, df_o, df_p)
    X, y = pipeline.get_feature_matrix(df_transformed)

    assert len(X) == 100
    assert len(y) == 100
    assert "smoothed_rto_rate" in X.columns
    assert "incomplete_address_flag" in X.columns
    assert "target_rto" in df_transformed.columns
