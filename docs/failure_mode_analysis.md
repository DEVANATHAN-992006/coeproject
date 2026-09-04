# Failure Mode Analysis & Edge Case Safeguards

## 1. Overview

In pharmacy operations, batching efficiency must never compromise patient safety or delivery reliability. This document presents a comprehensive failure mode analysis detailing how the **Constraint-Aware Batching System** detects, rejects, and mitigates operational edge cases.

---

## 2. Mandatory Failure Scenarios & Safeguards

### Scenario 1 — Tight Delivery Deadline Breach
- **Input Condition**: Order O-101 has an urgent promised delivery window (e.g. 25 minutes). Order O-102 is 1.5 km away with a 90-minute deadline.
- **Naïve Baseline Behavior**: Groups O-101 and O-102 together to save 1.8 km. The extra travel and stop duration causes O-101 to arrive at $t=32$ min ($7$ minutes late).
- **Constraint Engine Decision**: **REJECT**
- **Diagnostic Reason**: `"Rejected: delivery deadline would be violated (Order O-101 estimated delivery at t=32.0m > promised 25m, buffer 10m)"`
- **Safe Outcome**: O-101 is dispatched as a solo priority run. O-102 is combined with a later feasible batch.

---

### Scenario 2 — Product Incompatibility (ColdChain vs Hazmat / Cytotoxic)
- **Input Condition**: Order O-201 requires ColdChain refrigerated insulin ($2^\circ\text{C}-8^\circ\text{C}$). Order O-202 contains medical alcohol disinfectant (Hazmat) or oncology tablets (Cytotoxic).
- **Naïve Baseline Behavior**: Groups O-201 and O-202 into the same thermal delivery bag.
- **Constraint Engine Decision**: **REJECT**
- **Diagnostic Reason**: `"Rejected: incompatible product handling (O-201:ColdChain with O-202:Hazmat)"`
- **Safe Outcome**: Candidate insertion is rejected immediately without performing route calculations.

---

### Scenario 3 — Pickup Readiness Delay Bottleneck
- **Input Condition**: Order O-301 is ready immediately ($t=0$). Order O-302 requires compounding and will not be ready until $t=110$ min.
- **Naïve Baseline Behavior**: Holds rider at depot for 110 minutes waiting for O-302, causing O-301 to be delivered 80 minutes late.
- **Constraint Engine Decision**: **REJECT**
- **Diagnostic Reason**: `"Rejected: pickup not ready (order(s) O-302 require >90m wait)"`
- **Safe Outcome**: O-301 dispatches immediately at $t=0$. O-302 joins the afternoon dispatch wave once compounding is complete.

---

### Scenario 4 — Rider Order Capacity Exceeded
- **Input Condition**: Rider R-01 has a small motorcycle cargo box capped at maximum 3 orders. Batching algorithm attempts to add a 4th order.
- **Naïve Baseline Behavior**: Forces 4th order into cargo box, risking package damage or loss.
- **Constraint Engine Decision**: **REJECT**
- **Diagnostic Reason**: `"Rejected: rider capacity exceeded (4 orders > max 3)"`
- **Safe Outcome**: 4th order is routed to another available rider with remaining box capacity.

---

### Scenario 5 — Rider Workload Safety Threshold Exceeded
- **Input Condition**: Proposed batch route requires 145 minutes total driving, service, and depot return time, exceeding the 120-minute safety threshold.
- **Naïve Baseline Behavior**: Assigns 145-minute route, leading to courier fatigue and higher traffic accident risk.
- **Constraint Engine Decision**: **REJECT**
- **Diagnostic Reason**: `"Rejected: rider workload exceeds safe limit (145.0m > max 120.0m)"`
- **Safe Outcome**: Batch is split into two smaller feasible routes assigned to separate riders.

---

## 3. Failure Mode Matrix

| Failure Mode | Root Cause | Primary Constraint Involved | System Safeguard Action |
| :--- | :--- | :--- | :--- |
| **Deadline Breach** | Optimistic travel estimation | Delivery Time + Buffer | Rejects batch; forces solo priority dispatch |
| **Cross-Contamination** | Missing product tags | Product Compatibility | Pairwise group exclusions; instant rejection |
| **Depot Bottleneck** | Long compounding time | Pickup Readiness | Calculates max readiness; dispatches ready orders |
| **Overloading** | Cargo size mismatch | Rider Order Capacity | Enforces hard order count ceiling per rider |
| **Courier Fatigue** | Excessively long routes | Rider Workload Limit | Enforces max route duration cutoff (120m) |
