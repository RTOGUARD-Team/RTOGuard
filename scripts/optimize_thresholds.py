"""
Threshold Optimization Script for RTOGuard.

Simulates Pass A vs Pass B economics across candidate MEDIUM and HIGH risk cutoffs
on the exact 300-order temporal holdout dataset from scripts/compute_evaluation_metrics.py.
Identifies the threshold pair (t_med, t_high) that maximizes net_business_impact,
and reports precision, recall, and RTO rate reduction compared to current (0.30, 0.60).
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np

from app.core.scoring import score_order
from app.services.cost_calculator import CostCalculator
from app.services.action_recommendation import RecommendationAssumptions


def run_threshold_optimization():
    orders_path = PROJECT_ROOT / "app" / "data" / "orders.csv"
    customers_path = PROJECT_ROOT / "app" / "data" / "customers.csv"

    if not orders_path.exists():
        print(f"Error: {orders_path} not found.")
        sys.exit(1)

    print(f"Loading {orders_path}...")
    df = pd.read_csv(orders_path)
    df["order_ts_dt"] = pd.to_datetime(df["order_ts"])
    df = df.sort_values("order_ts_dt").reset_index(drop=True)

    # 70% Train / 30% Test temporal split (300 test holdout orders)
    train_size = int(len(df) * 0.70)
    test_df = df.iloc[train_size:].copy().reset_index(drop=True)

    # Pincode mapping
    cust_pincodes = {}
    if customers_path.exists():
        df_cust = pd.read_csv(customers_path)
        cust_pincodes = dict(
            zip(
                df_cust["customer_id"].astype(str).str.strip().str.lower(),
                df_cust["pincode"].astype(str).str.strip(),
            )
        )

    print(f"Scoring {len(test_df)} test holdout orders...")
    scored_orders = []
    for _, row in test_df.iterrows():
        cid = str(row["customer_id"]).strip().lower()
        order_dict = {
            "order_id": str(row["order_id"]),
            "customer_id": cid,
            "order_value": float(row["value"]),
            "payment_mode": str(row["payment_mode"]).upper(),
            "pincode": cust_pincodes.get(cid, "110001"),
            "category": str(row.get("category", "general")),
            "is_festive_window": bool(row.get("is_festive", 0)),
            "checkout_hour": int(row.get("hour_of_day", 14)),
            "address_quality_score": float(row.get("address_completeness", 0.8)),
        }
        res = score_order(order_dict)
        raw_outcome = str(row["outcome"]).strip().upper()
        is_rto = raw_outcome == "RTO"

        scored_orders.append({
            "order_id": order_dict["order_id"],
            "order_value": order_dict["order_value"],
            "payment_mode": order_dict["payment_mode"],
            "risk_score": float(res["risk_score"]),
            "is_rto": is_rto,
        })

    cost_calculator = CostCalculator()
    assumptions = cost_calculator.assumptions
    rec_assumptions = RecommendationAssumptions()

    total_rto_cost = assumptions.get_total_rto_cost()
    margin = assumptions.contribution_margin_rate
    part_dep_red = assumptions.partial_deposit_rto_reduction
    part_dep_abn = assumptions.partial_deposit_abandonment_rate
    conf_red = assumptions.confirmation_rto_reduction
    conf_abn = assumptions.confirmation_abandonment_rate

    # Pass A Baseline (identical across all threshold evaluations)
    baseline_rto_orders = sum(1.0 for o in scored_orders if o["is_rto"])
    baseline_loss = sum(total_rto_cost for o in scored_orders if o["is_rto"])
    baseline_rto_rate = baseline_rto_orders / len(scored_orders)

    def evaluate_threshold_pair(t_med: float, t_high: float):
        total_mitigated_rto_loss = 0.0
        total_mitigated_rto_orders = 0.0
        total_intervention_cost = 0.0
        total_conversion_loss = 0.0
        action_counts = {"SHIP_NORMAL": 0, "PARTIAL_DEPOSIT": 0, "CONFIRMATION": 0, "NO_COD_INTERVENTION": 0}

        y_true = []
        y_pred_med = []
        y_pred_high = []

        for o in scored_orders:
            score = o["risk_score"]
            is_rto = o["is_rto"]
            pmode = o["payment_mode"]
            val = o["order_value"]

            y_true.append(1 if is_rto else 0)
            y_pred_med.append(1 if score >= t_med else 0)
            y_pred_high.append(1 if score >= t_high else 0)

            # Determine action under candidate thresholds
            if pmode == "PREPAID":
                action = "NO_COD_INTERVENTION"
                suggested_deposit = 0.0
            elif score < t_med:
                action = "SHIP_NORMAL"
                suggested_deposit = 0.0
            elif score < t_high:
                action = "PARTIAL_DEPOSIT"
                dep_rate = rec_assumptions.deposit_min_rate + score * (
                    rec_assumptions.deposit_max_rate - rec_assumptions.deposit_min_rate
                )
                suggested_deposit = min(val * dep_rate, rec_assumptions.deposit_cap)
            else:
                action = "CONFIRMATION"
                suggested_deposit = 0.0

            action_counts[action] += 1

            # Direct intervention cost
            ord_interv_cost = cost_calculator.calculate_intervention_cost(
                order_value=val,
                action=action,
                suggested_deposit=suggested_deposit
            )
            total_intervention_cost += ord_interv_cost

            # Evaluate against ground truth
            if action in ("SHIP_NORMAL", "NO_COD_INTERVENTION"):
                if is_rto:
                    total_mitigated_rto_loss += total_rto_cost
                    total_mitigated_rto_orders += 1.0
            elif action == "PARTIAL_DEPOSIT":
                if is_rto:
                    total_mitigated_rto_loss += total_rto_cost * (1.0 - part_dep_red)
                    total_mitigated_rto_orders += 1.0 - part_dep_red
                else:
                    total_conversion_loss += val * margin * part_dep_abn
            elif action == "CONFIRMATION":
                if is_rto:
                    total_mitigated_rto_loss += total_rto_cost * (1.0 - conf_red)
                    total_mitigated_rto_orders += 1.0 - conf_red
                else:
                    total_conversion_loss += val * margin * conf_abn

        rto_loss_avoided = baseline_loss - total_mitigated_rto_loss
        net_impact = rto_loss_avoided - total_intervention_cost - total_conversion_loss
        intervention_rto_rate = total_mitigated_rto_orders / len(scored_orders)
        rto_rate_reduction_points = (baseline_rto_rate - intervention_rto_rate) * 100

        # Precision & Recall metrics
        y_true = np.array(y_true)
        y_pred_med = np.array(y_pred_med)
        y_pred_high = np.array(y_pred_high)

        def get_pr(pred, true):
            tp = int(np.sum((pred == 1) & (true == 1)))
            fp = int(np.sum((pred == 1) & (true == 0)))
            fn = int(np.sum((pred == 0) & (true == 1)))
            prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            return round(prec, 4), round(rec, 4)

        med_prec, med_rec = get_pr(y_pred_med, y_true)
        high_prec, high_rec = get_pr(y_pred_high, y_true)

        return {
            "t_med": round(t_med, 2),
            "t_high": round(t_high, 2),
            "net_business_impact": round(net_impact, 2),
            "rto_loss_avoided": round(rto_loss_avoided, 2),
            "intervention_cost": round(total_intervention_cost, 2),
            "conversion_loss": round(total_conversion_loss, 2),
            "rto_rate_reduction_points": round(rto_rate_reduction_points, 2),
            "mitigated_rto_rate": round(intervention_rto_rate, 4),
            "med_precision": med_prec,
            "med_recall": med_rec,
            "high_precision": high_prec,
            "high_recall": high_rec,
            "actions": action_counts,
        }

    # Grid search: sweep 0.10 to 0.80 in steps of 0.05
    step = 0.05
    thresholds = [round(x, 2) for x in np.arange(0.10, 0.85, step)]

    results = []
    for t_med in thresholds:
        for t_high in thresholds:
            if t_high <= t_med:
                continue
            res = evaluate_threshold_pair(t_med, t_high)
            results.append(res)

    results.sort(key=lambda x: x["net_business_impact"], reverse=True)

    # Current baseline: (0.30, 0.60)
    current_res = evaluate_threshold_pair(0.30, 0.60)
    best_res = results[0]

    print("\n" + "=" * 80)
    print("                 THRESHOLD OPTIMIZATION RESULTS (N=300)")
    print("=" * 80)
    print(f"Ground Truth Baseline: {int(baseline_rto_orders)} RTOs ({baseline_rto_rate*100:.1f}%) | Baseline Loss: Rs. {baseline_loss:,.2f}")
    print("-" * 80)

    print("\n1. CURRENT OPERATIONAL THRESHOLDS: (MEDIUM >= 0.30, HIGH >= 0.60)")
    print(f"   Net Business Impact:          Rs. {current_res['net_business_impact']:+,.2f}")
    print(f"   RTO Loss Avoided:             Rs. {current_res['rto_loss_avoided']:,.2f}")
    print(f"   Intervention Costs:           Rs. {current_res['intervention_cost']:,.2f}")
    print(f"   Conversion Friction Loss:     Rs. {current_res['conversion_loss']:,.2f}")
    print(f"   RTO Rate Reduction:           {current_res['rto_rate_reduction_points']:.2f}% points (from {baseline_rto_rate*100:.1f}% -> {current_res['mitigated_rto_rate']*100:.1f}%)")
    print(f"   Intervention Precision/Recall (>=0.30): {current_res['med_precision']*100:.1f}% / {current_res['med_recall']*100:.1f}%")
    print(f"   High-Risk Precision/Recall (>=0.60):    {current_res['high_precision']*100:.1f}% / {current_res['high_recall']*100:.1f}%")
    print(f"   Action Distribution:          {current_res['actions']}")

    print("\n2. OPTIMAL THRESHOLDS: (MEDIUM >= {:.2f}, HIGH >= {:.2f})".format(best_res["t_med"], best_res["t_high"]))
    print(f"   Net Business Impact:          Rs. {best_res['net_business_impact']:+,.2f}")
    print(f"   RTO Loss Avoided:             Rs. {best_res['rto_loss_avoided']:,.2f}")
    print(f"   Intervention Costs:           Rs. {best_res['intervention_cost']:,.2f}")
    print(f"   Conversion Friction Loss:     Rs. {best_res['conversion_loss']:,.2f}")
    print(f"   RTO Rate Reduction:           {best_res['rto_rate_reduction_points']:.2f}% points (from {baseline_rto_rate*100:.1f}% -> {best_res['mitigated_rto_rate']*100:.1f}%)")
    print(f"   Intervention Precision/Recall (>={best_res['t_med']:.2f}): {best_res['med_precision']*100:.1f}% / {best_res['med_recall']*100:.1f}%")
    print(f"   High-Risk Precision/Recall (>={best_res['t_high']:.2f}):    {best_res['high_precision']*100:.1f}% / {best_res['high_recall']*100:.1f}%")
    print(f"   Action Distribution:          {best_res['actions']}")

    print("\n3. TOP 5 CANDIDATE THRESHOLD PAIRS BY NET BUSINESS IMPACT:")
    print(f"   {'Rank':<4} | {'Med':<5} | {'High':<5} | {'Net Impact':<12} | {'Loss Avoided':<13} | {'Conv Loss':<10} | {'RTO Red %':<10} | {'Med Prec':<9} | {'High Prec'}")
    print("   " + "-" * 95)
    for rank, r in enumerate(results[:5], 1):
        print(
            f"   #{rank:<3} | {r['t_med']:<5.2f} | {r['t_high']:<5.2f} | "
            f"Rs. {r['net_business_impact']:<8,.2f} | Rs. {r['rto_loss_avoided']:<9,.2f} | "
            f"Rs. {r['conversion_loss']:<6,.2f} | {r['rto_rate_reduction_points']:<9.2f}% | "
            f"{r['med_precision']*100:<8.1f}% | {r['high_precision']*100:.1f}%"
        )
    print("=" * 80)

    return {
        "current": current_res,
        "optimal": best_res,
        "top_5": results[:5]
    }


if __name__ == "__main__":
    run_threshold_optimization()
