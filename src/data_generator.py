import random
import math
import sys
from pathlib import Path

# Add root directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np
from typing import List, Tuple, Dict

from config import (
    RANDOM_SEED, NUM_ORDERS, NUM_RIDERS, NUM_PRODUCTS, PHARMACY_DEPOT, DATA_DIR, GENERATED_DATA_DIR
)

from src.models import Product, Order, Rider

# Product Master Templates
PRODUCT_TEMPLATES = [
    {"name": "Insulin Glargine Pen 100U/ml", "temp_sensitive": True, "handling": "ColdChain", "group": "COLD_CHAIN", "incompat": ["HAZMAT", "CYTOTOXIC"]},
    {"name": "COVID-19 MRNA Vaccine Vials", "temp_sensitive": True, "handling": "ColdChain", "group": "COLD_CHAIN", "incompat": ["HAZMAT", "CYTOTOXIC"]},
    {"name": "Biologic Infusion Package (Enbrel)", "temp_sensitive": True, "handling": "ColdChain", "group": "COLD_CHAIN", "incompat": ["HAZMAT", "CYTOTOXIC"]},
    {"name": "Amoxicillin 500mg Oral Suspension", "temp_sensitive": False, "handling": "General", "group": "GENERAL", "incompat": []},
    {"name": "Atorvastatin 20mg Tablets", "temp_sensitive": False, "handling": "General", "group": "GENERAL", "incompat": []},
    {"name": "Metformin 850mg Prolonged Release", "temp_sensitive": False, "handling": "General", "group": "GENERAL", "incompat": []},
    {"name": "Lisinopril 10mg Tablets", "temp_sensitive": False, "handling": "General", "group": "GENERAL", "incompat": []},
    {"name": "Methotrexate 2.5mg Tablets (Cytotoxic)", "temp_sensitive": False, "handling": "Cytotoxic", "group": "CYTOTOXIC", "incompat": ["COLD_CHAIN", "NARCOTIC"]},
    {"name": "Tamoxifen Chemotherapy Agent 20mg", "temp_sensitive": False, "handling": "Cytotoxic", "group": "CYTOTOXIC", "incompat": ["COLD_CHAIN", "NARCOTIC"]},
    {"name": "Morphine Sulfate 10mg/ml Ampoules", "temp_sensitive": False, "handling": "Narcotic", "group": "NARCOTIC", "incompat": ["CYTOTOXIC", "HAZMAT"]},
    {"name": "Oxycodone HCl 15mg Extended Release", "temp_sensitive": False, "handling": "Narcotic", "group": "NARCOTIC", "incompat": ["CYTOTOXIC", "HAZMAT"]},
    {"name": "Medical Alcohol Disinfectant 70%", "temp_sensitive": False, "handling": "Hazmat", "group": "HAZMAT", "incompat": ["COLD_CHAIN", "NARCOTIC"]},
]

STREET_NAMES = [
    "Market St", "Mission St", "Geary Blvd", "Van Ness Ave", "Valencia St",
    "Castro St", "Haight St", "Lombard St", "Columbus Ave", "California St",
    "Howard St", "Folsom St", "Harrison St", "Bryant St", "Brannan St",
    "Divisadero St", "Fillmore St", "Polk St", "Sutter St", "Post St"
]

def generate_products() -> List[Product]:
    products = []
    for i, t in enumerate(PRODUCT_TEMPLATES[:NUM_PRODUCTS]):
        pid = f"PRD-{i+1:03d}"
        p = Product(
            product_id=pid,
            product_name=t["name"],
            temperature_sensitive=t["temp_sensitive"],
            special_handling=t["handling"],
            compatibility_group=t["group"],
            incompatible_groups=t["incompat"]
        )
        products.append(p)
    return products

