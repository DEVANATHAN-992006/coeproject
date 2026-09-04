from typing import List, Dict, Tuple
import copy

from src.models import Order, Rider, Product, Batch, Route
from src.distance import urban_distance
from src.routing import solve_route_sequence
from src.constraints import check_product_compatibility

def run_baseline_batching(
    orders: List[Order],
    riders: List[Rider],
    product_map: Dict[str, Product],
    current_time_min: float = 0.0
) -> Tuple[List[Batch], Dict[str, float]]:
    """
    Simulates legacy distance-based batching:
    - Sorts orders by time/location.
    - Groups geographically close orders up to basic capacity.
    - IGNORES deadlines, product incompatibility, pickup readiness delays, and workload safety limits.
    """
    orders_copy = [copy.deepcopy(o) for o in orders]
    riders_copy = [copy.deepcopy(r) for r in riders]

    batches: List[Batch] = []
    unassigned = list(orders_copy)

    # Sort unassigned by order_time
    unassigned.sort(key=lambda o: o.order_time)

    batch_counter = 1
    rider_index = 0

    while unassigned:
        rider = riders_copy[rider_index % len(riders_copy)]
        rider_index += 1

        # Seed batch with earliest order
        seed_order = unassigned.pop(0)
        current_batch_orders = [seed_order]

        # Greedy nearest neighbor clustering up to rider.maximum_orders
        while unassigned and len(current_batch_orders) < rider.maximum_orders:
            last_order = current_batch_orders[-1]
            # Find closest geographically
            closest_order = min(
                unassigned,
                key=lambda o: urban_distance(last_order.latitude, last_order.longitude, o.latitude, o.longitude)
            )
            # Distance threshold for naive grouping (e.g. within 5 km)
            dist = urban_distance(last_order.latitude, last_order.longitude, closest_order.latitude, closest_order.longitude)
            if dist <= 8.0:
                current_batch_orders.append(closest_order)
                unassigned.remove(closest_order)
            else:
                break

        # Dispatch departure time is naively assumed to be current time or max pickup ready time
        dep_time = max(current_time_min, max(o.pickup_ready_time for o in current_batch_orders))

        # Build route without applying safety buffers or constraint rejections
        route = solve_route_sequence(
            orders=current_batch_orders,
            departure_time_min=dep_time,
            depot_lat=rider.current_latitude,
            depot_lon=rider.current_longitude,
            apply_buffer=False
        )

        batch_id = f"BASE-B{batch_counter:03d}"
        batch = Batch(
            batch_id=batch_id,
            rider_id=rider.rider_id,
            orders=current_batch_orders,
            route=route,
            creation_time=current_time_min,
            status="DISPATCHED"
        )
        for o in current_batch_orders:
            o.assigned_rider = rider.rider_id
            o.status = "BATCHED"

        batches.append(batch)
        batch_counter += 1

    # Now post-audit the baseline batches for constraint violations
    metrics = evaluate_baseline_violations(batches, riders_copy, product_map, current_time_min)
    return batches, metrics

def evaluate_baseline_violations(
    batches: List[Batch],
    riders: List[Rider],
    product_map: Dict[str, Product],
    current_time_min: float = 0.0
) -> Dict[str, float]:
    """
    Audits baseline batches to measure real-world failure rate and constraint violations.
    """
    total_distance = sum(b.route.total_distance_km for b in batches if b.route)
    total_orders = sum(len(b.orders) for b in batches)
    num_batches = len(batches)
    avg_batch_size = total_orders / max(1, num_batches)

    late_deliveries = 0
    product_violations = 0
    pickup_violations = 0
    capacity_violations = 0
    workload_violations = 0

    rider_map = {r.rider_id: r for r in riders}

    for b in batches:
        rider = rider_map.get(b.rider_id)
        
        # 1. Capacity check
        if rider and len(b.orders) > rider.maximum_orders:
            capacity_violations += 1

        # 2. Product compatibility check
        prod_ok, _ = check_product_compatibility(b.orders, product_map)
        if not prod_ok:
            product_violations += 1

        # 3. Pickup readiness check (if scheduled departure < max ready time)
        max_ready = max(o.pickup_ready_time for o in b.orders)
        if b.route.departure_time_min < max_ready:
            pickup_violations += 1

        # 4. Workload check
        if rider and b.route.total_duration_min > rider.maximum_workload_minutes:
            workload_violations += 1

        # 5. Delivery deadline check
        for stop in b.route.stops:
            if stop.stop_type == "CUSTOMER" and stop.promised_delivery_time is not None:
                if stop.estimated_arrival_time > stop.promised_delivery_time:
                    late_deliveries += 1

    on_time_rate = ((total_orders - late_deliveries) / max(1, total_orders)) * 100.0

    return {
        "total_distance_km": round(total_distance, 2),
        "total_batches": num_batches,
        "avg_batch_size": round(avg_batch_size, 2),
        "total_orders": total_orders,
        "late_deliveries": late_deliveries,
        "on_time_delivery_rate": round(on_time_rate, 2),
        "product_violations": product_violations,
        "pickup_violations": pickup_violations,
        "capacity_violations": capacity_violations,
        "workload_violations": workload_violations,
    }
