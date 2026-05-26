import streamlit as st
import pandas as pd
import psycopg2
import requests
import plotly.express as px
import os

st.set_page_config(page_title="FOIE Audit Workbench", layout="wide")

DB_HOST = os.environ.get("POSTGRES_HOST", "postgres")
DB_NAME = os.environ.get("POSTGRES_DB", "foie_db")
DB_USER = os.environ.get("POSTGRES_USER", "airflow")
DB_PASS = os.environ.get("POSTGRES_PASSWORD", "airflow")
DB_PORT = os.environ.get("POSTGRES_PORT", "5432")

# DB Connection Helper
def get_data(query):
    conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS, port=DB_PORT)
    df = pd.read_sql(query, conn)
    conn.close()
    return df

st.title("🛡️ FOIE: Audit & Repair Workbench")
st.markdown("---")

# --- SIDEBAR: REPAIR WORKBENCH ---
st.sidebar.header("🛠️ Repair Workbench")
st.sidebar.info("Select a flagged order to fix its unit cost.")

# Fetch currently quarantined items for the dropdown
quarantine_list = get_data("SELECT order_id FROM stg_quarantine.orders_flagged")

if not quarantine_list.empty:
    selected_id = st.sidebar.selectbox("Select Order ID to Fix", quarantine_list['order_id'])
    new_price = st.sidebar.number_input("Enter Corrected Unit Cost", min_value=0.01, step=0.01)
    
    if st.sidebar.button("Submit Repair to Gold Ledger"):
        # We send the request to YOUR FastAPI service!
        payload = {"order_id": selected_id, "new_unit_cost": new_price}
        try:
            # We also need to log the edit for our history
            # For simplicity in this demo, the API handles the move, 
            # and we'll add a log entry here.
            response = requests.post("http://foie_api:8000/repair", json=payload)
            
            if response.status_code == 200:
                # Log the edit manually into our new audit table
                conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS, port=DB_PORT)
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO fct_gold.audit_log (order_id, new_unit_cost) VALUES (%s, %s)",
                    (selected_id, new_price)
                )
                conn.commit()
                cur.close()
                conn.close()
                st.sidebar.success(f"Order {selected_id} Repaired!")
                st.rerun() # Refresh the UI
            else:
                st.sidebar.error("Repair failed. Check API logs.")
        except Exception as e:
            st.sidebar.error(f"Connection Error: {e}")
else:
    st.sidebar.success("🎉 All clear! No orders in quarantine.")

# --- MAIN PAGE: VISUALS ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Quarantine Distribution")
    df_flag = get_data("SELECT flag_reason, COUNT(*) as count FROM stg_quarantine.orders_flagged GROUP BY 1")
    if not df_flag.empty:
        fig = px.pie(df_flag, values='count', names='flag_reason', hole=0.4, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("Quarantine is empty.")

with col2:
    st.subheader("📜 Recent Audit Trail (Past Edits)")
    df_history = get_data("SELECT order_id, new_unit_cost, repaired_at FROM fct_gold.audit_log ORDER BY repaired_at DESC LIMIT 10")
    if not df_history.empty:
        st.dataframe(df_history, use_container_width=True)
    else:
        st.info("No edits have been made yet.")

# --- BOTTOM: GOLD LEDGER ---
st.subheader("💎 High-Integrity Gold Ledger")
df_gold = get_data("SELECT * FROM fct_gold.orders_final ORDER BY repaired_at DESC")
st.table(df_gold.head(10))