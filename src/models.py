from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta

@dataclass
class Product:
    product_id: str
    product_name: str
    temperature_sensitive: bool
    special_handling: str  # e.g., 'ColdChain', 'Narcotics', 'General', 'Fragile', 'Hazmat'
    compatibility_group: str  # Primary group ID
    incompatible_groups: List[str]  # List of group IDs that cannot be batched together

    def to_dict(self) -> Dict[str, Any]:
        return {
            "product_id": self.product_id,
            "product_name": self.product_name,
            "temperature_sensitive": self.temperature_sensitive,
            "special_handling": self.special_handling,
            "compatibility_group": self.compatibility_group,
            "incompatible_groups": ",".join(self.incompatible_groups)
        }

@dataclass
class Order:
    order_id: str
    product_id: str
    product_name: str
    customer_location: str
    latitude: float
    longitude: float
    order_time: int  # minutes from shift start (e.g. 0 to 480)
    pickup_ready_time: int  # minutes from shift start
    promised_delivery_time: int  # minutes from shift start (deadline)
    quantity: int
    priority: str  # 'HIGH', 'MEDIUM', 'LOW'
    special_handling_required: str
    compatibility_group: str
    assigned_rider: Optional[str] = None
    status: str = "PENDING"  # PENDING, BATCHED, IN_TRANSIT, DELIVERED, REJECTED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "customer_location": self.customer_location,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "order_time": self.order_time,
            "pickup_ready_time": self.pickup_ready_time,
            "promised_delivery_time": self.promised_delivery_time,
            "quantity": self.quantity,
            "priority": self.priority,
            "special_handling_required": self.special_handling_required,
            "compatibility_group": self.compatibility_group,
            "assigned_rider": self.assigned_rider or "",
            "status": self.status
        }

@dataclass
class Rider:
    rider_id: str
    name: str
    maximum_orders: int
    maximum_workload_minutes: float
    current_latitude: float
    current_longitude: float
    shift_start: int  # minutes from day start
    shift_end: int  # minutes from day start
    status: str = "AVAILABLE"  # AVAILABLE, BUSY, OFF_DUTY

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rider_id": self.rider_id,
            "name": self.name,
            "maximum_orders": self.maximum_orders,
            "maximum_workload_minutes": self.maximum_workload_minutes,
            "current_latitude": self.current_latitude,
            "current_longitude": self.current_longitude,
            "shift_start": self.shift_start,
            "shift_end": self.shift_end,
            "status": self.status
        }

@dataclass
class RouteStop:
    stop_id: str
    location_name: str
    latitude: float
    longitude: float
    stop_type: str  # 'DEPOT' or 'CUSTOMER'
    order_id: Optional[str] = None
    estimated_arrival_time: float = 0.0
    estimated_departure_time: float = 0.0
    waiting_time_minutes: float = 0.0
    promised_delivery_time: Optional[int] = None
    is_late: bool = False

@dataclass
class Route:
    stops: List[RouteStop] = field(default_factory=list)
    total_distance_km: float = 0.0
    total_travel_time_min: float = 0.0
    total_service_time_min: float = 0.0
    total_waiting_time_min: float = 0.0
    total_duration_min: float = 0.0
    departure_time_min: float = 0.0
    is_feasible: bool = True
    feasibility_reason: str = "Valid Route"

@dataclass
class Batch:
    batch_id: str
    rider_id: str
    orders: List[Order] = field(default_factory=list)
    route: Optional[Route] = None
    creation_time: float = 0.0
    status: str = "CREATED"  # CREATED, DISPATCHED, COMPLETED, CANCELLED

    @property
    def order_ids(self) -> List[str]:
        return [o.order_id for o in self.orders]

@dataclass
class ConstraintResult:
    feasible: bool
    time_ok: bool
    product_ok: bool
    pickup_ready: bool
    capacity_ok: bool
    workload_ok: bool
    reason: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feasible": self.feasible,
            "time_ok": self.time_ok,
            "product_ok": self.product_ok,
            "pickup_ready": self.pickup_ready,
            "capacity_ok": self.capacity_ok,
            "workload_ok": self.workload_ok,
            "reason": self.reason,
            "details": self.details
        }

@dataclass
class AuditRecord:
    audit_id: Optional[int]
    timestamp: str
    plan_id: str
    batch_id: str
    action: str  # e.g., 'Plan created', 'Order batched', 'Batch rejected', 'Rider assigned'
    order_id: str
    rider_id: str
    old_state: str
    new_state: str
    reason: str
    triggered_by: str  # e.g., 'SYSTEM_OPTIMIZER', 'DISPATCHER', 'BASELINE_ENGINE'
