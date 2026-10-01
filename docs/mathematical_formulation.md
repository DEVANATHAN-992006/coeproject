# MEDIROUTE — Mathematical Formulation & Optimization Architecture

This document provides the formal mathematical formulation of the **MEDIROUTE** pharmacy delivery logistics problem, clearly distinguishing the theoretical optimization model from the practical production implementation.

---

## 1. System Architecture: Model vs. Implementation

> [!IMPORTANT]
> **Methodological Distinction**:
> The theoretical problem is a multi-constrained Vehicle Routing Problem with Time Windows and Heterogeneous Operational Constraints (VRPTW-HC), which is NP-hard. The current MEDIROUTE production solver **does not** solve this using mixed-integer linear programming (MILP) branch-and-cut solvers; rather, it implements an **iterative constraint-aware greedy insertion batching engine** coupled with:
> - **Exact TSP Permutations** for small candidate batches ($n \le 6$).
> - **Clarke-Wright Savings Heuristic** with 2-opt refinement for scalable candidate routing ($n > 6$).

---

## 2. Mathematical Optimization Model

### 2.1 Sets and Indices
- $R$: Set of available delivery couriers (riders), indexed by $r \in \{1, \dots, |R|\}$.
- $O$: Set of pending pharmacy prescription orders, indexed by $i, j \in \{1, \dots, |O|\}$.
- $P$: Set of pharmaceutical products, indexed by $p \in \{1, \dots, |P|\}$.
- $D_0$: Central Metro Pharmacy Depot location $(lat_0, lon_0)$.
- $S_r \subseteq O$: Ordered sequence of delivery stops assigned to courier $r$.
- $\text{route}_r = \langle D_0, s_{r,1}, s_{r,2}, \dots, s_{r,|S_r|}, D_0 \rangle$: Round-trip route traversed by courier $r$.

### 2.2 Objective Function

The primary optimization objective of MEDIROUTE is to **minimize total delivery travel distance** across all active couriers:

$$\min \sum_{r \in R} \text{Distance}(\text{route}_r)$$

where the route distance function $\text{Distance}(\text{route}_r)$ computes the cumulative urban road travel distance:

$$\text{Distance}(\text{route}_r) = d(D_0, s_{r,1}) + \sum_{k=1}^{|S_r|-1} d(s_{r,k}, s_{r,k+1}) + d(s_{r,|S_r|}, D_0)$$

In MEDIROUTE, $d(u, v)$ is calculated using the configured `urban_distance` formula:

$$d(u, v) = 1.30 \times \text{Haversine}(lat_u, lon_u, lat_v, lon_v)$$

applying a $1.30\times$ urban circuity factor to account for municipal road grid geometry.

---

## 3. The Five Hard Operational Constraints

Every candidate delivery batch $S_r$ must strictly satisfy five non-negotiable operational and clinical constraints.

### Constraint 1: Delivery Deadline (SLA Compliance)
For every order $i \in S_r$, the estimated arrival time plus the configured transit safety buffer must not exceed the patient's promised delivery deadline:

$$T^{\text{arrival}}_{r,i} + \Delta_{\text{buffer}} \le D_i \quad \forall i \in S_r$$

where:
- $T^{\text{arrival}}_{r,i}$: Estimated arrival timestamp at customer $i$'s delivery address (minutes from shift start).
- $\Delta_{\text{buffer}}$: Configured safety buffer (`TRAVEL_BUFFER_MIN = 10.0` minutes) protecting against traffic variance.
- $D_i$: Patient promised delivery deadline (`order.promised_delivery_time`, minutes from shift start).

### Constraint 2: Product Handling and Segregation Compatibility
For every candidate batch $S_r$, all pairwise co-loaded products must be mutually compatible to prevent cross-contamination or chemical hazard breaches:

$$\text{Compatible}(\text{product}_i, \text{product}_j) = \text{True} \quad \forall i, j \in S_r$$

Operational rules enforced by MEDIROUTE:
1. **ColdChain Segregation**: Temperature-sensitive biologics/vaccines cannot co-load with Cytotoxic agents or Volatile Hazmat disinfectants:
   $$\text{ColdChain} \cap \{\text{Hazmat}, \text{Cytotoxic}\} = \emptyset$$
2. **Narcotic Security**: Scheduled narcotics cannot co-load with Cytotoxic agents or Hazmat:
   $$\text{Narcotic} \cap \{\text{Cytotoxic}, \text{Hazmat}\} = \emptyset$$
3. **Explicit Incompatibility Matrix**: Two products cannot co-load if either product's `incompatible_groups` list contains the other product's `compatibility_group`.

### Constraint 3: Pickup Readiness & Maximum Dispatch Delay
A batch cannot depart the pharmacy before all included orders have completed dispensing and quality inspection. The batch departure timestamp $T^{\text{depart}}_r$ is dynamically determined as:

