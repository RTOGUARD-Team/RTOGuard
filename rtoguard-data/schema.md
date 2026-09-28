# 📊 RTOGuard Data Schema & Data Dictionary

## 🛡️ Privacy & Compliance Policy

> **CRITICAL REQUIREMENT:** Privacy by design is enforced across all tables and modules in `rtoguard-data`.
> - **Zero PII (Personally Identifiable Information):** No customer names, phone numbers, email addresses, street names, building numbers, or full residential addresses are collected, stored, or processed.
> - **Customer Anonymization:** `customer_id` MUST strictly use SHA-256 hashed identifiers (64-character hexadecimal strings) generated via a secure cryptographic digest (e.g., `sha256(salt + unique_id)`).
> - **Geographic Aggregation:** Location information is restricted to 6-digit Indian Postal Pincodes only.

---

## 📐 Relational Schema Overview

```
                      +-------------------+
                      |     customers     |
                      +-------------------+
                      | customer_id (PK)  | <---+
                      | signup_date       |     |
                      | pincode           |     |
                      +-------------------+     |
                                                | (1:N)
                                                |
                      +-------------------+     |
                      |      orders       |     |
                      +-------------------+     |
                      | order_id (PK)     |     |
                      | customer_id (FK) -+-----+
                      | order_ts          |
                      | value             |
                      | payment_mode      |
                      | category          |
                      | discount_pct      |
                      | hour_of_day       |
                      | address_completeness|
                      | cart_pattern      |
                      | is_festive        |
                      | outcome           |
                      +-------------------+
                               |
                               | (FK pincode matches pincode_stats)
                               v
                      +-------------------+
                      |   pincode_stats   |
                      +-------------------+
                      | pincode (PK)      |
                      | tier              |
                      | smoothed_rto_rate |
                      | order_count       |
                      +-------------------+
```

---

## 📖 Data Dictionary

### 1. `customers` Table

Stores anonymized customer profiles with signup timeline and primary delivery pincode.

| Column Name | Pydantic Type | SQL Type | Valid Range / Allowed Values | Constraint / Validation Rule | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `customer_id` | `str` | `VARCHAR(64)` | 64-char Hex String | SHA-256 regex `^[a-f0-9]{64}$` | Unique cryptographic hash identifying the customer. Strictly anonymized. |
| `signup_date` | `date` | `DATE` | `2020-01-01` to `current_date` | ISO 8601 YYYY-MM-DD format | Date when customer account was registered. |
| `pincode` | `str` | `VARCHAR(6)` | `100000` to `999999` | 6-digit Indian PIN code regex `^[1-9][0-9]{5}$` | Primary pincode associated with customer account. |

---

### 2. `orders` Table

Stores transaction logs at point-of-checkout including order value, payment mode, behavioral flags, and operational outcome.

| Column Name | Pydantic Type | SQL Type | Valid Range / Allowed Values | Constraint / Validation Rule | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `order_id` | `str` | `VARCHAR(36)` | String identifier | Unique non-empty string e.g. `ord_a1b2c3d4` | Unique identifier for each order transaction. |
| `customer_id` | `str` | `VARCHAR(64)` | 64-char Hex String | Foreign Key matching `customers.customer_id` (`^[a-f0-9]{64}$`) | Cryptographically hashed customer ID. |
| `order_ts` | `datetime` | `TIMESTAMP` | ISO 8601 format | Valid datetime timestamp | Timestamp when order was placed. |
| `value` | `float` | `NUMERIC(10,2)` | `0.01` to `500000.00` | strictly `> 0.0` (INR) | Total monetary value of order in Indian Rupees (₹). |
| `payment_mode` | `Enum` | `VARCHAR(10)` | `'COD'`, `'prepaid'` | Must be one of `PaymentMode` enum | Payment method selected by customer. |
| `category` | `str` | `VARCHAR(50)` | Fashion, Electronics, Footwear, Beauty, Home, Accessories | Non-empty string category | Product merchandise classification category. |
| `discount_pct` | `float` | `NUMERIC(5,2)` | `0.00` to `100.00` | `0.0 <= discount_pct <= 100.0` | Percentage discount applied on order. |
| `hour_of_day` | `int` | `SMALLINT` | `0` to `23` | `0 <= hour_of_day <= 23` | Hour of day (24-hour format) when order was initiated. |
| `address_completeness` | `float` | `NUMERIC(3,2)` | `0.00` to `1.00` | `0.0 <= address_completeness <= 1.0` | Composite score indicating address structural quality (house #, street, landmark presence). |
| `cart_pattern` | `int` | `SMALLINT` | `0` or `1` | Binary flag (`0` or `1`) | Flag indicating suspicious cart behavior (e.g. ordering multiple sizes of the same apparel item). |
| `is_festive` | `int` | `SMALLINT` | `0` or `1` | Binary flag (`0` or `1`) | Flag indicating whether order was placed during peak festive sales window (e.g., Navratri/Diwali). |
| `outcome` | `Enum` | `VARCHAR(10)` | `'delivered'`, `'RTO'` | Must be one of `OutcomeMode` enum | Fulfillment result (`delivered` = successfully delivered, `RTO` = Return-to-Origin). |

---

### 3. `pincode_stats` Table

Maintains risk profiles and historical fulfillment statistics for Indian postal pincodes.

| Column Name | Pydantic Type | SQL Type | Valid Range / Allowed Values | Constraint / Validation Rule | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `pincode` | `str` | `VARCHAR(6)` | `100000` to `999999` | 6-digit Indian PIN code regex `^[1-9][0-9]{5}$` | Indian postal PIN code. |
| `tier` | `int` | `SMALLINT` | `1`, `2`, `3` | Integer `1` (Metro), `2` (Tier-2 City), `3` (Tier-3/Rural) | Geographic tier classification. |
| `smoothed_rto_rate` | `float` | `NUMERIC(5,4)` | `0.0000` to `1.0000` | `0.0 <= smoothed_rto_rate <= 1.0` | Bayesian / m-estimate smoothed historical RTO rate for pincode. |
| `order_count` | `int` | `INTEGER` | `>= 0` | Non-negative integer | Total historical orders recorded for pincode. |

---

## 🔒 Security & PII Exclusion Standard

To ensure compliance with Indian DPDP (Digital Personal Data Protection) Act and global data governance standards, the following fields are strictly forbidden:
- `name` / `first_name` / `last_name`
- `phone` / `mobile` / `telephone`
- `email`
- `address` / `street` / `flat_no` / `landmark` / `full_address`

Any attempt to pass or store these attributes in Pydantic models will trigger a validation error.
