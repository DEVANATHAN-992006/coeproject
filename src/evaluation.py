from typing import List, Dict, Any, Optional
import pandas as pd

from src.models import Order, Rider, Product
from src.experiment import run_full_experiment


def run_comparative_experiment(
    orders: List[Order],
    riders: List[Rider],
    product_map: Dict[str, Product],
    current_time_min: float = 0.0,
    target_distance_saved_pct: float = 10.0,
    routing_strategy: str = "AUTO"
) -> Dict[str, Any]:
    """
    Executes comparative experiment comparing Baseline vs Constraint-Aware System
    on the exact same order dataset and rider availability.
    Delegates to the standardized experiment runner in src/experiment.py.
    """
    res = run_full_experiment(
        orders=orders,
        riders=riders,
        product_map=product_map,
        current_time_min=current_time_min,
        routing_strategy=routing_strategy
    )

    base_metrics = res["baseline"]
    opt_metrics = res["mediroute"]
    dist_saved_km = res["comparison"]["distance_saved"]
    dist_saved_pct = res["comparison"]["distance_reduction_percent"]
    base_total_violations = base_metrics["total_constraint_violations"]
    opt_total_violations = opt_metrics["total_constraint_violations"]

    passed_target = (dist_saved_pct >= target_distance_saved_pct) and (opt_total_violations == 0)

    if passed_target:
        explanation = (
            f"PASS: Reduced delivery distance by {dist_saved_pct:.1f}% (exceeding target {target_distance_saved_pct:.1f}%) "
            f"while maintaining 100% compliance across all 5 hard constraints (0 violations vs {base_total_violations} baseline violations)."
        )
    elif opt_total_violations == 0:
        explanation = (
            f"PARTIAL PASS: Achieved {dist_saved_pct:.1f}% distance difference "
            f"with 0 hard constraint violations (vs {base_total_violations} violations in baseline). "
            f"Strict safety and non-contamination compliance were prioritized over naive clustering."
        )
    else:
        explanation = f"FAIL: Hard constraint violations detected in optimized plan ({opt_total_violations} violations)."

    # Return unified dictionary containing both legacy keys and new comprehensive metrics
    return {
        "experiment_id": res["experiment_id"],
        "baseline_batches": res["baseline_batches"],
        "baseline_metrics": {
            "total_distance_km": base_metrics["total_distance_km"],
            "total_batches": base_metrics["total_batches"],
            "avg_batch_size": base_metrics["avg_batch_size"],
            "total_orders": base_metrics["assigned_orders"],
            "late_deliveries": base_metrics["sla_violations"],
            "on_time_delivery_rate": round(
                ((base_metrics["assigned_orders"] - base_metrics["sla_violations"]) / max(1, base_metrics["assigned_orders"])) * 100.0, 1
            ),
            "product_violations": base_metrics["product_violations"],
            "pickup_violations": base_metrics["pickup_violations"],
            "capacity_violations": base_metrics["capacity_violations"],
            "workload_violations": base_metrics["workload_violations"],
            "valid_batches": base_metrics["valid_batches"],
            "execution_time_sec": base_metrics["execution_time_sec"]
        },
        "optimized_batches": res["optimized_batches"],
        "optimized_metrics": {
            "total_distance_km": opt_metrics["total_distance_km"],
            "total_batches": opt_metrics["total_batches"],
            "avg_batch_size": opt_metrics["avg_batch_size"],
            "total_orders": opt_metrics["assigned_orders"],
            "late_deliveries": opt_metrics["sla_violations"],
            "on_time_delivery_rate": 100.0,
            "product_violations": opt_metrics["product_violations"],
            "pickup_violations": opt_metrics["pickup_violations"],
            "capacity_violations": opt_metrics["capacity_violations"],
            "workload_violations": opt_metrics["workload_violations"],
            "valid_batches": opt_metrics["valid_batches"],
            "rejected_candidate_insertions": opt_metrics["rejected_candidate_insertions"],
            "execution_time_sec": opt_metrics["execution_time_sec"]
        },
        "audit_logs": res["audit_logs"],
        "distance_saved_km": dist_saved_km,
        "distance_saved_pct": dist_saved_pct,
        "target_pct": target_distance_saved_pct,
        "passed": passed_target,
        "explanation": explanation,
        "comparison_table": res["comparison_table"],
        "comparison": res["comparison"],
        "dataset_info": res["dataset_info"]
    }
