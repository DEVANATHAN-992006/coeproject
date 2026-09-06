with open("report_final_text_8k.txt", "r", encoding="utf-8") as f:
    t = f.read()

# Let's compress phrasing across sections:

# Abstract & Intro
t = t.replace(
"Pharmacy delivery batching reduces courier distance and costs but risks missed deadlines, product contamination, depot delays, overloaded cargo boxes, and rider fatigue. This 35% progress report presents MEDIROUTE, a constraint-aware control center optimizing delivery batching while enforcing five hard constraints: deadlines (with buffer), product compatibility, pickup readiness, rider capacity, and rider workload limits. At the 35% milestone, the database, 5-constraint engine, greedy solver, baseline benchmark, SQLite audit logger, Streamlit UI, and a 14-test-case suite are implemented. Expected outcomes include reduced delivery distance and guaranteed constraint compliance.",
"Pharmacy delivery batching lowers courier distance and costs but risks missed deadlines, product contamination, depot delays, overloaded cargo boxes, and rider fatigue. This 35% progress report presents MEDIROUTE, a constraint-aware control center optimizing batching while enforcing five hard constraints: deadlines (with buffer), product compatibility, pickup readiness, rider capacity, and rider workload limits. At the 35% milestone, the database, 5-constraint engine, greedy solver, baseline benchmark, SQLite audit logger, Streamlit UI, and a 14-test-case suite are implemented. Expected outcomes include reduced delivery distance and guaranteed constraint compliance."
)

t = t.replace(
"Pharmacy last-mile delivery is time-critical; delays directly impact patient health. Pharmacies batch prescription orders to minimize delivery mileage and operating costs. Unlike e-commerce, pharmacy delivery involves promised delivery windows, handling exclusions, packaging limits, and preparation delays. Intelligent logistics systems must balance route efficiency with strict compliance to operational safety boundaries.",
"Pharmacy last-mile delivery is time-critical; delays directly impact patient health. Pharmacies batch prescription orders to minimize delivery mileage and operating costs. Unlike e-commerce, pharmacy delivery involves promised windows, product handling exclusions, packaging limits, and compounding delays. Intelligent logistics systems must balance route efficiency with strict compliance to operational safety boundaries."
)

# Problem Statement & Objectives
t = t.replace(
"Distance-only batching focuses purely on proximity, ignoring safety rules. This causes six failure modes:\n- Delivery Deadlines: Extra stops delay deliveries, breaching promised time windows.\n- Product Compatibility: Grouping ColdChain drugs with Hazmat or Cytotoxic compounds risks contamination.\n- Pickup Readiness: Dispatching couriers before compounding completes causes idle depot waiting.\n- Rider Capacity: Exceeding cargo box limits risks package damage or loss.\n- Rider Workload: Excessively long routes exceed driver fatigue limits (capped at 120 minutes continuous driving).\n- Unnecessary Distance: Uncoordinated individual dispatches create redundant travel mileage.",
"Distance-only batching focuses purely on proximity, ignoring safety rules. This causes six failure modes:\n- Delivery Deadlines: Extra stops delay deliveries, breaching promised time windows.\n- Product Compatibility: Grouping ColdChain drugs with Hazmat or Cytotoxic compounds risks contamination.\n- Pickup Readiness: Dispatching couriers before compounding completes causes idle depot waiting.\n- Rider Capacity: Exceeding cargo box limits risks package damage or loss.\n- Rider Workload: Excessively long routes exceed fatigue limits (capped at 120 minutes continuous driving).\n- Unnecessary Distance: Uncoordinated individual dispatches create redundant travel mileage."
)

t = t.replace(
"Objectives of MEDIROUTE:\n- Create feasible delivery batches by grouping compatible prescription orders.\n- Enforce five hard operational constraints (deadlines, product groups, pickup readiness, rider capacity, rider workload).\n- Assign orders to riders safely without exceeding physical or workload limits.\n- Reduce delivery distance compared to an unconstrained baseline.\n- Maintain an auditable record of batching decisions and rejection rationale.\n- Evaluate system robustness using realistic failure-case test scenarios.",
"Objectives of MEDIROUTE:\n- Create feasible delivery batches by grouping compatible prescription orders.\n- Enforce five hard operational constraints (deadlines, product groups, pickup readiness, rider capacity, rider workload).\n- Assign orders to riders safely without exceeding physical or workload limits.\n- Reduce delivery distance compared to an unconstrained baseline.\n- Maintain an auditable record of batching decisions and rejection rationale.\n- Evaluate system robustness using realistic failure-case test scenarios."
)

# Existing System & Proposed System
t = t.replace(
"Conventional pharmacy delivery relies on individual dispatching or manual distance-only batching. Individual dispatching requires separate round trips per order, causing high mileage, fuel waste, and low fleet utilization. Manual distance-based batching clusters orders by proximity alone without verifying stop delays, product exclusions, compounding readiness, or courier fatigue caps, causing frequent deadline breaches.",
"Conventional pharmacy delivery relies on individual dispatching or manual distance-only batching. Individual dispatching requires separate round trips per order, causing high mileage, fuel waste, and low fleet utilization. Manual distance-based batching clusters orders by proximity alone without verifying stop delays, product exclusions, compounding readiness, or fatigue caps, causing frequent deadline breaches."
)

t = t.replace(
"MEDIROUTE is a constraint-aware control center prioritizing orders by urgency, evaluating candidate insertions against five hard constraints, and optimizing stop sequences. If any constraint is violated, the system rejects the insertion, logs a diagnostic reason, and evaluates alternative assignments. Key modules include order management, constraint validation, priority greedy batching, rider assignment, route planning, SQLite audit trail, baseline benchmarking, and failure testing.",
"MEDIROUTE is a constraint-aware control center prioritizing orders by urgency, evaluating candidate insertions against five hard constraints, and optimizing stop sequences. If any constraint is violated, the system rejects the insertion, logs a diagnostic reason, and evaluates alternative assignments. Key modules include order management, constraint validation, priority greedy batching, rider assignment, route planning, SQLite audit trail, baseline benchmarking, and failure testing."
)

# Methodology & System Modules
t = t.replace(
"Workflow: Orders Ingestion -> Priority Sorting -> Constraint Verification -> Feasible Batch Creation -> Rider Assignment -> TSP Route Sequencing -> Validation -> Audit Logging.\nHard constraints (capacity, product compatibility, pickup readiness delay, delivery deadlines with a 10-minute safety buffer, and rider workload limits) are checked BEFORE a batch is considered valid. Only feasible insertions yielding net distance savings are accepted.",
"Workflow: Orders Ingestion -> Priority Sorting -> Constraint Verification -> Feasible Batch Creation -> Rider Assignment -> TSP Route Sequencing -> Validation -> Audit Logging.\nHard constraints (capacity, product compatibility, pickup readiness delay, delivery deadlines with a 10-minute safety buffer, and rider workload limits) are checked BEFORE a batch is considered valid. Only feasible insertions yielding net distance savings are accepted."
)

t = t.replace(
"- Overview: Executive dashboard displaying orders, active batches, and system status.\n- Orders: Ingests and manages prescription orders, priorities, product types, and deadlines.\n- Dispatch Planning: Formulates constraint-compliant plans using priority greedy solving.\n- Routes: Generates stop sequences and timelines using exact TSP permutations.\n- Performance/Baseline Comparison: Benchmarks optimized plans against an unconstrained baseline.\n- Constraint Validation: Isolates and executes the 5 hard constraint checkers.\n- Audit Trail: Log viewer for searching transaction histories and rejection reasons.\n- Stakeholder Feedback: Captures survey feedback metrics.",
"- Overview: Dashboard displaying orders, active batches, and system status.\n- Orders: Manages prescription orders, priorities, product types, and deadlines.\n- Dispatch Planning: Formulates constraint-compliant plans using priority greedy solving.\n- Routes: Generates stop sequences and timelines using exact TSP permutations.\n- Performance/Baseline Comparison: Benchmarks plans against an unconstrained baseline.\n- Constraint Validation: Executes the 5 hard constraint checkers.\n- Audit Trail: Log viewer for searching transaction histories and rejection reasons.\n- Stakeholder Feedback: Captures survey feedback metrics."
)