def generate_riders(seed: int = RANDOM_SEED) -> List[Rider]:
    random.seed(seed)
    riders = []
    rider_names = [
        "Alex Rivera", "Brenda Chen", "Carlos Gomez", "David Miller", "Elena Rostova",
        "Frank Wright", "Grace Kim", "Hassan Ali", "Irene Zhao", "James Wilson",
        "Kavita Patel", "Liam O'Connor", "Maria Santos", "Nathaniel Brown", "Olivia Taylor",
        "Pablo Fernandez", "Quinn Jackson", "Rachel Green", "Samir Khan", "Tina Martinez"
    ]
    for i in range(NUM_RIDERS):
        rid = f"R-{i+1:02d}"
        name = rider_names[i] if i < len(rider_names) else f"Rider {i+1}"
        max_orders = random.choice([4, 5, 5, 6, 6])
        max_workload = float(random.choice([90, 105, 120, 120]))
        r = Rider(
            rider_id=rid,
            name=name,
            maximum_orders=max_orders,
            maximum_workload_minutes=max_workload,
            current_latitude=PHARMACY_DEPOT["latitude"],
            current_longitude=PHARMACY_DEPOT["longitude"],
            shift_start=0,  # 8:00 AM
            shift_end=540,  # 5:00 PM
            status="AVAILABLE"
        )
        riders.append(r)
    return riders

def generate_orders(products: List[Product], seed: int = RANDOM_SEED) -> List[Order]:
    random.seed(seed)
    np.random.seed(seed)
    orders = []

    # Pharmacy coordinates
    base_lat = PHARMACY_DEPOT["latitude"]
    base_lon = PHARMACY_DEPOT["longitude"]

    # 4 distinct geographical clusters around the city
    clusters = [
        (0.02, 0.02),    # North-East
        (-0.02, 0.03),   # South-East
        (-0.03, -0.02),  # South-West
        (0.03, -0.02),   # North-West
        (0.00, 0.00)     # Downtown central
    ]

    for i in range(NUM_ORDERS):
        oid = f"ORD-{i+1:04d}"
        product = random.choice(products)
        
        # Pick spatial cluster + gaussian noise (approx 1-12 km radius)
        c_lat, c_lon = random.choice(clusters)
        lat_offset = np.random.normal(c_lat, 0.015)
        lon_offset = np.random.normal(c_lon, 0.018)
        lat = base_lat + lat_offset
        lon = base_lon + lon_offset

        street_num = random.randint(100, 2500)
        street_name = random.choice(STREET_NAMES)
        loc_name = f"{street_num} {street_name}"

        # Timeline generation (minutes from 8:00 AM start, 0 to 420)
        # Order creation time distributed across morning/afternoon waves
        order_time = int(np.random.exponential(scale=120))
        order_time = min(max(0, order_time), 400)

        # Readiness time (compounding / packaging time)
        prep_time = random.choice([10, 15, 20, 30, 45])
        ready_time = order_time + prep_time

        # Priority & Delivery Deadline
        priority_roll = random.random()
        if priority_roll < 0.20:
            priority = "HIGH"
            window = random.choice([40, 50, 60])
        elif priority_roll < 0.70:
            priority = "MEDIUM"
            window = random.choice([75, 90, 105])
        else:
            priority = "LOW"
            window = random.choice([120, 150, 180])

        promised_delivery_time = ready_time + window
        qty = random.randint(1, 4)

        order = Order(
            order_id=oid,
            product_id=product.product_id,
            product_name=product.product_name,
            customer_location=loc_name,
            latitude=lat,
            longitude=lon,
            order_time=order_time,
            pickup_ready_time=ready_time,
            promised_delivery_time=promised_delivery_time,
            quantity=qty,
            priority=priority,
            special_handling_required=product.special_handling,
            compatibility_group=product.compatibility_group,
            assigned_rider=None,
            status="PENDING"
        )
        orders.append(order)

    # Sort orders chronologically by order_time
    orders.sort(key=lambda x: (x.order_time, x.pickup_ready_time))
    return orders

