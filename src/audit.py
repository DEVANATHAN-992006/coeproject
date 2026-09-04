import sqlite3
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path

from config import DB_PATH

__all__ = [
    "get_db_connection",
    "init_database",
    "write_audit_logs",
    "deduplicate_audit_log_records",
    "get_audit_history",
    "save_stakeholder_feedback",
    "get_stakeholder_feedback"
]

def get_db_connection():

    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """
    Initializes SQLite tables for audit history, delivery plans, and stakeholder feedback.
    Applies schema migration for execution_id idempotency.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Audit Log Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
            execution_id TEXT NOT NULL DEFAULT 'EXEC-001',
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
        )
    """)

    # Schema check for execution_id column if upgrading existing DB
    cursor.execute("PRAGMA table_info(audit_log)")
    columns = [row[1] for row in cursor.fetchall()]
    if "execution_id" not in columns:
        cursor.execute("ALTER TABLE audit_log ADD COLUMN execution_id TEXT NOT NULL DEFAULT 'EXEC-001'")

    # 2. Delivery Plans Summary Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS delivery_plans (
            plan_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            algorithm_type TEXT NOT NULL,
            total_orders INTEGER,
            total_batches INTEGER,
            total_distance_km REAL,
            distance_saved_km REAL,
            distance_saved_pct REAL,
            late_deliveries INTEGER,
            constraint_violations INTEGER
        )
    """)

    # 3. Stakeholder Feedback Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stakeholder_feedback (
            feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            user_name TEXT,
            user_role TEXT,
            q1_understandable INTEGER,
            q2_warnings_clear INTEGER,
            q3_batch_info_useful INTEGER,
            q4_rider_safety INTEGER,
            q5_audit_useful INTEGER,
            comments TEXT,
            is_simulated INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()

def write_audit_logs(
    audit_records: List[Dict[str, Any]],
    plan_id: str = "PLAN-001",
    execution_id: str = "EXEC-001"
):
    """
    Appends audit records to the immutable audit_log table.
    Enforces execution-level idempotency: skips insertion if records for this execution_id already exist.
    """
    init_database()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check for execution-level idempotency
    cursor.execute("SELECT COUNT(*) FROM audit_log WHERE execution_id = ?", (execution_id,))
    if cursor.fetchone()[0] > 0:
        # Execution already logged; skip duplicate recording on Streamlit re-renders
        conn.close()
        return

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for rec in audit_records:
        cursor.execute("""
            INSERT INTO audit_log (
                execution_id, timestamp, plan_id, batch_id, action, order_id, rider_id,
                old_state, new_state, reason, triggered_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            execution_id,
            rec.get("timestamp", now_str),
            rec.get("plan_id", plan_id),
            rec.get("batch_id", "NONE"),
            rec.get("action", "UNKNOWN"),
            rec.get("order_id", "NONE"),
            rec.get("rider_id", "NONE"),
            rec.get("old_state", "NONE"),
            rec.get("new_state", "NONE"),
            rec.get("reason", "No reason specified"),
            rec.get("triggered_by", "SYSTEM")
        ))

    conn.commit()
    conn.close()

def deduplicate_audit_log_records():
    """
    Clean up accidental duplicate rows from older test runs while preserving historical audit records.
    """
    init_database()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM audit_log 
        WHERE audit_id NOT IN (
            SELECT MIN(audit_id)
            FROM audit_log
            GROUP BY execution_id, plan_id, batch_id, action, order_id, rider_id, old_state, new_state, reason
        )
    """)
    conn.commit()
    conn.close()

def get_audit_history(
    plan_id: Optional[str] = None,
    execution_id: Optional[str] = None,
    batch_id: Optional[str] = None,
    rider_id: Optional[str] = None,
    order_id: Optional[str] = None,
    action: Optional[str] = None
) -> pd.DataFrame:
    """
    Query audit history with optional filters. Returns DataFrame.
    """
    init_database()
    conn = get_db_connection()

    query = "SELECT * FROM audit_log WHERE 1=1"
    params = []

    if plan_id:
        query += " AND plan_id = ?"
        params.append(plan_id)
    if execution_id:
        query += " AND execution_id = ?"
        params.append(execution_id)
    if batch_id:
        query += " AND batch_id = ?"
        params.append(batch_id)
    if rider_id:
        query += " AND rider_id = ?"
        params.append(rider_id)
    if order_id:
        query += " AND order_id = ?"
        params.append(order_id)
    if action:
        query += " AND action LIKE ?"
        params.append(f"%{action}%")

    query += " ORDER BY audit_id DESC"

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def save_stakeholder_feedback(
    user_name: str,
    user_role: str,
    q1: int, q2: int, q3: int, q4: int, q5: int,
    comments: str,
    is_simulated: int = 0
):
    init_database()
    conn = get_db_connection()
    cursor = conn.cursor()

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO stakeholder_feedback (
            timestamp, user_name, user_role, q1_understandable, q2_warnings_clear,
            q3_batch_info_useful, q4_rider_safety, q5_audit_useful, comments, is_simulated
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (now_str, user_name, user_role, q1, q2, q3, q4, q5, comments, is_simulated))

    conn.commit()
    conn.close()

def get_stakeholder_feedback() -> pd.DataFrame:
    init_database()
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM stakeholder_feedback ORDER BY feedback_id DESC", conn)
    conn.close()
    return df
