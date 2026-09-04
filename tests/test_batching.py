import pytest
from src.data_generator import generate_products, generate_riders, generate_orders
from src.batching import run_constraint_aware_batching
from src.audit import write_audit_logs, get_audit_history

def test_constraint_aware_batching_execution():
    products = generate_products()
    riders = generate_riders(seed=42)
    orders = generate_orders(products, seed=42)[:50]  # Test subset of 50 orders for speed
    prod_map = {p.product_id: p for p in products}

    batches, audit_logs, metrics = run_constraint_aware_batching(
        orders=orders,
        riders=riders,
        product_map=prod_map,
        current_time_min=0.0
    )

    assert len(batches) > 0
    assert metrics["late_deliveries"] == 0
    assert metrics["product_violations"] == 0
    assert metrics["pickup_violations"] == 0
    assert metrics["capacity_violations"] == 0
    assert metrics["workload_violations"] == 0
    assert metrics["on_time_delivery_rate"] == 100.0
    assert len(audit_logs) > 0

def test_audit_log_idempotency_deduplication():
    records = [
        {"action": "PLAN CREATED", "order_id": "O-TEST", "rider_id": "R-TEST", "old_state": "NONE", "new_state": "CREATED", "reason": "Test record"}
    ]
    exec_id = "EXEC-IDEMPOTENCY-TEST"

    # Write first time
    write_audit_logs(records, plan_id="PLAN-IDEM-1", execution_id=exec_id)
    df1 = get_audit_history(execution_id=exec_id)
    initial_count = len(df1)
    assert initial_count == 1

    # Attempt second write with identical execution_id
    write_audit_logs(records, plan_id="PLAN-IDEM-1", execution_id=exec_id)
    df2 = get_audit_history(execution_id=exec_id)
    assert len(df2) == initial_count  # Count must remain 1 (no duplicates inserted)

def test_data_integrity_and_assignment_uniqueness():
    products = generate_products()
    riders = generate_riders(seed=42)
    orders = generate_orders(products, seed=42)[:30]
    prod_map = {p.product_id: p for p in products}

    batches, _, _ = run_constraint_aware_batching(orders, riders, prod_map, 0.0)

    assigned_orders = []
    for b in batches:
        for o in b.orders:
            assigned_orders.append(o.order_id)

    # 1. No order should be assigned to multiple batches
    assert len(assigned_orders) == len(set(assigned_orders))

    # 2. Every valid batch must have a feasible route
    for b in batches:
        assert b.route is not None
        assert b.route.is_feasible is True