# Technology & Status
t = t.replace(
"- Python: Core language for logic, constraints, and solver.\n- Streamlit: Web framework for interactive UI.\n- SQLite: Database for persistent storage and audit logs.\n- Pandas: Data manipulation and tabular analysis.\n- Plotly: Interactive charting and visualization.\n- Pytest: Automated testing framework for unit and failure tests.",
"- Python: Core language for logic, constraints, and solver.\n- Streamlit: Web framework for interactive UI.\n- SQLite: Database for persistent storage and audit logs.\n- Pandas: Data manipulation and tabular analysis.\n- Plotly: Interactive charting and visualization.\n- Pytest: Automated testing framework for unit and failure tests."
)

t = t.replace(
"Work completed at the 35% milestone:\n- Functional Streamlit Web Application with an 8-module control center UI.\n- Database & Order Handling using SQLite (pharmacy.db) and synthetic dataset (500 orders, 20 riders, 30 products).\n- Baseline & Constraint-Aware Batching Engines for comparative evaluation.\n- 5-Hard-Constraint Engine validating capacity, workload, product compatibility, pickup readiness, and deadlines.\n- Route Sequencing & Timeline Visualization using exact TSP permutations (n <= 6).\n- Immutable Audit Logging tracking plan initializations, state changes, and rejection reasons.\n- Failure-Case Simulator evaluating mandatory edge cases.\n- Control Center UI Redesign for visual dispatch management.\nSystem correctness is verified by an automated Pytest suite containing 14 test cases (all pass cleanly).",
"Work completed at the 35% milestone:\n- Streamlit Web Application with an 8-module control center UI.\n- Database & Order Handling using SQLite (pharmacy.db) and synthetic data (500 orders, 20 riders, 30 products).\n- Baseline & Constraint-Aware Batching Engines for evaluation.\n- 5-Hard-Constraint Engine validating capacity, workload, product compatibility, pickup readiness, and deadlines.\n- Route Sequencing & Timeline Visualization using exact TSP permutations (n <= 6).\n- Immutable Audit Logging tracking plan initializations, state changes, and rejection reasons.\n- Failure-Case Simulator evaluating mandatory edge cases.\n- Control Center UI Redesign for visual dispatch management.\nSystem correctness is verified by an automated Pytest suite containing 14 test cases (all pass)."
)

# Failure Case Validation, Expected Results, Future Work, Conclusion, References
t = t.replace(
"The system is validated against five failure scenarios:\n1. Tight Delivery Deadline: Rejects batching when added stops breach deadlines.\n2. Incompatible Products: Rejects grouping ColdChain drugs with Hazmat or Cytotoxic compounds.\n3. Pickup Not Ready: Rejects batching orders requiring excessive pickup waiting (>90 mins).\n4. Rider Capacity Exceeded: Rejects batching when order count exceeds cargo box limits.\n5. Rider Workload Exceeded: Rejects routes exceeding the 120-minute continuous driving limit.\nThese test cases verify that MEDIROUTE never improves efficiency by violating safety constraints.",
"The system is validated against five failure scenarios:\n1. Tight Delivery Deadline: Rejects batching when added stops breach deadlines.\n2. Incompatible Products: Rejects grouping ColdChain drugs with Hazmat or Cytotoxic compounds.\n3. Pickup Not Ready: Rejects batching orders requiring excessive pickup waiting (>90 mins).\n4. Rider Capacity Exceeded: Rejects batching when order count exceeds box limits.\n5. Rider Workload Exceeded: Rejects routes exceeding the 120-minute continuous driving limit.\nThese test cases verify that MEDIROUTE never improves efficiency by violating safety constraints."
)

