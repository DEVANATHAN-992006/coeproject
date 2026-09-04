# Field Workflow Map: Pharmacy Delivery Batching Integration

## 1. Existing Pharmacy Delivery Workflow

The traditional operational workflow for time-sensitive pharmacy deliveries proceeds linearly:

```mermaid
graph TD
    A["1. Customer Order Placed"] --> B["2. Pharmacy Receives & Verifies Order"]
    B --> C["3. Medication Compounded & Prepared"]
    C --> D["4. Pickup Readiness Confirmed"]
    D --> E["5. Orders Considered for Batching / Dispatch"]
    E --> F["6. Rider Assigned"]
    F --> G["7. Pickup from Pharmacy Depot"]
    G --> H["8. Customer Delivery & Handover"]
    H --> I["9. Delivery Status & Audit Recorded"]
```

---

## 2. Legacy Operational Problem

In the legacy workflow:
- **Individual Delivery**: Orders are dispatched one-by-one, resulting in high courier distance, fuel cost, and poor rider utilization.
- **Naive Distance Batching**: Dispatchers group nearby orders strictly by geographic proximity. However, this causes severe operational failures:
  - **Late Deliveries**: Adding stops causes promised delivery deadlines to be missed.
  - **Product Incompatibility**: Refrigerated vaccines (ColdChain) are accidentally grouped with volatile chemicals or narcotics.
  - **Unready Pickups**: Riders are dispatched before medication compounding is completed, wasting rider time at the pharmacy.
  - **Unsafe Rider Workloads**: Riders are assigned excessively long multi-stop routes exceeding fatigue limits.

---

## 3. Integrated Constraint-Aware Architecture

The **Constraint-Aware Batching System** seamlessly integrates at **Stage 5 (Orders Considered for Batching)** without disrupting existing pharmacy systems:

```mermaid
graph TD
    A["Order Received & Prepared"] --> B["Pickup Readiness Confirmed"]
    B --> C[["Constraint-Aware Batching System Integration"]]
    
    subgraph Constraint-Aware Core Engine
        C --> D{"1. Rider Capacity Check"}
        D -- Pass --> E{"2. Product Compatibility Check"}
        E -- Pass --> F{"3. Pickup Readiness Delay Check"}
        F -- Pass --> G{"4. Route & Deadline Simulation"}
        G -- Pass --> H{"5. Rider Workload Safety Check"}
        
        D -- Reject --> R["Log Failure & Reject Batch"]
        E -- Reject --> R
        F -- Reject --> R
        G -- Reject --> R
        H -- Reject --> R
    end

    H -- All Constraints Passed --> I["Calculate Net Distance Saved"]
    I --> J["Create Validated Batch & Assign Rider"]
    J --> K[("Immutable Audit DB (pharmacy.db)")]
    J --> L["Dispatch Rider for Pickup & Delivery"]
```

---

## 4. Operational Stage Summary

| Stage | Action | Legacy Risk | Constraint-Aware Solution |
| :--- | :--- | :--- | :--- |
| **1. Order Reception** | Customer places prescription | Manual delay | Structured priority & deadline tags |
| **2. Preparation** | Pharmacist compounding | Unverified readiness | Real-time `pickup_ready_time` tracking |
| **3. Batching Decision** | Grouping orders for courier | Deadline breaches & product mixing | Hard-constraint engine checks all 5 safety rules |
| **4. Routing & Dispatch** | Generating courier sequence | Sub-optimal routes & fatigue | TSP sequence optimization with safety buffer |
| **5. Audit & Compliance** | Logging dispatch history | Overwritten / unverified logs | Immutable SQLite audit history (`audit_log`) |
