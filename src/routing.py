import itertools
from typing import List, Tuple, Dict, Optional
from config import PHARMACY_DEPOT, SERVICE_TIME_PER_STOP_MIN, TRAVEL_BUFFER_MIN, AVERAGE_SPEED_KMH
from src.models import Order, Route, RouteStop
from src.distance import urban_distance, calculate_travel_time_min

def solve_route_sequence(
    orders: List[Order],
    departure_time_min: float,
    depot_lat: float = PHARMACY_DEPOT["latitude"],
    depot_lon: float = PHARMACY_DEPOT["longitude"],
    depot_name: str = PHARMACY_DEPOT["name"],
    include_return_to_depot: bool = True,
    apply_buffer: bool = True
) -> Route:
    """
    Constructs the optimal route sequence for a set of orders starting from the pharmacy depot.
    For small batch sizes (n <= 6), evaluates exact TSP perms to minimize total distance.
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

    # Find shortest distance sequence using TSP permutations for n <= 6, or Nearest-Neighbor for larger
    best_order_sequence = orders
    best_distance = float("inf")

    if len(orders) <= 6:
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
    else:
        # Greedy Nearest-Neighbor heuristic
        unvisited = list(orders)
        curr_lat, curr_lon = depot_lat, depot_lon
        seq = []
        tot_dist = 0.0
        while unvisited:
            next_order = min(unvisited, key=lambda o: urban_distance(curr_lat, curr_lon, o.latitude, o.longitude))
            d = urban_distance(curr_lat, curr_lon, next_order.latitude, next_order.longitude)
            tot_dist += d
            curr_lat, curr_lon = next_order.latitude, next_order.longitude
            seq.append(next_order)
            unvisited.remove(next_order)
        if include_return_to_depot:
            tot_dist += urban_distance(curr_lat, curr_lon, depot_lat, depot_lon)
        best_order_sequence = seq
        best_distance = tot_dist

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
