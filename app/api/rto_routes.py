from fastapi import APIRouter, HTTPException

from app.rto_schemas import (
    RecommendationRequest,
    CostRequest,
    SimulationRequest,
    RawSimulationRequest,
    RawOrder
)

from app.core.scoring import score_order as ml_score_order

from app.core.customer_repository import get_customer_profile, is_new_customer

from app.services.action_recommendation import (
    ActionRecommendationEngine
)

from app.services.cost_calculator import (
    CostCalculator
)

from app.services.simulation_engine import (
    SimulationEngine
)

from app.models import create_prediction_doc
import logging as _logging
_db_log = _logging.getLogger("rtoguard.db")


def _save_to_db(
    order_dict: dict,
    prediction_doc: dict,
    customer_status: str,
    customer_id,
) -> None:
    """
    Saves 3 things to MongoDB after every scoring request:
      1. predictions  -- full ML result + action (audit trail)
      2. orders       -- raw incoming order (order log)
      3. customers    -- upserts new customer with cold-start profile
                        so they appear as known on next order
    Errors are logged but never crash the API response.
    """
    try:
        from app.db import predictions_collection, orders_collection, customers_collection
        from datetime import datetime, timezone

        # 1. Save prediction result
        predictions_collection.insert_one(prediction_doc)
        _db_log.info("Prediction saved for order %s", prediction_doc.get("order_id"))

        # 2. Save the raw order
        order_doc = dict(order_dict)
        order_doc["scored_at"] = datetime.now(timezone.utc)
        orders_collection.update_one(
            {"order_id": order_doc.get("order_id")},
            {"$set": order_doc},
            upsert=True,
        )
        _db_log.info("Order saved: %s", order_doc.get("order_id"))

        # 3. If NEW customer, register them so next order uses real profile
        if customer_status == "new":
            new_customer_doc = {
                "customer_id"            : customer_id,
                "past_orders_count"      : 1,
                "past_rto_orders"        : 0,
                "past_rto_rate"          : 0.0,
                "address_stability_score": 0.50,
                "distinct_addresses_used": 1,
                "tenure_months"          : 0,
                "orders_per_month"       : 0.0,
                "orders_last_90d"        : 1,
                "prev_cod_orders"        : 1 if order_dict.get("payment_mode", "").upper() == "COD" else 0,
                "prev_cod_success_rate"  : 0.0,
                "cod_share_history"      : 1.0 if order_dict.get("payment_mode", "").upper() == "COD" else 0.0,
                "avg_order_value"        : float(order_dict.get("order_value", 0)),
                "registered_at"          : datetime.now(timezone.utc),
            }
            customers_collection.update_one(
                {"customer_id": customer_id},
                {"$set": new_customer_doc},
                upsert=True,
            )
            _db_log.info("New customer %s registered in DB", customer_id)

    except Exception as e:
        _db_log.error("DB save failed (non-critical): %s", e)




# =====================================================
# ROUTER
# =====================================================

router = APIRouter(
    prefix="/rto",
    tags=["RTOGuard"]
)


# =====================================================
# CREATE ENGINE OBJECTS
# =====================================================

recommendation_engine = (
    ActionRecommendationEngine()
)

cost_calculator = (
    CostCalculator()
)

simulation_engine = (
    SimulationEngine(
        recommendation_engine=
            recommendation_engine,

        cost_calculator=
            cost_calculator
    )
)


# =====================================================
# 1. ACTION RECOMMENDATION
# =====================================================

@router.post("/recommend-action")
def recommend_action(
    request: RecommendationRequest
):

    try:

        result = (
            recommendation_engine
            .recommend(

                risk_score=
                    request.risk_score,

                order_value=
                    request.order_value,

                payment_mode=
                    request.payment_mode,

                top_factors=
                    request.top_factors
            )
        )

        return result

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


# =====================================================
# 2. COST CALCULATOR
# =====================================================

@router.post("/calculate-cost")
def calculate_cost(
    request: CostRequest
):

    try:

        # First determine action

        recommendation = (
            recommendation_engine
            .recommend(

                risk_score=
                    request.risk_score,

                order_value=
                    request.order_value,

                payment_mode=
                    request.payment_mode,

                top_factors=
                    request.top_factors
            )
        )

        # Then calculate economics

        economics = (
            cost_calculator
            .calculate(

                order_value=
                    request.order_value,

                risk_score=
                    request.risk_score,

                action=
                    recommendation[
                        "recommended_action"
                    ],

                suggested_deposit=
                    recommendation[
                        "suggested_deposit"
                    ]
            )
        )

        return economics

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


# =====================================================
# 3. COMPLETE ORDER DECISION
# =====================================================

