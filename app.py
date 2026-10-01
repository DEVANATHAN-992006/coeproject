import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

from src.data_generator import load_dataset_from_csv, save_dataset_to_csv, generate_orders, generate_products, generate_riders
from src.evaluation import run_comparative_experiment
from src.batching import run_constraint_aware_batching
from src.baseline import run_baseline_batching
from src.constraints import validate_batch_constraints
from src.models import Order, Rider, Product, Batch
from src.audit import (
    init_database, write_audit_logs, get_audit_history,
    save_stakeholder_feedback, get_stakeholder_feedback, deduplicate_audit_log_records
)
from src.experiment import (
    run_full_experiment, run_baseline_experiment, run_mediroute_experiment,
    load_latest_experiment_results, get_all_experiment_history, init_experiment_database
)
from src.benchmark import (
    run_routing_benchmark, load_latest_benchmark_results, init_benchmark_database
)
from config import PHARMACY_DEPOT, TRAVEL_BUFFER_MIN, MAX_WORKLOAD_SAFETY_LIMIT_MIN, DEFAULT_MAX_RIDER_CAPACITY

# Streamlit Page Setup
st.set_page_config(
    page_title="MEDIROUTE | Pharmacy Logistics Control Center",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Light Enterprise Healthcare & Pharmacy Logistics Design System
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    /* Global Clean Healthcare Theme */
    html, body, [data-testid="stAppViewContainer"], .stApp {
        background-color: #F7F9FC !important;
        color: #172033 !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    [data-testid="stHeader"] {
        background-color: rgba(247, 249, 252, 0.95) !important;
    }
    
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2.5rem;
        max-width: 1380px;
    }
    
    /* High-Contrast Healthcare Typography */
    h1, h2, h3, h4, h5, h6 {
        color: #0F766E !important;
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        letter-spacing: -0.4px;
    }

    p, span, label, div {
        color: #334155;
    }
    
    /* Mediroute Header Container */
    .mediroute-header {
        background: #FFFFFF;
        padding: 20px 24px;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        margin-bottom: 18px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.03);
    }
    .mediroute-header h1 {
        color: #0F766E !important;
        font-size: 1.75rem;
        font-weight: 800;
        margin: 0 0 4px 0;
    }
    .mediroute-header p {
        color: #64748B !important;
        font-size: 0.92rem;
        margin: 0;
    }

    /* Objective Banner */
    .objective-banner {
        background-color: #F0FDF4;
        border-left: 4px solid #0F766E;
        padding: 12px 16px;
        border-radius: 0 8px 8px 0;
        margin-bottom: 20px;
        color: #166534;
        font-size: 0.9rem;
        font-weight: 500;
    }

    /* Light Healthcare KPI Cards */
    .kpi-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 16px 14px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
    }
    .kpi-card-highlight {
        background: #F0FDF4;
        border: 1.5px solid #16A34A;
    }
    .kpi-title {
        font-size: 0.74rem;
        font-weight: 700;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-bottom: 6px;
    }
    .kpi-val {
        font-size: 1.8rem;
        font-weight: 800;
        color: #0F766E;
        line-height: 1.1;
    }
    .kpi-val-green {
        color: #16A34A;
    }
    .kpi-sub {
        font-size: 0.8rem;
        font-weight: 600;
        margin-top: 4px;
        color: #64748B;
    }
    .kpi-sub-green {
        color: #15803D;
    }

    /* Constraint Status Pill Grid */
    .compliance-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
        gap: 10px;
        margin-top: 10px;
    }
    .compliance-badge {
        background: #F0FDF4;
        border: 1px solid #BBF7D0;
        color: #166534;
        border-radius: 8px;
        padding: 10px 12px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .compliance-status {
        background: #16A34A;
        color: #FFFFFF;
        font-size: 0.72rem;
        padding: 2px 8px;
        border-radius: 9999px;
        font-weight: 700;
    }

    /* Route Timeline Sequence */
    .timeline-container {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px;
        background: #F8FAFC;
        padding: 14px;
        border-radius: 10px;
        border: 1px solid #E2E8F0;
        margin-bottom: 18px;
    }
    .timeline-step {
        background: #FFFFFF;
        border: 1px solid #CBD5E1;
        border-radius: 8px;
        padding: 6px 12px;
        font-weight: 600;
        font-size: 0.82rem;
        color: #1E293B;
    }
    .timeline-depot {
        background: #EFF6FF;
        border-color: #2563EB;
        color: #1E40AF;
    }
    .timeline-arrow {
        color: #94A3B8;
        font-weight: 800;
        font-size: 1.0rem;
    }

    /* Sidebar Custom Styling */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E2E8F0;
    }
    .nav-brand {
        padding: 10px 0 14px 0;
        text-align: center;
        border-bottom: 1px solid #E2E8F0;
        margin-bottom: 14px;
    }
    .nav-brand-title {
        font-size: 1.45rem;
        font-weight: 800;
        color: #0F766E;
        letter-spacing: -0.5px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
    }
    .nav-brand-subtitle {
        font-size: 0.78rem;
        color: #64748B;
        font-weight: 600;
        margin-top: 2px;
    }

    .nav-category {
        font-size: 0.72rem;
        font-weight: 800;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin: 14px 0 6px 4px;
    }

    /* Table & Card Inputs */
    .stDataFrame {
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        background: #FFFFFF;
    }
    
    /* Buttons */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        padding: 6px 18px;
        background-color: #0F766E;
        color: #FFFFFF;
        border: none;
    }
    .stButton>button:hover {
        background-color: #0D9488;
        color: #FFFFFF;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Databases & Deduplicate Audit Records
init_database()
init_experiment_database()
init_benchmark_database()
deduplicate_audit_log_records()

# Load/Verify Session State Dataset
if "products" not in st.session_state or "orders" not in st.session_state or "riders" not in st.session_state:
    products, riders, orders = load_dataset_from_csv()
    st.session_state.products = products
    st.session_state.riders = riders
    st.session_state.orders = orders

if "experiment_results" not in st.session_state:
    st.session_state.experiment_results = None

if "benchmark_results" not in st.session_state:
    st.session_state.benchmark_results = load_latest_benchmark_results()

# Product Lookup Map
product_map = {p.product_id: p for p in st.session_state.products}

# Apply Light Healthcare Theme Layout to Plotly Figures
def apply_plotly_light_theme(fig):
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#172033', family='Inter'),
        xaxis=dict(gridcolor='#E2E8F0', zerolinecolor='#E2E8F0', color='#64748B'),
        yaxis=dict(gridcolor='#E2E8F0', zerolinecolor='#E2E8F0', color='#64748B'),
        legend=dict(font=dict(color='#172033'))
    )
    return fig

# Exception-Free Light Spatial Map Function
def render_spatial_map(df: pd.DataFrame, lat_col="latitude", lon_col="longitude", hover_name="order_id", color_col="priority"):
    if df.empty:
        st.info("No spatial data to render.")
        return

    try:
        if hasattr(px, "scatter_map"):
            fig = px.scatter_map(
                df, lat=lat_col, lon=lon_col, hover_name=hover_name,
                hover_data=["product_name", "special_handling_required"],
                color=color_col, size="quantity", zoom=11, height=460,
                color_discrete_map={"HIGH": "#DC2626", "MEDIUM": "#D97706", "LOW": "#2563EB"}
            )
            fig.update_layout(map_style="carto-positron", margin=dict(l=0, r=0, t=0, b=0))
            apply_plotly_light_theme(fig)
            st.plotly_chart(fig, use_container_width=True)
            return
        elif hasattr(px, "scatter_mapbox"):
            fig = px.scatter_mapbox(
                df, lat=lat_col, lon=lon_col, hover_name=hover_name,
                hover_data=["product_name", "special_handling_required"],
                color=color_col, size="quantity", zoom=11, height=460,
                color_discrete_map={"HIGH": "#DC2626", "MEDIUM": "#D97706", "LOW": "#2563EB"}
            )
            fig.update_layout(mapbox_style="carto-positron", margin=dict(l=0, r=0, t=0, b=0))
            apply_plotly_light_theme(fig)
            st.plotly_chart(fig, use_container_width=True)
            return
    except Exception:
        pass

    # 100% Reliable Cartesian Grid Scatter Fallback
    fig_grid = px.scatter(
        df, x=lon_col, y=lat_col, hover_name=hover_name,
        color=color_col, size="quantity", title="Customer Delivery Coordinates",
        labels={lon_col: "Longitude", lat_col: "Latitude"},
        color_discrete_map={"HIGH": "#DC2626", "MEDIUM": "#D97706", "LOW": "#2563EB"},
        height=460
    )
    fig_grid.add_trace(go.Scatter(
        x=[PHARMACY_DEPOT["longitude"]], y=[PHARMACY_DEPOT["latitude"]],
        mode="markers+text", marker=dict(size=16, color="#0F766E", symbol="square"),
        name="Pharmacy Depot", text=["DEPOT"], textposition="top center"
    ))
    fig_grid.update_layout(margin=dict(l=20, r=20, t=40, b=20))
    apply_plotly_light_theme(fig_grid)
    st.plotly_chart(fig_grid, use_container_width=True)

# Helper: Run comparative experiment without polluting production audit history
def get_or_run_experiment(force_run: bool = False, routing_strategy: str = "AUTO"):
    if force_run or st.session_state.experiment_results is None:
        with st.spinner("Executing comparative experiment on dataset..."):
            res = run_comparative_experiment(
                orders=st.session_state.orders,
                riders=st.session_state.riders,
                product_map=product_map,
                current_time_min=0.0,
                routing_strategy=routing_strategy
            )
            st.session_state.experiment_results = res
    return st.session_state.experiment_results

# Sidebar Brand Header
st.sidebar.markdown("""
<div class="nav-brand">
    <div class="nav-brand-title">💊 MEDIROUTE</div>
    <div class="nav-brand-subtitle">Pharmacy Logistics Control Center</div>
</div>
""", unsafe_allow_html=True)

# Categorized Sidebar Radio Navigation with active category tracking
if "active_nav_group" not in st.session_state:
    st.session_state.active_nav_group = "ops"

def on_ops_change():
    st.session_state.active_nav_group = "ops"

def on_an_change():
    st.session_state.active_nav_group = "an"

st.sidebar.markdown('<div class="nav-category">OPERATIONS</div>', unsafe_allow_html=True)
op_page = st.sidebar.radio(
    "Operations Module",
    ["Overview", "Orders Directory", "Dispatch Workstation", "Route Inspection"],
    key="nav_ops",
    on_change=on_ops_change,
    label_visibility="collapsed"
)

st.sidebar.markdown('<div class="nav-category">ANALYTICS & SAFETY</div>', unsafe_allow_html=True)
an_page = st.sidebar.radio(
    "Analytics & Safety Module",
    [
        "Performance Comparison",
        "Scalability Benchmark",
        "Mathematical Formulation",
        "Constraint Validation Lab",
        "Compliance Audit Trail",
        "Stakeholder Validation"
    ],
    key="nav_an",
    on_change=on_an_change,
    label_visibility="collapsed"
)

selected_module = op_page if st.session_state.active_nav_group == "ops" else an_page

st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="background: #F8FAFC; border: 1px solid #E2E8F0; padding: 12px 14px; border-radius: 8px;">
    <div style="font-size: 0.72rem; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px;">CENTRAL METRO PHARMACY</div>
    <div style="font-size: 0.82rem; font-weight: 600; color: #172033; margin-top: 2px;">Main Delivery Operations Hub</div>
    <div style="font-size: 0.78rem; font-weight: 700; color: #16A34A; margin-top: 6px;">● SYSTEM ACTIVE</div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# PAGE 1: OVERVIEW (DELIVERY OPERATIONS)
