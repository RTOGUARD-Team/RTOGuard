"""
Pydantic Models for RTOGuard Data Tables.

Includes strict validation for:
- customer_id: Hashed SHA-256 string (64 hex characters)
- pincode: 6-digit Indian Postal PIN code
- orders: Value ranges, hour of day, address completeness, cart pattern, festive flags
- pincode_stats: Tier (1/2/3), smoothed RTO rate (0-1), non-negative order count
- Strict PII guard against storing sensitive personal data.
"""

import re
from datetime import date, datetime
from enum import Enum
from typing import Literal, Union, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class PaymentMode(str, Enum):
    COD = "COD"
    PREPAID = "prepaid"


class OutcomeMode(str, Enum):
    DELIVERED = "delivered"
    RTO = "RTO"


# Forbidden PII attributes to prevent privacy leakage
FORBIDDEN_PII_FIELDS = {
    "name", "first_name", "last_name", "full_name",
    "phone", "mobile", "telephone", "phone_number",
    "email", "email_address",
    "address", "street", "landmark", "full_address", "house_no"
}


class Customer(BaseModel):
    """
    Customer table model.
    Contains strictly anonymized customer profiles.
    """
    customer_id: str = Field(
        ...,
        description="SHA-256 hashed customer identifier (64 hex characters).",
        examples=["e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"]
    )
    signup_date: date = Field(
        ...,
        description="Date of customer account creation (YYYY-MM-DD)."
    )
    pincode: str = Field(
        ...,
        description="Primary 6-digit Indian postal pincode.",
        examples=["110001", "560001", "400001"]
    )

    @field_validator("customer_id")
    @classmethod
    def validate_customer_id(cls, v: str) -> str:
        v_clean = v.strip().lower()
        if not re.match(r"^[a-f0-9]{64}$", v_clean):
            raise ValueError("customer_id must be a 64-character SHA-256 hex string.")
        return v_clean

    @field_validator("pincode")
    @classmethod
    def validate_pincode(cls, v: str) -> str:
        v_clean = str(v).strip()
        if not re.match(r"^[1-9][0-9]{5}$", v_clean):
            raise ValueError("pincode must be a valid 6-digit Indian postal PIN code.")
        return v_clean

    @model_validator(mode="before")
    @classmethod
    def reject_pii_fields(cls, values: dict) -> dict:
        if isinstance(values, dict):
            for key in values.keys():
                if key.lower() in FORBIDDEN_PII_FIELDS:
                    raise ValueError(f"PII Field violation: '{key}' is not allowed in Customer model.")
        return values


class Order(BaseModel):
    """
    Order transaction table model.
    Stores checkout signals, payment mode, behavioral flags, and operational outcome.
    """
    order_id: str = Field(
        ...,
        description="Unique order identifier.",
        examples=["ord_1001", "ord_a8f92b"]
    )
    customer_id: str = Field(
        ...,
        description="SHA-256 hashed customer identifier."
    )
    order_ts: datetime = Field(
        ...,
        description="Timestamp of order creation (ISO 8601)."
    )
    value: float = Field(
        ...,
        gt=0.0,
        description="Order total value in INR (> 0.0).",
        examples=[1499.00]
    )
    payment_mode: PaymentMode = Field(
        ...,
        description="Payment mode selected at checkout ('COD' or 'prepaid')."
    )
    category: str = Field(
        ...,
        min_length=1,
        description="Product category (e.g. Apparel, Electronics, Footwear)."
    )
    discount_pct: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Discount percentage applied (0.0 to 100.0)."
    )
    hour_of_day: int = Field(
        ...,
        ge=0,
        le=23,
        description="Hour of day when order was placed (0 to 23)."
    )
    address_completeness: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Score between 0.0 and 1.0 representing address structural completeness."
    )
    cart_pattern: int = Field(
        ...,
        ge=0,
        le=1,
        description="Flag indicating suspicious cart pattern (1 = multiple sizes of same item, 0 = normal)."
    )
    is_festive: int = Field(
        ...,
        ge=0,
        le=1,
        description="Flag indicating order during peak festive season (1 = festive, 0 = standard)."
    )
    outcome: OutcomeMode = Field(
        ...,
        description="Order outcome ('delivered' or 'RTO')."
    )

    @field_validator("customer_id")
    @classmethod
    def validate_customer_id(cls, v: str) -> str:
        v_clean = v.strip().lower()
        if not re.match(r"^[a-f0-9]{64}$", v_clean):
            raise ValueError("customer_id must be a 64-character SHA-256 hex string.")
        return v_clean

    @field_validator("cart_pattern", "is_festive", mode="before")
    @classmethod
    def convert_bool_or_int(cls, v: Union[bool, int, float]) -> int:
        if isinstance(v, bool):
            return 1 if v else 0
        val = int(v)
        if val not in (0, 1):
            raise ValueError("Flag must be 0 or 1.")
        return val

    @model_validator(mode="before")
    @classmethod
    def reject_pii_fields(cls, values: dict) -> dict:
        if isinstance(values, dict):
            for key in values.keys():
                if key.lower() in FORBIDDEN_PII_FIELDS:
                    raise ValueError(f"PII Field violation: '{key}' is not allowed in Order model.")
        return values


class PincodeStats(BaseModel):
    """
    Pincode statistics table model.
    Stores tier classification and smoothed RTO risk rates for Indian postal codes.
    """
    pincode: str = Field(
        ...,
        description="6-digit Indian postal pincode."
    )
    tier: Literal[1, 2, 3] = Field(
        ...,
        description="Geographic tier: 1 (Metro), 2 (Tier-2 City), 3 (Tier-3 / Rural)."
    )
    smoothed_rto_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Bayesian smoothed historical RTO rate (0.0 to 1.0)."
    )
    order_count: int = Field(
        ...,
        ge=0,
        description="Total historical order volume for this pincode."
    )

    @field_validator("pincode")
    @classmethod
    def validate_pincode(cls, v: str) -> str:
        v_clean = str(v).strip()
        if not re.match(r"^[1-9][0-9]{5}$", v_clean):
            raise ValueError("pincode must be a valid 6-digit Indian postal PIN code.")
        return v_clean

    @model_validator(mode="before")
    @classmethod
    def reject_pii_fields(cls, values: dict) -> dict:
        if isinstance(values, dict):
            for key in values.keys():
                if key.lower() in FORBIDDEN_PII_FIELDS:
                    raise ValueError(f"PII Field violation: '{key}' is not allowed in PincodeStats model.")
        return values
