# 🛡️ RTOGuard Data (`rtoguard-data`)

> **Python 3.11 Data Generator, Pydantic Schema Validation, Feature Engineering & Real-time Ingestion Feed for RTOGuard AI.**

---

## 📌 Project Overview

`rtoguard-data` is the data processing engine for **RTOGuard AI**. It provides cryptographically anonymized, Pydantic v2-validated synthetic datasets, feature pipelines, high-risk notification alerting, and real-time ingestion endpoints for Cash-on-Delivery (COD) Return-to-Origin (RTO) risk analysis across Indian e-commerce checkout systems.

---

## 🏗️ Directory Structure

```
rtoguard-data/
├── data/
│   ├── raw/                 # Generated raw CSV datasets
│   └── processed/           # Transformed Parquet feature stores
├── src/
│   ├── models.py            # Pydantic v2 schemas for customers, orders, pincode_stats
│   ├── generator/           # Domain-driven synthetic data generator (Faker & NumPy)
│   ├── features/            # Feature engineering pipeline & Bayesian risk smoothing
│   ├── feed/                # Real-time FastAPI ingestion & lookup endpoints
│   └── notify/              # 3-Tier operational notification dispatcher
├── tests/                   # Pytest suite covering models, generator, features, feed, notify
├── schema.md                # Comprehensive data dictionary, types, and valid ranges
├── requirements.txt         # Project dependencies (pandas, numpy, scikit-learn, faker, etc.)
└── README.md                # Project documentation & execution guide
```

---

## 🔒 Privacy & PII Compliance Standard

`rtoguard-data` enforces strict **Privacy by Design**:
- ❌ **Forbidden Attributes:** No `name`, `phone`, `email`, or `full address` are collected, stored, or processed.
- 🔐 **Cryptographic Anonymization:** `customer_id` is strictly stored as a **64-character SHA-256 hex digest** (`^[a-f0-9]{64}$`).
- 📍 **Aggregated Geography:** Geographic signals are strictly restricted to 6-digit Indian Postal Pincodes.

---

## 📊 Database Tables & Pydantic Models

| Table Name | Entity Description | Key Attributes & Constraints |
| :--- | :--- | :--- |
| **`customers`** | Anonymized Customer Profiles | `customer_id` (SHA-256 hash), `signup_date` (YYYY-MM-DD), `pincode` (6-digit) |
| **`orders`** | Checkout Transaction Logs | `order_id`, `customer_id`, `order_ts`, `value` (>0), `payment_mode` (`COD`/`prepaid`), `category`, `discount_pct` (0-100), `hour_of_day` (0-23), `address_completeness` (0.0-1.0), `cart_pattern` (0/1), `is_festive` (0/1), `outcome` (`delivered`/`RTO`) |
| **`pincode_stats`** | Pincode Risk Profiles | `pincode` (6-digit), `tier` (1, 2, or 3), `smoothed_rto_rate` (0.0-1.0), `order_count` (>=0) |

---

## 🚀 Quickstart & Installation

### 1. Prerequisites
- **Python 3.11+**

### 2. Installation

```bash
# Navigate to project directory
cd rtoguard-data

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## ⚡ Execution Commands

### Generate Synthetic Data

Generate Pydantic-validated dataset into `data/raw` (CSV) and `data/processed` (Parquet):

```bash
python -m src.generator.synthetic_data
```

### Run Data Feed API Service

Launch FastAPI real-time ingestion server on `http://localhost:8000`:

```bash
uvicorn src.feed.data_feed:app --reload --port 8000
```

- **Health Check:** `GET http://localhost:8000/health`
- **Interactive Swagger Docs:** `http://localhost:8000/docs`

### Run Pytest Test Suite

Execute complete unit & integration test suite:

```bash
pytest tests/ -v
```

---

## 🧪 Operational Action Matrix (3-Tier Risk Engine)

`rtoguard-data` powers RTOGuard's **3-Tier Operational Action Matrix**:
- 🟢 **`0.0 - 0.3` Low Risk:** **Ship as Normal COD** (Zero checkout friction)
- 🟡 **`0.3 - 0.6` Medium Risk:** **Require Partial Prepaid Deposit** (Secures buyer intent)
- 🔴 **`0.6 - 1.0` High Risk:** **Route to Confirmation Call / Prepaid Only** (Prevents financial loss before dispatch)
