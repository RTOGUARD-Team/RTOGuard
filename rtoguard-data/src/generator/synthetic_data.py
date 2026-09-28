"""
Synthetic Data Generator for RTOGuard.

Generates privacy-compliant, realistic datasets for Indian D2C checkout analysis:
- customers: hashed customer IDs, signup dates, pincodes
- orders: order logs with checkout signals, payment mode, behavioral flags, outcome
- pincode_stats: pincodes, geographic tiers, smoothed RTO rates, order counts

Strictly avoids PII (no names, phone numbers, or full addresses).
"""

import hashlib
import os
import random
from datetime import date, datetime, timedelta
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
from faker import Faker

from ..models import Customer, Order, OutcomeMode, PaymentMode, PincodeStats

# Representative Indian postal pincodes mapped to geographic tiers
PINCODE_TIER_MAPPING: List[Tuple[str, int]] = [
    # Tier 1 (Metros)
    ("110001", 1), ("110020", 1), ("400001", 1), ("400050", 1),
    ("560001", 1), ("560034", 1), ("700001", 1), ("600001", 1),
    ("500001", 1), ("411001", 1),
    # Tier 2 (Growth Cities)
    ("302001", 2), ("141001", 2), ("800001", 2), ("452001", 2),
    ("226001", 2), ("380001", 2), ("641001", 2), ("530001", 2),
    ("462001", 2), ("248001", 2),
    # Tier 3 (Semi-Urban / Rural)
    ("841301", 3), ("246701", 3), ("781001", 3), ("176215", 3),
    ("364001", 3), ("834001", 3), ("799001", 3), ("795001", 3),
    ("851101", 3), ("273001", 3)
]

CATEGORIES = ["Apparel", "Electronics", "Footwear", "Beauty & Care", "Home & Kitchen", "Fashion Accessories"]


def hash_customer_identifier(raw_id: str, salt: str = "rtoguard_salt_2026") -> str:
    """Generates a secure 64-character SHA-256 hex string from raw identifier."""
    return hashlib.sha256(f"{salt}_{raw_id}".encode("utf-8")).hexdigest()


