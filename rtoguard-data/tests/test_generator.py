"""
Unit tests for synthetic data generator module.
"""

import os
import shutil
import tempfile
import pytest

from src.generator import SyntheticDataGenerator


def test_synthetic_generator_execution():
    gen = SyntheticDataGenerator(seed=123)
    pincodes = gen.generate_pincode_stats()
    assert len(pincodes) > 0
    assert all(p.tier in (1, 2, 3) for p in pincodes)

    customers = gen.generate_customers(num_customers=50)
    assert len(customers) == 50
    assert all(len(c.customer_id) == 64 for c in customers)

    orders = gen.generate_orders(customers, pincodes, num_orders=100)
    assert len(orders) == 100
    assert all(o.value > 0 for o in orders)


def test_pipeline_file_export():
    temp_dir = tempfile.mkdtemp()
    try:
        gen = SyntheticDataGenerator(seed=42)
        df_c, df_o, df_p = gen.run_pipeline(temp_dir, num_customers=20, num_orders=50)

        assert os.path.exists(os.path.join(temp_dir, "raw", "customers.csv"))
        assert os.path.exists(os.path.join(temp_dir, "raw", "orders.csv"))
        assert os.path.exists(os.path.join(temp_dir, "raw", "pincode_stats.csv"))

        assert os.path.exists(os.path.join(temp_dir, "processed", "customers.parquet"))
        assert os.path.exists(os.path.join(temp_dir, "processed", "orders.parquet"))
        assert os.path.exists(os.path.join(temp_dir, "processed", "pincode_stats.parquet"))

        assert len(df_c) == 20
        assert len(df_o) == 50
        assert len(df_p) > 0
    finally:
        shutil.rmtree(temp_dir)
