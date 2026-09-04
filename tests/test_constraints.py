import pytest
from src.models import Order, Rider, Product
from src.constraints import validate_batch_constraints, check_product_compatibility, check_pickup_readiness
from config import PHARMACY_DEPOT

@pytest.fixture
def sample_rider():
    return Rider(
        rider_id="R-TEST",
        name="Test Rider",
        maximum_orders=4,
        maximum_workload_minutes=90.0,
        current_latitude=PHARMACY_DEPOT["latitude"],
        current_longitude=PHARMACY_DEPOT["longitude"],
        shift_start=0,
        shift_end=480
    )

@pytest.fixture
def product_map():
    return {
        "P-COLD": Product("P-COLD", "Insulin", True, "ColdChain", "COLD_CHAIN", ["HAZMAT", "CYTOTOXIC"]),
        "P-GEN": Product("P-GEN", "Aspirin", False, "General", "GENERAL", []),
        "P-HAZ": Product("P-HAZ", "Alcohol", False, "Hazmat", "HAZMAT", ["COLD_CHAIN", "NARCOTIC"]),
        "P-CYTO": Product("P-CYTO", "Tamoxifen", False, "Cytotoxic", "CYTOTOXIC", ["COLD_CHAIN", "NARCOTIC"])
    }

def test_rider_capacity_constraint(sample_rider, product_map):
    # Create 5 orders for a rider capped at 4
    orders = [
        Order(f"O-{i}", "P-GEN", "Aspirin", f"Loc {i}", PHARMACY_DEPOT["latitude"] + 0.01*i, PHARMACY_DEPOT["longitude"], 0, 10, 120, 1, "MEDIUM", "General", "GENERAL")
        for i in range(5)
    ]
    res = validate_batch_constraints(orders, sample_rider, product_map=product_map)
    assert res.feasible is False
    assert res.capacity_ok is False
    assert "rider capacity exceeded" in res.reason.lower()

def test_product_compatibility_constraint(sample_rider, product_map):
    # Combine ColdChain and Hazmat
    o1 = Order("O-1", "P-COLD", "Insulin", "Loc 1", PHARMACY_DEPOT["latitude"] + 0.01, PHARMACY_DEPOT["longitude"], 0, 10, 120, 1, "HIGH", "ColdChain", "COLD_CHAIN")
    o2 = Order("O-2", "P-HAZ", "Alcohol", "Loc 2", PHARMACY_DEPOT["latitude"] + 0.02, PHARMACY_DEPOT["longitude"], 0, 10, 120, 1, "MEDIUM", "Hazmat", "HAZMAT")

    res = validate_batch_constraints([o1, o2], sample_rider, product_map=product_map)
    assert res.feasible is False
    assert res.product_ok is False
    assert "incompatible product" in res.reason.lower()

def test_pickup_readiness_constraint(sample_rider, product_map):
    # Order ready at t=120m, current time is 0m
    o1 = Order("O-1", "P-GEN", "Aspirin", "Loc 1", PHARMACY_DEPOT["latitude"] + 0.01, PHARMACY_DEPOT["longitude"], 0, 120, 150, 1, "MEDIUM", "General", "GENERAL")
    
    ok, departure_time, reason = check_pickup_readiness([o1], current_time_min=0.0)
    assert ok is False
    assert "pickup not ready" in reason.lower()

def test_delivery_time_deadline_constraint(sample_rider, product_map):
    # Far away order with impossible deadline (promised delivery in 5 minutes, but travel takes 20 mins)
    o1 = Order("O-1", "P-GEN", "Aspirin", "Far Loc", PHARMACY_DEPOT["latitude"] + 0.15, PHARMACY_DEPOT["longitude"] + 0.15, 0, 0, 5, 1, "HIGH", "General", "GENERAL")

    res = validate_batch_constraints([o1], sample_rider, current_time_min=0.0, product_map=product_map)
    assert res.feasible is False
    assert res.time_ok is False
    assert "delivery deadline would be violated" in res.reason.lower()

def test_rider_workload_constraint(sample_rider, product_map):
    # Rider maximum workload is 90 mins. Create multi-stop route exceeding 90 mins.
    rider_small_workload = Rider("R-SMALL", "Small Rider", 10, 30.0, PHARMACY_DEPOT["latitude"], PHARMACY_DEPOT["longitude"], 0, 480)

    # 3 orders spread out causing 45 minutes travel/service
    orders = [
        Order(f"O-{i}", "P-GEN", "Aspirin", f"Loc {i}", PHARMACY_DEPOT["latitude"] + 0.05*i, PHARMACY_DEPOT["longitude"] + 0.05*i, 0, 0, 300, 1, "LOW", "General", "GENERAL")
        for i in range(1, 4)
    ]

    res = validate_batch_constraints(orders, rider_small_workload, product_map=product_map)
    assert res.feasible is False
    assert res.workload_ok is False
    assert "workload exceeds safe limit" in res.reason.lower()
