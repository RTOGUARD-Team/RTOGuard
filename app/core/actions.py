def recommend_action(score: float):
    if score < 0.3:
        return "SHIP_COD", "Low RTO risk"

    if score < 0.6:
        return "PARTIAL_DEPOSIT", "Medium RTO risk"

    return "CONFIRMATION_CALL", "High RTO risk"