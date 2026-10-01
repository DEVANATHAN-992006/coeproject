import itertools
from typing import List, Tuple, Dict, Optional
from config import PHARMACY_DEPOT, SERVICE_TIME_PER_STOP_MIN, TRAVEL_BUFFER_MIN, AVERAGE_SPEED_KMH
from src.models import Order, Route, RouteStop
from src.distance import urban_distance, calculate_travel_time_min

def exact_permutation_tsp(
    orders: List[Order],
    depot_lat: float,
    depot_lon: float,
    include_return_to_depot: bool = True
) -> Tuple[List[Order], float]:
    """
    Evaluates all n! permutations to determine the exact shortest TSP route sequence.
    
    Properties:
    - Optimal for the supported small batch size (n <= 6).
    - Computationally expensive: factorial growth O(n!) makes it unsuitable for large batches.
    """
    if not orders:
        return [], 0.0

    best_order_sequence = list(orders)
    best_distance = float("inf")

    for perm in itertools.permutations(orders):
        dist = 0.0
        curr_lat, curr_lon = depot_lat, depot_lon
        for order in perm:
            d = urban_distance(curr_lat, curr_lon, order.latitude, order.longitude)
            dist += d
            curr_lat, curr_lon = order.latitude, order.longitude
        if include_return_to_depot:
            dist += urban_distance(curr_lat, curr_lon, depot_lat, depot_lon)

        if dist < best_distance:
            best_distance = dist
            best_order_sequence = list(perm)

    return best_order_sequence, best_distance


def clarke_wright_savings_tsp(
    orders: List[Order],
    depot_lat: float,
    depot_lon: float,
    include_return_to_depot: bool = True
) -> Tuple[List[Order], float]:
    """
    Constructs a scalable approximate route sequence using the Clarke-Wright Savings heuristic
    with 2-opt tour refinement.
    
    Properties:
    - Scalable heuristic practical for larger batches.
    - The Clarke-Wright implementation is deterministic for identical inputs and configuration
      and provides substantially better scalability than factorial-time brute-force permutation search.
    - Does not guarantee global optimality.
    """
    n = len(orders)
    if n == 0:
        return [], 0.0
    if n == 1:
        d = urban_distance(depot_lat, depot_lon, orders[0].latitude, orders[0].longitude)
        if include_return_to_depot:
            d += urban_distance(orders[0].latitude, orders[0].longitude, depot_lat, depot_lon)
        return list(orders), d
    if n == 2:
        # Evaluate both permutations directly for n=2
        d1 = (urban_distance(depot_lat, depot_lon, orders[0].latitude, orders[0].longitude) +
              urban_distance(orders[0].latitude, orders[0].longitude, orders[1].latitude, orders[1].longitude) +
              (urban_distance(orders[1].latitude, orders[1].longitude, depot_lat, depot_lon) if include_return_to_depot else 0.0))
        d2 = (urban_distance(depot_lat, depot_lon, orders[1].latitude, orders[1].longitude) +
              urban_distance(orders[1].latitude, orders[1].longitude, orders[0].latitude, orders[0].longitude) +
              (urban_distance(orders[0].latitude, orders[0].longitude, depot_lat, depot_lon) if include_return_to_depot else 0.0))
        if d1 <= d2:
            return [orders[0], orders[1]], d1
        return [orders[1], orders[0]], d2

    # Step 1: Precompute distance from depot to each order
    d_depot = [
        urban_distance(depot_lat, depot_lon, o.latitude, o.longitude)
        for o in orders
    ]
    d_return = [
        urban_distance(o.latitude, o.longitude, depot_lat, depot_lon)
        for o in orders
    ]

    # Precompute pairwise distances between order locations
    dist_matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            d = urban_distance(orders[i].latitude, orders[i].longitude, orders[j].latitude, orders[j].longitude)
            dist_matrix[i][j] = d
            dist_matrix[j][i] = d

    # Step 2: Compute pairwise savings s(i, j) = d(0, i) + d(0, j) - d(i, j)
    savings = []
    for i in range(n):
        for j in range(i + 1, n):
            s = d_depot[i] + d_depot[j] - dist_matrix[i][j]
            savings.append((s, i, j))

    # Sort savings descending; tie-break deterministically by node indices
    savings.sort(key=lambda item: (-item[0], item[1], item[2]))

    # Step 3: Initialize routes as individual lists [i]
    routes: Dict[int, List[int]] = {i: [i] for i in range(n)}
    node_to_route = {i: i for i in range(n)}

    for s_val, i, j in savings:
        r_i = node_to_route[i]
        r_j = node_to_route[j]

        # Cannot merge if already in the same route
        if r_i == r_j:
            continue

        route_i = routes[r_i]
        route_j = routes[r_j]

        i_is_start = (route_i[0] == i)
        i_is_end = (route_i[-1] == i)
        j_is_start = (route_j[0] == j)
        j_is_end = (route_j[-1] == j)

        if not (i_is_start or i_is_end) or not (j_is_start or j_is_end):
            continue

        # Merge based on connected endpoints
        if i_is_end and j_is_start:
            merged = route_i + route_j
        elif i_is_start and j_is_end:
            merged = route_j + route_i
        elif i_is_end and j_is_end:
            merged = route_i + list(reversed(route_j))
        elif i_is_start and j_is_start:
            merged = list(reversed(route_i)) + route_j
        else:
            continue

        routes[r_i] = merged
        del routes[r_j]
        for node in merged:
            node_to_route[node] = r_i

        if len(routes) == 1:
            break

    # If disconnected sub-routes remain, join them greedily
    remaining_routes = list(routes.values())
    current_tour = remaining_routes[0]
    for other in remaining_routes[1:]:
        cost_normal = dist_matrix[current_tour[-1]][other[0]]
        cost_reversed = dist_matrix[current_tour[-1]][other[-1]]
        if cost_normal <= cost_reversed:
            current_tour = current_tour + other
        else:
            current_tour = current_tour + list(reversed(other))

    best_tour_indices = current_tour

    def calculate_tour_distance(tour_indices: List[int]) -> float:
        if not tour_indices:
            return 0.0
        tot = d_depot[tour_indices[0]]
        for k in range(len(tour_indices) - 1):
            tot += dist_matrix[tour_indices[k]][tour_indices[k + 1]]
        if include_return_to_depot:
            tot += d_return[tour_indices[-1]]
        return tot

    best_dist = calculate_tour_distance(best_tour_indices)

    # 2-opt refinement on the single tour
    improved = True
    iterations = 0
    max_2opt_iterations = 50

    while improved and iterations < max_2opt_iterations:
        improved = False
        iterations += 1
        for i in range(len(best_tour_indices) - 1):
            for j in range(i + 2, len(best_tour_indices)):
                new_tour = best_tour_indices[:i + 1] + list(reversed(best_tour_indices[i + 1:j + 1])) + best_tour_indices[j + 1:]
                new_dist = calculate_tour_distance(new_tour)
                if new_dist < best_dist - 1e-6:
                    best_dist = new_dist
                    best_tour_indices = new_tour
                    improved = True
                    break
            if improved:
                break

    # Evaluate reversed tour orientation
    reversed_tour = list(reversed(best_tour_indices))
    reversed_dist = calculate_tour_distance(reversed_tour)
    if reversed_dist < best_dist:
        best_tour_indices = reversed_tour
        best_dist = reversed_dist

    ordered_orders = [orders[idx] for idx in best_tour_indices]
    return ordered_orders, best_dist


