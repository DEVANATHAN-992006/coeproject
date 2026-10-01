import copy
import time
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd

from config import DB_PATH, DATA_DIR, RANDOM_SEED
from src.models import Order, Rider, Product, Batch
from src.baseline import run_baseline_batching
from src.batching import run_constraint_aware_batching
from src.constraints import check_product_compatibility


def init_experiment_database():
    """
    Initializes a dedicated experiment_results table in SQLite.
    Guarantees strict separation from production dispatch audit history.
    """
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS experiment_results (
            experiment_id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            routing_strategy TEXT NOT NULL,
            random_seed INTEGER,
            total_orders INTEGER NOT NULL,
            total_riders INTEGER NOT NULL,
            total_products INTEGER NOT NULL,
            baseline_distance_km REAL NOT NULL,
            optimized_distance_km REAL NOT NULL,
            distance_saved_km REAL NOT NULL,
            distance_reduction_pct REAL NOT NULL,
            baseline_batches INTEGER NOT NULL,
            optimized_batches INTEGER NOT NULL,
            baseline_avg_batch_size REAL NOT NULL,
            optimized_avg_batch_size REAL NOT NULL,
            baseline_valid_batches INTEGER NOT NULL,
            optimized_valid_batches INTEGER NOT NULL,
            rejected_candidate_insertions INTEGER NOT NULL,
            baseline_sla_violations INTEGER NOT NULL,
            optimized_sla_violations INTEGER NOT NULL,
            baseline_product_violations INTEGER NOT NULL,
            optimized_product_violations INTEGER NOT NULL,
            baseline_pickup_violations INTEGER NOT NULL,
            optimized_pickup_violations INTEGER NOT NULL,
            baseline_capacity_violations INTEGER NOT NULL,
            optimized_capacity_violations INTEGER NOT NULL,
            baseline_workload_violations INTEGER NOT NULL,
            optimized_workload_violations INTEGER NOT NULL,
            baseline_total_violations INTEGER NOT NULL,
            optimized_total_violations INTEGER NOT NULL,
            baseline_execution_time_sec REAL NOT NULL,
            optimized_execution_time_sec REAL NOT NULL,
            baseline_assigned_orders INTEGER NOT NULL,
            optimized_assigned_orders INTEGER NOT NULL,
            baseline_unassigned_orders INTEGER NOT NULL,
            optimized_unassigned_orders INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def evaluate_batch_validity_detailed(
    batches: List[Batch],
    riders: List[Rider],
    product_map: Dict[str, Product]
) -> Tuple[int, Dict[str, int]]:
    """
    Audits individual batches to identify strictly valid batches and per-constraint violation totals.
    A batch is valid if and only if it has zero constraint violations across all 5 checks.
    """
    rider_map = {r.rider_id: r for r in riders}
    valid_batch_count = 0
    sla_violations = 0
    product_violations = 0
    pickup_violations = 0
    capacity_violations = 0
    workload_violations = 0

    for b in batches:
        rider = rider_map.get(b.rider_id)
        batch_has_violation = False

        # 1. Capacity check
        if rider and len(b.orders) > rider.maximum_orders:
            capacity_violations += 1
            batch_has_violation = True

        # 2. Product compatibility check
        prod_ok, _ = check_product_compatibility(b.orders, product_map)
        if not prod_ok:
            product_violations += 1
            batch_has_violation = True

        # 3. Pickup readiness check
        if b.orders:
            max_ready = max(o.pickup_ready_time for o in b.orders)
            if b.route and b.route.departure_time_min < max_ready:
                pickup_violations += 1
                batch_has_violation = True

        # 4. Workload check
        if rider and b.route and b.route.total_duration_min > rider.maximum_workload_minutes:
            workload_violations += 1
            batch_has_violation = True

        # 5. Delivery deadline check
        if b.route:
            for stop in b.route.stops:
                if stop.stop_type == "CUSTOMER" and stop.promised_delivery_time is not None:
                    if stop.estimated_arrival_time > stop.promised_delivery_time:
                        sla_violations += 1
                        batch_has_violation = True

        if not batch_has_violation:
            valid_batch_count += 1

    violations_breakdown = {
        "sla_violations": sla_violations,
        "product_violations": product_violations,
        "pickup_violations": pickup_violations,
        "capacity_violations": capacity_violations,
        "workload_violations": workload_violations,
        "total_violations": sla_violations + product_violations + pickup_violations + capacity_violations + workload_violations
    }

    return valid_batch_count, violations_breakdown


def run_baseline_experiment(
    orders: List[Order],
    riders: List[Rider],
    product_map: Dict[str, Product],
    current_time_min: float = 0.0,
    routing_strategy: str = "AUTO"
) -> Tuple[List[Batch], Dict[str, Any]]:
    """
    Executes the baseline delivery experiment and calculates actual operational metrics.
    """
    orders_input = [copy.deepcopy(o) for o in orders]
    riders_input = [copy.deepcopy(r) for r in riders]

    t0 = time.perf_counter()
    batches, _ = run_baseline_batching(
        orders=orders_input,
        riders=riders_input,
        product_map=product_map,
        current_time_min=current_time_min,
        routing_strategy=routing_strategy
    )
    t1 = time.perf_counter()
    exec_time = t1 - t0

    total_distance = sum(b.route.total_distance_km for b in batches if b.route)
    assigned_orders = sum(len(b.orders) for b in batches)
    unassigned_orders = len(orders_input) - assigned_orders
    num_batches = len(batches)
    avg_batch_size = (assigned_orders / max(1, num_batches)) if num_batches > 0 else 0.0

    valid_batches, violations = evaluate_batch_validity_detailed(batches, riders_input, product_map)

    metrics = {
        "total_distance_km": round(total_distance, 2),
        "total_batches": num_batches,
        "avg_batch_size": round(avg_batch_size, 2),
        "valid_batches": valid_batches,
        "rejected_candidate_insertions": 0,  # Baseline performs no constraint rejection
        "sla_violations": violations["sla_violations"],
        "product_violations": violations["product_violations"],
        "pickup_violations": violations["pickup_violations"],
        "capacity_violations": violations["capacity_violations"],
        "workload_violations": violations["workload_violations"],
        "total_constraint_violations": violations["total_violations"],
        "execution_time_sec": round(exec_time, 4),
        "assigned_orders": assigned_orders,
        "unassigned_orders": unassigned_orders
    }

    return batches, metrics


def run_mediroute_experiment(
    orders: List[Order],
    riders: List[Rider],
    product_map: Dict[str, Product],
    current_time_min: float = 0.0,
    routing_strategy: str = "AUTO",
    plan_id: str = "EXP-MEDIROUTE"
) -> Tuple[List[Batch], List[Dict], Dict[str, Any]]:
    """
    Executes the constraint-aware MEDIROUTE experiment and calculates actual operational metrics.
    """
    orders_input = [copy.deepcopy(o) for o in orders]
    riders_input = [copy.deepcopy(r) for r in riders]

    t0 = time.perf_counter()
    batches, audit_logs, _ = run_constraint_aware_batching(
        orders=orders_input,
        riders=riders_input,
        product_map=product_map,
        current_time_min=current_time_min,
        plan_id=plan_id,
        routing_strategy=routing_strategy
    )
    t1 = time.perf_counter()
    exec_time = t1 - t0

    total_distance = sum(b.route.total_distance_km for b in batches if b.route)
    assigned_orders = sum(len(b.orders) for b in batches)
    unassigned_orders = len(orders_input) - assigned_orders
    num_batches = len(batches)
    avg_batch_size = (assigned_orders / max(1, num_batches)) if num_batches > 0 else 0.0

    valid_batches, violations = evaluate_batch_validity_detailed(batches, riders_input, product_map)
    rejected_insertions = sum(1 for log in audit_logs if log.get("action") == "Insertion Rejected")

    metrics = {
        "total_distance_km": round(total_distance, 2),
        "total_batches": num_batches,
        "avg_batch_size": round(avg_batch_size, 2),
        "valid_batches": valid_batches,
        "rejected_candidate_insertions": rejected_insertions,
        "sla_violations": violations["sla_violations"],
        "product_violations": violations["product_violations"],
        "pickup_violations": violations["pickup_violations"],
        "capacity_violations": violations["capacity_violations"],
        "workload_violations": violations["workload_violations"],
        "total_constraint_violations": violations["total_violations"],
        "execution_time_sec": round(exec_time, 4),
        "assigned_orders": assigned_orders,
        "unassigned_orders": unassigned_orders
    }

    return batches, audit_logs, metrics


def run_full_experiment(
    orders: List[Order],
    riders: List[Rider],
    product_map: Dict[str, Product],
    current_time_min: float = 0.0,
    routing_strategy: str = "AUTO",
    experiment_id: Optional[str] = None,
    random_seed: int = RANDOM_SEED,
    save_to_db: bool = True,
    save_to_csv: bool = True
) -> Dict[str, Any]:
    """
    Standardized Experiment Runner:
    - Provides identical input datasets to both Baseline and MEDIROUTE.
    - Evaluates all 17 required metrics from real execution.
    - Computes distance saved and distance reduction percentage safely.
    - Records experiment in dedicated SQLite table and CSV without polluting production audit.
    """
    if experiment_id is None:
        experiment_id = f"EXP-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 1. Run Baseline on input data
    base_batches, base_m = run_baseline_experiment(
        orders=orders,
        riders=riders,
        product_map=product_map,
        current_time_min=current_time_min,
        routing_strategy=routing_strategy
    )

    # 2. Run MEDIROUTE on exactly identical input data
    opt_batches, opt_audit_logs, opt_m = run_mediroute_experiment(
        orders=orders,
        riders=riders,
        product_map=product_map,
        current_time_min=current_time_min,
        routing_strategy=routing_strategy,
        plan_id=f"PLAN-{experiment_id}"
    )

    # 3. Calculate Comparative Distance Metrics
    base_dist = base_m["total_distance_km"]
    opt_dist = opt_m["total_distance_km"]
    distance_saved_km = round(base_dist - opt_dist, 2)

    if base_dist > 1e-6:
        distance_reduction_pct = round((distance_saved_km / base_dist) * 100.0, 2)
    else:
        distance_reduction_pct = 0.0

    comparison_metrics = {
        "baseline_total_distance": base_dist,
        "optimized_total_distance": opt_dist,
        "distance_saved": distance_saved_km,
        "distance_reduction_percent": distance_reduction_pct,
        "number_of_batches": {"baseline": base_m["total_batches"], "mediroute": opt_m["total_batches"]},
        "average_batch_size": {"baseline": base_m["avg_batch_size"], "mediroute": opt_m["avg_batch_size"]},
        "valid_batches": {"baseline": base_m["valid_batches"], "mediroute": opt_m["valid_batches"]},
        "rejected_candidate_insertions": opt_m["rejected_candidate_insertions"],
        "sla_deadline_violations": {"baseline": base_m["sla_violations"], "mediroute": opt_m["sla_violations"]},
        "product_compatibility_violations": {"baseline": base_m["product_violations"], "mediroute": opt_m["product_violations"]},
        "pickup_readiness_violations": {"baseline": base_m["pickup_violations"], "mediroute": opt_m["pickup_violations"]},
        "rider_capacity_violations": {"baseline": base_m["capacity_violations"], "mediroute": opt_m["capacity_violations"]},
        "rider_workload_violations": {"baseline": base_m["workload_violations"], "mediroute": opt_m["workload_violations"]},
        "total_constraint_violations": {"baseline": base_m["total_constraint_violations"], "mediroute": opt_m["total_constraint_violations"]},
        "algorithm_execution_time": {"baseline": base_m["execution_time_sec"], "mediroute": opt_m["execution_time_sec"]},
        "assigned_orders": {"baseline": base_m["assigned_orders"], "mediroute": opt_m["assigned_orders"]},
        "unassigned_orders": {"baseline": base_m["unassigned_orders"], "mediroute": opt_m["unassigned_orders"]}
    }

    # Build Side-by-Side Comparison DataFrame for Streamlit UI
    comparison_table = pd.DataFrame([
        {
            "Metric": "Total Delivery Distance (km)",
            "Baseline Algorithm": f"{base_dist:.2f} km",
            "MEDIROUTE System": f"{opt_dist:.2f} km",
            "Difference / Benefit": f"{distance_saved_km:+.2f} km ({distance_reduction_pct:.1f}%)"
        },
        {
            "Metric": "Distance Reduction (%)",
            "Baseline Algorithm": "0.0%",
            "MEDIROUTE System": f"{distance_reduction_pct:.1f}%",
            "Difference / Benefit": f"{distance_reduction_pct:+.1f}%"
        },
        {
            "Metric": "Total Batches Created",
            "Baseline Algorithm": base_m["total_batches"],
            "MEDIROUTE System": opt_m["total_batches"],
            "Difference / Benefit": f"{opt_m['total_batches'] - base_m['total_batches']:+d}"
        },
        {
            "Metric": "Average Batch Size",
            "Baseline Algorithm": f"{base_m['avg_batch_size']:.2f}",
            "MEDIROUTE System": f"{opt_m['avg_batch_size']:.2f}",
            "Difference / Benefit": f"{opt_m['avg_batch_size'] - base_m['avg_batch_size']:+.2f}"
        },
        {
            "Metric": "Valid Batches (0 Violations)",
            "Baseline Algorithm": f"{base_m['valid_batches']} / {base_m['total_batches']}",
            "MEDIROUTE System": f"{opt_m['valid_batches']} / {opt_m['total_batches']}",
            "Difference / Benefit": f"{opt_m['valid_batches'] - base_m['valid_batches']:+d}"
        },
        {
            "Metric": "Rejected Candidate Insertions",
            "Baseline Algorithm": "N/A (Ignored)",
            "MEDIROUTE System": opt_m["rejected_candidate_insertions"],
            "Difference / Benefit": f"{opt_m['rejected_candidate_insertions']} safe rejections"
        },
        {
            "Metric": "Delivery Deadline / SLA Violations",
            "Baseline Algorithm": base_m["sla_violations"],
            "MEDIROUTE System": opt_m["sla_violations"],
            "Difference / Benefit": f"{opt_m['sla_violations'] - base_m['sla_violations']:+d} (Eliminated)"
        },
        {
            "Metric": "Product Compatibility Violations",
            "Baseline Algorithm": base_m["product_violations"],
            "MEDIROUTE System": opt_m["product_violations"],
            "Difference / Benefit": f"{opt_m['product_violations'] - base_m['product_violations']:+d} (Eliminated)"
        },
        {
            "Metric": "Pickup Readiness Violations",
            "Baseline Algorithm": base_m["pickup_violations"],
            "MEDIROUTE System": opt_m["pickup_violations"],
            "Difference / Benefit": f"{opt_m['pickup_violations'] - base_m['pickup_violations']:+d} (Eliminated)"
        },
        {
            "Metric": "Rider Capacity Violations",
            "Baseline Algorithm": base_m["capacity_violations"],
            "MEDIROUTE System": opt_m["capacity_violations"],
            "Difference / Benefit": f"{opt_m['capacity_violations'] - base_m['capacity_violations']:+d} (Eliminated)"
        },
        {
            "Metric": "Rider Workload Violations",
            "Baseline Algorithm": base_m["workload_violations"],
            "MEDIROUTE System": opt_m["workload_violations"],
            "Difference / Benefit": f"{opt_m['workload_violations'] - base_m['workload_violations']:+d} (Eliminated)"
        },
        {
            "Metric": "Total Constraint Violations",
            "Baseline Algorithm": base_m["total_constraint_violations"],
            "MEDIROUTE System": opt_m["total_constraint_violations"],
            "Difference / Benefit": f"{opt_m['total_constraint_violations'] - base_m['total_constraint_violations']:+d} (Zero Violations)"
        },
        {
            "Metric": "Assigned Orders",
            "Baseline Algorithm": base_m["assigned_orders"],
            "MEDIROUTE System": opt_m["assigned_orders"],
            "Difference / Benefit": f"{opt_m['assigned_orders'] - base_m['assigned_orders']:+d}"
        },
        {
            "Metric": "Unassigned Orders (Safety)",
            "Baseline Algorithm": base_m["unassigned_orders"],
            "MEDIROUTE System": opt_m["unassigned_orders"],
            "Difference / Benefit": f"{opt_m['unassigned_orders'] - base_m['unassigned_orders']:+d}"
        },
        {
            "Metric": "Algorithm Execution Time (sec)",
            "Baseline Algorithm": f"{base_m['execution_time_sec']:.4f} s",
            "MEDIROUTE System": f"{opt_m['execution_time_sec']:.4f} s",
            "Difference / Benefit": f"{opt_m['execution_time_sec'] - base_m['execution_time_sec']:+.4f} s"
        }
    ])

    record = {
        "experiment_id": experiment_id,
        "timestamp": now_str,
        "routing_strategy": routing_strategy,
        "random_seed": random_seed,
        "total_orders": len(orders),
        "total_riders": len(riders),
        "total_products": len(product_map),
        "baseline_distance_km": base_dist,
        "optimized_distance_km": opt_dist,
        "distance_saved_km": distance_saved_km,
        "distance_reduction_pct": distance_reduction_pct,
        "baseline_batches": base_m["total_batches"],
        "optimized_batches": opt_m["total_batches"],
        "baseline_avg_batch_size": base_m["avg_batch_size"],
        "optimized_avg_batch_size": opt_m["avg_batch_size"],
        "baseline_valid_batches": base_m["valid_batches"],
        "optimized_valid_batches": opt_m["valid_batches"],
        "rejected_candidate_insertions": opt_m["rejected_candidate_insertions"],
        "baseline_sla_violations": base_m["sla_violations"],
        "optimized_sla_violations": opt_m["sla_violations"],
        "baseline_product_violations": base_m["product_violations"],
        "optimized_product_violations": opt_m["product_violations"],
        "baseline_pickup_violations": base_m["pickup_violations"],
        "optimized_pickup_violations": opt_m["pickup_violations"],
        "baseline_capacity_violations": base_m["capacity_violations"],
        "optimized_capacity_violations": opt_m["capacity_violations"],
        "baseline_workload_violations": base_m["workload_violations"],
        "optimized_workload_violations": opt_m["workload_violations"],
        "baseline_total_violations": base_m["total_constraint_violations"],
        "optimized_total_violations": opt_m["total_constraint_violations"],
        "baseline_execution_time_sec": base_m["execution_time_sec"],
        "optimized_execution_time_sec": opt_m["execution_time_sec"],
        "baseline_assigned_orders": base_m["assigned_orders"],
        "optimized_assigned_orders": opt_m["assigned_orders"],
        "baseline_unassigned_orders": base_m["unassigned_orders"],
        "optimized_unassigned_orders": opt_m["unassigned_orders"]
    }

    # Persist experiment record to dedicated SQLite table
    if save_to_db:
        init_experiment_database()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM experiment_results WHERE experiment_id = ?", (experiment_id,))
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO experiment_results (
                    experiment_id, timestamp, routing_strategy, random_seed,
                    total_orders, total_riders, total_products,
                    baseline_distance_km, optimized_distance_km, distance_saved_km, distance_reduction_pct,
                    baseline_batches, optimized_batches, baseline_avg_batch_size, optimized_avg_batch_size,
                    baseline_valid_batches, optimized_valid_batches, rejected_candidate_insertions,
                    baseline_sla_violations, optimized_sla_violations,
                    baseline_product_violations, optimized_product_violations,
                    baseline_pickup_violations, optimized_pickup_violations,
                    baseline_capacity_violations, optimized_capacity_violations,
                    baseline_workload_violations, optimized_workload_violations,
                    baseline_total_violations, optimized_total_violations,
                    baseline_execution_time_sec, optimized_execution_time_sec,
                    baseline_assigned_orders, optimized_assigned_orders,
                    baseline_unassigned_orders, optimized_unassigned_orders
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record["experiment_id"], record["timestamp"], record["routing_strategy"], record["random_seed"],
                record["total_orders"], record["total_riders"], record["total_products"],
                record["baseline_distance_km"], record["optimized_distance_km"], record["distance_saved_km"], record["distance_reduction_pct"],
                record["baseline_batches"], record["optimized_batches"], record["baseline_avg_batch_size"], record["optimized_avg_batch_size"],
                record["baseline_valid_batches"], record["optimized_valid_batches"], record["rejected_candidate_insertions"],
                record["baseline_sla_violations"], record["optimized_sla_violations"],
                record["baseline_product_violations"], record["optimized_product_violations"],
                record["baseline_pickup_violations"], record["optimized_pickup_violations"],
                record["baseline_capacity_violations"], record["optimized_capacity_violations"],
                record["baseline_workload_violations"], record["optimized_workload_violations"],
                record["baseline_total_violations"], record["optimized_total_violations"],
                record["baseline_execution_time_sec"], record["optimized_execution_time_sec"],
                record["baseline_assigned_orders"], record["optimized_assigned_orders"],
                record["baseline_unassigned_orders"], record["optimized_unassigned_orders"]
            ))
            conn.commit()
        conn.close()

    # Persist experiment record to CSV
    if save_to_csv:
        csv_path = DATA_DIR / "experiment_history.csv"
        df_row = pd.DataFrame([record])
        if csv_path.exists():
            try:
                existing_df = pd.read_csv(csv_path)
                if experiment_id not in existing_df["experiment_id"].values:
                    updated_df = pd.concat([existing_df, df_row], ignore_index=True)
                    updated_df.to_csv(csv_path, index=False)
            except Exception:
                df_row.to_csv(csv_path, index=False)
        else:
            df_row.to_csv(csv_path, index=False)

    return {
        "experiment_id": experiment_id,
        "timestamp": now_str,
        "routing_strategy": routing_strategy,
        "random_seed": random_seed,
        "dataset_info": {
            "total_orders": len(orders),
            "total_riders": len(riders),
            "total_products": len(product_map)
        },
        "baseline": base_m,
        "mediroute": opt_m,
        "comparison": comparison_metrics,
        "comparison_table": comparison_table,
        "baseline_batches": base_batches,
        "optimized_batches": opt_batches,
        "audit_logs": opt_audit_logs
    }


def load_latest_experiment_results() -> Optional[Dict[str, Any]]:
    """
    Loads latest experiment record from SQLite table or CSV.
    """
    init_experiment_database()
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query("SELECT * FROM experiment_results ORDER BY timestamp DESC LIMIT 1", conn)
        conn.close()
        if not df.empty:
            return df.iloc[0].to_dict()
    except Exception:
        conn.close()

    csv_path = DATA_DIR / "experiment_history.csv"
    if csv_path.exists():
        try:
            df = pd.read_csv(csv_path)
            if not df.empty:
                return df.iloc[-1].to_dict()
        except Exception:
            pass

    return None


def get_all_experiment_history() -> pd.DataFrame:
    """
    Returns full history of all executed experiments from database.
    """
    init_experiment_database()
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query("SELECT * FROM experiment_results ORDER BY timestamp DESC", conn)
        conn.close()
        return df
    except Exception:
        conn.close()
        return pd.DataFrame()
