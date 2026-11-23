## Running Docker without external volume injection

> if we are intended to fully use local path as volume injection, we can 
> avoid `external = true` in `volumes:`. For example, inspect below yaml.  

```yaml
version: '3.8'
services:
  mysql:
    image: mysql:8.0
    container_name: local_mysql_db
    restart: always
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_ROOT_PASSWORD}
      MYSQL_DATABASE: ${DB_NAME}
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
    networks:
      - pipeline-net

  airflow:
    build:
      context: .
      dockerfile: Dockerfile.airflow
    image: airflow-local-dev:latest
    container_name: airflow_local_dev
    restart: always
    depends_on:
      - mysql
    environment:
      - AIRFLOW__CORE__EXECUTOR=LocalExecutor
      - AIRFLOW__CORE__LOAD_EXAMPLES=False
      - MYSQL_HOST=mysql
      - PYTHONPATH=/opt/airflow
      - AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=${DB_URL}
    ports:
      - "8080:8080"
    volumes:
      - ./dags:/opt/airflow/dags
      - ./config:/opt/airflow/config
      - ./pipelines:/opt/airflow/pipelines
      - ./common:/opt/airflow/common
      - ./main:/opt/airflow/main
    command: standalone
    networks:
      - pipeline-net

  pipeline:
    build: .
    image: izzo-pipeline
    container_name: python_etl_pipeline
    volumes:
      - ./config:/app/config
    depends_on:
      - mysql
    environment:
      - MYSQL_HOST=mysql
    networks:
      - pipeline-net

volumes:
  mysql_data:
    driver: local

networks:
  pipeline-net:
    driver: bridge
```

> simultaneously, this will give us this `.dockerignore` instead

```text
###############################
# caches / sys
###############################
.git/
.venv/
venv/
__pycache__/

... # and so on untill

###############################
# vol injection
###############################
.env
.env.*
# common/  
# config/
# dags/
# main/
# pipelines/
# sql/
# start_kit/

# wghat happens here: all working path are re-directed to docker container 
# instead of our git-remote position, this mean now any changes in git-remote will not take effects on docker container unless : we compose down dcker and recreate the container.
```

> and somewhere in start.yaml, we will need to writes secrets into config 
```yaml
name: compose it mayynnnnnn

on:
  #schedule:
  #  - cron: '0 0 * * *'
  workflow_dispatch:

jobs:
  run:
    runs-on: self-hosted

    steps:
      - name: Checkout repo
        uses: actions/checkout@v4

      - name: Install dependencies on runner
        run: pip install -r requirements.txt

      - name: Write Connection-Kit / Token / Header for Requests
        shell: python
        env:
          SECRET_GITHUB: ${{ secrets.GITHUB }}
          SECRET_LARK: ${{ secrets.LARK }}
          SECRET_LARKTABLE: ${{ secrets.LARKTABLE }}
          SECRET_MYSQL: ${{ secrets.MYSQL }}
          SECRET_IZZO: ${{ secrets.IZZO }}
          ENV_DB_URL: ${{ secrets.ENV_DB_URL }}
          ENV_AIRFLOW_USER: ${{ secrets.ENV_AIRFLOW_USER }}
          ENV_AIRFLOW_PASSWORD: ${{ secrets.ENV_AIRFLOW_PASSWORD }}
        run: |
          import json
          import os

          os.makedirs("config", exist_ok=True)

          secrets_map = {
              "config/git.json": os.environ.get("SECRET_GITHUB", ""),
              "config/lark.json": os.environ.get("SECRET_LARK", ""),
              "config/lark_report_tables.json": os.environ.get("SECRET_LARKTABLE", ""),
              "config/mysql.json": os.environ.get("SECRET_MYSQL", ""),
              "config/izzo.json": os.environ.get("SECRET_IZZO", ""),
          }

          db_root_password = ""
          db_name = ""

          for path, val in secrets_map.items():
              with open(path, "w", encoding="utf-8") as f:
                  f.write(val)

              if path == "config/mysql.json" and val.strip():
                  parsed = json.loads(val)
                  izzo_cfg = parsed.get("packages", {}).get("izzo", {})
                  db_root_password = izzo_cfg.get("MYSQL_PASSWORD", "")
                  db_name = izzo_cfg.get("MYSQL_DATABASE", {}).get("raw", "")

          with open(".env", "w", encoding="utf-8") as f:
              f.write(f"DB_ROOT_PASSWORD={db_root_password}\n")
              f.write(f"DB_NAME={db_name}\n")
              f.write(f"DB_URL={os.environ.get('ENV_DB_URL', '')}\n")
              f.write(f"AIRFLOW_USER={os.environ.get('ENV_AIRFLOW_USER', '')}\n")
              f.write(f"AIRFLOW_PASSWORD={os.environ.get('ENV_AIRFLOW_PASSWORD', '')}\n")
            
      - name: Writes / Create Essentials Files
        run: python -m start_kit.repo_start

      - name: Run pipeline via Docker Compose
        run: docker compose up -d --build
```