class SyntheticDataGenerator:
    """
    Generator class to produce realistic, Pydantic-validated synthetic datasets.
    """

    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(seed)
        np.random.seed(seed)
        self.fake = Faker("en_IN")
        Faker.seed(seed)

    def generate_pincode_stats(self, base_order_count: int = 500) -> List[PincodeStats]:
        """Generates pincode tier mappings and smoothed RTO rates."""
        pincode_records = []

        for pincode, tier in PINCODE_TIER_MAPPING:
            order_cnt = int(random.normalvariate(base_order_count * (4 - tier), 50))
            order_cnt = max(50, order_cnt)

            # Baseline RTO rate increases with tier (Tier 1 ~ 12%, Tier 2 ~ 22%, Tier 3 ~ 35%)
            base_rto = 0.12 if tier == 1 else (0.22 if tier == 2 else 0.35)
            # Add noise and perform m-estimate smoothing
            prior_weight = 20.0
            prior_rto = 0.20
            observed_rto = np.clip(random.normalvariate(base_rto, 0.04), 0.05, 0.50)
            smoothed_rto = (observed_rto * order_cnt + prior_rto * prior_weight) / (order_cnt + prior_weight)

            stat = PincodeStats(
                pincode=pincode,
                tier=tier,
                smoothed_rto_rate=round(float(smoothed_rto), 4),
                order_count=order_cnt
            )
            pincode_records.append(stat)

        return pincode_records

    def generate_customers(self, num_customers: int = 500) -> List[Customer]:
        """Generates anonymized customer records with hashed IDs."""
        customers = []
        pincodes = [p for p, _ in PINCODE_TIER_MAPPING]

        start_date = date(2024, 1, 1)
        end_date = date(2026, 9, 1)
        days_range = (end_date - start_date).days

        for i in range(num_customers):
            raw_uuid = f"cust_raw_id_{i + 1}_{random.randint(10000, 99999)}"
            cust_id = hash_customer_identifier(raw_uuid)
            signup_d = start_date + timedelta(days=random.randint(0, days_range))
            pin = random.choice(pincodes)

            cust = Customer(
                customer_id=cust_id,
                signup_date=signup_d,
                pincode=pin
            )
            customers.append(cust)

        return customers

    def generate_orders(
        self,
        customers: List[Customer],
        pincode_stats: List[PincodeStats],
        num_orders: int = 2000
    ) -> List[Order]:
        """
        Generates realistic order logs with domain risk factors driving RTO outcome.
        """
        pincode_map: Dict[str, PincodeStats] = {p.pincode: p for p in pincode_stats}
        orders = []

        start_time = datetime(2025, 1, 1, 0, 0, 0)
        end_time = datetime(2026, 9, 28, 23, 59, 59)
        time_span_seconds = int((end_time - start_time).total_seconds())

        for i in range(num_orders):
            order_id = f"ord_{100000 + i + 1}"
            customer = random.choice(customers)
            pin_stat = pincode_map[customer.pincode]

            # Timestamp & Hour of day
            random_offset = random.randint(0, time_span_seconds)
            order_ts = start_time + timedelta(seconds=random_offset)
            hour_of_day = order_ts.hour

            # Is Festive check (Diwali/Navratri/Dussehra window: Oct 1 - Nov 15)
            is_festive = 1 if (order_ts.month in (10, 11) and order_ts.day <= 15) or random.random() < 0.1 else 0

            # Payment mode (70% COD in D2C India baseline)
            payment_mode = PaymentMode.COD if random.random() < 0.70 else PaymentMode.PREPAID

            # Order value
            cat = random.choice(CATEGORIES)
            base_val = random.choice([499, 799, 1299, 2499, 4999, 8999])
            value = round(float(base_val + random.uniform(-100, 300)), 2)

            # Discount percentage
            discount_pct = round(float(random.choice([0.0, 10.0, 15.0, 25.0, 40.0, 50.0])), 2)

            # Address completeness score (0.2 to 1.0)
            address_completeness = round(float(np.clip(random.normalvariate(0.75, 0.2), 0.2, 1.0)), 2)

            # Cart pattern (multiple sizes of same item in apparel/footwear)
            if cat in ["Apparel", "Footwear"] and random.random() < 0.18:
                cart_pattern = 1
            else:
                cart_pattern = 1 if random.random() < 0.05 else 0

            # Calculate RTO Risk Score for ground truth simulation
            rto_prob = 0.02  # Prepaid baseline < 2%

            if payment_mode == PaymentMode.COD:
                rto_prob = pin_stat.smoothed_rto_rate  # Base tier risk

                # Modifiers
                if address_completeness < 0.5:
                    rto_prob += 0.20
                if cart_pattern == 1:
                    rto_prob += 0.25
                if is_festive == 1:
                    rto_prob += 0.10
                if hour_of_day in [0, 1, 2, 3, 4]:
                    rto_prob += 0.12
                if discount_pct > 35.0:
                    rto_prob += 0.08

            rto_prob = float(np.clip(rto_prob, 0.01, 0.95))
            outcome = OutcomeMode.RTO if random.random() < rto_prob else OutcomeMode.DELIVERED

            order = Order(
                order_id=order_id,
                customer_id=customer.customer_id,
                order_ts=order_ts,
                value=value,
                payment_mode=payment_mode,
                category=cat,
                discount_pct=discount_pct,
                hour_of_day=hour_of_day,
                address_completeness=address_completeness,
                cart_pattern=cart_pattern,
                is_festive=is_festive,
                outcome=outcome
            )
            orders.append(order)

        return orders

    def run_pipeline(
        self,
        output_dir: str,
        num_customers: int = 500,
        num_orders: int = 2000
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Runs complete synthetic data pipeline, validates with Pydantic models,
        and saves raw/processed data files.
        """
        raw_dir = os.path.join(output_dir, "raw")
        processed_dir = os.path.join(output_dir, "processed")
        os.makedirs(raw_dir, exist_ok=True)
        os.makedirs(processed_dir, exist_ok=True)

        print(f"Generating {len(PINCODE_TIER_MAPPING)} pincode risk stats...")
        pincodes = self.generate_pincode_stats()

        print(f"Generating {num_customers} customer profiles...")
        customers = self.generate_customers(num_customers=num_customers)

        print(f"Generating {num_orders} order records with risk factors...")
        orders = self.generate_orders(customers, pincodes, num_orders=num_orders)

        # Convert to DataFrames
        df_pincodes = pd.DataFrame([p.model_dump() for p in pincodes])
        df_customers = pd.DataFrame([c.model_dump() for c in customers])
        df_orders = pd.DataFrame([o.model_dump() for o in orders])

        # Convert Enum strings cleanly
        df_orders["payment_mode"] = df_orders["payment_mode"].astype(str)
        df_orders["outcome"] = df_orders["outcome"].astype(str)
        df_customers["signup_date"] = pd.to_datetime(df_customers["signup_date"])
        df_orders["order_ts"] = pd.to_datetime(df_orders["order_ts"])

        # Save to raw
        df_pincodes.to_csv(os.path.join(raw_dir, "pincode_stats.csv"), index=False)
        df_customers.to_csv(os.path.join(raw_dir, "customers.csv"), index=False)
        df_orders.to_csv(os.path.join(raw_dir, "orders.csv"), index=False)

        # Save to processed (Parquet format)
        try:
            df_pincodes.to_parquet(os.path.join(processed_dir, "pincode_stats.parquet"), index=False)
            df_customers.to_parquet(os.path.join(processed_dir, "customers.parquet"), index=False)
            df_orders.to_parquet(os.path.join(processed_dir, "orders.parquet"), index=False)
        except Exception as e:
            print(f"Parquet export skipped or failed ({e}); CSV raw files generated successfully.")

        print(f"[SUCCESS] Successfully generated and saved datasets to {output_dir}")
        return df_customers, df_orders, df_pincodes


if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
    gen = SyntheticDataGenerator(seed=42)
    gen.run_pipeline(base_dir, num_customers=300, num_orders=1000)