@router.post("/score-order")
def score_order(
    request: RawOrder
):
    """
    Evaluates an incoming customer order end-to-end:
    1. Fetches customer history from MongoDB (falls back to in-memory for dev).
    2. Runs Riya's ML Risk Scoring Engine  → risk_score & top_factors.
    3. Shubham's Action Recommendation    → recommended_action, risk_level.
    4. Shubham's Cost Calculator          → financial impact metrics.
    5. Saves prediction audit doc to MongoDB predictions_collection.
    """
    try:
        order_dict = request.model_dump()

        # ---------------------------------------------
        # STEP 0: Customer History Lookup (MongoDB → mock fallback)
        # ---------------------------------------------
        customer_profile = get_customer_profile(request.customer_id)
        customer_status  = "new" if is_new_customer(customer_profile) else "returning"

        # ---------------------------------------------
        # STEP 1: ML Risk Scoring Engine (Riya)
        # ---------------------------------------------
        ml_result   = ml_score_order(order_dict)
        risk_score  = ml_result["risk_score"]
        top_factors = ml_result.get("top_factors", [])

        # ---------------------------------------------
        # STEP 2: Action Recommendation Engine (Shubham)
        # ---------------------------------------------
        recommendation = recommendation_engine.recommend(
            risk_score   = risk_score,
            order_value  = request.order_value,
            payment_mode = request.payment_mode,
            top_factors  = top_factors,
        )

        # ---------------------------------------------
        # STEP 3: Economics & Cost Calculator (Shubham)
        # ---------------------------------------------
        economics = cost_calculator.calculate(
            order_value      = request.order_value,
            risk_score       = risk_score,
            action           = recommendation["recommended_action"],
            suggested_deposit= recommendation["suggested_deposit"],
        )

        # ---------------------------------------------
        # STEP 4: Persist audit trail to MongoDB
        # ---------------------------------------------
        prediction_doc = create_prediction_doc(
            order_id   = str(request.order_id or ""),
            risk_score = risk_score,
            action     = recommendation["recommended_action"],
            reason     = "; ".join(top_factors[:3]),
        )
        prediction_doc["customer_id"]     = request.customer_id
        prediction_doc["customer_status"] = customer_status
        _save_to_db(
            order_dict      = order_dict,
            prediction_doc  = prediction_doc,
            customer_status = customer_status,
            customer_id     = request.customer_id,
        )

        # ---------------------------------------------
        # STEP 5: Combined Decision Response
        # ---------------------------------------------
        return {
            "order_id"       : request.order_id,
            "customer_status": customer_status,          # "new" or "returning"
            "risk_score"     : risk_score,
            "top_factors"    : top_factors,
            **recommendation,
            **economics,
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


# =====================================================
# 4. SIMULATION
# =====================================================

@router.post("/simulate")
def simulate(
    request: SimulationRequest
):

    try:

        # ---------------------------------------------
        # If frontend sends orders
        # use those orders.
        # ---------------------------------------------

        if request.orders:

            orders = [

                order.model_dump()

                for order in request.orders
            ]

        # ---------------------------------------------
        # Otherwise generate synthetic orders
        # ---------------------------------------------

        else:

            orders = (
                simulation_engine
                .generate_synthetic_orders(

                    number_of_orders=
                        request.order_count,

                    seed=
                        request.seed
                )
            )

        # ---------------------------------------------
        # RUN SIMULATION
        # ---------------------------------------------

        result = (
            simulation_engine
            .simulate(
                orders
            )
        )

        return result

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


# =====================================================
# 5. QUICK 1000 ORDER DEMO
# =====================================================

@router.get("/simulation-demo")
def simulation_demo():

    orders = (
        simulation_engine
        .generate_synthetic_orders(
            number_of_orders=1000,
            seed=42
        )
    )

    return (
        simulation_engine
        .simulate(
            orders
        )
    )


# =====================================================
# 6. SCORE + SIMULATE (combined)
# =====================================================

@router.post("/simulate-orders")
def simulate_with_scoring(
    request: RawSimulationRequest
):
    """
    Takes raw orders (no risk_score needed).
    Step 1: Runs ML scoring on each order.
    Step 2: Feeds scored orders into simulation engine.
    Returns full simulation results.
    """

    try:

        scored_orders = []

        for i, raw_order in enumerate(
            request.orders
        ):

            # -----------------------------------------
            # ML SCORING
            # -----------------------------------------

            order_dict = raw_order.model_dump()

            ml_result = ml_score_order(order_dict)

            # -----------------------------------------
            # BUILD SCORED ORDER
            # -----------------------------------------

            scored_orders.append({
                "order_id":
                    order_dict.get("order_id")
                    or f"ORD{i+1:04d}",

                "order_value":
                    order_dict["order_value"],

                "payment_mode":
                    order_dict["payment_mode"],

                "risk_score":
                    ml_result["risk_score"],

                "top_factors":
                    ml_result.get(
                        "top_factors", []
                    )
            })

        # ---------------------------------------------
        # RUN SIMULATION
        # ---------------------------------------------

        result = (
            simulation_engine
            .simulate(scored_orders)
        )

        return result

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )