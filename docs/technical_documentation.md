# Technical Documentation: Constraint-Aware Batching System for Pharmacy Deliveries

## 1. Executive Summary

The **Constraint-Aware Pharmacy Delivery Batching System** is an enterprise operations-research and logistics engine designed to optimize courier delivery batching for time-sensitive pharmaceutical prescriptions.

### Core Tradeoff & Objective
Batching nearby orders reduces vehicle travel distance, fuel consumption, and operational cost. However, naive batching leads to late deliveries, product contamination, pickup bottlenecks, and rider fatigue.

> **Primary Objective**: Maximize delivery distance savings **if and only if** all mandatory operational, product, readiness, capacity, and rider safety constraints are 100% satisfied.

---

## 2. System Architecture

```
+-------------------+      +-------------------------+      +-------------------------+
|  Synthetic Data   | ---> |   Constraint Engine     | ---> |  Priority-First Greedy  |
| Generator (500)   |      |  (5 Hard Constraints)   |      |    Batching Solver      |
+-------------------+      +-------------------------+      +-------------------------+
                                                                         |
                                                                         v
+-------------------+      +-------------------------+      +-------------------------+
| Streamlit Web UI  | <--- |   SQLite Audit Engine   | <--- |   TSP Route Sequencer   |
| (8 Interactive)   |      |  (Immutable History)    |      |  (Stop ETAs & Buffers)  |
+-------------------+      +-------------------------+      +-------------------------+
```

### Core Components
1. **`src/models.py`**: Dataclasses for `Order`, `Product`, `Rider`, `Route`, `Batch`, `ConstraintResult`, `AuditRecord`.
2. **`src/constraints.py`**: Isolated constraint validation module.
3. **`src/distance.py` & `src/routing.py`**: Haversine/Manhattan distance calculations and exact TSP permutation route solver.
4. **`src/batching.py`**: Priority-queue greedy batch insertion solver.
5. **`src/baseline.py`**: Naive unconstrained spatial batching algorithm for benchmark comparison.
6. **`src/audit.py`**: SQLite database interface for immutable audit tracking.
7. **`src/evaluation.py`**: Comparative benchmark evaluation metrics suite.

---

## 3. Mathematical & Constraint Formulation

Let $B = \{o_1, o_2, \dots, o_k\}$ be a candidate order batch assigned to rider $R$ at current time $t_0$.

### 3.1. Rider Capacity Constraint
$$|B| \le \text{Cap}_{\max}(R)$$

### 3.2. Product Compatibility Constraint
For every pair $(o_i, o_j) \in B \times B$:
$$\text{Group}(o_j) \notin \text{IncompatibleGroups}(\text{Product}(o_i))$$
Specifically:
- $\text{ColdChain} \cap (\text{Hazmat} \cup \text{Cytotoxic}) = \emptyset$
- $\text{Narcotic} \cap (\text{Cytotoxic} \cup \text{Hazmat}) = \emptyset$

### 3.3. Pickup Readiness Constraint
Departure time $t_{\text{dep}}$ from pharmacy depot:
$$t_{\text{dep}} = \max\left(t_0, \max_{o_i \in B} \text{ReadyTime}(o_i)\right)$$

### 3.4. Delivery Deadline Constraint
For every stop $i$ in route sequence $\pi$:
$$t_{\text{arr}}(\pi_i) + \Delta_{\text{buffer}} \le \text{PromisedDeadline}(\pi_i)$$
where $\Delta_{\text{buffer}} = 10.0\text{ minutes}$.

### 3.5. Rider Workload Safety Constraint
Total route duration $T_{\text{total}}$ including travel, pickup waiting, customer service handovers, and depot return:
$$T_{\text{total}} \le \min\left(\text{Workload}_{\max}(R), 120.0\text{ minutes}\right)$$

---

## 4. Database Audit History Schema

SQLite table `audit_log`:

```sql
CREATE TABLE audit_log (
    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    plan_id TEXT NOT NULL,
    batch_id TEXT NOT NULL,
    action TEXT NOT NULL,
    order_id TEXT NOT NULL,
    rider_id TEXT NOT NULL,
    old_state TEXT NOT NULL,
    new_state TEXT NOT NULL,
    reason TEXT NOT NULL,
    triggered_by TEXT NOT NULL
);
```

---

## 5. System Performance & Verification

The system includes automated tests (`pytest`) covering:
1. Individual constraint checkers (`tests/test_constraints.py`)
2. Five mandatory failure scenarios (`tests/test_failure_cases.py`)
3. Full batching optimizer (`tests/test_batching.py`)
4. Baseline benchmark execution (`tests/test_baseline.py`)

Run tests via:
```bash
python -m pytest -v
```