$$T^{\text{depart}}_r = \max\left(T_{\text{current}}, \max_{i \in S_r} R_i\right)$$

where $R_i$ is order $i$'s packaging readiness timestamp (`pickup_ready_time`).

Furthermore, to prevent excessive dispatch stall where couriers wait idly for long packaging delays:

$$\max_{i \in S_r} R_i - T_{\text{current}} \le 90.0 \text{ minutes}$$

Any order requiring more than a 90-minute wait from the current scheduling horizon is rejected from immediate batching.

### Constraint 4: Courier Order Capacity
The number of orders assigned to courier $r$'s batch cannot exceed the courier's physical transport capacity:

$$|S_r| \le C_r \quad \forall r \in R$$

where $C_r$ is `rider.maximum_orders` (typically 4 to 6 orders per batch, default parameter `DEFAULT_MAX_RIDER_CAPACITY = 5`).

### Constraint 5: Courier Workload Safety Limit
To ensure courier occupational safety and prevent fatigue-induced accidents, total route shift duration must remain within both the individual courier limit and the system safety boundary:

$$\text{TotalDuration}(\text{route}_r) \le \min\left(W_r, W_{\max}\right) \quad \forall r \in R$$

where:
- $\text{TotalDuration}(\text{route}_r) = T^{\text{travel}}_r + T^{\text{service}}_r + T^{\text{waiting}}_r$.
- $T^{\text{service}}_r = |S_r| \times \text{SERVICE\_TIME\_PER\_STOP\_MIN}$ ($5.0$ minutes per customer stop).
- $W_r$: Courier's configured maximum workload (`rider.maximum_workload_minutes`).
- $W_{\max}$: Hard system safety limit (`MAX_WORKLOAD_SAFETY_LIMIT_MIN = 120.0` minutes).

---

## 4. Feasibility Model and Insertion Policy

A candidate insertion of order $o_{\text{new}}$ into batch $S_r$ is feasible if and only if all five hard constraint predicates evaluate to True:

$$\text{Feasible}(S_r \cup \{o_{\text{new}}\}) = \text{DeadlineOK} \land \text{CompatibilityOK} \land \text{PickupReadyOK} \land \text{CapacityOK} \land \text{WorkloadOK}$$

### Rejection Policy:
If any constraint evaluates to False:
1. The candidate insertion is immediately **rejected**.
2. The specific constraint failure reason is logged into the immutable audit record.
3. The order remains pending until an alternative feasible batch or available courier is identified.

---

## 5. Routing Optimization Strategies

For any candidate order subset $S_r$, the optimal visiting sequence is resolved via one of three configurable strategies:

### 5.1 Strategy 1: Exact TSP Permutations (`EXACT_TSP`)
- Evaluates all $|S_r|!$ permutations to select the sequence that minimizes round-trip distance.
- **Properties**: Guaranteed globally optimal route sequence for the given subset $S_r$.
- **Limitation**: Factorial computational complexity $O(n!)$ causes exponential runtime growth as $n$ increases, making it impractical for $n > 6$.

### 5.2 Strategy 2: Clarke-Wright Savings Heuristic (`SCALABLE_HEURISTIC`)
- Computes pairwise travel savings $s(i, j) = d(D_0, i) + d(D_0, j) - d(i, j)$.
- Merges customer tours in descending order of savings, followed by 2-opt tour refinement.
- **Properties**: The Clarke-Wright implementation is deterministic for identical inputs and configuration and provides substantially better scalability than factorial-time brute-force permutation search.
- **Limitation**: Does not guarantee global optimality (approximate heuristic).

### 5.3 Strategy 3: Automatic Hybrid (`AUTO`, Default)
$$\text{Strategy}(S_r) = \begin{cases} \text{Exact TSP} & \text{if } |S_r| \le 6 \\ \text{Clarke-Wright Savings} & \text{if } |S_r| > 6 \end{cases}$$

---

## 6. Penalty Optimization as a Future Extension

> [!NOTE]
> **Future Architectural Extension**:
> Classical operations research formulations frequently incorporate soft constraints into the objective function via Lagrangian relaxation or penalty terms:
>
> $$\min \sum_{r \in R} \text{Distance}(\text{route}_r) + \lambda_1 \sum_{i} \max(0, T^{\text{arrival}}_i - D_i) + \lambda_2 \sum_{r} \max(0, |S_r| - C_r) + \lambda_3 \sum \text{Incompatibilities}$$
>
> **Current MEDIROUTE Policy**:
> The current MEDIROUTE implementation **treats all five operational constraints as hard feasibility conditions**. Infeasible candidates are rejected rather than assigned numerical penalty costs. This design decision ensures zero regulatory violations in clinical medication dispatch, guaranteeing patient safety and chain-of-custody compliance.
