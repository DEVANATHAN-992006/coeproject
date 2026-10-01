import sqlite3
import pytest
import pandas as pd
from config import DB_PATH, RANDOM_SEED
from src.data_generator import generate_products, generate_riders, generate_orders
from src.experiment import (
    run_full_experiment,
    run_baseline_experiment,
    run_mediroute_experiment,
    init_experiment_database
)
from src.audit import get_audit_history


@pytest.fixture
def test_dataset():
    products = generate_products()
    riders = generate_riders(seed=RANDOM_SEED)
    orders = generate_orders(products, seed=RANDOM_SEED)[:50]
    product_map = {p.product_id: p for p in products}
    return orders, riders, product_map


def test_same_dataset_used_by_baseline_and_mediroute(test_dataset):
    """Verify that both Baseline and MEDIROUTE receive identical input objects."""
    orders, riders, product_map = test_dataset
    
    res = run_full_experiment(
        orders=orders,
        riders=riders,
        product_map=product_map,
        experiment_id="TEST-FAIR-001",
        save_to_db=False,
        save_to_csv=False
    )
    
    # Check dataset info recorded
    assert res["dataset_info"]["total_orders"] == len(orders)
    assert res["dataset_info"]["total_riders"] == len(riders)
    assert res["dataset_info"]["total_products"] == len(product_map)
    
    # Check that both baseline and mediroute received 50 orders
    assert res["baseline"]["assigned_orders"] + res["baseline"]["unassigned_orders"] == len(orders)
    assert res["mediroute"]["assigned_orders"] + res["mediroute"]["unassigned_orders"] == len(orders)


def test_distance_saved_calculation(test_dataset):
    """Verify distance_saved equals baseline_distance - optimized_distance."""
    orders, riders, product_map = test_dataset
    
    res = run_full_experiment(
        orders=orders,
        riders=riders,
        product_map=product_map,
        save_to_db=False,
        save_to_csv=False
    )
    
    base_dist = res["baseline"]["total_distance_km"]
    opt_dist = res["mediroute"]["total_distance_km"]
    expected_saved = round(base_dist - opt_dist, 2)
    
    assert res["comparison"]["distance_saved"] == expected_saved


def test_distance_reduction_calculation(test_dataset):
    """Verify distance_reduction_percent equals (distance_saved / baseline_distance) * 100."""
    orders, riders, product_map = test_dataset
    
    res = run_full_experiment(
        orders=orders,
        riders=riders,
        product_map=product_map,
        save_to_db=False,
        save_to_csv=False
    )
    
    base_dist = res["baseline"]["total_distance_km"]
    saved_dist = res["comparison"]["distance_saved"]
    expected_pct = round((saved_dist / base_dist) * 100.0, 2)
    
    assert res["comparison"]["distance_reduction_percent"] == expected_pct


def test_constraint_violation_metrics(test_dataset):
    """Verify that MEDIROUTE strictly maintains 0 constraint violations across all 5 categories."""
    orders, riders, product_map = test_dataset
    
    res = run_full_experiment(
        orders=orders,
        riders=riders,
        product_map=product_map,
        save_to_db=False,
        save_to_csv=False
    )
    
    opt_m = res["mediroute"]
    assert opt_m["sla_violations"] == 0
    assert opt_m["product_violations"] == 0
    assert opt_m["pickup_violations"] == 0
    assert opt_m["capacity_violations"] == 0
    assert opt_m["workload_violations"] == 0
    assert opt_m["total_constraint_violations"] == 0
    assert opt_m["valid_batches"] == opt_m["total_batches"]


def test_experiment_persistence_in_db_and_csv(test_dataset):
    """Verify experiment records are stored in the dedicated SQLite experiment table."""
    orders, riders, product_map = test_dataset
    exp_id = "TEST-PERSIST-999"
    
    init_experiment_database()
    res = run_full_experiment(
        orders=orders,
        riders=riders,
        product_map=product_map,
        experiment_id=exp_id,
        save_to_db=True,
        save_to_csv=True
    )
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT experiment_id, total_orders, baseline_distance_km FROM experiment_results WHERE experiment_id = ?", (exp_id,))
    row = cursor.fetchone()
    conn.close()
    
    assert row is not None
    assert row[0] == exp_id
    assert row[1] == len(orders)
    assert row[2] == res["baseline"]["total_distance_km"]


def test_no_hardcoded_experimental_results(test_dataset):
    """Verify metrics change dynamically when inputs change (no hard-coded static returns)."""
    orders, riders, product_map = test_dataset
    
    # Run with 20 orders
    res_20 = run_full_experiment(orders[:20], riders, product_map, save_to_db=False, save_to_csv=False)
    # Run with 40 orders
    res_40 = run_full_experiment(orders[:40], riders, product_map, save_to_db=False, save_to_csv=False)
    
    # Distances and batches must differ dynamically
    assert res_20["baseline"]["total_distance_km"] != res_40["baseline"]["total_distance_km"]
    assert res_20["mediroute"]["total_batches"] != res_40["mediroute"]["total_batches"]


def test_production_audit_not_polluted_by_benchmark_or_experiment(test_dataset):
    """Verify production audit_log table is NOT modified by experiment executions."""
    orders, riders, product_map = test_dataset
    
    # Check initial production audit count
    df_init = get_audit_history()
    init_count = len(df_init)
    
    # Run experiment
    run_full_experiment(
        orders=orders,
        riders=riders,
        product_map=product_map,
        experiment_id="TEST-AUDIT-ISOLATION",
        save_to_db=True,
        save_to_csv=False
    )
    
    # Production audit count must remain unchanged
    df_after = get_audit_history()
    assert len(df_after) == init_count


def test_experiment_ids_remain_unique(test_dataset):
    """Verify duplicate insertions with same experiment_id are handled idempotently."""
    orders, riders, product_map = test_dataset
    exp_id = "TEST-IDEM-ID-001"
    
    # First write
    run_full_experiment(orders, riders, product_map, experiment_id=exp_id, save_to_db=True, save_to_csv=False)
    # Second write with same experiment_id
    run_full_experiment(orders, riders, product_map, experiment_id=exp_id, save_to_db=True, save_to_csv=False)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM experiment_results WHERE experiment_id = ?", (exp_id,))
    count = cursor.fetchone()[0]
    conn.close()
    
    assert count == 1
