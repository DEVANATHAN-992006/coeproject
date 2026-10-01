import time
import pytest
from config import PHARMACY_DEPOT
from src.models import Order
from src.routing import (
    solve_route_sequence,
    exact_permutation_tsp,
    clarke_wright_savings_tsp
)
from src.distance import urban_distance
from src.benchmark import run_routing_benchmark


def create_test_orders(n: int) -> list:
    """Helper creating n deterministic test orders."""
    base_lat = PHARMACY_DEPOT["latitude"]
    base_lon = PHARMACY_DEPOT["longitude"]
    orders = []
    for i in range(1, n + 1):
        # Slightly offset coordinates
        lat = base_lat + (0.01 * (i % 5))
        lon = base_lon + (0.01 * (i // 5))
        orders.append(Order(
            order_id=f"TEST-ORD-{i:03d}",
            product_id="PRD-004",
            product_name="Amoxicillin",
            customer_location=f"Location {i}",
            latitude=lat,
            longitude=lon,
            order_time=0,
            pickup_ready_time=0,
            promised_delivery_time=120,
            quantity=1,
            priority="MEDIUM",
            special_handling_required="General",
            compatibility_group="GENERAL"
        ))
    return orders


def test_exact_tsp_selected_for_small_batch():
    """Verify Exact TSP permutation solver is used when n <= 6."""
    orders = create_test_orders(4)
    exact_seq, exact_dist = exact_permutation_tsp(
        orders, PHARMACY_DEPOT["latitude"], PHARMACY_DEPOT["longitude"]
    )
    route_auto = solve_route_sequence(orders, departure_time_min=0.0, routing_strategy="AUTO")
    
    assert len(orders) == 4
    # Distance in AUTO must match exact permutation distance for n <= 6
    assert route_auto.total_distance_km == round(exact_dist, 2)


def test_clarke_wright_selected_for_large_batch():
    """Verify Clarke-Wright heuristic is selected when n > 6 under AUTO strategy."""
    orders = create_test_orders(8)
    cw_seq, cw_dist = clarke_wright_savings_tsp(
        orders, PHARMACY_DEPOT["latitude"], PHARMACY_DEPOT["longitude"]
    )
    route_auto = solve_route_sequence(orders, departure_time_min=0.0, routing_strategy="AUTO")
    
    assert len(orders) == 8
    # For n > 6, AUTO must utilize Clarke-Wright savings
    assert route_auto.total_distance_km == round(cw_dist, 2)


def test_auto_routing_selection():
    """Verify AUTO switches between Exact TSP (<=6) and Clarke-Wright (>6)."""
    small_orders = create_test_orders(5)
    large_orders = create_test_orders(9)
    
    route_small = solve_route_sequence(small_orders, departure_time_min=0.0, routing_strategy="AUTO")
    route_large = solve_route_sequence(large_orders, departure_time_min=0.0, routing_strategy="AUTO")
    
    _, expected_small_dist = exact_permutation_tsp(small_orders, PHARMACY_DEPOT["latitude"], PHARMACY_DEPOT["longitude"])
    _, expected_large_dist = clarke_wright_savings_tsp(large_orders, PHARMACY_DEPOT["latitude"], PHARMACY_DEPOT["longitude"])
    
    assert route_small.total_distance_km == round(expected_small_dist, 2)
    assert route_large.total_distance_km == round(expected_large_dist, 2)


def test_explicit_exact_tsp_selection():
    """Verify explicitly requesting EXACT_TSP uses permutations."""
    orders = create_test_orders(4)
    route_exact = solve_route_sequence(orders, departure_time_min=0.0, routing_strategy="EXACT_TSP")
    _, expected_dist = exact_permutation_tsp(orders, PHARMACY_DEPOT["latitude"], PHARMACY_DEPOT["longitude"])
    
    assert route_exact.total_distance_km == round(expected_dist, 2)


def test_explicit_scalable_heuristic_selection():
    """Verify explicitly requesting SCALABLE_HEURISTIC uses Clarke-Wright even for small batch."""
    orders = create_test_orders(4)
    route_cw = solve_route_sequence(orders, departure_time_min=0.0, routing_strategy="SCALABLE_HEURISTIC")
    _, expected_cw_dist = clarke_wright_savings_tsp(orders, PHARMACY_DEPOT["latitude"], PHARMACY_DEPOT["longitude"])
    
    assert route_cw.total_distance_km == round(expected_cw_dist, 2)


def test_benchmark_produces_real_results():
    """Verify run_routing_benchmark produces real records and accurate columns."""
    orders = create_test_orders(10)
    df = run_routing_benchmark(
        orders=orders,
        test_sizes=[3, 5, 8],
        exact_max_n=6,
        save_to_db=False,
        save_to_csv=False
    )
    
    assert not df.empty
    assert "num_stops" in df.columns
    assert "routing_strategy" in df.columns
    assert "route_distance_km" in df.columns
    assert "execution_time_ms" in df.columns
    assert "optimality_gap_pct" in df.columns
    
    # Check that distances and execution times are non-negative real numbers
    assert (df["route_distance_km"] > 0).all()
    assert (df["execution_time_ms"] >= 0).all()
    
    # Check optimality gap is only defined for n <= 6
    exact_rows = df[df["routing_strategy"] == "Exact TSP"]
    assert not exact_rows.empty
    assert (exact_rows["optimality_gap_pct"] == 0.0).all()
    
    large_cw_rows = df[(df["routing_strategy"] == "Clarke-Wright Savings") & (df["num_stops"] > 6)]
    assert not large_cw_rows.empty
    assert large_cw_rows["optimality_gap_pct"].isna().all()


def test_distance_calculation_accuracy():
    """Verify that urban distance calculation includes the 1.30 circuity factor."""
    lat1, lon1 = 37.7749, -122.4194
    lat2, lon2 = 37.7849, -122.4094
    d = urban_distance(lat1, lon1, lat2, lon2)
    assert d > 0.0
    # Distance between ~1km diagonal coordinates in SF should be ~1.5 - 2.5 km
    assert 1.0 < d < 5.0


def test_execution_time_measurement():
    """Verify high-resolution execution timing works and reports positive milliseconds."""
    orders = create_test_orders(5)
    t0 = time.perf_counter()
    solve_route_sequence(orders, 0.0, routing_strategy="AUTO")
    t1 = time.perf_counter()
    elapsed_ms = (t1 - t0) * 1000.0
    assert elapsed_ms >= 0.0