def save_dataset_to_csv(products: List[Product], riders: List[Rider], orders: List[Order]):
    # Save Products CSV
    df_products = pd.DataFrame([p.to_dict() for p in products])
    df_products.to_csv(DATA_DIR / "products.csv", index=False)
    df_products.to_csv(GENERATED_DATA_DIR / "products.csv", index=False)

    # Save Riders CSV
    df_riders = pd.DataFrame([r.to_dict() for r in riders])
    df_riders.to_csv(DATA_DIR / "riders.csv", index=False)
    df_riders.to_csv(GENERATED_DATA_DIR / "riders.csv", index=False)

    # Save Orders CSV
    df_orders = pd.DataFrame([o.to_dict() for o in orders])
    df_orders.to_csv(DATA_DIR / "orders.csv", index=False)
    df_orders.to_csv(GENERATED_DATA_DIR / "orders.csv", index=False)

    print(f"Dataset successfully generated & saved to '{DATA_DIR}':")
    print(f" - {len(products)} products")
    print(f" - {len(riders)} riders")
    print(f" - {len(orders)} orders")

def load_dataset_from_csv() -> Tuple[List[Product], List[Rider], List[Order]]:
    products_file = DATA_DIR / "products.csv"
    riders_file = DATA_DIR / "riders.csv"
    orders_file = DATA_DIR / "orders.csv"

    if not (products_file.exists() and riders_file.exists() and orders_file.exists()):
        print("CSV files not found. Generating new dataset...")
        products = generate_products()
        riders = generate_riders()
        orders = generate_orders(products)
        save_dataset_to_csv(products, riders, orders)
        return products, riders, orders

    # Load Products
    df_p = pd.read_csv(products_file)
    products = []
    for _, row in df_p.iterrows():
        incompat = [g.strip() for g in str(row["incompatible_groups"]).split(",") if g.strip()]
        products.append(Product(
            product_id=str(row["product_id"]),
            product_name=str(row["product_name"]),
            temperature_sensitive=bool(row["temperature_sensitive"]),
            special_handling=str(row["special_handling"]),
            compatibility_group=str(row["compatibility_group"]),
            incompatible_groups=incompat
        ))

    # Load Riders
    df_r = pd.read_csv(riders_file)
    riders = []
    for _, row in df_r.iterrows():
        riders.append(Rider(
            rider_id=str(row["rider_id"]),
            name=str(row["name"]),
            maximum_orders=int(row["maximum_orders"]),
            maximum_workload_minutes=float(row["maximum_workload_minutes"]),
            current_latitude=float(row["current_latitude"]),
            current_longitude=float(row["current_longitude"]),
            shift_start=int(row["shift_start"]),
            shift_end=int(row["shift_end"]),
            status=str(row.get("status", "AVAILABLE"))
        ))

    # Load Orders
    df_o = pd.read_csv(orders_file)
    orders = []
    for _, row in df_o.iterrows():
        assigned = str(row["assigned_rider"]) if pd.notna(row["assigned_rider"]) and str(row["assigned_rider"]) != "" else None
        orders.append(Order(
            order_id=str(row["order_id"]),
            product_id=str(row["product_id"]),
            product_name=str(row["product_name"]),
            customer_location=str(row["customer_location"]),
            latitude=float(row["latitude"]),
            longitude=float(row["longitude"]),
            order_time=int(row["order_time"]),
            pickup_ready_time=int(row["pickup_ready_time"]),
            promised_delivery_time=int(row["promised_delivery_time"]),
            quantity=int(row["quantity"]),
            priority=str(row["priority"]),
            special_handling_required=str(row["special_handling_required"]),
            compatibility_group=str(row["compatibility_group"]),
            assigned_rider=assigned,
            status=str(row.get("status", "PENDING"))
        ))

    return products, riders, orders

if __name__ == "__main__":
    products = generate_products()
    riders = generate_riders()
    orders = generate_orders(products)
    save_dataset_to_csv(products, riders, orders)
