import time
import sqlite3
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from config import PHARMACY_DEPOT, DATA_DIR, DB_PATH
from src.models import Order
from src.routing import exact_permutation_tsp, clarke_wright_savings_tsp


def init_benchmark_database():
    """
    Initializes a dedicated routing_benchmark table in SQLite.
    Keeps benchmark data strictly separate from production audit logs.
    """
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS routing_benchmark (
            benchmark_id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_timestamp TEXT NOT NULL,
            num_stops INTEGER NOT NULL,
            routing_method TEXT NOT NULL,
            route_distance_km REAL NOT NULL,
            execution_time_ms REAL NOT NULL,
            optimality_gap_pct REAL
        )
    """)
    conn.commit()
    conn.close()


def run_routing_benchmark(
    orders: List[Order],
    depot_lat: float = PHARMACY_DEPOT["latitude"],
    depot_lon: float = PHARMACY_DEPOT["longitude"],
    test_sizes: Optional[List[int]] = None,
    exact_max_n: int = 6,
    save_to_db: bool = True,
    save_to_csv: bool = True
) -> pd.DataFrame:
    """
    Executes a real empirical scalability benchmark comparing Exact TSP vs Clarke-Wright Savings
    using identical order locations.
    
    Benchmark design:
    - Tests practical batch sizes (default: 3, 4, 5, 6, 8, 10, 15, 20).
    - For n <= exact_max_n: runs both Exact TSP and Clarke-Wright on the identical stop subset.
      Computes the true optimality gap: ((CW_dist - Exact_dist) / Exact_dist) * 100.
    - For n > exact_max_n: runs Clarke-Wright only, avoiding factorial explosion.
      Optimality gap is recorded as None (not applicable since true optimum is unknown).
    - Measures real route distance and execution time using high-precision time.perf_counter().
    - Never uses hard-coded or fabricated metrics.
    """
    if test_sizes is None:
        test_sizes = [3, 4, 5, 6, 8, 10, 15, 20]

    # Filter test sizes that can be fulfilled by the available orders
    valid_sizes = [n for n in test_sizes if n <= len(orders)]
    if not valid_sizes and orders:
        valid_sizes = [len(orders)]

    results: List[Dict[str, Any]] = []
    run_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for n in valid_sizes:
        # Guarantee identical input locations for comparison
        subset = list(orders[:n])

        exact_dist = None
        exact_time_ms = None

        # 1. Run Exact TSP if n <= exact_max_n
        if n <= exact_max_n:
            t0 = time.perf_counter()
            _, exact_dist = exact_permutation_tsp(
                subset, depot_lat, depot_lon, include_return_to_depot=True
            )
            t1 = time.perf_counter()
            exact_time_ms = (t1 - t0) * 1000.0

            results.append({
                "num_stops": n,
                "routing_strategy": "Exact TSP",
                "route_distance_km": round(exact_dist, 3),
                "execution_time_ms": round(exact_time_ms, 3),
                "optimality_gap_pct": 0.0  # Exact TSP is the optimal reference
            })

        # 2. Run Clarke-Wright Savings Heuristic
        t0 = time.perf_counter()
        _, cw_dist = clarke_wright_savings_tsp(
            subset, depot_lat, depot_lon, include_return_to_depot=True
        )
        t1 = time.perf_counter()
        cw_time_ms = (t1 - t0) * 1000.0

        # Calculate optimality gap ONLY where mathematically meaningful (n <= exact_max_n)
        gap_pct = None
        if exact_dist is not None and exact_dist > 0:
            gap_pct = round(((cw_dist - exact_dist) / exact_dist) * 100.0, 2)

        results.append({
            "num_stops": n,
            "routing_strategy": "Clarke-Wright Savings",
            "route_distance_km": round(cw_dist, 3),
            "execution_time_ms": round(cw_time_ms, 3),
            "optimality_gap_pct": gap_pct
        })

    df = pd.DataFrame(results)

    # Persist results without polluting production audit log
    if save_to_csv:
        csv_path = DATA_DIR / "routing_benchmark.csv"
        df.to_csv(csv_path, index=False)

    if save_to_db:
        init_benchmark_database()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        for _, row in df.iterrows():
            cursor.execute("""
                INSERT INTO routing_benchmark (
                    run_timestamp, num_stops, routing_method,
                    route_distance_km, execution_time_ms, optimality_gap_pct
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                run_timestamp,
                int(row["num_stops"]),
                str(row["routing_strategy"]),
                float(row["route_distance_km"]),
                float(row["execution_time_ms"]),
                float(row["optimality_gap_pct"]) if pd.notna(row["optimality_gap_pct"]) else None
            ))
        conn.commit()
        conn.close()

    return df


def load_latest_benchmark_results() -> Optional[pd.DataFrame]:
    """
    Loads benchmark results from data/routing_benchmark.csv or SQLite table.
    """
    csv_path = DATA_DIR / "routing_benchmark.csv"
    if csv_path.exists():
        try:
            return pd.read_csv(csv_path)
        except Exception:
            pass

    init_benchmark_database()
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query("SELECT * FROM routing_benchmark ORDER BY benchmark_id DESC", conn)
        conn.close()
        return df if not df.empty else None
    except Exception:
        conn.close()
        return None
