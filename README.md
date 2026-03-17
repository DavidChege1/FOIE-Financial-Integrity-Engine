# 🛡️ FOIE: Financial-Ops Integrity Engine

FOIE is a high-integrity data engineering platform built to solve a common enterprise problem: **Dirty ERP Data**. In many financial organizations, upstream systems provide corrupt data (negative costs, missing supplier IDs, or malformed timestamps) that can lead to millions in reporting errors.

This engine acts as a "Financial Gatekeeper," utilizing a modern data stack to identify, quarantine, and provide a human-in-the-loop repair interface for anomalous financial records.

## 🏗️ The Architecture

The platform is fully containerized and runs on a 5-tier architecture:

1. **Data Generation:** A custom Python engine that simulates realistic, "messy" ERP transactions.
2. **Orchestration:** Apache Airflow manages the DAGs for ingestion and automated auditing.
3. **Storage Layer:** PostgreSQL utilizes a 3-tier schema architecture:
   - `stg_raw`: Landing zone for raw ingestion.
   - `stg_quarantine`: Isolated storage for records that failed integrity checks.
   - `fct_gold`: High-integrity production ledger.
4. **Service Layer:** FastAPI provides a RESTful interface for machine-to-machine data repair.
5. **Frontend Monitoring:** Streamlit provides a "CFO Dashboard" to visualize "Value at Risk" and an Audit Workbench for manual record correction.

## 🚀 Key Features

- **Automated Audit Gates:** SQL-based logic that checks for financial anomalies (e.g., $UnitCost <= 0$) and relational integrity.
- **Human-in-the-Loop Repair:** An interactive UI allowing auditors to update quarantined records and promote them to the "Gold" ledger.
- **Full Audit Trail:** Every manual edit is logged in a dedicated audit table, ensuring compliance with standard accounting practices (ACCA/SOX).
- **Type-Safe Casting:** Robust handling of data-type mismatches between Pandas-inferred types and strict PostgreSQL schemas.

## 🛠️ Quick Start (Docker)

Ensure you have Docker and Docker-Compose installed on your machine (Tested on Windows 10 IoT LTSC via WSL2).

**1. Clone the Repo:**

```bash
git clone https://github.com/YOUR_USERNAME/FOIE-Financial-Integrity-Engine.git
cd FOIE-Financial-Integrity-Engine
```

**2. Spin up the Infrastructure:**

```bash
docker-compose up -d
```

**3. Generate Initial Data:**

```bash
python3 generate_erp_data.py
```

**Access the Stack:**

- **Airflow:** [http://localhost:8080](http://localhost:8080) (admin/admin)
- **Dashboard:** [http://localhost:8501](http://localhost:8501)
- **API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

## 📈 Future Roadmap

- [ ] Implement OAuth2 authentication for the Repair API.
- [ ] Add Redis caching for high-speed dashboard telemetry.
- [ ] Integrate Great Expectations for advanced data quality profiling.

## 💡 Why this project?

This project demonstrates a full-lifecycle understanding of Data Engineering and Financial Governance. It isn't just about moving data—it's about ensuring data can be trusted for high-stakes financial decision-making.