def solve_route_sequence(
    orders: List[Order],
    departure_time_min: float,
    depot_lat: float = PHARMACY_DEPOT["latitude"],
    depot_lon: float = PHARMACY_DEPOT["longitude"],
    depot_name: str = PHARMACY_DEPOT["name"],
    include_return_to_depot: bool = True,
    apply_buffer: bool = True,
    routing_strategy: str = "AUTO"
) -> Route:
    """
    Constructs the delivery route sequence starting from the pharmacy depot.
    
    Routing Strategies supported:
    - AUTO (default): Uses Exact TSP for small batches (n <= 6) and Clarke-Wright Savings for larger batches.
    - EXACT_TSP: Brute-force evaluation of all n! permutations (optimal for n <= 6).
    - SCALABLE_HEURISTIC: Clarke-Wright Savings heuristic with 2-opt refinement.
    
    Calculates exact stop arrival times, service times, and deadline violations.
    """
    if not orders:
        depot_stop = RouteStop(
            stop_id="DEPOT-00",
            location_name=depot_name,
            latitude=depot_lat,
            longitude=depot_lon,
            stop_type="DEPOT",
            estimated_arrival_time=departure_time_min,
            estimated_departure_time=departure_time_min
        )
        return Route(
            stops=[depot_stop],
            total_distance_km=0.0,
            total_travel_time_min=0.0,
            total_service_time_min=0.0,
            total_waiting_time_min=0.0,
            total_duration_min=0.0,
            departure_time_min=departure_time_min,
            is_feasible=True,
            feasibility_reason="Empty Route"
        )

    # Strategy Resolution
    strategy_norm = (routing_strategy or "AUTO").upper().strip()

    if strategy_norm in ["EXACT_TSP", "EXACT"]:
        best_order_sequence, best_distance = exact_permutation_tsp(
            orders=orders,
            depot_lat=depot_lat,
            depot_lon=depot_lon,
            include_return_to_depot=include_return_to_depot
        )
    elif strategy_norm in ["SCALABLE_HEURISTIC", "CLARKE_WRIGHT", "HEURISTIC"]:
        best_order_sequence, best_distance = clarke_wright_savings_tsp(
            orders=orders,
            depot_lat=depot_lat,
            depot_lon=depot_lon,
            include_return_to_depot=include_return_to_depot
        )
    else:  # "AUTO" default
        if len(orders) <= 6:
            best_order_sequence, best_distance = exact_permutation_tsp(
                orders=orders,
                depot_lat=depot_lat,
                depot_lon=depot_lon,
                include_return_to_depot=include_return_to_depot
            )
        else:
            best_order_sequence, best_distance = clarke_wright_savings_tsp(
                orders=orders,
                depot_lat=depot_lat,
                depot_lon=depot_lon,
                include_return_to_depot=include_return_to_depot
            )

    # Build detailed route timeline
    stops = []
    depot_stop = RouteStop(
        stop_id="DEPOT-START",
        location_name=depot_name,
        latitude=depot_lat,
        longitude=depot_lon,
        stop_type="DEPOT",
        estimated_arrival_time=departure_time_min,
        estimated_departure_time=departure_time_min
    )
    stops.append(depot_stop)

    current_time = departure_time_min
    current_lat, current_lon = depot_lat, depot_lon
    total_travel_time = 0.0
    total_service_time = 0.0
    total_waiting_time = 0.0
    is_feasible = True
    violation_reasons = []

    for idx, order in enumerate(best_order_sequence):
        dist_from_prev = urban_distance(current_lat, current_lon, order.latitude, order.longitude)
        travel_time = calculate_travel_time_min(dist_from_prev)
        total_travel_time += travel_time

        arrival_time = current_time + travel_time
        
        # Check deadline compliance
        # Required buffer to account for traffic/delays
        buffer_val = TRAVEL_BUFFER_MIN if apply_buffer else 0.0
        projected_effective_arrival = arrival_time + buffer_val

        is_late = projected_effective_arrival > order.promised_delivery_time
        if is_late:
            is_feasible = False
            lateness = arrival_time - order.promised_delivery_time
            violation_reasons.append(
                f"Order {order.order_id} estimated delivery at t={arrival_time:.1f}m (promised {order.promised_delivery_time}m, buffer {buffer_val}m)"
            )

        service_time = SERVICE_TIME_PER_STOP_MIN
        total_service_time += service_time
        departure_from_stop = arrival_time + service_time

        stop = RouteStop(
            stop_id=f"STOP-{idx+1:02d}",
            location_name=order.customer_location,
            latitude=order.latitude,
            longitude=order.longitude,
            stop_type="CUSTOMER",
            order_id=order.order_id,
            estimated_arrival_time=arrival_time,
            estimated_departure_time=departure_from_stop,
            waiting_time_minutes=0.0,
            promised_delivery_time=order.promised_delivery_time,
            is_late=is_late
        )
        stops.append(stop)

        current_time = departure_from_stop
        current_lat, current_lon = order.latitude, order.longitude

    if include_return_to_depot:
        dist_to_depot = urban_distance(current_lat, current_lon, depot_lat, depot_lon)
        return_travel_time = calculate_travel_time_min(dist_to_depot)
        total_travel_time += return_travel_time
        end_time = current_time + return_travel_time

        return_stop = RouteStop(
            stop_id="DEPOT-END",
            location_name=f"{depot_name} (Return)",
            latitude=depot_lat,
            longitude=depot_lon,
            stop_type="DEPOT",
            estimated_arrival_time=end_time,
            estimated_departure_time=end_time
        )
        stops.append(return_stop)
        total_duration = end_time - departure_time_min
    else:
        total_duration = current_time - departure_time_min

    feasibility_reason = "Valid Route Timeline" if is_feasible else "; ".join(violation_reasons)

    return Route(
        stops=stops,
        total_distance_km=round(best_distance, 2),
        total_travel_time_min=round(total_travel_time, 1),
        total_service_time_min=round(total_service_time, 1),
        total_waiting_time_min=round(total_waiting_time, 1),
        total_duration_min=round(total_duration, 1),
        departure_time_min=departure_time_min,
        is_feasible=is_feasible,
        feasibility_reason=feasibility_reason
    )
