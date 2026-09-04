import sys
from pathlib import Path
import json
import pandas as pd
import matplotlib.pyplot as plt

# Add root project path to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

from src.data_generator import load_dataset_from_csv
from src.evaluation import run_comparative_experiment
from src.constraints import validate_batch_constraints
from src.models import Order, Rider, Product
from config import PHARMACY_DEPOT

def execute_notebook_experiment():
    print("=== Running Pharmacy Delivery Batching Experiment ===")
    
    # 1. Load Data
    products, riders, orders = load_dataset_from_csv()
    product_map = {p.product_id: p for p in products}

    print(f"Loaded {len(orders)} orders, {len(riders)} riders, {len(products)} products.")

    # 2. Run Comparative Benchmark
    exp_results = run_comparative_experiment(
        orders=orders,
        riders=riders,
        product_map=product_map,
        current_time_min=0.0,
        target_distance_saved_pct=10.0
    )

    print("\n=== Experiment Comparison Table ===")
    print(exp_results["comparison_table"].to_string(index=False))

    print(f"\nTarget Saved %: {exp_results['target_pct']}%")
    print(f"Measured Saved %: {exp_results['distance_saved_pct']:.2f}%")
    print(f"Evaluation: {exp_results['explanation']}")

    # 3. Create Plots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Distance Comparison
    metrics = ['Baseline', 'Constraint-Aware']
    distances = [exp_results['baseline_metrics']['total_distance_km'], exp_results['optimized_metrics']['total_distance_km']]
    ax1.bar(metrics, distances, color=['#e74c3c', '#2ecc71'])
    ax1.set_ylabel('Total Distance (km)')
    ax1.set_title('Total Delivery Distance Comparison')
    for i, v in enumerate(distances):
        ax1.text(i, v + 20, f"{v:.1f} km", ha='center', fontweight='bold')

    # Violations Comparison
    violations_base = exp_results['baseline_metrics']['late_deliveries'] + exp_results['baseline_metrics']['product_violations'] + exp_results['baseline_metrics']['pickup_violations'] + exp_results['baseline_metrics']['capacity_violations'] + exp_results['baseline_metrics']['workload_violations']
    violations_opt = exp_results['optimized_metrics']['late_deliveries'] + exp_results['optimized_metrics']['product_violations'] + exp_results['optimized_metrics']['pickup_violations'] + exp_results['optimized_metrics']['capacity_violations'] + exp_results['optimized_metrics']['workload_violations']
    
    ax2.bar(metrics, [violations_base, violations_opt], color=['#e74c3c', '#2ecc71'])
    ax2.set_ylabel('Total Constraint Violations')
    ax2.set_title('Constraint Violations Count')
    for i, v in enumerate([violations_base, violations_opt]):
        ax2.text(i, v + 0.5, str(v), ha='center', fontweight='bold')

    plt.tight_layout()
    chart_path = Path(__file__).resolve().parent / "experiment_charts.png"
    plt.savefig(chart_path)
    print(f"\nSaved experiment plot to '{chart_path}'")

    return exp_results

if __name__ == "__main__":
    execute_notebook_experiment()
