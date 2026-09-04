import os
from pathlib import Path

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

# Pharmacy Depot Location (Central City Location)
PHARMACY_DEPOT = {
    "name": "Central Metro Pharmacy",
    "address": "100 Health Sciences Plaza",
    "latitude": 37.7749,
    "longitude": -122.4194
}

# Synthetic Data Generation Settings
RANDOM_SEED = 42
NUM_ORDERS = 500
NUM_RIDERS = 20
NUM_PRODUCTS = 12

# Operational Parameters
AVERAGE_SPEED_KMH = 25.0  # Urban delivery rider average speed
SERVICE_TIME_PER_STOP_MIN = 5.0  # Time to handover package at customer location
TRAVEL_BUFFER_MIN = 10.0  # Safety buffer added to travel time estimations
MAX_WORKLOAD_SAFETY_LIMIT_MIN = 120.0  # Max continuous shift workload minutes per batch route
DEFAULT_MAX_RIDER_CAPACITY = 5  # Max orders per batch per rider

# File Paths
DATA_DIR = BASE_DIR / "data"
GENERATED_DATA_DIR = DATA_DIR / "generated"
DATABASE_DIR = BASE_DIR / "database"
DB_PATH = DATABASE_DIR / "pharmacy.db"
DOCS_DIR = BASE_DIR / "docs"
PRESENTATION_DIR = BASE_DIR / "presentation"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
GENERATED_DATA_DIR.mkdir(exist_ok=True)
DATABASE_DIR.mkdir(exist_ok=True)
DOCS_DIR.mkdir(exist_ok=True)
PRESENTATION_DIR.mkdir(exist_ok=True)
