import pytest
from src.models import Order, Rider, Product
from src.constraints import validate_batch_constraints
from config import PHARMACY_DEPOT

@pytest.fixture
def product_map():
    return {
        "P-COLD": Product("P-COLD", "Insulin", True, "ColdChain", "COLD_CHAIN", ["HAZMAT", "CYTOTOXIC"]),
        "P-GEN": Product("P-GEN", "Aspirin", False, "General", "GENERAL", []),
        "P-HAZ": Product("P-HAZ", "Alcohol", False, "Hazmat", "HAZMAT", ["COLD_CHAIN", "NARCOTIC"])
    }

@pytest.fixture
def standard_rider():
    return Rider(
        rider_id="R-01",
        name="Standard Rider",
        maximum_orders=4,
        maximum_workload_minutes=90.0,
        current_latitude=PHARMACY_DEPOT["latitude"],
        current_longitude=PHARMACY_DEPOT["longitude"],
        shift_start=0,
        shift_end=480
    )

def test_failure_case_1_tight_deadline(standard_rider, product_map):
    """
    Case 1 — Tight deadline: Two nearby orders cannot be batched because one would become late.
    O2 is closer to depot, so TSP visits O2 first. But visiting O2 adds departure delay, pushing O1 (deadline 20m) past its limit.
    """
    # Order 1: Urgent (promised delivery in 20 mins), located further away (+0.03)
    o1 = Order("O-101", "P-GEN", "Aspirin", "Location A (Urgent)", PHARMACY_DEPOT["latitude"] + 0.03, PHARMACY_DEPOT["longitude"] + 0.03, 0, 0, 20, 1, "HIGH", "General", "GENERAL")
    # Order 2: Closer (+0.01), deadline 90 mins
    o2 = Order("O-102", "P-GEN", "Aspirin", "Location B", PHARMACY_DEPOT["latitude"] + 0.01, PHARMACY_DEPOT["longitude"] + 0.01, 0, 0, 90, 1, "MEDIUM", "General", "GENERAL")

    res = validate_batch_constraints([o1, o2], standard_rider, product_map=product_map)
    assert res.feasible is False
    assert res.time_ok is False
    assert "delivery deadline would be violated" in res.reason.lower()


def test_failure_case_2_incompatible_products(standard_rider, product_map):
    """
    Case 2 — Incompatible products: ColdChain medication cannot be batched with Volatile Hazmat.
    """
    o1 = Order("O-201", "P-COLD", "Insulin", "Location A", PHARMACY_DEPOT["latitude"] + 0.01, PHARMACY_DEPOT["longitude"] + 0.01, 0, 0, 120, 1, "HIGH", "ColdChain", "COLD_CHAIN")
    o2 = Order("O-202", "P-HAZ", "Alcohol", "Location B", PHARMACY_DEPOT["latitude"] + 0.012, PHARMACY_DEPOT["longitude"] + 0.012, 0, 0, 120, 1, "MEDIUM", "Hazmat", "HAZMAT")

    res = validate_batch_constraints([o1, o2], standard_rider, product_map=product_map)
    assert res.feasible is False
    assert res.product_ok is False
    assert "incompatible product" in res.reason.lower()

def test_failure_case_3_pickup_not_ready(standard_rider, product_map):
    """
    Case 3 — Pickup not ready: Order preparation requires 100 minutes wait, exceeding maximum dispatch delay.
    """
    o1 = Order("O-301", "P-GEN", "Aspirin", "Location A", PHARMACY_DEPOT["latitude"] + 0.01, PHARMACY_DEPOT["longitude"] + 0.01, 0, 120, 180, 1, "MEDIUM", "General", "GENERAL")

    res = validate_batch_constraints([o1], standard_rider, current_time_min=0.0, product_map=product_map)
    assert res.feasible is False
    assert res.pickup_ready is False
    assert "pickup not ready" in res.reason.lower()

def test_failure_case_4_rider_capacity(product_map):
    """
    Case 4 — Rider capacity: Batch exceeds rider's maximum order capacity limit (e.g. 3 max orders, trying 4).
    """
    small_capacity_rider = Rider("R-CAP", "Cap Rider", 3, 120.0, PHARMACY_DEPOT["latitude"], PHARMACY_DEPOT["longitude"], 0, 480)
    orders = [
        Order(f"O-40{i}", "P-GEN", "Aspirin", f"Location {i}", PHARMACY_DEPOT["latitude"] + 0.005*i, PHARMACY_DEPOT["longitude"], 0, 0, 120, 1, "LOW", "General", "GENERAL")
        for i in range(1, 5)
    ]

    res = validate_batch_constraints(orders, small_capacity_rider, product_map=product_map)
    assert res.feasible is False
    assert res.capacity_ok is False
    assert "rider capacity exceeded" in res.reason.lower()

def test_failure_case_5_rider_workload(product_map):
    """
    Case 5 — Rider workload: Route duration exceeds maximum safe workload minutes.
    """
    short_workload_rider = Rider("R-WORK", "Workload Rider", 5, 45.0, PHARMACY_DEPOT["latitude"], PHARMACY_DEPOT["longitude"], 0, 480)
    
    # 3 orders located far apart causing total route duration > 45 minutes
    orders = [
        Order("O-501", "P-GEN", "Aspirin", "Loc 1", PHARMACY_DEPOT["latitude"] + 0.05, PHARMACY_DEPOT["longitude"] + 0.05, 0, 0, 300, 1, "LOW", "General", "GENERAL"),
        Order("O-502", "P-GEN", "Aspirin", "Loc 2", PHARMACY_DEPOT["latitude"] - 0.05, PHARMACY_DEPOT["longitude"] - 0.05, 0, 0, 300, 1, "LOW", "General", "GENERAL"),
    ]

    res = validate_batch_constraints(orders, short_workload_rider, product_map=product_map)
    assert res.feasible is False
    assert res.workload_ok is False
    assert "workload exceeds safe limit" in res.reason.lower()
