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

**RTOGuard AI** replaces blunt, blanket policies (like blocking COD above fixed thresholds) with a dynamic **3-Tier Decision Matrix** powered by multi-signal risk scoring.

---

## 🎯 Core Features

- **⚡ Real-Time Checkout Risk Engine (`0.0` – `1.0`):** Evaluates buyer history, pincode reliability tier, order value, category risk, and festive volume multipliers.
- **🚦 3-Tier Operational Action Matrix:**
  - `0.0 - 0.3` **Low Risk** ➔ **Ship as Normal COD** (Zero checkout friction)
  - `0.3 - 0.6` **Medium Risk** ➔ **Require Partial Prepaid Deposit** (Secures buyer intent)
  - `0.6 - 1.0` **High Risk** ➔ **Route to Confirmation Call / Prepaid Only** (Requires manual verification before dispatch)
- **📈 Dual-Pass Replay Simulation:** Executes side-by-side financial comparison between **Pass A (Baseline Loss)** and **Pass B (AI-Mitigated Loss)** across order batches.
- **💰 ROI Calculator:** Quantifies concrete financial savings in **₹ Saved per 1,000 Orders**.
- **🎆 Festive Season Stress-Tester:** Simulates festive surge risk multipliers to evaluate operational resilience under peak holiday load.

---

## 🏗️ Architecture & Project Structure

```
RTOGuard/
├── app/
│   ├── main.py            # FastAPI entry point & CORS configuration
│   ├── config.py          # Environment settings & model parameters
│   ├── db.py              # Database connection & session setup
│   ├── models.py          # ORM data models (Customers, Orders, Pincodes)
│   ├── schemas.py         # Pydantic request & response validation schemas
│   ├── core/              # Scoring algorithm & simulation logic
│   ├── routers/           # API endpoints (scoring, dashboard, simulation)
│   └── services/          # Business logic & notifications
├── frontend/
│   └── app.js             # Interactive operations dashboard logic
├── data/                  # Synthetic datasets & pincode risk mapping
├── notebooks/             # Exploratory analysis & model validation
├── tests/                 # Unit & API test suite
├── PRD.md                 # Detailed Product Requirements Document
└── requirements.txt       # Python dependencies
```

---

## ⚙️ Tech Stack

* **Backend Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.10+)
* **ASGI Server:** [Uvicorn](https://www.uvicorn.org/)
* **Data Processing & ML:** [Pandas](https://pandas.pydata.org/), [NumPy](https://numpy.org/), [Scikit-learn](https://scikit-learn.org/)
* **Schema Validation:** [Pydantic v2](https://docs.pydantic.dev/)
* **Frontend:** Modern Vanilla JavaScript, HTML5 & CSS3 Operations Dashboard

---

## 🔌 API Specification

### 1. Score Order (`POST /api/score-order`)
Evaluates an incoming checkout order and returns the RTO risk score along with a 3-tier recommended action.

**Request Payload:**
```json
{
  "customer_id": "CUST-98231",
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

### 2. Dual-Pass Batch Simulation (`GET /api/simulate`)
Simulates baseline vs. AI-intervened outcomes on order historical datasets.

**Query Parameters:**
- `batch_size`: Number of orders to simulate (e.g., `1000`)
- `festive_mode`: `true` | `false`

**Response Summary:**
- `baseline_rto_loss`: Total losses without intervention
- `ai_rto_loss`: Total losses after RTOGuard interventions
- `net_rupees_saved`: Net financial savings (Primary KPI)
- `rto_rate_reduction`: Percentage drop in RTO default rate

### 3. Dashboard Metrics (`GET /api/dashboard/summary`)
Returns aggregated metrics, high-risk order counts, and tier distribution for operations teams.

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

### 3. Run Development Server

```bash
uvicorn app.main:app --reload
```

The FastAPI server will launch at `http://127.0.0.1:8000`.

* **Interactive API Documentation (Swagger UI):** [`http://127.0.0.1:8000/docs`](http://127.0.0.1:8000/docs)
* **ReDoc Documentation:** [`http://127.0.0.1:8000/redoc`](http://127.0.0.1:8000/redoc)

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
