def recommend_action(score: float) -> tuple[str, str]:
    """Return (action, reason) based on risk score.

    TODO: Replace with ActionRecommendationEngine from services
    once routers are consolidated.
    """
    if score < 0.3:
        return "SHIP_COD", "Low RTO risk — ship normally"

    if score < 0.6:
        return "PARTIAL_DEPOSIT", "Medium RTO risk — request partial deposit"

    return "CONFIRMATION_CALL", "High RTO risk — require confirmation before shipping"