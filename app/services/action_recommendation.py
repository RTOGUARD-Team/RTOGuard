from dataclasses import dataclass


@dataclass
class RecommendationAssumptions:
    deposit_min_rate: float = 0.05
    deposit_max_rate: float = 0.25
    deposit_cap: float = 500.0


class ActionRecommendationEngine:

    def __init__(
        self,
        assumptions: RecommendationAssumptions | None = None
    ):
        self.assumptions = (
            assumptions
            if assumptions
            else RecommendationAssumptions()
        )

    # --------------------------------------------------
    # Convert risk score into LOW / MEDIUM / HIGH
    # --------------------------------------------------

    @staticmethod
    def get_risk_level(risk_score: float) -> str:

        if not 0.0 <= risk_score <= 1.0:
            raise ValueError(
                "risk_score must be between 0 and 1"
            )

        if risk_score < 0.30:
            return "LOW"

        elif risk_score < 0.60:
            return "MEDIUM"

        else:
            return "HIGH"

    # --------------------------------------------------
    # Calculate deposit percentage based on risk
    # --------------------------------------------------

    def get_deposit_rate(self, risk_score: float) -> float:

        return (
            self.assumptions.deposit_min_rate
            + risk_score
            * (
                self.assumptions.deposit_max_rate
                - self.assumptions.deposit_min_rate
            )
        )

    # --------------------------------------------------
    # Main recommendation function
    # --------------------------------------------------

    def recommend(
        self,
        risk_score: float,
        order_value: float,
        payment_mode: str,
        top_factors: list[str] | None = None
    ):

        if order_value <= 0:
            raise ValueError(
                "order_value must be greater than 0"
            )

        if not 0.0 <= risk_score <= 1.0:
            raise ValueError(
                "risk_score must be between 0 and 1"
            )

        payment_mode = payment_mode.upper()

        risk_level = self.get_risk_level(risk_score)

        # ----------------------------------------------
        # PREPAID ORDER
        # ----------------------------------------------

        if payment_mode == "PREPAID":

            return {
                "risk_score": round(risk_score, 4),
                "risk_level": risk_level,
                "recommended_action": "NO_COD_INTERVENTION",
                "suggested_deposit": 0.0,
                "reason": (
                    "Order is already prepaid; "
                    "COD intervention is not required."
                ),
                "top_factors": top_factors or []
            }

        # ----------------------------------------------
        # LOW RISK
        # ----------------------------------------------

        if risk_level == "LOW":

            return {
                "risk_score": round(risk_score, 4),
                "risk_level": "LOW",
                "recommended_action": "SHIP_NORMAL",
                "suggested_deposit": 0.0,
                "reason": (
                    "Low expected RTO risk; "
                    "ship as normal COD."
                ),
                "top_factors": top_factors or []
            }

        # ----------------------------------------------
        # MEDIUM RISK
        # ----------------------------------------------

        elif risk_level == "MEDIUM":

            deposit_rate = self.get_deposit_rate(
                risk_score
            )

            suggested_deposit = min(
                order_value * deposit_rate,
                self.assumptions.deposit_cap
            )

            return {
                "risk_score": round(risk_score, 4),
                "risk_level": "MEDIUM",
                "recommended_action": "PARTIAL_DEPOSIT",
                "suggested_deposit": round(
                    suggested_deposit,
                    2
                ),
                "reason": (
                    "Medium risk; request a partial "
                    "deposit to reduce exposure while "
                    "preserving conversion."
                ),
                "top_factors": top_factors or []
            }

        # ----------------------------------------------
        # HIGH RISK
        # ----------------------------------------------

        else:

            return {
                "risk_score": round(risk_score, 4),
                "risk_level": "HIGH",
                "recommended_action": "CONFIRMATION",
                "suggested_deposit": 0.0,
                "reason": (
                    "High risk; place the order in the "
                    "confirmation queue or require "
                    "prepaid commitment before shipping."
                ),
                "top_factors": top_factors or []
            }