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

        total_baseline_rto_orders = 0.0

        total_intervention_rto_orders = 0.0

        total_baseline_loss = 0.0

        total_intervention_loss = 0.0

        total_rto_loss_avoided = 0.0

        total_intervention_cost = 0.0

        total_conversion_loss = 0.0

        total_net_impact = 0.0

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
        total_rto_cost = self.cost_calculator.assumptions.get_total_rto_cost()
        margin = self.cost_calculator.assumptions.contribution_margin_rate

        # =============================================
        # PROCESS EVERY ORDER AGAINST GROUND TRUTH
        # =============================================

        for order in orders:

            # -----------------------------------------
            # 1. GROUND TRUTH OUTCOME RESOLUTION
            # -----------------------------------------
            raw_outcome = str(order.get("actual_outcome") or order.get("outcome") or "").upper()
            if raw_outcome in ("RTO", "RETURNED"):
                is_rto = True
            elif raw_outcome in ("DELIVERED", "COMPLETED", "SUCCESS"):
                is_rto = False
            else:
                is_rto = (order.get("risk_score", 0.0) >= 0.50)

            # -----------------------------------------
            # PASS A: BASELINE (Zero intervention)
            # Evaluated against actual ground truth
            # -----------------------------------------
            order_baseline_loss = total_rto_cost if is_rto else 0.0
            order_baseline_rto = 1.0 if is_rto else 0.0
            total_baseline_loss += order_baseline_loss
            total_baseline_rto_orders += order_baseline_rto

            # -----------------------------------------
            # PASS B: AI-MITIGATED
            # Model decides action from predicted risk
            # -----------------------------------------
            recommendation = (
                self.recommendation_engine
                .recommend(
                    risk_score=order["risk_score"],
                    order_value=order["order_value"],
                    payment_mode=order["payment_mode"],
                    top_factors=order.get("top_factors", [])
                )
            )

            action = recommendation["recommended_action"]
            suggested_deposit = recommendation["suggested_deposit"]
            action_counts[action] = action_counts.get(action, 0) + 1

            order_val = float(order["order_value"])

            # 1. Direct intervention cost
            ord_intervention_cost = self.cost_calculator.calculate_intervention_cost(
                order_value=order_val,
                action=action,
                suggested_deposit=suggested_deposit
            )

            # 2. Evaluate financial impact against ground truth
            if action in ("SHIP_NORMAL", "NO_COD_INTERVENTION"):
                ord_mitigated_rto_loss = total_rto_cost if is_rto else 0.0
                ord_mitigated_rto_orders = 1.0 if is_rto else 0.0
                ord_conversion_loss = 0.0
            elif action == "PARTIAL_DEPOSIT":
                reduction = self.cost_calculator.assumptions.partial_deposit_rto_reduction
                abandonment = self.cost_calculator.assumptions.partial_deposit_abandonment_rate
                if is_rto:
                    ord_mitigated_rto_loss = total_rto_cost * (1.0 - reduction)
                    ord_mitigated_rto_orders = 1.0 - reduction
                    ord_conversion_loss = 0.0
                else:
                    ord_mitigated_rto_loss = 0.0
                    ord_mitigated_rto_orders = 0.0
                    ord_conversion_loss = order_val * margin * abandonment
            elif action == "CONFIRMATION":
                reduction = self.cost_calculator.assumptions.confirmation_rto_reduction
                abandonment = self.cost_calculator.assumptions.confirmation_abandonment_rate
                if is_rto:
                    ord_mitigated_rto_loss = total_rto_cost * (1.0 - reduction)
                    ord_mitigated_rto_orders = 1.0 - reduction
                    ord_conversion_loss = 0.0
                else:
                    ord_mitigated_rto_loss = 0.0
                    ord_mitigated_rto_orders = 0.0
                    ord_conversion_loss = order_val * margin * abandonment
            else:
                ord_mitigated_rto_loss = total_rto_cost if is_rto else 0.0
                ord_mitigated_rto_orders = 1.0 if is_rto else 0.0
                ord_conversion_loss = 0.0

            ord_loss_avoided = order_baseline_loss - ord_mitigated_rto_loss
            ord_net_impact = ord_loss_avoided - ord_intervention_cost - ord_conversion_loss
            ord_total_intervention_loss = ord_mitigated_rto_loss + ord_intervention_cost + ord_conversion_loss

            total_intervention_loss += ord_total_intervention_loss
            total_intervention_rto_orders += ord_mitigated_rto_orders
            total_rto_loss_avoided += ord_loss_avoided
            total_intervention_cost += ord_intervention_cost
            total_conversion_loss += ord_conversion_loss
            total_net_impact += ord_net_impact

            economics = {
                "baseline_rto_probability": order_baseline_rto,
                "intervention_rto_probability": round(ord_mitigated_rto_orders, 4),
                "baseline_expected_rto_loss": round(order_baseline_loss, 2),
                "intervention_expected_rto_loss": round(ord_total_intervention_loss, 2),
                "rto_loss_avoided": round(ord_loss_avoided, 2),
                "intervention_cost": round(ord_intervention_cost, 2),
                "conversion_loss_impact": round(ord_conversion_loss, 2),
                "net_impact": round(ord_net_impact, 2),
            }

            order_results.append({
                **order,
                "outcome": "RTO" if is_rto else "DELIVERED",
                **recommendation,
                **economics
            })

        # =============================================
        # AGGREGATE METRICS
        # =============================================

        number_of_orders = len(orders)

        baseline_rto_rate = (
            total_baseline_rto_orders
            / number_of_orders
        )

        intervention_rto_rate = (
            total_intervention_rto_orders
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
                        total_baseline_rto_orders,
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
                        total_intervention_rto_orders,
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
                    [],

                "outcome":
                    "RTO" if random.random() < risk_score else "DELIVERED"
            })

        return orders