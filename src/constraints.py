from typing import List, Dict, Tuple, Optional
from src.models import Order, Rider, Product, ConstraintResult, Route
from src.routing import solve_route_sequence
from config import TRAVEL_BUFFER_MIN, MAX_WORKLOAD_SAFETY_LIMIT_MIN

def check_product_compatibility(
    orders: List[Order],
    product_map: Optional[Dict[str, Product]] = None
) -> Tuple[bool, str]:
    """
    Evaluates pairwise product handling and compatibility group rules across all orders in candidate batch.
    Returns (product_ok, reason).
    """
    if len(orders) <= 1:
        return True, "Single order batch is intrinsically compatible"

    # Check pairwise compatibility groups
    for i in range(len(orders)):
        for j in range(i + 1, len(orders)):
            o1, o2 = orders[i], orders[j]
            
            # Check explicit compatibility group conflicts
            g1, g2 = o1.compatibility_group, o2.compatibility_group
            h1, h2 = o1.special_handling_required, o2.special_handling_required

            # Rule 1: ColdChain cannot be mixed with Hazmat or Cytotoxic
            if (h1 == "ColdChain" and h2 in ["Hazmat", "Cytotoxic"]) or (h2 == "ColdChain" and h1 in ["Hazmat", "Cytotoxic"]):
                return False, f"Rejected: incompatible product handling ({o1.order_id}:{h1} with {o2.order_id}:{h2})"

            # Rule 2: Narcotics cannot be mixed with Cytotoxic or Hazmat
            if (h1 == "Narcotic" and h2 in ["Cytotoxic", "Hazmat"]) or (h2 == "Narcotic" and h1 in ["Cytotoxic", "Hazmat"]):
                return False, f"Rejected: product safety conflict ({o1.order_id}:{h1} with {o2.order_id}:{h2})"

            # Rule 3: Product metadata explicit incompatible groups
            if product_map:
                p1 = product_map.get(o1.product_id)
                p2 = product_map.get(o2.product_id)
                if p1 and g2 in p1.incompatible_groups:
                    return False, f"Rejected: product {p1.product_name} incompatible with group {g2}"
                if p2 and g1 in p2.incompatible_groups:
                    return False, f"Rejected: product {p2.product_name} incompatible with group {g1}"

    return True, "Product compatibility satisfied"

def check_pickup_readiness(
    orders: List[Order],
    current_time_min: float
) -> Tuple[bool, float, str]:
    """
    Evaluates pickup readiness times for candidate batch orders.
    Calculates required batch departure time = max(current_time, max(pickup_ready_times)).
    Returns (pickup_ready_ok, calculated_departure_time, reason).
    """
    if not orders:
        return True, current_time_min, "No orders"

    max_ready_time = max(o.pickup_ready_time for o in orders)
    departure_time = max(current_time_min, max_ready_time)

    # Check if any order requires excessive waiting that would stall dispatch unreasonably (> 60 mins delay)
    waiting_delay = max_ready_time - current_time_min
    if waiting_delay > 90.0:
        unready_orders = [o.order_id for o in orders if o.pickup_ready_time > current_time_min + 60.0]
        return False, departure_time, f"Rejected: pickup not ready (order(s) {', '.join(unready_orders)} require >90m wait)"

    return True, departure_time, f"Pickup ready at t={departure_time:.1f}m"

def validate_batch_constraints(
    orders: List[Order],
    rider: Rider,
    current_time_min: float = 0.0,
    product_map: Optional[Dict[str, Product]] = None,
    apply_buffer: bool = True
) -> ConstraintResult:
    """
    Comprehensive Constraint Checker evaluating all 5 mandatory operational constraints:
    1. Rider Capacity
    2. Product Compatibility
    3. Pickup Readiness
    4. Delivery Time Deadlines
    5. Rider Workload Safety Limit
    """
    details = {}

    # 1. Check Rider Order Capacity
    capacity_ok = len(orders) <= rider.maximum_orders
    if not capacity_ok:
        reason = f"Rejected: rider capacity exceeded ({len(orders)} orders > max {rider.maximum_orders})"
        return ConstraintResult(
            feasible=False, time_ok=True, product_ok=True, pickup_ready=True,
            capacity_ok=False, workload_ok=True, reason=reason, details=details
        )

    # 2. Check Product Compatibility
    product_ok, prod_reason = check_product_compatibility(orders, product_map)
    if not product_ok:
        return ConstraintResult(
            feasible=False, time_ok=True, product_ok=False, pickup_ready=True,
            capacity_ok=True, workload_ok=True, reason=prod_reason, details=details
        )

    # 3. Check Pickup Readiness & Calculate Departure Time
    pickup_ready, departure_time, ready_reason = check_pickup_readiness(orders, current_time_min)
    if not pickup_ready:
        return ConstraintResult(
            feasible=False, time_ok=True, product_ok=True, pickup_ready=False,
            capacity_ok=True, workload_ok=True, reason=ready_reason, details=details
        )

    # 4. Simulate Route Sequence & Check Delivery Deadlines
    route = solve_route_sequence(
        orders=orders,
        departure_time_min=departure_time,
        depot_lat=rider.current_latitude,
        depot_lon=rider.current_longitude,
        apply_buffer=apply_buffer
    )

    time_ok = route.is_feasible
    if not time_ok:
        reason = f"Rejected: delivery deadline would be violated ({route.feasibility_reason})"
        return ConstraintResult(
            feasible=False, time_ok=False, product_ok=True, pickup_ready=True,
            capacity_ok=True, workload_ok=True, reason=reason, details={"route": route}
        )

    # 5. Check Rider Workload Safety Limit
    max_allowed_workload = min(rider.maximum_workload_minutes, MAX_WORKLOAD_SAFETY_LIMIT_MIN)
    workload_ok = route.total_duration_min <= max_allowed_workload
    if not workload_ok:
        reason = f"Rejected: rider workload exceeds safe limit ({route.total_duration_min:.1f}m > max {max_allowed_workload:.1f}m)"
        return ConstraintResult(
            feasible=False, time_ok=True, product_ok=True, pickup_ready=True,
            capacity_ok=True, workload_ok=False, reason=reason, details={"route": route}
        )

    # All constraints passed cleanly
    return ConstraintResult(
        feasible=True,
        time_ok=True,
        product_ok=True,
        pickup_ready=True,
        capacity_ok=True,
        workload_ok=True,
        reason="Batch fully feasible across all mandatory constraints",
        details={"route": route}
    )
