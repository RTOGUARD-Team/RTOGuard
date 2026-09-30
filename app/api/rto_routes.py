from fastapi import APIRouter, HTTPException

from app.rto_schemas import (
    RecommendationRequest,
    CostRequest,
    SimulationRequest,
    RawSimulationRequest,
    RawOrder,
    OrderOutcomeRequest
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
    Saves and updates MongoDB after every scoring request:
      1. predictions  -- full ML result + action (audit trail)
      2. orders       -- raw incoming order (order log)
      3. customers    -- IF NEW: registers them with initial profile
                      -- IF RETURNING: increments past_orders_count & orders_last_90d
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
        order_doc["status"] = "PENDING_DISPATCH"
        orders_collection.update_one(
            {"order_id": order_doc.get("order_id")},
            {"$set": order_doc},
            upsert=True,
        )
        _db_log.info("Order saved: %s", order_doc.get("order_id"))

        # 3. Update customer history in database
        is_cod = order_dict.get("payment_mode", "").upper() == "COD"
        order_val = float(order_dict.get("order_value", 0))

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
                "prev_cod_orders"        : 1 if is_cod else 0,
                "prev_cod_success_rate"  : 0.0,
                "cod_share_history"      : 1.0 if is_cod else 0.0,
                "avg_order_value"        : order_val,
                "registered_at"          : datetime.now(timezone.utc),
            }
            customers_collection.update_one(
                {"customer_id": customer_id},
                {"$set": new_customer_doc},
                upsert=True,
            )
            _db_log.info("New customer %s registered in DB", customer_id)
        else:
            # RETURNING CUSTOMER: increment their order counts
            # Query candidate ID variants (int or str)
            cand_query = {"$or": [{"customer_id": customer_id}]}
            try:
                cand_query["$or"].append({"customer_id": int(customer_id)})
            except (ValueError, TypeError):
                pass
            cand_query["$or"].append({"customer_id": str(customer_id)})

            update_ops = {
                "$inc": {
                    "past_orders_count": 1,
                    "orders_last_90d": 1,
                }
            }
            if is_cod:
                update_ops["$inc"]["prev_cod_orders"] = 1

            customers_collection.update_one(cand_query, update_ops)
            _db_log.info("Incremented order history for returning customer %s", customer_id)

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


# =====================================================
# 7. LIVE EVALUATED ORDERS FROM DB
# =====================================================

@router.get("/evaluated-orders")
def get_evaluated_orders(limit: int = 50):
    """
    Fetch evaluated orders merged with their predictions from MongoDB.
    Used by Frontend Dashboard, Orders Feed, and OrderDrawer.
    """
    try:
        from app.db import orders_collection, predictions_collection

        # Fetch recent predictions sorted by newest first
        predictions = list(predictions_collection.find().sort("_id", -1).limit(limit))

        evaluated_list = []
        for pred in predictions:
            order_id = pred.get("order_id")
            order_doc = orders_collection.find_one({"order_id": order_id}) or {}

            # Map to frontend UI schema
            risk_score = float(pred.get("risk_score", 0.0))
            if risk_score > 0.65:
                risk_level = "High"
            elif risk_score >= 0.35:
                risk_level = "Medium"
            else:
                risk_level = "Low"

            # Parse reasons / top_factors
            reasons_raw = pred.get("reason", "")
            reasons = [r.strip() for r in reasons_raw.split(";") if r.strip()]

            order_val = float(order_doc.get("order_value", 1500.0))

            evaluated_list.append({
                "order_id": order_id or f"ORD-{str(pred['_id'])[-6:]}",
                "customer_id": str(pred.get("customer_id") or order_doc.get("customer_id") or "CUS-1001"),
                "order_value": order_val,
                "payment_mode": str(order_doc.get("payment_mode", "COD")).upper(),
                "pincode": str(order_doc.get("pincode", "110001")),
                "category": str(order_doc.get("category", "General")).title(),
                "risk_score": risk_score,
                "risk_level": risk_level,
                "reasons": reasons if reasons else ["Low Historical RTO Risk"],
                "recommended_action": pred.get("action", "SHIP_NORMAL"),
                "expected_loss_prevented": round(order_val * risk_score * 0.35, 2),
                "scored_at": pred.get("scored_at").isoformat() if hasattr(pred.get("scored_at"), "isoformat") else str(pred.get("scored_at") or ""),
            })

        return evaluated_list

    except Exception as e:
        _db_log.error("Failed to fetch evaluated orders: %s", e)
        return []


# =====================================================
# 8. LIVE DASHBOARD KPI SUMMARY
# =====================================================

