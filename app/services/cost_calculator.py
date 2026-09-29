from dataclasses import dataclass


@dataclass
class CostAssumptions:

    # ---------------------------------------------
    # RTO COST
    # ---------------------------------------------

    forward_logistics_cost: float = 200.0
    reverse_logistics_cost: float = 300.0
    acquisition_cost: float = 200.0
    other_rto_cost: float = 50.0

    # ---------------------------------------------
    # INTERVENTION COST
    # ---------------------------------------------

    confirmation_agent_cost: float = 25.0

    deposit_fixed_handling_cost: float = 10.0

    deposit_handling_rate: float = 0.01

    # ---------------------------------------------
    # CONVERSION
    # ---------------------------------------------

    contribution_margin_rate: float = 0.20

    # ---------------------------------------------
    # SIMULATION ASSUMPTIONS
    # ---------------------------------------------

    partial_deposit_rto_reduction: float = 0.25

    confirmation_rto_reduction: float = 0.40

    partial_deposit_abandonment_rate: float = 0.07

    confirmation_abandonment_rate: float = 0.15

    # ---------------------------------------------
    # TOTAL RTO COST
    # ---------------------------------------------

    def get_total_rto_cost(self) -> float:

        return (
            self.forward_logistics_cost
            + self.reverse_logistics_cost
            + self.acquisition_cost
            + self.other_rto_cost
        )


class CostCalculator:

    def __init__(
        self,
        assumptions: CostAssumptions | None = None
    ):

        self.assumptions = (
            assumptions
            if assumptions
            else CostAssumptions()
        )

    # =================================================
    # EXPECTED RTO LOSS
    # =================================================

    def expected_rto_loss(
        self,
        risk_score: float
    ) -> float:

        if not 0 <= risk_score <= 1:
            raise ValueError(
                "risk_score must be between 0 and 1"
            )

        total_rto_cost = (
            self.assumptions.get_total_rto_cost()
        )

        return risk_score * total_rto_cost

    # =================================================
    # INTERVENTION RTO PROBABILITY
    # =================================================

    def calculate_intervention_probability(
        self,
        baseline_probability: float,
        action: str
    ) -> float:

        if action in [
            "SHIP_NORMAL",
            "NO_COD_INTERVENTION"
        ]:

            return baseline_probability

        elif action == "PARTIAL_DEPOSIT":

            return (
                baseline_probability
                * (
                    1
                    - self.assumptions
                    .partial_deposit_rto_reduction
                )
            )

        elif action == "CONFIRMATION":

            return (
                baseline_probability
                * (
                    1
                    - self.assumptions
                    .confirmation_rto_reduction
                )
            )

        else:

            raise ValueError(
                f"Unknown action: {action}"
            )

    # =================================================
    # INTERVENTION COST
    # =================================================

    def calculate_intervention_cost(
        self,
        order_value: float,
        action: str,
        suggested_deposit: float = 0.0
    ) -> float:

        if action in [
            "SHIP_NORMAL",
            "NO_COD_INTERVENTION"
        ]:

            return 0.0

        elif action == "PARTIAL_DEPOSIT":

            return (
                self.assumptions
                .deposit_fixed_handling_cost
                +
                suggested_deposit
                * self.assumptions
                .deposit_handling_rate
            )

        elif action == "CONFIRMATION":

            return (
                self.assumptions
                .confirmation_agent_cost
            )

        else:

            raise ValueError(
                f"Unknown action: {action}"
            )

    # =================================================
    # CONVERSION LOSS
    # =================================================

    def calculate_conversion_loss(
        self,
        order_value: float,
        action: str
    ) -> float:

        if action in [
            "SHIP_NORMAL",
            "NO_COD_INTERVENTION"
        ]:

            abandonment_rate = 0.0

        elif action == "PARTIAL_DEPOSIT":

            abandonment_rate = (
                self.assumptions
                .partial_deposit_abandonment_rate
            )

        elif action == "CONFIRMATION":

            abandonment_rate = (
                self.assumptions
                .confirmation_abandonment_rate
            )

        else:

            raise ValueError(
                f"Unknown action: {action}"
            )

        return (
            order_value
            * self.assumptions.contribution_margin_rate
            * abandonment_rate
        )

    # =================================================
    # COMPLETE COST CALCULATION
    # =================================================

    def calculate(
        self,
        order_value: float,
        risk_score: float,
        action: str,
        suggested_deposit: float = 0.0
    ):

        # ---------------------------------------------
        # BASELINE
        # ---------------------------------------------

        baseline_probability = risk_score

        baseline_loss = (
            self.expected_rto_loss(
                baseline_probability
            )
        )

        # ---------------------------------------------
        # INTERVENTION
        # ---------------------------------------------

        intervention_probability = (
            self.calculate_intervention_probability(
                baseline_probability,
                action
            )
        )

        intervention_loss = (
            self.expected_rto_loss(
                intervention_probability
            )
        )

        # ---------------------------------------------
        # SAVING
        # ---------------------------------------------

        rto_loss_avoided = (
            baseline_loss
            - intervention_loss
        )

        # ---------------------------------------------
        # INTERVENTION COST
        # ---------------------------------------------

        intervention_cost = (
            self.calculate_intervention_cost(
                order_value,
                action,
                suggested_deposit
            )
        )

        # ---------------------------------------------
        # CONVERSION LOSS
        # ---------------------------------------------

        conversion_loss = (
            self.calculate_conversion_loss(
                order_value,
                action
            )
        )

        # ---------------------------------------------
        # NET IMPACT
        # ---------------------------------------------

        net_impact = (
            rto_loss_avoided
            - intervention_cost
            - conversion_loss
        )

        return {

            "baseline_rto_probability":
                round(
                    baseline_probability,
                    4
                ),

            "intervention_rto_probability":
                round(
                    intervention_probability,
                    4
                ),

            "baseline_expected_rto_loss":
                round(
                    baseline_loss,
                    2
                ),

            "intervention_expected_rto_loss":
                round(
                    intervention_loss,
                    2
                ),

            "rto_loss_avoided":
                round(
                    rto_loss_avoided,
                    2
                ),

            "intervention_cost":
                round(
                    intervention_cost,
                    2
                ),

            "conversion_loss_impact":
                round(
                    conversion_loss,
                    2
                ),

            "net_impact":
                round(
                    net_impact,
                    2
                )
        }