import random

from app.services.action_recommendation import (
    ActionRecommendationEngine
)

from app.services.cost_calculator import (
    CostCalculator
)


class SimulationEngine:

    def __init__(
        self,
        recommendation_engine=None,
        cost_calculator=None
    ):

        self.recommendation_engine = (
            recommendation_engine
            if recommendation_engine
            else ActionRecommendationEngine()
        )

        self.cost_calculator = (
            cost_calculator
            if cost_calculator
            else CostCalculator()
        )

    # =================================================
    # RUN SIMULATION
    # =================================================

    def simulate(
        self,
        orders: list[dict]
    ):

        if not orders:

            raise ValueError(
                "orders cannot be empty"
            )

        # ---------------------------------------------
        # TOTALS
        # ---------------------------------------------

        total_baseline_probability = 0

        total_intervention_probability = 0

        total_baseline_loss = 0

        total_intervention_loss = 0

        total_rto_loss_avoided = 0

        total_intervention_cost = 0

        total_conversion_loss = 0

        total_net_impact = 0

        # ---------------------------------------------
        # ACTION COUNTS
        # ---------------------------------------------

        action_counts = {

            "SHIP_NORMAL": 0,

            "PARTIAL_DEPOSIT": 0,

            "CONFIRMATION": 0,

            "NO_COD_INTERVENTION": 0
        }

        order_results = []

        # =============================================
        # PROCESS EVERY ORDER
        # =============================================

        for order in orders:

            # -----------------------------------------
            # ACTION RECOMMENDATION
            # -----------------------------------------

            recommendation = (
                self.recommendation_engine
                .recommend(
                    risk_score=order["risk_score"],

                    order_value=order["order_value"],

                    payment_mode=order["payment_mode"],

                    top_factors=order.get(
                        "top_factors",
                        []
                    )
                )
            )

            # -----------------------------------------
            # COST CALCULATION
            # -----------------------------------------

            economics = (
                self.cost_calculator
                .calculate(

                    order_value=
                        order["order_value"],

                    risk_score=
                        order["risk_score"],

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

            action = (
                recommendation[
                    "recommended_action"
                ]
            )

            action_counts[action] += 1

            # -----------------------------------------
            # ADD TO TOTALS
            # -----------------------------------------

            total_baseline_probability += (
                economics[
                    "baseline_rto_probability"
                ]
            )

            total_intervention_probability += (
                economics[
                    "intervention_rto_probability"
                ]
            )

            total_baseline_loss += (
                economics[
                    "baseline_expected_rto_loss"
                ]
            )

            total_intervention_loss += (
                economics[
                    "intervention_expected_rto_loss"
                ]
            )

            total_rto_loss_avoided += (
                economics[
                    "rto_loss_avoided"
                ]
            )

            total_intervention_cost += (
                economics[
                    "intervention_cost"
                ]
            )

            total_conversion_loss += (
                economics[
                    "conversion_loss_impact"
                ]
            )

            total_net_impact += (
                economics[
                    "net_impact"
                ]
            )

            # -----------------------------------------
            # SAVE ORDER RESULT
            # -----------------------------------------

            order_results.append({

                **order,

                **recommendation,

                **economics
            })

        # =============================================
        # AGGREGATE METRICS
        # =============================================

        number_of_orders = len(orders)

        baseline_rto_rate = (
            total_baseline_probability
            / number_of_orders
        )

        intervention_rto_rate = (
            total_intervention_probability
            / number_of_orders
        )

        rto_rate_change = (
            baseline_rto_rate
            - intervention_rto_rate
        )

        saved_per_1000 = (
            total_net_impact
            * 1000
            / number_of_orders
        )

        # =============================================
        # FINAL RESPONSE
        # =============================================

        return {

            "order_count":
                number_of_orders,

            "baseline": {

                "expected_rto_rate":
                    round(
                        baseline_rto_rate,
                        4
                    ),

                "expected_rto_orders":
                    round(
                        total_baseline_probability,
                        2
                    ),

                "expected_rto_loss":
                    round(
                        total_baseline_loss,
                        2
                    )
            },

            "rtoguard": {

                "expected_rto_rate":
                    round(
                        intervention_rto_rate,
                        4
                    ),

                "expected_rto_orders":
                    round(
                        total_intervention_probability,
                        2
                    ),

                "expected_rto_loss":
                    round(
                        total_intervention_loss,
                        2
                    ),

                "action_counts":
                    action_counts
            },

            "impact": {

                "rto_loss_avoided":
                    round(
                        total_rto_loss_avoided,
                        2
                    ),

                "intervention_cost":
                    round(
                        total_intervention_cost,
                        2
                    ),

                "conversion_loss_impact":
                    round(
                        total_conversion_loss,
                        2
                    ),

                "net_business_impact":
                    round(
                        total_net_impact,
                        2
                    ),

                "rto_rate_change_points":
                    round(
                        rto_rate_change * 100,
                        2
                    ),

                "rupees_saved_per_1000_orders":
                    round(
                        saved_per_1000,
                        2
                    )
            },

            "orders":
                order_results
        }

    # =================================================
    # SYNTHETIC DATA FOR HACKATHON
    # =================================================

    @staticmethod
    def generate_synthetic_orders(
        number_of_orders=1000,
        seed=42
    ):

        random.seed(seed)

        orders = []

        for i in range(
            1,
            number_of_orders + 1
        ):

            # -----------------------------------------
            # PAYMENT MODE
            # -----------------------------------------

            payment_mode = (
                "COD"
                if random.random() < 0.78
                else "PREPAID"
            )

            # -----------------------------------------
            # ORDER VALUE
            # -----------------------------------------

            order_value = round(
                random.uniform(
                    500,
                    6000
                ),
                2
            )

            # -----------------------------------------
            # BASE RISK
            # -----------------------------------------

            risk_score = random.betavariate(
                2.0,
                4.0
            )

            # COD increases risk

            if payment_mode == "COD":

                risk_score += 0.12

            # Higher value increases risk

            if order_value >= 4000:

                risk_score += 0.10

            # Add noise

            risk_score += random.uniform(
                -0.08,
                0.08
            )

            # Keep inside 0-1

            risk_score = max(
                0.01,
                min(
                    0.99,
                    risk_score
                )
            )

            orders.append({

                "order_id":
                    f"ORD{i:04d}",

                "order_value":
                    order_value,

                "payment_mode":
                    payment_mode,

                "risk_score":
                    risk_score,

                "top_factors":
                    []
            })

        return orders