def score_order(order) -> float:
    """Score an order for RTO risk. Returns a float between 0 and 1.

    TODO: Replace with real ML model inference.
    """
    score = 0.2

    # COD orders are riskier
    if getattr(order, "payment_mode", "cod") == "cod":
        score += 0.25

    # High-value orders are riskier
    if getattr(order, "order_value", 0) >= 4000:
        score += 0.15

    # Festive window increases risk
    if getattr(order, "is_festive_window", False):
        score += 0.10

    # Electronics category is riskier
    if getattr(order, "category", "") == "electronics":
        score += 0.10

    return min(score, 1.0)