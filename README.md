# 🛡️ RTOGuard AI

> **"Every COD order is effectively an unsecured loan."**  
> **RTOGuard AI** scores Cash-on-Delivery (COD) orders for Return-to-Origin (RTO) default risk at the point of checkout and executes automated operational interventions — stopping financial leakage *before* reverse logistics costs are incurred.

---

## 📌 Executive Overview

Direct-to-Consumer (D2C) brands in India experience severe Return-to-Origin (RTO) rates ranging from **20% to 35%**, driven almost entirely by Cash-on-Delivery (COD) orders (~26% RTO for COD vs. <2% for prepaid).

### 💸 Financial Impact per Returned Parcel
* **Reverse Logistics Expense:** ₹150 – ₹300 per parcel
* **Total Write-off (Logistics + CAC):** ₹450 – ₹900 per parcel
* **Festive Risk Exposure:** 30%–35% of annual revenue occurs during peak festive windows (Navratri/Diwali), compounding default losses.

**RTOGuard AI** replaces blunt, blanket policies (like blocking COD above fixed thresholds) with a dynamic **3-Tier Decision Matrix** powered by multi-signal risk scoring, synthetic data generation, and real-time checkout ingestion feeds.

---

## 🎯 Core Features

- **⚡ Real-Time Checkout Risk Engine (`0.0` – `1.0`):** Evaluates buyer history, pincode reliability tier, order value, category risk, address structural completeness, cart size anomalies, and festive volume multipliers.
- **🚦 3-Tier Operational Action Matrix:**
  - 🟢 `0.0 - 0.3` **Low Risk** ➔ **Ship as Normal COD** (Zero checkout friction)
  - 🟡 `0.3 - 0.6` **Medium Risk** ➔ **Require Partial Prepaid Deposit** (Secures buyer intent with delivery deposit)
  - 🔴 `0.6 - 1.0` **High Risk** ➔ **Route to Confirmation Call / Prepaid Only** (Requires manual verification before dispatch)
- **📈 Dual-Pass Replay Simulation:** Executes side-by-side financial comparison between **Pass A (Baseline Loss)** and **Pass B (AI-Mitigated Loss)** across order batches.
- **💰 ROI Calculator:** Quantifies concrete financial savings in **₹ Saved per 1,000 Orders**.
- **📦 Data Processing & Synthetic Generator (`rtoguard-data`):** Privacy-first data pipeline with Pydantic v2 schemas, cryptographic customer ID hashing (SHA-256), Bayesian pincode risk smoothing, and FastAPI data feeds.
- **🔒 Privacy by Design:** Strict enforcement excluding all Personally Identifiable Information (PII) — zero names, phone numbers, or full street addresses stored anywhere.

---

## 🏗️ Architecture & Project Structure

```
RTOGuard/
├── app/                        # Main FastAPI backend application
│   ├── main.py                 # FastAPI entry point & CORS configuration
│   ├── config.py               # Environment settings & model parameters
│   ├── db.py                   # Database connection & session setup
│   ├── models.py               # ORM data models (Customers, Orders, Pincodes)
│   ├── schemas.py              # Pydantic request & response validation schemas
│   ├── core/                   # Scoring algorithm & simulation logic
│   ├── routers/                # API endpoints (scoring, dashboard, simulation)
│   └── services/               # Business logic & notifications
├── rtoguard-data/              # Data generation, validation & feed sub-project
│   ├── data/
│   │   ├── raw/                # Generated raw CSV datasets
│   │   └── processed/          # Transformed Parquet feature stores
│   ├── src/
│   │   ├── models.py           # Pydantic v2 schemas with PII guards
│   │   ├── generator/          # Domain-driven synthetic checkout log generator
│   │   ├── features/           # ML feature engineering & Bayesian pincode smoothing
│   │   ├── feed/               # Real-time FastAPI ingestion & lookup server
│   │   └── notify/             # 3-Tier risk action notifier
│   ├── tests/                  # Pytest integration test suite (19 tests)
│   ├── schema.md               # Detailed Data Dictionary & security compliance rules
│   ├── requirements.txt        # Sub-project dependencies (pandas, numpy, scikit-learn, etc.)
│   └── README.md               # rtoguard-data module documentation
├── frontend/                   # Operations Dashboard frontend (HTML5/CSS3/Vanilla JS)
├── notebooks/                  # Exploratory analysis & model validation
├── tests/                      # Core test suite
├── PRD.md                      # Product Requirements Document
├── requirements.txt            # System dependencies
└── README.md                   # System documentation
```

---

## 🔒 Privacy & Compliance Policy

