from fastapi import APIRouter, HTTPException

from app.rto_schemas import (
    RecommendationRequest,
    CostRequest,
    SimulationRequest,
    RawSimulationRequest
)

from app.core.scoring import score_order as ml_score_order

from app.services.action_recommendation import (
    ActionRecommendationEngine
)

from app.services.cost_calculator import (
    CostCalculator
)

from app.services.simulation_engine import (
    SimulationEngine
)


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
    request: RecommendationRequest
):

    try:

        # ---------------------------------------------
        # STEP 1
        # Recommendation
        # ---------------------------------------------

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

        # ---------------------------------------------
        # STEP 2
        # Economics
        # ---------------------------------------------

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

        # ---------------------------------------------
        # STEP 3
        # COMBINE
        # ---------------------------------------------

        return {

            **recommendation,

            **economics
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


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