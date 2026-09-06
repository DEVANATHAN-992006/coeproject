report_text = """1. TITLE
MEDIROUTE – Constraint-Aware Pharmacy Logistics Control Center

2. ABSTRACT
Pharmacy delivery batching reduces courier distance and costs but risks missed deadlines, drug contamination, depot delays, overloaded cargo boxes, and rider fatigue. This 35% progress review introduces MEDIROUTE, a constraint-aware pharmacy logistics control center optimizing delivery batching while enforcing hard operational safety boundaries. The system evaluates five mandatory constraints: delivery deadlines (with a safety buffer), product compatibility, pickup readiness, rider capacity, and rider workload limits. At the 35% milestone, the database schema, 5-hard-constraint engine, priority greedy solver, baseline benchmark simulator, SQLite audit logger, Streamlit interface, and a 14-test-case verification suite are implemented and verified. Expected outcomes include reduced delivery distance and guaranteed constraint compliance without compromising safety.

3. INTRODUCTION
Pharmacy last-mile delivery is time-critical; delays directly impact patient health. Pharmacies batch prescription orders to minimize delivery mileage and operating costs. Unlike e-commerce, last-mile pharmacy delivery involves promised delivery windows, handling exclusions, packaging limits, and preparation delays. Intelligent logistics systems must balance route efficiency with strict compliance to operational safety boundaries.

4. PROBLEM STATEMENT
Distance-only delivery batching focuses purely on proximity, ignoring operational safety rules. This causes six failure modes:
- Delivery Deadlines: Intermediate stops delay deliveries, breaching promised time windows.
- Product Compatibility: Grouping ColdChain drugs with Hazmat or Cytotoxic compounds creates contamination risks.
- Pickup Readiness: Dispatching couriers before compounding completes causes idle depot waiting.
- Rider Capacity: Exceeding motorcycle cargo box limits risks package damage or loss.
- Rider Workload: Excessively long routes exceed driver fatigue limits (capped at 120 minutes continuous driving).
- Unnecessary Distance: Uncoordinated individual dispatches create redundant travel mileage.

5. OBJECTIVES
The main objectives of MEDIROUTE are:
- Create feasible delivery batches by grouping compatible prescription orders.
- Respect all five hard operational constraints (deadlines, product groups, pickup readiness, rider capacity, rider workload).
- Assign orders to riders safely without exceeding physical or workload limits.
- Reduce overall delivery distance compared to an unconstrained baseline.
- Maintain an auditable, immutable record of batching decisions and rejection rationale.
- Evaluate system robustness using realistic failure-case test scenarios.

6. EXISTING SYSTEM
Conventional pharmacy delivery relies on individual dispatching or manual distance-only batching. Individual dispatching incurs separate round trips per order, causing high mileage, fuel waste, and low fleet utilization. Manual distance-based batching clusters orders by proximity alone, failing to verify stop delays, product exclusions, compounding readiness, or courier fatigue caps, causing frequent deadline breaches.

7. PROPOSED SYSTEM
MEDIROUTE is a constraint-aware decision-support control center. It prioritizes orders by urgency, evaluates candidate batch insertions against five hard constraints, and optimizes stop sequences. If any constraint is violated, the system rejects the insertion, logs a diagnostic reason, and evaluates alternative assignments. Key modules include order management, constraint validation, priority greedy batching, rider assignment, route planning, an immutable SQLite audit trail, baseline benchmarking, and failure testing.

8. METHODOLOGY
Workflow: Orders Ingestion -> Priority Sorting -> Constraint Verification -> Feasible Batch Creation -> Rider Assignment -> TSP Route Sequencing -> Validation -> Audit Logging.
Hard constraints (rider capacity, product compatibility, pickup readiness delay, delivery deadlines with a 10-minute safety buffer, and rider workload limits) are strictly checked BEFORE a batch is considered valid. Only feasible insertions yielding net distance savings are accepted.

9. SYSTEM MODULES
- Overview: Executive dashboard displaying orders, active batches, and system status.
- Orders: Ingests and manages prescription orders, priorities, product types, and deadlines.
- Dispatch Planning: Formulates constraint-compliant plans using priority greedy solving.
- Routes: Generates optimal stop sequences and timelines using exact TSP permutations.
- Performance/Baseline Comparison: Benchmarks optimized plans against an unconstrained baseline.
- Constraint Validation: Isolates and executes the 5 hard constraint checkers.
- Audit Trail: Immutable log viewer for searching transaction histories and rejection reasons.
- Stakeholder Feedback: Captures dispatcher and safety officer survey metrics.

10. TECHNOLOGY USED
- Python: Core language for logic, constraints, and solver.
- Streamlit: Web framework for interactive UI.
- SQLite: Database for persistent storage and audit logs.
- Pandas: Data manipulation and tabular analysis.
- Plotly: Interactive charting and visualization.
- Pytest: Automated testing framework for unit and failure tests.

11. CURRENT IMPLEMENTATION STATUS – 35%
Work completed at the 35% milestone:
- Functional Streamlit Web Application featuring an 8-module control center interface.
- Database & Order Handling using SQLite (pharmacy.db) and synthetic data (500 orders, 20 riders, 30 products).
- Baseline & Constraint-Aware Batching Engines for comparative evaluation.
- 5-Hard-Constraint Engine validating capacity, workload, product compatibility, pickup readiness, and delivery deadlines.
- Route Sequencing & Timeline Visualization using exact TSP permutations (n <= 6).
- Immutable Audit Logging tracking plan initializations, state changes, and rejection reasons.
- Failure-Case Simulator evaluating mandatory edge-case scenarios.
- Enterprise Control Center UI Redesign for clear visual dispatch management.
System correctness is verified by an automated Pytest suite containing exactly 14 test cases across constraints, batching, baseline, and failure scenarios (all 14 pass cleanly).

12. FAILURE CASE VALIDATION
The system is validated against five mandatory failure scenarios:
1. Tight Delivery Deadline: Rejects batching when added stops breach delivery deadlines.
2. Incompatible Products: Rejects grouping ColdChain drugs with Hazmat or Cytotoxic compounds.
3. Pickup Not Ready: Rejects batching orders requiring excessive pickup waiting (>90 mins).
4. Rider Capacity Exceeded: Rejects batching when order count exceeds cargo box limits.
5. Rider Workload Exceeded: Rejects routes exceeding the 120-minute continuous driving limit.
These test cases verify that MEDIROUTE never improves efficiency by violating operational safety constraints.

13. EXPECTED RESULTS
As a 35% progress report, numerical results are not fabricated. Expected outcomes are:
- Measurable reduction in total courier travel distance compared to individual dispatching.
- 100% creation of valid, constraint-compliant delivery batches with zero hard violations.
- Safe rider assignments adhering strictly to box capacity and workload fatigue limits.
- Transparent, auditable log history capturing all operational decisions.
- Demonstrated safety and operational improvement over the unconstrained baseline.

14. FUTURE WORK
Planned development and future enhancements include:
- Testing on larger real-world pharmacy dispatch datasets.
- Route optimization and parallelized solving for larger order pools.
- Broader stakeholder validation trials with dispatchers and safety officers.
- System containerization, field deployment, and pilot testing.
- Improved scalability and real-time dynamic re-batching capabilities.
- Incorporating operational constraints such as live traffic updates and GPS tracking.

15. CONCLUSION
The current 35% implementation establishes the core architectural and algorithmic foundation of MEDIROUTE. The 5-hard-constraint engine, greedy solver, baseline benchmark, SQLite audit system, Streamlit interface, and 14-test-case suite are fully operational. Remaining work will focus on large-scale experimentation, stakeholder validation, performance optimization, and final deployment.

16. REFERENCES
[1] P. Toth & D. Vigo, Eds., Vehicle Routing Problem, SIAM, 2014.
[2] C. Archetti et al., "VRP with time windows for pharmaceutical distribution," Comput. Oper. Res., 2015.
[3] M. Savelsbergh & M. Sol, "General pickup and delivery problem," Transp. Sci., 1995.
[4] T. Vidal et al., "Heuristics for multi-attribute VRP," Eur. J. Oper. Res., 2013.
[5] G. Ghiani et al., Operations Research in Logistics & Supply Chain Management, Wiley, 2004.
[6] M. Solomon, "Algorithms for VRPTW," Oper. Res., 1987.
[7] G. Laporte, "The vehicle routing problem: An overview," Eur. J. Oper. Res., 1992.
"""