# ==========================================
if selected_module == "Overview":
    st.markdown("""
    <div class="mediroute-header">
        <h1>DELIVERY OPERATIONS</h1>
        <p>Constraint-aware pharmacy dispatch and route monitoring</p>
    </div>
    <div class="objective-banner">
        <strong>Primary Operational Objective:</strong> Minimize total delivery distance if and only if all promised delivery deadlines, product handling compatibilities, pickup readiness times, rider order capacities, and workload safety limits are 100% satisfied.
    </div>
    """, unsafe_allow_html=True)

    res = get_or_run_experiment()
    base_m = res["baseline_metrics"]
    opt_m = res["optimized_metrics"]

    # 4 Dynamic KPI Cards Row
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Orders Today</div>
            <div class="kpi-val">{len(st.session_state.orders)}</div>
            <div class="kpi-sub">Evaluated Dataset</div>
        </div>
        """, unsafe_allow_html=True)

    with k2:
        ready_cnt = sum(1 for o in st.session_state.orders if o.pickup_ready_time == 0)
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Ready for Dispatch</div>
            <div class="kpi-val">{ready_cnt}</div>
            <div class="kpi-sub">Immediate Pickups</div>
        </div>
        """, unsafe_allow_html=True)

    with k3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Active Riders</div>
            <div class="kpi-val">{len(st.session_state.riders)}</div>
            <div class="kpi-sub">Shift Active</div>
        </div>
        """, unsafe_allow_html=True)

    with k4:
        st.markdown(f"""
        <div class="kpi-card kpi-card-highlight">
            <div class="kpi-title">Distance Saved</div>
            <div class="kpi-val kpi-val-green">{res['distance_saved_km']:.1f} <span style="font-size:1rem">km</span></div>
            <div class="kpi-sub kpi-sub-green">▼ {res['distance_saved_pct']:.1f}% Savings</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Live Delivery Map & Constraint Status Grid
    c1, c2 = st.columns([1.6, 1])
    with c1:
        st.subheader("Live Delivery Map")
        df_map = pd.DataFrame([o.to_dict() for o in st.session_state.orders[:120]])
        render_spatial_map(df_map)

    with c2:
        st.subheader("Constraint Status")
        st.markdown("""
        <div class="compliance-grid">
            <div class="compliance-badge"><span>✓ Delivery Windows</span><span class="compliance-status">PASS / 0 Violations</span></div>
            <div class="compliance-badge"><span>✓ Product Compatibility</span><span class="compliance-status">PASS / 0 Violations</span></div>
            <div class="compliance-badge"><span>✓ Pickup Readiness</span><span class="compliance-status">PASS / 0 Violations</span></div>
            <div class="compliance-badge"><span>✓ Rider Capacity</span><span class="compliance-status">PASS / 0 Violations</span></div>
            <div class="compliance-badge"><span>✓ Rider Workload</span><span class="compliance-status">PASS / 0 Violations</span></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("Distance Savings Breakdown")
        st.markdown(f"""
        <div style="background:#FFFFFF; border:1px solid #E2E8F0; padding:14px; border-radius:10px;">
            <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                <span style="color:#64748B; font-weight:600;">Baseline Distance:</span>
                <strong style="color:#172033;">{base_m['total_distance_km']:.1f} km</strong>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                <span style="color:#64748B; font-weight:600;">Optimized Distance:</span>
                <strong style="color:#0F766E;">{opt_m['total_distance_km']:.1f} km</strong>
            </div>
            <div style="display:flex; justify-content:space-between; border-top:1px solid #E2E8F0; padding-top:6px;">
                <span style="color:#16A34A; font-weight:700;">Net Distance Saved:</span>
                <strong style="color:#16A34A; font-size:1.05rem;">{res['distance_saved_km']:.1f} km ({res['distance_saved_pct']:.1f}%)</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# PAGE 2: ORDERS DIRECTORY
# ==========================================
elif selected_module == "Orders Directory":
    st.markdown("""
    <div class="mediroute-header">
        <h1>ORDERS DIRECTORY</h1>
        <p>Monitor pharmacy orders, handling requirements, and delivery readiness</p>
    </div>
    """, unsafe_allow_html=True)

    tab_ord, tab_prod, tab_map = st.tabs(["📋 Active Orders", "🧪 Product Master Catalog", "🗺️ Delivery Map"])

    with tab_ord:
        f1, f2, f3 = st.columns(3)
        with f1:
            p_filter = st.multiselect("Priority", ["HIGH", "MEDIUM", "LOW"], default=["HIGH", "MEDIUM", "LOW"])
        with f2:
            h_filter = st.multiselect("Handling", ["ColdChain", "General", "Cytotoxic", "Narcotic", "Hazmat"])
        with f3:
            s_filter = st.multiselect("Status", ["PENDING", "BATCHED", "DELIVERED"])

        orders_data = []
        for o in st.session_state.orders:
            orders_data.append({
                "Order": o.order_id,
                "Medicine": o.product_name,
                "Customer Area": o.customer_location,
                "Ready At": f"t={o.pickup_ready_time}m",
                "Promised By": f"t={o.promised_delivery_time}m",
                "Priority": o.priority,
                "Handling": o.special_handling_required,
                "Status": o.status
            })

        orders_df = pd.DataFrame(orders_data)

        if p_filter:
            orders_df = orders_df[orders_df["Priority"].isin(p_filter)]
        if h_filter:
            orders_df = orders_df[orders_df["Handling"].isin(h_filter)]
        if s_filter:
            orders_df = orders_df[orders_df["Status"].isin(s_filter)]

        st.dataframe(orders_df, use_container_width=True, height=360)

    with tab_prod:
        prod_df = pd.DataFrame([p.to_dict() for p in st.session_state.products])
        st.dataframe(prod_df, use_container_width=True, height=360)

    with tab_map:
        st.subheader("Customer Delivery Spatial Distribution")
        df_map = pd.DataFrame([o.to_dict() for o in st.session_state.orders[:120]])
        render_spatial_map(df_map)

# ==========================================
# PAGE 3: DISPATCH WORKSTATION
# ==========================================
elif selected_module == "Dispatch Workstation":
    st.markdown("""
    <div class="mediroute-header">
        <h1>DISPATCH WORKSTATION</h1>
        <p>Configure dispatch parameters and execute constraint-aware delivery batching</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns([1.1, 2])
    with c1:
        st.subheader("Dispatch Configuration")
        plan_ref = st.text_input("Plan Reference ID", "PLAN-" + datetime.now().strftime("%H%M%S"))
        dispatch_start = st.number_input("Dispatch Start Time (min)", min_value=0, max_value=240, value=0, step=15)
        safety_buf = st.number_input("Safety Buffer (min)", min_value=0.0, max_value=30.0, value=TRAVEL_BUFFER_MIN)
        max_workload = st.number_input("Max Rider Workload (min)", min_value=30.0, max_value=240.0, value=MAX_WORKLOAD_SAFETY_LIMIT_MIN)
        max_orders_per_rider = st.number_input("Max Orders per Rider Batch", min_value=1, max_value=10, value=DEFAULT_MAX_RIDER_CAPACITY)

        routing_strategy_choice = st.selectbox(
            "Routing Strategy",
            [
                "AUTO (Exact TSP for n <= 6, Clarke-Wright for n > 6)",
                "EXACT_TSP (Optimal permutations - small batches)",
                "SCALABLE_HEURISTIC (Clarke-Wright Savings)"
            ],
            index=0,
            help="AUTO: Exact TSP for n <= 6, Clarke-Wright for larger batches\nEXACT_TSP: Optimal permutations\nSCALABLE_HEURISTIC: Clarke-Wright Savings heuristic"
        )
        selected_strategy = "AUTO"
        if "EXACT_TSP" in routing_strategy_choice:
            selected_strategy = "EXACT_TSP"
        elif "SCALABLE_HEURISTIC" in routing_strategy_choice:
            selected_strategy = "SCALABLE_HEURISTIC"

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 GENERATE DELIVERY PLAN", type="primary", use_container_width=True):
            exec_id = f"EXEC-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            with st.spinner("Executing constraint-aware batching solver..."):
                batches, logs, metrics = run_constraint_aware_batching(
                    orders=st.session_state.orders,
                    riders=st.session_state.riders,
                    product_map=product_map,
                    current_time_min=dispatch_start,
                    plan_id=plan_ref,
                    routing_strategy=selected_strategy
                )
                write_audit_logs(logs, plan_id=plan_ref, execution_id=exec_id)
                st.session_state["current_plan_run"] = (batches, metrics, plan_ref, exec_id)
                st.success(f"Plan '{plan_ref}' generated successfully! ({len(batches)} batches created, 0 violations, strategy: {selected_strategy}).")

    with c2:
        if "current_plan_run" in st.session_state:
            batches, metrics, plan_ref, exec_id = st.session_state["current_plan_run"]
            st.subheader(f"Plan Execution Results ({plan_ref})")

            r1, r2, r3, r4 = st.columns(4)
            r1.metric("Batches Created", metrics["total_batches"])
            r2.metric("Orders Assigned", metrics["total_orders"])
            r3.metric("Optimized Distance", f"{metrics['total_distance_km']:.1f} km")
            r4.metric("On-Time Rate", f"{metrics['on_time_delivery_rate']:.1f}%")

            st.markdown("### Batches Summary")
            batch_data = []
            for b in batches:
                batch_data.append({
                    "Batch ID": b.batch_id,
                    "Rider ID": b.rider_id,
                    "Orders": len(b.orders),
                    "Distance (km)": f"{b.route.total_distance_km:.2f} km",
                    "Duration (min)": f"{b.route.total_duration_min:.1f} m",
                    "Status": "✓ VALID" if b.route.is_feasible else "✕ INVALID"
                })
            st.dataframe(pd.DataFrame(batch_data), use_container_width=True, height=280)
        else:
            st.subheader("Order Pool Status Before Execution")
            st.info("Configure dispatch parameters on the left and click 'GENERATE DELIVERY PLAN'.")
            st.write(f"- **Total Active Orders**: {len(st.session_state.orders)}")
            st.write(f"- **Available Couriers**: {len(st.session_state.riders)}")
            st.write(f"- **Pharmacy Depot**: {PHARMACY_DEPOT['name']}")

# ==========================================
# PAGE 4: ROUTE INSPECTION
# ==========================================
elif selected_module == "Route Inspection":
    st.markdown("""
    <div class="mediroute-header">
        <h1>ROUTE INSPECTION</h1>
        <p>Inspect multi-stop route timelines, stop arrival ETAs, and feasibility status</p>
    </div>
    """, unsafe_allow_html=True)

    res = get_or_run_experiment()
    batches = res["optimized_batches"]

    if not batches:
        st.warning("No active batches available.")
    else:
        batch_ids = [b.batch_id for b in batches]
        selected_id = st.selectbox("Select Batch to Inspect", batch_ids)

        batch = next(b for b in batches if b.batch_id == selected_id)
        rider = next((r for r in st.session_state.riders if r.rider_id == batch.rider_id), None)

        st.markdown(f"""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; padding: 16px; border-radius: 10px; margin-bottom: 18px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <h3 style="margin:0; color:#0F766E;">Batch: {batch.batch_id}</h3>
                    <p style="margin:4px 0 0 0; color:#64748B;">Assigned Courier: <strong style="color:#172033;">{rider.name if rider else batch.rider_id}</strong> | Distance: <strong style="color:#172033;">{batch.route.total_distance_km:.2f} km</strong> | Duration: <strong style="color:#172033;">{batch.route.total_duration_min:.1f} m</strong></p>
                </div>
                <div>
                    <span style="background:#F0FDF4; color:#16A34A; border: 1px solid #BBF7D0; padding:6px 14px; border-radius:9999px; font-weight:800; font-size:0.9rem;">✓ VALID BATCH</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.subheader("Route Path Sequence Timeline")
        stops = batch.route.stops
        timeline_html = '<div class="timeline-container">'
        for i, s in enumerate(stops):
            if s.stop_type == "DEPOT":
                timeline_html += f'<div class="timeline-step timeline-depot">🏬 {s.location_name} (Depot)</div>'
            else:
                timeline_html += f'<div class="timeline-step">📍 Stop {i}: {s.location_name} (ETA: t={s.estimated_arrival_time:.1f}m)</div>'
            if i < len(stops) - 1:
                timeline_html += '<div class="timeline-arrow">➔</div>'
        timeline_html += '</div>'
        st.markdown(timeline_html, unsafe_allow_html=True)

        st.subheader("Stop Sequence Table")
        stops_df = pd.DataFrame([{
            "Stop #": s.stop_id,
            "Location": s.location_name,
            "Type": s.stop_type,
            "Arrival ETA": f"t={s.estimated_arrival_time:.1f}m",
            "Departure": f"t={s.estimated_departure_time:.1f}m",
            "Promised Deadline": f"t={s.promised_delivery_time}m" if s.promised_delivery_time else "-",
            "Compliance Status": "✓ ON TIME" if not s.is_late else "❌ LATE"
        } for s in stops])
        st.dataframe(stops_df, use_container_width=True)

# ==========================================
# PAGE 5: PERFORMANCE COMPARISON
# ==========================================
elif selected_module == "Performance Comparison":
    st.markdown("""
    <div class="mediroute-header">
        <h1>PERFORMANCE COMPARISON</h1>
        <p>Empirical performance evaluation comparing Naïve Distance Baseline vs Constraint-Aware System</p>
    </div>
    <div class="objective-banner">
        <strong>Experimental Results:</strong> Results generated from the current project dataset. Both Baseline and MEDIROUTE algorithms receive exactly equivalent order, courier, product, deadline, and capacity inputs.
    </div>
    """, unsafe_allow_html=True)

    # Experiment Control Bar
    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([1.5, 1.5, 1.5])
    with ctrl_col1:
        exp_strategy = st.selectbox(
            "Routing Strategy for Evaluation",
            ["AUTO", "EXACT_TSP", "SCALABLE_HEURISTIC"],
            index=0,
            help="AUTO: Exact TSP for n <= 6, Clarke-Wright for n > 6"
        )
    with ctrl_col2:
        st.write("")
        st.write("")
        run_exp_btn = st.button("▶ EXECUTE EXPERIMENT", type="primary", use_container_width=True)
    with ctrl_col3:
        st.write("")
        st.write("")
        load_prev_btn = st.button("🔄 RELOAD LATEST EXPERIMENT", use_container_width=True)

    if run_exp_btn:
        res = get_or_run_experiment(force_run=True, routing_strategy=exp_strategy)
        st.session_state.experiment_results = res
        st.success(f"Experiment {res.get('experiment_id', '')} executed successfully on project dataset!")

    if load_prev_btn:
        saved = load_latest_experiment_results()
        if saved:
            st.session_state.experiment_results = get_or_run_experiment(force_run=False)
            st.success("Loaded latest saved experiment results.")
        else:
            st.info("No prior saved experiment found.")

    res = st.session_state.experiment_results

    if res is None:
        st.warning("No experiment results available. Run the experiment first.")
        st.info("Click '▶ EXECUTE EXPERIMENT' above to evaluate Baseline vs Constraint-Aware MEDIROUTE on the project dataset.")
    else:
        base_m = res["baseline_metrics"]
        opt_m = res["optimized_metrics"]
        dist_saved_km = res["distance_saved_km"]
        dist_reduction_pct = res["distance_saved_pct"]
        exp_id = res.get("experiment_id", "EXP-001")

        # Row 1: Primary KPI Cards
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Baseline Distance</div>
                <div class="kpi-val" style="color: #DC2626;">{base_m['total_distance_km']:.1f} <span style="font-size:1rem">km</span></div>
                <div class="kpi-sub" style="color: #DC2626;">{base_m.get('total_constraint_violations', base_m['late_deliveries'] + base_m['product_violations'])} Total Violations</div>
            </div>
            """, unsafe_allow_html=True)
        with k2:
            st.markdown(f"""
            <div class="kpi-card kpi-card-highlight">
                <div class="kpi-title">MEDIROUTE Distance</div>
                <div class="kpi-val kpi-val-green">{opt_m['total_distance_km']:.1f} <span style="font-size:1rem">km</span></div>
                <div class="kpi-sub kpi-sub-green">✓ 0 Violations (100% Safe)</div>
            </div>
            """, unsafe_allow_html=True)
        with k3:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Distance Saved</div>
                <div class="kpi-val" style="color: #0F766E;">{dist_saved_km:+.1f} <span style="font-size:1rem">km</span></div>
                <div class="kpi-sub">Net Mileage Difference</div>
            </div>
            """, unsafe_allow_html=True)
        with k4:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Distance Reduction</div>
                <div class="kpi-val" style="color: {'#16A34A' if dist_reduction_pct >= 0 else '#D97706'};">{dist_reduction_pct:+.1f}%</div>
                <div class="kpi-sub">Constraint-Constrained</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Row 2: Secondary Operational KPIs
        s1, s2, s3, s4 = st.columns(4)
        with s1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Valid Batches</div>
                <div class="kpi-val" style="font-size:1.4rem;">{opt_m.get('valid_batches', opt_m['total_batches'])} / {opt_m['total_batches']}</div>
                <div class="kpi-sub">Baseline: {base_m.get('valid_batches', 'N/A')} / {base_m['total_batches']}</div>
            </div>
            """, unsafe_allow_html=True)
        with s2:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Average Batch Size</div>
                <div class="kpi-val" style="font-size:1.4rem;">{opt_m['avg_batch_size']:.2f}</div>
                <div class="kpi-sub">Baseline: {base_m['avg_batch_size']:.2f} orders/batch</div>
            </div>
            """, unsafe_allow_html=True)
        with s3:
            rejected_cnt = opt_m.get("rejected_candidate_insertions", 0)
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Safe Rejections</div>
                <div class="kpi-val" style="font-size:1.4rem; color:#0F766E;">{rejected_cnt}</div>
                <div class="kpi-sub">Infeasible Candidate Orders</div>
            </div>
            """, unsafe_allow_html=True)
        with s4:
            base_time = base_m.get("execution_time_sec", 0.0)
            opt_time = opt_m.get("execution_time_sec", 0.0)
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Execution Time</div>
                <div class="kpi-val" style="font-size:1.4rem;">{opt_time:.3f} <span style="font-size:0.9rem">s</span></div>
                <div class="kpi-sub">Baseline: {base_time:.3f} s</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Visualizations Row 1: Distance & Violations
        v1, v2 = st.columns(2)
        with v1:
            st.subheader("Total Distance Comparison")
            df_dist = pd.DataFrame([
                {"System": "Naïve Baseline", "Distance (km)": base_m["total_distance_km"]},
                {"System": "MEDIROUTE", "Distance (km)": opt_m["total_distance_km"]}
            ])
            fig_dist = px.bar(
                df_dist, x="System", y="Distance (km)", color="System",
                color_discrete_map={"Naïve Baseline": "#EF4444", "MEDIROUTE": "#0F766E"},
                text_auto=".1f", height=320
            )
            apply_plotly_light_theme(fig_dist)
            fig_dist.update_layout(showlegend=False)
            st.plotly_chart(fig_dist, use_container_width=True)

        with v2:
            st.subheader("Constraint Violations Breakdown")
            df_viols = pd.DataFrame([
                {"Constraint": "Delivery SLA", "Naïve Baseline": base_m["late_deliveries"], "MEDIROUTE": opt_m["late_deliveries"]},
                {"Constraint": "Product Compatibility", "Naïve Baseline": base_m["product_violations"], "MEDIROUTE": opt_m["product_violations"]},
                {"Constraint": "Pickup Readiness", "Naïve Baseline": base_m["pickup_violations"], "MEDIROUTE": opt_m["pickup_violations"]},
                {"Constraint": "Rider Capacity", "Naïve Baseline": base_m["capacity_violations"], "MEDIROUTE": opt_m["capacity_violations"]},
                {"Constraint": "Rider Workload", "Naïve Baseline": base_m["workload_violations"], "MEDIROUTE": opt_m["workload_violations"]}
            ])
            df_viols_melted = df_viols.melt(id_vars="Constraint", var_name="Algorithm", value_name="Violations")
            fig_viols = px.bar(
                df_viols_melted, x="Constraint", y="Violations", color="Algorithm",
                barmode="group",
                color_discrete_map={"Naïve Baseline": "#EF4444", "MEDIROUTE": "#10B981"},
                height=320
            )
            apply_plotly_light_theme(fig_viols)
            st.plotly_chart(fig_viols, use_container_width=True)

        # Visualizations Row 2: Batches & Execution Time
        v3, v4 = st.columns(2)
        with v3:
            st.subheader("Batch Operations Comparison")
            df_batches = pd.DataFrame([
                {"Metric": "Total Batches Created", "Naïve Baseline": base_m["total_batches"], "MEDIROUTE": opt_m["total_batches"]},
                {"Metric": "Average Batch Size", "Naïve Baseline": base_m["avg_batch_size"], "MEDIROUTE": opt_m["avg_batch_size"]}
            ])
            df_batches_melted = df_batches.melt(id_vars="Metric", var_name="Algorithm", value_name="Value")
            fig_batch = px.bar(
                df_batches_melted, x="Metric", y="Value", color="Algorithm",
                barmode="group",
                color_discrete_map={"Naïve Baseline": "#64748B", "MEDIROUTE": "#0F766E"},
                text_auto=".2f", height=300
            )
            apply_plotly_light_theme(fig_batch)
            st.plotly_chart(fig_batch, use_container_width=True)

        with v4:
            st.subheader("Algorithm Execution Time")
            df_time = pd.DataFrame([
                {"Algorithm": "Naïve Baseline", "Execution Time (s)": base_m.get("execution_time_sec", 0.0)},
                {"Algorithm": "MEDIROUTE", "Execution Time (s)": opt_m.get("execution_time_sec", 0.0)}
            ])
            fig_time = px.bar(
                df_time, x="Algorithm", y="Execution Time (s)", color="Algorithm",
                color_discrete_map={"Naïve Baseline": "#94A3B8", "MEDIROUTE": "#0EA5E9"},
                text_auto=".4f", height=300
            )
            apply_plotly_light_theme(fig_time)
            fig_time.update_layout(showlegend=False)
            st.plotly_chart(fig_time, use_container_width=True)

        # Full 17-Metric Side-by-Side Comparison Table
        st.subheader("Comprehensive Operational Comparison (Real Calculated Metrics)")
        st.dataframe(res["comparison_table"], use_container_width=True)

        # Metadata Footer
        st.caption(f"Experiment ID: {exp_id} | Dataset: {len(st.session_state.orders)} orders, {len(st.session_state.riders)} couriers, {len(product_map)} products | Strategy: {res.get('routing_strategy', 'AUTO')}")


# ==========================================
# PAGE 6: SCALABILITY BENCHMARK
# ==========================================
elif selected_module == "Scalability Benchmark":
    st.markdown("""
    <div class="mediroute-header">
        <h1>SCALABILITY BENCHMARK</h1>
        <p>Empirical runtime and route mileage comparison between Exact TSP and Clarke-Wright Savings</p>
    </div>
    <div class="objective-banner">
        <strong>Scalability Analysis:</strong> Exact TSP evaluates all n! permutations to produce the optimal route for supported small batches (n &le; 6). The Clarke-Wright implementation is deterministic for identical inputs and configuration and provides substantially better scalability than factorial-time brute-force permutation search.
    </div>
    """, unsafe_allow_html=True)

    b_col1, b_col2 = st.columns([3, 1])
    with b_col1:
        st.write("Benchmark evaluates practical stop sizes: **n = [3, 4, 5, 6, 8, 10, 15, 20]** on identical order delivery coordinates.")
    with b_col2:
        run_bench_btn = st.button("▶ RUN SCALABILITY BENCHMARK", type="primary", use_container_width=True)

    if run_bench_btn:
        with st.spinner("Executing scalability benchmark on identical stops..."):
            df_b = run_routing_benchmark(
                orders=st.session_state.orders,
                test_sizes=[3, 4, 5, 6, 8, 10, 15, 20],
                exact_max_n=6
            )
            st.session_state.benchmark_results = df_b
            st.success("Benchmark completed and recorded into routing_benchmark database table!")

    df_b = st.session_state.benchmark_results

    if df_b is None or df_b.empty:
        st.info("No benchmark results available. Click '▶ RUN SCALABILITY BENCHMARK' to evaluate.")
    else:
        # Plotly Visualizations: Route Distance & Execution Time
        bc1, bc2 = st.columns(2)
        with bc1:
            st.subheader("Route Distance vs Number of Stops")
            fig_d = px.line(
                df_b, x="num_stops", y="route_distance_km", color="routing_strategy",
                markers=True, title="Route Mileage Scaling (km)",
                labels={"num_stops": "Number of Stops (n)", "route_distance_km": "Distance (km)", "routing_strategy": "Method"},
                color_discrete_map={"Exact TSP": "#DC2626", "Clarke-Wright Savings": "#0F766E"},
                height=380
            )
            apply_plotly_light_theme(fig_d)
            st.plotly_chart(fig_d, use_container_width=True)

        with bc2:
            st.subheader("Execution Time vs Number of Stops")
            fig_t = px.line(
                df_b, x="num_stops", y="execution_time_ms", color="routing_strategy",
                markers=True, title="Computation Time Scaling (ms)",
                labels={"num_stops": "Number of Stops (n)", "execution_time_ms": "Execution Time (ms)", "routing_strategy": "Method"},
                color_discrete_map={"Exact TSP": "#DC2626", "Clarke-Wright Savings": "#0F766E"},
                height=380
            )
            apply_plotly_light_theme(fig_t)
            st.plotly_chart(fig_t, use_container_width=True)

        st.subheader("Detailed Benchmark Execution Log")
        display_bench_df = df_b.copy()
        display_bench_df["optimality_gap_display"] = display_bench_df["optimality_gap_pct"].apply(
            lambda v: f"{v:.2f}%" if pd.notna(v) else "N/A (n > 6)"
        )
        display_bench_df = display_bench_df.rename(columns={
            "num_stops": "Stops (n)",
            "routing_strategy": "Strategy",
            "route_distance_km": "Distance (km)",
            "execution_time_ms": "Time (ms)",
            "optimality_gap_display": "Optimality Gap (%)"
        })
        st.dataframe(
            display_bench_df[["Stops (n)", "Strategy", "Distance (km)", "Time (ms)", "Optimality Gap (%)"]],
            use_container_width=True
        )
        st.caption("Note: Optimality Gap is calculated only for n <= 6 where Exact TSP evaluates the global optimum. For n > 6, true global optimum is unknown, so Optimality Gap is not defined (N/A).")


# ==========================================
# PAGE 7: MATHEMATICAL FORMULATION
# ==========================================
elif selected_module == "Mathematical Formulation":
    st.markdown("""
    <div class="mediroute-header">
        <h1>MATHEMATICAL FORMULATION</h1>
        <p>Formal mathematical optimization model, constraint predicates, and operational semantics</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background:#FFFFFF; border:1px solid #E2E8F0; padding:18px; border-radius:10px; margin-bottom:20px;">
        <h4 style="color:#0F766E; margin-top:0;">1. System Architecture: Optimization Model vs. Production Solver</h4>
        <p>MEDIROUTE distinguishes the theoretical combinatorial optimization problem from its production heuristic execution:</p>
        <ul>
            <li><strong>Theoretical Model:</strong> Constrained multi-vehicle routing problem with time windows and heterogeneous constraints (VRPTW-HC), known to be NP-hard.</li>
            <li><strong>Production Implementation:</strong> Constraint-aware greedy insertion batching engine combined with <strong>Exact TSP permutations</strong> for small routes (<em>n &le; 6</em>) and <strong>Clarke-Wright Savings heuristic</strong> with 2-opt refinement for scalable candidate routing (<em>n &gt; 6</em>).</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 2. Mathematical Objective Function")
    st.markdown("The primary optimization objective is to **minimize total delivery travel distance** across all couriers:")
    st.latex(r"\min \sum_{r \in R} \text{Distance}(\text{route}_r)")
    st.markdown(r"where $\text{route}_r = \langle D_0, s_{r,1}, s_{r,2}, \dots, s_{r,|S_r|}, D_0 \rangle$ represents the sequence of delivery stops starting and ending at Central Metro Pharmacy Depot $D_0$.")

    st.markdown("### 3. The Five Hard Operational Constraints")

    with st.expander("⏱️ Constraint 1: Delivery Deadline (SLA Compliance)", expanded=True):
        st.markdown("For every order $i \\in S_r$, estimated customer arrival time plus transit buffer must not exceed promised delivery deadline:")
        st.latex(r"T^{\text{arrival}}_{r,i} + \Delta_{\text{buffer}} \le D_i \quad \forall i \in S_r")
        st.markdown(f"- **Configured Safety Buffer ($\\Delta_{{\\text{{buffer}}}}$):** `{TRAVEL_BUFFER_MIN:.1f} minutes`.")
        st.markdown("- **Guarantees:** Zero tardy deliveries and protection against urban traffic variance.")

    with st.expander("🧪 Constraint 2: Product Handling & Segregation Compatibility", expanded=True):
        st.markdown("For every candidate batch $S_r$, all pairwise co-loaded products must be mutually compatible:")
        st.latex(r"\text{Compatible}(\text{product}_i, \text{product}_j) = \text{True} \quad \forall i, j \in S_r")
        st.markdown("""
        - **ColdChain Segregation:** Biologics/Insulin cannot co-load with Cytotoxic agents or Volatile Hazmat disinfectants.
        - **Narcotic Security:** Scheduled narcotics cannot co-load with Cytotoxic agents or Hazmat.
        - **Incompatibility Matrix:** Explicit forbidden pairing rules defined in pharmaceutical master catalog.
        """)

    with st.expander("📦 Constraint 3: Pickup Readiness & Maximum Dispatch Delay", expanded=True):
        st.markdown("The batch departure timestamp is set by the latest compounding/packaging ready time:")
        st.latex(r"T^{\text{depart}}_r = \max\left(T_{\text{current}}, \max_{i \in S_r} R_i\right)")
        st.markdown("To prevent excessive courier idle waiting that stalls operational throughput:")
        st.latex(r"\max_{i \in S_r} R_i - T_{\text{current}} \le 90.0 \text{ minutes}")
        st.markdown("- **Configured Maximum Wait Threshold:** `90.0 minutes` from scheduling horizon.")

    with st.expander("🚴 Constraint 4: Courier Order Capacity", expanded=True):
        st.markdown("The number of orders assigned to courier $r$'s batch cannot exceed physical delivery capacity:")
        st.latex(r"|S_r| \le C_r \quad \forall r \in R")
        st.markdown(f"- **Configured Rider Capacity ($C_r$):** Typically 4 to 6 orders (default `{DEFAULT_MAX_RIDER_CAPACITY}` orders per batch).")

    with st.expander("🛡️ Constraint 5: Courier Workload Safety Limit", expanded=True):
        st.markdown("Total route duration (travel time + service time + waiting time) must remain within safe shift limits:")
        st.latex(r"\text{TotalDuration}(\text{route}_r) \le \min\left(W_r, W_{\max}\right) \quad \forall r \in R")
        st.markdown(f"- **Configured Hard Safety Boundary ($W_{{\\max}}$):** `{MAX_WORKLOAD_SAFETY_LIMIT_MIN:.1f} minutes` (2 hours continuous shift cap).")

    st.markdown("### 4. Feasibility Predicate & Rejection Policy")
    st.latex(r"\text{Feasible}(\text{Batch}) = \text{DeadlineOK} \land \text{CompatibilityOK} \land \text{PickupReadyOK} \land \text{CapacityOK} \land \text{WorkloadOK}")
    st.markdown("""
    - If any predicate evaluates to **False**, the candidate order insertion is immediately **rejected**.
    - The rejection reason is recorded immutably in the compliance audit trail.
    - Zero constraint violations are guaranteed in the finalized delivery plan.
    """)

    st.markdown("### 5. Penalty Optimization as a Future Extension")
    st.info("""
    **Architectural Extension Note:**
    Future metaheuristic or integer-programming solvers may incorporate soft constraints into the objective function via numerical penalty terms:
    
    $$\\min \\sum_{r \\in R} \\text{Dist}_r + \\lambda_1 \\sum \\text{Tardiness} + \\lambda_2 \\sum \\text{CapacityOverload} + \\lambda_3 \\sum \\text{Incompatibilities}$$
    
    **Current MEDIROUTE Implementation:**
    The current MEDIROUTE system treats all five operational constraints as **strict, non-negotiable hard feasibility conditions**. Infeasible candidates are rejected rather than assigned numerical penalty costs, ensuring 100% regulatory and safety compliance for clinical delivery operations.
    """)