t = t.replace(
"As a 35% progress report, numerical results are not fabricated. Expected outcomes are:\n- Reduction in total courier travel distance compared to individual dispatching.\n- Creation of valid, constraint-compliant delivery batches with zero hard violations.\n- Safe rider assignments adhering to box capacity and workload fatigue limits.\n- Transparent, auditable log history capturing all operational decisions.\n- Demonstrated safety and operational improvement over the baseline.",
"As a 35% progress report, numerical results are not fabricated. Expected outcomes are:\n- Reduction in courier travel distance compared to individual dispatching.\n- Creation of valid, constraint-compliant delivery batches with zero hard violations.\n- Safe rider assignments adhering to box capacity and workload fatigue limits.\n- Transparent, auditable log history capturing operational decisions.\n- Demonstrated safety and operational improvement over the baseline."
)

t = t.replace(
"Planned development and future enhancements include:\n- Testing on larger real-world pharmacy datasets.\n- Route optimization and parallelized solving for larger order pools.\n- Stakeholder validation trials with dispatchers and safety officers.\n- System containerization, field deployment, and pilot testing.\n- Improved scalability and real-time dynamic re-batching.\n- Incorporating live traffic updates and GPS tracking.",
"Planned development and future enhancements include:\n- Testing on larger real-world pharmacy datasets.\n- Route optimization and parallelized solving for larger order pools.\n- Stakeholder validation trials with dispatchers and safety officers.\n- System containerization, field deployment, and pilot testing.\n- Improved scalability and real-time dynamic re-batching.\n- Incorporating live traffic updates and GPS tracking."
)

t = t.replace(
"The current 35% implementation establishes the core foundation of MEDIROUTE. The 5-hard-constraint engine, greedy solver, baseline benchmark, SQLite audit system, Streamlit UI, and 14-test-case suite are operational. Remaining work focuses on large-scale experimentation, stakeholder validation, performance optimization, and final deployment.",
"The current 35% implementation establishes the core foundation of MEDIROUTE. The 5-hard-constraint engine, greedy solver, baseline benchmark, SQLite audit system, Streamlit UI, and 14-test-case suite are operational. Remaining work focuses on large-scale experimentation, stakeholder validation, performance optimization, and final deployment."
)

t = t.replace(
"[1] P. Toth & D. Vigo, Vehicle Routing Problem, SIAM, 2014.\n[2] C. Archetti et al., \"VRP with time windows for pharmaceutical distribution,\" Comput. Oper. Res., 2015.\n[3] M. Savelsbergh & M. Sol, \"General pickup and delivery problem,\" Transp. Sci., 1995.\n[4] T. Vidal et al., \"Heuristics for multi-attribute VRP,\" Eur. J. Oper. Res., 2013.\n[5] G. Ghiani et al., Operations Research in Logistics & Supply Chain Management, Wiley, 2004.\n[6] M. Solomon, \"Algorithms for VRPTW,\" Oper. Res., 1987.\n[7] G. Laporte, \"The vehicle routing problem: An overview,\" Eur. J. Oper. Res., 1992.",
"[1] P. Toth & D. Vigo, Vehicle Routing Problem, SIAM, 2014.\n[2] C. Archetti et al., \"VRP with time windows for pharmaceutical distribution,\" Comput. Oper. Res., 2015.\n[3] M. Savelsbergh & M. Sol, \"General pickup and delivery problem,\" Transp. Sci., 1995.\n[4] T. Vidal et al., \"Heuristics for multi-attribute VRP,\" Eur. J. Oper. Res., 2013.\n[5] G. Ghiani et al., Operations Research in Logistics & Supply Chain Management, Wiley, 2004.\n[6] M. Solomon, \"Algorithms for VRPTW,\" Oper. Res., 1987.\n[7] G. Laporte, \"The vehicle routing problem: An overview,\" Eur. J. Oper. Res., 1992."
)

print("Updated len:", len(t))

with open("report_final_text_8k.txt", "w", encoding="utf-8") as f:
    f.write(t)