# Let's compress further by editing long paragraphs
lines = report_text.strip().split('\n')
print("Total lines:", len(lines))

# Write concise version to achieve ~6,800 chars
concise_text = """1. TITLE
MEDIROUTE – Constraint-Aware Pharmacy Logistics Control Center

2. ABSTRACT
Pharmacy delivery batching reduces courier distance and costs but risks missed deadlines, drug contamination, depot delays, overloaded cargo boxes, and rider fatigue. This 35% progress review report introduces MEDIROUTE, a constraint-aware pharmacy logistics control center optimizing delivery batching while enforcing hard operational safety boundaries. The system evaluates five mandatory constraints: delivery deadlines (with a 10-minute safety buffer), product compatibility, pickup readiness, rider capacity, and rider workload limits. At the 35% milestone, the database schema, 5-hard-constraint engine, priority greedy solver, baseline benchmark simulator, SQLite audit logger, Streamlit UI, and a 14-test-case verification suite are implemented and verified. Expected outcomes include reduced delivery distance and guaranteed constraint compliance without compromising patient safety or rider limits.

3. INTRODUCTION
Pharmacy last-mile delivery is time-critical; delivery delays directly impact patient health. Pharmacies batch prescription orders to minimize delivery mileage and operating costs. Unlike e-commerce, last-mile pharmacy delivery involves promised delivery windows, handling exclusions, packaging limits, and preparation delays. Intelligent logistics systems must balance route efficiency with strict compliance to operational safety boundaries.

4. PROBLEM STATEMENT
Distance-only delivery batching focuses purely on proximity, ignoring operational safety rules. This causes six primary operational failure modes:
- Delivery Deadlines: Intermediate stops delay deliveries, breaching promised time windows.
- Product Compatibility: Grouping ColdChain drugs with Hazmat or Cytotoxic compounds creates contamination risks.
- Pickup Readiness: Dispatching couriers before compounding completes causes idle depot waiting.
- Rider Capacity: Exceeding motorcycle cargo box limits risks package damage or loss.
- Rider Workload: Excessively long routes exceed driver fatigue limits (capped at 120 minutes continuous driving).
- Unnecessary Distance: Uncoordinated individual dispatches create redundant travel mileage.

5. OBJECTIVES
The main objectives of MEDIROUTE are:
- Create feasible delivery batches by grouping compatible prescription orders.
- Respect all five hard operational constraints (deadlines, product groups, pickup readiness, rider capacity, rider workload).
- Assign orders to riders safely without exceeding physical or workload capacity limits.
- Reduce overall delivery distance compared to an unconstrained individual/naive baseline.
- Maintain an auditable, immutable record of batching decisions and rejection rationale.
- Evaluate system robustness using realistic failure-case test scenarios.

6. EXISTING SYSTEM
Conventional pharmacy delivery relies on individual order dispatching or manual distance-only batching. Individual dispatching incurs separate round trips per order, causing high mileage, fuel waste, and low fleet utilization. Manual distance-based batching clusters orders by proximity alone, failing to verify stop delays, product exclusions, compounding readiness, or courier fatigue caps, causing frequent deadline breaches and operational failures.

7. PROPOSED SYSTEM
MEDIROUTE is a constraint-aware decision-support control center. It prioritizes orders by urgency, evaluates candidate batch insertions against five hard constraints, and optimizes stop sequences. If any constraint is violated, the system rejects the insertion, logs a diagnostic reason, and evaluates alternative assignments. Key modules include order management, constraint validation, priority greedy batching, rider assignment, route planning, an immutable SQLite audit trail, baseline benchmarking, and automated failure testing.

8. METHODOLOGY
Workflow: Orders Ingestion -> Priority Sorting -> Constraint Verification -> Feasible Batch Creation -> Rider Assignment -> TSP Route Sequencing -> Validation -> Audit Logging.
Hard constraints (rider capacity, product compatibility, pickup readiness delay, delivery deadlines with a 10-minute safety buffer, and rider workload limits) are strictly checked BEFORE a batch is considered valid. Only feasible insertions yielding net distance savings are accepted.

9. SYSTEM MODULES
- Overview: Executive dashboard displaying orders, active batches, and system status.
- Orders: Ingests and manages prescription orders, priorities, product types, and deadlines.
- Dispatch Planning: Formulates constraint-compliant plans using priority greedy solving.
- Routes: Generates optimal stop sequences and timelines using exact TSP permutations.
- Performance/Baseline Comparison: Benchmarks optimized plans against an unconstrained baseline.
- Constraint Validation: Isolates and executes the 5 hard constraint checkers.
- Audit Trail: Immutable log viewer for searching transaction histories and rejection reasons.
- Stakeholder Feedback: Captures dispatcher and safety officer survey metrics.

10. TECHNOLOGY USED
- Python: Core language for logic, constraints, and solver.
- Streamlit: Web framework for interactive control center UI.
- SQLite: Database for persistent storage and audit logs.
- Pandas: Data manipulation and tabular analysis.
- Plotly: Interactive charting and visualization.
- Pytest: Automated testing framework for unit and failure tests.

11. CURRENT IMPLEMENTATION STATUS – 35%
Work completed at the 35% milestone:
- Functional Streamlit Web Application featuring an 8-module control center interface.
- Database & Order Handling using SQLite (pharmacy.db) and synthetic data (500 orders, 20 riders, 30 products).
- Baseline & Constraint-Aware Batching Engines for comparative evaluation.
- 5-Hard-Constraint Engine validating capacity, workload, product compatibility, pickup readiness, and delivery deadlines.
- Route Sequencing & Timeline Visualization using exact TSP permutations (n <= 6).
- Immutable Audit Logging tracking plan initializations, state changes, and rejection reasons.
- Failure-Case Simulator evaluating mandatory edge-case scenarios.
- Enterprise Control Center UI Redesign for clear visual dispatch management.
System correctness is verified by an automated Pytest suite containing exactly 14 test cases across constraints, batching, baseline, and failure scenarios (all 14 pass cleanly).

12. FAILURE CASE VALIDATION
The system is validated against five mandatory failure scenarios:
1. Tight Delivery Deadline: Rejects batching when added stops breach delivery deadlines.
2. Incompatible Products: Rejects grouping ColdChain drugs with Hazmat or Cytotoxic compounds.
3. Pickup Not Ready: Rejects batching orders requiring excessive pickup waiting (>90 mins).
4. Rider Capacity Exceeded: Rejects batching when order count exceeds cargo box limits.
5. Rider Workload Exceeded: Rejects routes exceeding the 120-minute continuous driving limit.
These test cases verify that MEDIROUTE never improves efficiency by violating operational safety constraints.

13. EXPECTED RESULTS
As a 35% progress report, numerical results are not fabricated. Expected outcomes are:
- Measurable reduction in total courier travel distance compared to individual dispatching.
- 100% creation of valid, constraint-compliant delivery batches with zero hard violations.
- Safe rider assignments adhering strictly to box capacity and workload fatigue limits.
- Transparent, auditable log history capturing all operational decisions.
- Demonstrated safety and operational improvement over the unconstrained baseline.

14. FUTURE WORK
Planned development and future enhancements include:
- Testing on larger real-world pharmacy dispatch datasets.
- Route optimization and parallelized solving for larger order pools.
- Broader stakeholder validation trials with dispatchers and safety officers.
- System containerization, field deployment, and pilot testing.
- Improved scalability and real-time dynamic re-batching capabilities.
- Incorporating operational constraints such as live traffic updates and GPS tracking.

15. CONCLUSION
The current 35% implementation establishes the core architectural and algorithmic foundation of MEDIROUTE. The 5-hard-constraint engine, greedy solver, baseline benchmark, SQLite audit system, Streamlit interface, and 14-test-case suite are fully operational. Remaining work will focus on large-scale experimentation, stakeholder validation, performance optimization, and final deployment.

16. REFERENCES
[1] P. Toth & D. Vigo, Eds., Vehicle Routing Problem, SIAM, 2014.
[2] C. Archetti et al., "VRP with time windows for pharmaceutical distribution," Comput. Oper. Res., 2015.
[3] M. Savelsbergh & M. Sol, "General pickup and delivery problem," Transp. Sci., 1995.
[4] T. Vidal et al., "Heuristics for multi-attribute VRP," Eur. J. Oper. Res., 2013.
[5] G. Ghiani et al., Operations Research in Logistics & Supply Chain Management, Wiley, 2004.
[6] M. Solomon, "Algorithms for VRPTW," Oper. Res., 1987.
[7] G. Laporte, "The vehicle routing problem: An overview," Eur. J. Oper. Res., 1992.
"""

with open("final_report.txt", "w", encoding="utf-8") as f:
    f.write(concise_text.strip())

print("Saved file size:", len(concise_text.strip()))
