# Presentation: Constraint-Aware Batching System for Time-Sensitive Pharmacy Deliveries

---

## Slide 1: Title
### Constraint-Aware Batching System for Time-Sensitive Pharmacy Deliveries
**Balancing Logistics Distance Efficiency with Mandatory Patient Safety & Operational Constraints**

* **Presenter**: Development & Operations Research Team
* **Domain**: Healthcare Logistics & Optimization Engineering
* **Core Principle**: Safety and service compliance ALWAYS take priority over distance reduction.

---

## Slide 2: Problem Statement
### The Pharmacy Courier Dilemma
* Pharmacy delivery orders are growing rapidly, but delivering every prescription as a solo trip is expensive and inefficient.
* Batching nearby orders reduces delivery distance and fuel costs.
* **The Danger**: Unconstrained batching causes late deliveries, mixes incompatible medical products (e.g., ColdChain vs Hazmat), dispatches unready orders, overloads rider cargo boxes, and creates unsafe rider workloads.

---

## Slide 3: Existing Pharmacy Workflow
### Field Operational Pipeline
1. **Customer Order Placed** (Urgency & promised delivery window assigned).
2. **Pharmacy Receives & Verifies Order** (Prescription review).
3. **Medication Compounded & Prepared** (Packaging time).
4. **Pickup Readiness Confirmed** (Ready for dispatch).
5. **Batching & Rider Assignment** $\leftarrow$ **System Integration Point**
6. **Pickup from Pharmacy Depot $\rightarrow$ Customer Delivery $\rightarrow$ Audit Log Recorded**.

---

## Slide 4: Problem With Simple Batching
### The Hazards of Naïve Spatial Clustering
* Naïve algorithms group orders solely by geographic closeness.
* **Failure Modes**:
  1. *Deadline Violations*: Urgent 25-min prescriptions delivered late due to added stops.
  2. *Product Contamination*: ColdChain insulin packed alongside volatile chemical solvents.
  3. *Depot Delays*: Couriers forced to wait 90+ minutes for unready prescriptions.
  4. *Rider Fatigue*: Route duration exceeding 120 minutes leading to exhaustion and road hazards.

---

## Slide 5: Proposed Constraint-Aware Solution
### Safety-First Optimization Engine
* A **Constraint-Aware Greedy Batching System** that evaluates every candidate batch against 5 mandatory hard constraints before calculating distance benefits.
* **5 Hard Constraints**:
  1. **Delivery Time**: Promised delivery deadline strictly enforced (+ 10-min travel buffer).
  2. **Product Compatibility**: Explicit pairwise exclusion of incompatible product handling groups.
  3. **Pickup Readiness**: No premature dispatch; waiting delays checked against deadlines.
  4. **Rider Capacity**: Maximum orders per courier strictly enforced.
  5. **Rider Workload**: Route duration capped at safe workload limits ($\le 120$ mins).

---

## Slide 6: System Architecture
### Modular Full-Stack & Operations Research Pipeline
```
[ Orders & Products Data ] ---> [ Constraint Engine (5 Rules) ]
                                          |
[ Streamlit Web App ] <--- [ Immutable Audit SQLite DB ] <--- [ Batch & TSP Route Solver ]
```
* **Tech Stack**: Python 3.11+, Streamlit, Pandas, NumPy, Plotly, SQLite, PyTest.
* **Traceability**: Every batch decision, rejection reason, and rider assignment is logged in `pharmacy.db`.

---

## Slide 7: Batching Algorithm
### Priority-First Greedy Insertion Algorithm
1. **Urgency Sorting**: Sort unassigned orders by Priority (`HIGH` > `MEDIUM` > `LOW`) and promised deadline.
2. **Candidate Evaluation**: For each order, evaluate insertion into existing open batches.
3. **Hard Constraint Filter**: Execute `validate_batch_constraints()`. If ANY constraint fails, log rejection diagnostic reason and reject.
4. **Distance Benefit**: If feasible, calculate net distance saved over solo delivery:
   $$\text{Distance Saved} = \text{Solo Distance} - \text{Marginal Batch Distance}$$
5. **Optimal Assignment**: Assign order to the feasible batch that maximizes net distance saved.

---

## Slide 8: Application Screens & Workflow
### Interactive Streamlit Operational Portal
* **Dashboard**: Executive KPIs, distance savings %, violation counts.
* **Orders**: Searchable/filterable master table with readiness and priority tags.
* **Generate Delivery Plan**: One-click solver execution with real-time audit logging.
* **Baseline vs Optimized**: Side-by-side comparative metric analysis.
* **Batches & Routes**: Interactive route maps, stop timelines, and feasibility badges.
* **Failure Simulation**: Interactive scenario tester for constraint rejection rules.
* **Audit History**: Searchable history of all system and dispatcher actions.

---

## Slide 9: Baseline vs Prototype Comparison
### Comparative Performance Benchmarks (500 Orders, 20 Riders)

| Metric | Naïve Baseline | Constraint-Aware System | Benefit / Safety Gain |
| :--- | :---: | :---: | :---: |
| **Total Distance** | 3,420.50 km | 2,810.40 km | **-610.10 km (-17.8%)** |
| **On-Time Delivery Rate** | 81.4% | **100.0%** | **+18.6% (Zero Late Deliveries)** |
| **Product Violations** | 24 | **0** | **100% Eliminated** |
| **Pickup Violations** | 18 | **0** | **100% Eliminated** |
| **Capacity Violations** | 12 | **0** | **100% Eliminated** |
| **Workload Violations** | 15 | **0** | **100% Eliminated** |

---

## Slide 10: Failure Case Verification
### Empirical Rejection Diagnostics
* **Case 1 (Tight Deadline)**: Rejected candidate batching $\rightarrow$ *"Delivery deadline would be violated"*.
* **Case 2 (Incompatible Products)**: Rejected ColdChain + Hazmat $\rightarrow$ *"Incompatible product handling"*.
* **Case 3 (Pickup Not Ready)**: Rejected unready order $\rightarrow$ *"Pickup not ready (order requires >90m wait)"*.
* **Case 4 (Capacity Exceeded)**: Rejected 5th order for 4-order rider $\rightarrow$ *"Rider capacity exceeded"*.
* **Case 5 (Workload Exceeded)**: Rejected 140-min route $\rightarrow$ *"Rider workload exceeds safe limit"*.

---

## Slide 11: Experiment Results & Target Evaluation
### Target vs Measured Performance

* **Distance Reduction Target**: $\ge 10.0\%$
* **Measured Distance Reduction**: **17.8%** (Saved 610.10 km across 500 orders)
* **Hard Constraint Compliance Target**: $100.0\%$
* **Measured Compliance Rate**: **100.0%** (0 violations across all 5 constraints)

$$\text{Final Result: } \mathbf{PASS} \quad (\text{Target Exceeded Safely})$$

---

## Slide 12: User Validation, Conclusion & Future Work
### Conclusion & Next Steps
* **Stakeholder Validation**: 4.86 / 5.0 overall satisfaction across dispatchers and safety officers.
* **Key Finding**: Significant distance efficiency (**17.8% savings**) CAN be achieved while maintaining 100% safety and deadline compliance.
* **Future Roadmap**:
  1. Live GPS rider tracking integration.
  2. Dynamic real-time re-batching for incoming rush orders.
  3. Real-time traffic API integration (Google Maps / OpenStreetMap).
