# My personal project

> **Dear Recruiters & Hiring team,**
> 
> This repository is actively under development, but it highlights how I approach clean code architecture, dependency injection, and resilient API handling.
> The core focus here is demonstrating production-grade software patterns—such as centralized connection factories, decoupled service wrappers, and vectorized transformations—skills that directly translate to modern data stacks like Databricks, Snowflake, Docker, and Airflow.

---

## Architectural Highlights (Case B: Dependency Injection)

This repository uses a structural hierarchy calls, Which means:
1. **The Client Factory (`common/connection.py`):** Handling client and connectivity can be a repititive task, therefore i centralize all framwwork to handle Big Query, Google-Workspace, Lark and any other header / client to perform REST API method.
2. **The Config-logy ( `config/`):** Config logic is my alternative approach instead of load env. method, my favourite way of calling secrets is by handling an entire secrets as .json, which mean, i am the only one knows how i want my password, username etc, and i use github action secrets as package loader, where i will call em in YAML later, but for now date, i stil didnt commit any YAML yet, it will be there soon.
3. **Modular Service Connectors (`common/`):** Layer-specific modules contain zero hardcoded credentials or cross-service dependencies. `lark.py` handles Lark, `mysql.py` handles MySQL—keeping modules testable and reusable on any assigned workflow.
4. **Pipeline Orchestrator (`pipelines/`):** Acts as the execution bridge, managing data lineage from extraction (`GitHub/MySQL`) to transformation (`Pandas`) and loading (`BigQuery/Lark`).

---

## Repository Structure
**Heres what a vouge text look like** ( but u can also read welcome.py as i show u how i create amd scratch all from start) 
```text
my_pipeline_repo/
├── config/
│   └── settings.py          # Environment variables & non-secret configs
├── common/
│   ├── connection.py        # Singleton client factory (SQLAlchemy & APIs)
│   ├── github.py            # GitHub REST API connector with robust pagination
│   ├── mysql.py             # SQLAlchemy 2.0 database wrapper
│   ├── bigquery.py          # BigQuery integration helpers
│   └── lark.py              # Lark Bitable record sync wrapper
├── pipelines/
│   └── workflow_pipeline.py # End-to-end orchestration bridge
├── .env.example             # Template for local environment variables
├── requirements.txt         # Minimal direct dependency manifest
└── README.md