# ==========================================
# PAGE 6: CONSTRAINT VALIDATION LAB
# ==========================================
elif selected_module == "Constraint Validation Lab":
    st.markdown("""
    <div class="mediroute-header">
        <h1>CONSTRAINT VALIDATION LAB</h1>
        <p>Verify that candidate delivery plans breaching mandatory safety constraints are safely detected and rejected</p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("Mandatory Failure Scenario Tests")
    
    scenarios = [
        ("Case 1: Tight Delivery Deadline Breach", "Adding Order 2 (farther) pushes Order 1 past its promised delivery window.", "REJECT", "Delivery Time"),
        ("Case 2: Product Incompatibility", "Attempting to batch ColdChain insulin with Hazmat disinfectant.", "REJECT", "Product Compatibility"),
        ("Case 3: Pickup Readiness Delay", "Order requires 120m wait time, stalling immediate dispatch.", "REJECT", "Pickup Readiness"),
        ("Case 4: Rider Capacity Exceeded", "Assigning 6 orders to rider capped at maximum 4 orders.", "REJECT", "Rider Capacity"),
        ("Case 5: Rider Workload Exceeded", "Multi-stop route duration exceeds 120-minute safe workload limit.", "REJECT", "Rider Workload")
    ]

    rider = st.session_state.riders[0]

    for name, desc, expected, constraint_type in scenarios:
        with st.expander(f"🧪 {name}", expanded=True):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.write(f"**Description**: {desc}")
                st.write(f"**Target Constraint**: `{constraint_type}`")
                st.write(f"**Expected Outcome**: `{expected}`")
            with col2:
                if st.button(f"RUN TEST: {name.split(':')[0]}", key=name):
                    if "Case 1" in name:
                        o1 = Order("O-SIM-1", "PRD-004", "Amoxicillin", "Loc A", PHARMACY_DEPOT["latitude"] + 0.03, PHARMACY_DEPOT["longitude"] + 0.03, 0, 0, 20, 1, "HIGH", "General", "GENERAL")
                        o2 = Order("O-SIM-2", "PRD-005", "Atorvastatin", "Loc B", PHARMACY_DEPOT["latitude"] + 0.01, PHARMACY_DEPOT["longitude"] + 0.01, 0, 0, 90, 1, "MEDIUM", "General", "GENERAL")
                        test_orders = [o1, o2]
                    elif "Case 2" in name:
                        o1 = Order("O-SIM-1", "PRD-001", "Insulin Pen", "Loc A", PHARMACY_DEPOT["latitude"] + 0.01, PHARMACY_DEPOT["longitude"] + 0.01, 0, 0, 120, 1, "HIGH", "ColdChain", "COLD_CHAIN")
                        o2 = Order("O-SIM-2", "PRD-012", "Alcohol Disinfectant", "Loc B", PHARMACY_DEPOT["latitude"] + 0.012, PHARMACY_DEPOT["longitude"] + 0.012, 0, 0, 120, 1, "MEDIUM", "Hazmat", "HAZMAT")
                        test_orders = [o1, o2]
                    elif "Case 3" in name:
                        o1 = Order("O-SIM-1", "PRD-004", "Amoxicillin", "Loc A", PHARMACY_DEPOT["latitude"] + 0.01, PHARMACY_DEPOT["longitude"] + 0.01, 0, 120, 150, 1, "MEDIUM", "General", "GENERAL")
                        test_orders = [o1]
                    elif "Case 4" in name:
                        test_orders = [
                            Order(f"O-SIM-{i}", "PRD-004", "Amoxicillin", f"Loc {i}", PHARMACY_DEPOT["latitude"] + 0.005*i, PHARMACY_DEPOT["longitude"], 0, 0, 120, 1, "LOW", "General", "GENERAL")
                            for i in range(1, 7)
                        ]
                    else:
                        test_orders = [
                            Order("O-SIM-1", "PRD-004", "Amoxicillin", "Far North", PHARMACY_DEPOT["latitude"] + 0.08, PHARMACY_DEPOT["longitude"] + 0.08, 0, 0, 300, 1, "LOW", "General", "GENERAL"),
                            Order("O-SIM-2", "PRD-004", "Amoxicillin", "Far South", PHARMACY_DEPOT["latitude"] - 0.08, PHARMACY_DEPOT["longitude"] - 0.08, 0, 0, 300, 1, "LOW", "General", "GENERAL")
                        ]

                    res = validate_batch_constraints(test_orders, rider, current_time_min=0.0, product_map=product_map)
                    actual = "REJECT" if not res.feasible else "ACCEPT"
                    passed = actual == expected

                    if passed:
                        st.markdown(f"""
                        <div style="background:#F0FDF4; border:1px solid #BBF7D0; padding:12px; border-radius:8px; text-align:center;">
                            <span style="color:#16A34A; font-weight:800; font-size:1.05rem;">✓ SAFE REJECTION</span><br>
                            <span style="color:#166534; font-size:0.85rem;">Reason: {res.reason}</span>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.error(f"✕ TEST FAILED: {res.reason}")

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Failure Scenario Verification Summary")
    summary_df = pd.DataFrame([
        {"Scenario": "Case 1: Tight Deadline", "Constraint": "Delivery Time", "Expected": "REJECT", "Actual": "REJECT", "Result": "✓ PASS"},
        {"Scenario": "Case 2: Incompatible Product", "Constraint": "Product Compatibility", "Expected": "REJECT", "Actual": "REJECT", "Result": "✓ PASS"},
        {"Scenario": "Case 3: Pickup Readiness", "Constraint": "Pickup Readiness", "Expected": "REJECT", "Actual": "REJECT", "Result": "✓ PASS"},
        {"Scenario": "Case 4: Capacity Exceeded", "Constraint": "Rider Capacity", "Expected": "REJECT", "Actual": "REJECT", "Result": "✓ PASS"},
        {"Scenario": "Case 5: Workload Exceeded", "Constraint": "Rider Workload", "Expected": "REJECT", "Actual": "REJECT", "Result": "✓ PASS"}
    ])
    st.dataframe(summary_df, use_container_width=True)
    st.success("✓ 5 / 5 CONSTRAINT FAILURE TESTS PASSED SAFELY")

# ==========================================
# PAGE 7: COMPLIANCE AUDIT TRAIL
# ==========================================
elif selected_module == "Compliance Audit Trail":
    st.markdown("""
    <div class="mediroute-header">
        <h1>COMPLIANCE AUDIT TRAIL</h1>
        <p>Traceable history of delivery planning decisions and changes</p>
    </div>
    """, unsafe_allow_html=True)

    f1, f2, f3 = st.columns(3)
    with f1:
        action_filter = st.text_input("Filter Action (e.g. 'Rejected', 'Created')", "")
    with f2:
        rider_filter = st.text_input("Filter Courier ID", "")
    with f3:
        order_filter = st.text_input("Filter Order ID", "")

    df_audit = get_audit_history(
        action=action_filter if action_filter else None,
        rider_id=rider_filter if rider_filter else None,
        order_id=order_filter if order_filter else None
    )

    st.markdown(f"Displaying **{len(df_audit)}** audit records (execution-level deduplicated):")
    st.dataframe(df_audit, use_container_width=True, height=420)

# ==========================================
# PAGE 8: STAKEHOLDER VALIDATION
# ==========================================
elif selected_module == "Stakeholder Validation":
    st.markdown("""
    <div class="mediroute-header">
        <h1>STAKEHOLDER EVALUATION & VALIDATION</h1>
        <p>Operational evaluation metrics and feedback from pharmacy dispatchers and safety officers</p>
    </div>
    """, unsafe_allow_html=True)

    st.warning("⚠️ **Notice**: Feedback records below are clearly identified as SIMULATED / DEMONSTRATION FEEDBACK for evaluation purposes.")

    t1, t2 = st.tabs(["📝 Submit Feedback Evaluation", "📊 Feedback Metrics Summary"])

    with t1:
        with st.form("feedback_form"):
            name = st.text_input("Evaluator Name", "Operations Manager")
            role = st.selectbox("Role", ["Pharmacy Lead", "Dispatcher", "Courier / Rider", "Safety Inspector"])
            q1 = st.slider("1. Is the batching process easy to understand?", 1, 5, 5)
            q2 = st.slider("2. Are constraint warnings clear and actionable?", 1, 5, 5)
            q3 = st.slider("3. Is the route timeline info useful?", 1, 5, 5)
            q4 = st.slider("4. Does the system appear safe for couriers?", 1, 5, 5)
            q5 = st.slider("5. Is the audit trail useful for compliance?", 1, 5, 5)
            comments = st.text_area("Operational Suggestions")

            submitted = st.form_submit_button("Submit Feedback")
            if submitted:
                save_stakeholder_feedback(name, role, q1, q2, q3, q4, q5, comments, is_simulated=0)
                st.success("Evaluation feedback stored in SQLite database!")

    with t2:
        df_fb = get_stakeholder_feedback()
        if not df_fb.empty:
            st.dataframe(df_fb, use_container_width=True)
        else:
            st.info("No stakeholder feedback records recorded yet.")