`RTOGuard` enforces strict **Privacy by Design**:
- ❌ **Zero PII:** No customer names, phone numbers, email addresses, street names, flat numbers, or full residential addresses are collected or stored.
- 🔐 **Cryptographic Anonymization:** `customer_id` is strictly stored as a **64-character SHA-256 hex digest** (`^[a-f0-9]{64}$`).
- 📍 **Geographic Aggregation:** Location information is restricted to 6-digit Indian Postal PIN codes.

---

## ⚙️ Tech Stack

* **Backend Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.11+)
* **ASGI Server:** [Uvicorn](https://www.uvicorn.org/)
* **Data Processing & ML:** [Pandas](https://pandas.pydata.org/), [NumPy](https://numpy.org/), [Scikit-learn](https://scikit-learn.org/), [PyArrow](https://arrow.apache.org/docs/python/)
* **Schema Validation:** [Pydantic v2](https://docs.pydantic.dev/)
* **Synthetic Generation:** [Faker](https://faker.readthedocs.io/) & Cryptographic Hashing (`hashlib`)
* **Testing:** [Pytest](https://docs.pytest.org/), [HTTPX](https://www.python-httpx.org/)
* **Frontend:** Modern Vanilla JavaScript, HTML5 & CSS3 Operations Dashboard

---

## 🔌 API Specification

### 1. Score Order (`POST /api/score-order`)
Evaluates an incoming checkout order and returns the RTO risk score along with a 3-tier recommended action.

**Request Payload:**
```json
{
  "customer_id": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "order_value": 2450.00,
  "payment_mode": "COD",
  "pincode": "110001",
  "category": "Apparel",
  "is_festive_window": true
}
```

**Response:**
```json
{
  "order_id": "ORD-45210",
  "risk_score": 0.48,
  "risk_level": "Medium",
  "recommended_action": "Require Partial Prepaid Deposit",
  "reasons": [
    "High Order Value (> ₹2,000)",
    "Festive Window Multiplier Active",
    "Pincode Tier 2 Default Baseline"
  ],
  "expected_loss_prevented": 360.00
}
```

### 2. Data Feed Service Endpoints (`rtoguard-data/src/feed/data_feed.py`)
- **`GET /`**: Service welcome & active routes index.
- **`GET /health`**: Data feed health check & loaded dataset counts.
- **`POST /feed/order`**: Ingest and validate checkout orders against Pydantic models.
- **`POST /feed/customer`**: Ingest SHA-256 hashed customer profiles.
- **`POST /feed/pincode`**: Ingest and update pincode risk statistics.
- **`GET /stats/pincode/{pincode}`**: Retrieve tier (1/2/3) and Bayesian smoothed RTO rate for any 6-digit PIN code.

### 3. Dual-Pass Batch Simulation (`GET /api/simulate`)
Simulates baseline vs. AI-intervened outcomes on order historical datasets.

---

## 🚀 Getting Started

### 1. Clone & Set Up Environment

```bash
# Clone the repository
git clone https://github.com/RTOGUARD-Team/RTOGuard.git
cd RTOGuard

# Create and activate virtual environment
python -m venv .venv

# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# On macOS/Linux:
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Generate Synthetic Datasets

```bash
cd rtoguard-data
python -m src.generator.synthetic_data
cd ..
```

### 4. Run Development Servers

**Run Main FastAPI Application:**
```bash
uvicorn app.main:app --reload --port 8000
```

**Run Data Feed Service (Optional):**
```bash
uvicorn rtoguard-data.src.feed.data_feed:app --reload --port 8001
```

- **Interactive API Documentation (Swagger UI):** [`http://127.0.0.1:8000/docs`](http://127.0.0.1:8000/docs)
- **Data Feed Docs:** [`http://127.0.0.1:8001/docs`](http://127.0.0.1:8001/docs)

### 5. Run Test Suite

```bash
cd rtoguard-data
pytest tests/ -v
```

---

## 📊 Key Metric Benchmark Target

| Metric | Baseline (Unmitigated) | RTOGuard AI Target |
| :--- | :--- | :--- |
| **COD RTO Rate** | ~26% | **15% – 19%** |
| **Average Loss per RTO** | ₹450 – ₹900 | **Mitigated at Checkout** |
| **Primary KPI** | Unmonitored | **₹ Saved per 1,000 Orders** |

---

## 🏆 Hackathon Context

Developed for the **OpsGenieAI Track** (8-Day Hackathon). RTOGuard AI addresses operational efficiency, loss forecasting, and e-commerce business process optimization.

---

## 📜 License

[MIT License](LICENSE) — Feel free to use and adapt for D2C risk mitigation solutions.
