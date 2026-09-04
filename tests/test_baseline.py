import pytest
from src.data_generator import generate_products, generate_riders, generate_orders
from src.baseline import run_baseline_batching

def test_baseline_batching_execution():
    products = generate_products()
    riders = generate_riders(seed=42)
    orders = generate_orders(products, seed=42)[:50]
    prod_map = {p.product_id: p for p in products}

    batches, metrics = run_baseline_batching(
        orders=orders,
        riders=riders,
        product_map=prod_map,
        current_time_min=0.0
    )

    assert len(batches) > 0
    assert "total_distance_km" in metrics
    assert "late_deliveries" in metrics