@router.get("/dashboard-summary")
def get_dashboard_summary():
    """
    Computes real-time KPI metrics from MongoDB predictions and orders.
    """
    try:
        from app.db import predictions_collection, orders_collection

        total_orders = predictions_collection.count_documents({})
        if total_orders == 0:
            return {
                "total_orders": 0,
                "high_risk_orders": 0,
                "rto_risk_percentage": "0.0",
                "total_order_value": 0.0,
                "expected_loss_prevented": 0.0,
            }

        preds = list(predictions_collection.find())
        high_risk_count = 0
        total_value = 0.0
        total_loss_prevented = 0.0

        for p in preds:
            score = float(p.get("risk_score", 0.0))
            if score > 0.65:
                high_risk_count += 1

            # Fetch matching order value
            o = orders_collection.find_one({"order_id": p.get("order_id")}) or {}
            val = float(o.get("order_value", 1500.0))
            total_value += val
            total_loss_prevented += round(val * score * 0.35, 2)

        return {
            "total_orders": total_orders,
            "high_risk_orders": high_risk_count,
            "rto_risk_percentage": f"{(high_risk_count / total_orders * 100):.1f}",
            "total_order_value": round(total_value, 2),
            "expected_loss_prevented": round(total_loss_prevented, 2),
        }

    except Exception as e:
        _db_log.error("Failed to calculate dashboard summary: %s", e)
        return {
            "total_orders": 0,
            "high_risk_orders": 0,
            "rto_risk_percentage": "0.0",
            "total_order_value": 0.0,
            "expected_loss_prevented": 0.0,
        }


# =====================================================
# 9. ORDER OUTCOME FEEDBACK LOOP (Post-Delivery Status)
# =====================================================

@router.post("/order-outcome")
def record_order_outcome(request: OrderOutcomeRequest):
    """
    Closes the real-world feedback loop when a courier delivers or returns an order:
    1. Updates the order status in `orders_collection` ('DELIVERED' or 'RTO' / 'RETURNED').
    2. Updates the customer's behavioral record in `customers_collection`:
       - If RTO / RETURNED: increments `past_rto_orders` += 1.
       - Recomputes new `past_rto_rate` = past_rto_orders / past_orders_count.
    """
    try:
        from app.db import orders_collection, customers_collection
        from datetime import datetime, timezone

        norm_status = request.status.strip().upper()
        if norm_status not in ["DELIVERED", "RTO", "RETURNED", "CANCELLED"]:
            raise HTTPException(
                status_code=400,
                detail="Status must be one of: 'DELIVERED', 'RTO', 'RETURNED', 'CANCELLED'"
            )

        # 1. Find and update the order
        order = orders_collection.find_one({"order_id": request.order_id})
        if not order:
            raise HTTPException(
                status_code=404,
                detail=f"Order {request.order_id} not found in database."
            )

        orders_collection.update_one(
            {"order_id": request.order_id},
            {
                "$set": {
                    "delivery_status": norm_status,
                    "outcome_recorded_at": datetime.now(timezone.utc),
                    "notes": request.notes,
                }
            }
        )

        # 2. Update customer RTO profile
        customer_id = order.get("customer_id")
        customer_updated = False
        new_rto_rate = 0.0

        if customer_id is not None:
            cand_query = {"$or": [{"customer_id": customer_id}]}
            try:
                cand_query["$or"].append({"customer_id": int(customer_id)})
            except (ValueError, TypeError):
                pass
            cand_query["$or"].append({"customer_id": str(customer_id)})

            cust_doc = customers_collection.find_one(cand_query)

            if cust_doc:
                is_rto = norm_status in ["RTO", "RETURNED"]
                past_orders = max(int(cust_doc.get("past_orders_count", 1)), 1)
                past_rto = int(cust_doc.get("past_rto_orders", 0))

                if is_rto:
                    past_rto += 1

                new_rto_rate = round(past_rto / past_orders, 4)

                update_dict = {
                    "$set": {
                        "past_rto_orders": past_rto,
                        "past_rto_rate": new_rto_rate,
                    }
                }
                customers_collection.update_one(cand_query, update_dict)
                customer_updated = True
                _db_log.info(
                    "Customer %s updated: past_rto_orders=%d, new_rto_rate=%.4f",
                    customer_id, past_rto, new_rto_rate
                )

        return {
            "order_id": request.order_id,
            "status": norm_status,
            "customer_id": customer_id,
            "customer_profile_updated": customer_updated,
            "new_rto_rate": new_rto_rate,
            "message": f"Order {request.order_id} marked as {norm_status}. Customer history updated."
        }

    except HTTPException:
        raise
    except Exception as e:
        _db_log.error("Failed to record order outcome: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
