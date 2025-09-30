# 🌲 Wildfire Monitor – AI-Augmented Data Pipeline & Dashboard

## 🚀 Overview

Wildfire Monitor is a full-stack, AI-enhanced data platform designed to monitor, analyze, and visualize wildfire trends across the United States. It combines real-time data ingestion, remote data pipeline orchestration, modern data lake practices, and an interactive dashboard with LLM-powered natural language query capabilities.

---

## 🧱 Architecture Overview

- **Airflow + Astronomer**: Orchestrates data pipelines using **Remote Execution Agents** on AWS EKS.
- **Data Lake**: Ingested data is stored in a Bronze → Silver → Gold layered structure on AWS S3.
- **LLM Integration**: GPT-based assistant turns natural language questions into data queries and insights.
- **Go Backend**: Lightweight REST API that interfaces with gold-layer data and AI services.
- **React + Chakra UI**: Frontend dashboard with charts, maps, and AI chat assistant.
- **DuckDB**: Local SQL engine used by the API to run queries on Parquet datasets.

---

## 🗺️ Features

✅ Real-time ingestion of wildfire and weather data  
✅ Structured Bronze → Silver → Gold transformation pipeline  
✅ Astronomer Remote Execution Agents for scalable pipeline execution  
✅ Chatbot assistant for querying wildfire metrics in plain English  
✅ Interactive charts and maps  
✅ AI-generated summaries and alerts  
✅ Fully containerized local development and cloud deployment

---

## 🗂️ Folder Structure

wildfire-monitor/
├── airflow/         # Airflow DAGs and configs
├── api-server/      # Go REST API
├── ui/              # React + Chakra UI dashboard
├── data/            # Test or dev parquet files
├── infra/           # AWS IaC (EKS, S3, IAM)
└── docker-compose.yml

---

## 📦 Tech Stack

| Layer        | Technology                   |
|--------------|------------------------------|
| Orchestration | Apache Airflow + Astronomer |
| Remote Exec   | Astronomer Remote Execution Agents |
| Infra         | AWS EKS, S3, Secrets Manager |
| Transforms    | DuckDB, Pandas, Python       |
| Backend       | Go (Gin or Fiber)            |
| Frontend      | React, Chakra UI, Recharts   |
| Maps          | React Leaflet                |
| AI Assistant  | OpenAI GPT / Claude          |
| Dev Tools     | Docker, Makefile, Terraform  |

---

## 🧪 Example Prompts (AI Assistant)

- _"Are there wildfires in Texas today?"_  
- _"Which state had the most fires last week?"_  
- _"Show me trends in wind speed during fire events in California"_  
- _"Summarize the wildfire situation in the US for the past 7 days."_

---

## 🛠️ Development

### Run Locally
- [ ] `docker-compose up --build`

### Run Airflow Dev (Local Only)
- [ ] `cd airflow`
- [ ] `astro dev start`

### Run UI
- [ ] `cd ui`
- [ ] `npm install`
- [ ] `npm run dev`

---

## 🚀 Remote Execution Setup (Astronomer Agents on EKS)

> This project uses **Astronomer's Remote Execution Agents** to run Airflow tasks remotely in an EKS cluster.

### Prerequisites
- [x] AWS EKS cluster and VPC created
- [x] S3 bucket created for data lake
- [ ] IAM roles configured for Agent access to S3 + Secrets Manager

### Setup Checklist

#### 1. Generate Agent Token
- [ ] Go to Astronomer Cloud UI → Workspace → Deployment → "Remote Execution" tab
- [ ] Generate Agent Token

#### 2. Download Helm Chart Template
- [ ] Get `values.yaml` from Astronomer UI containing:
  - `agentToken`
  - `astroApiUrl`
  - `deploymentId`

#### 3. Configure IAM + Network
- [ ] Attach policies to Agent IAM role for:
  - [ ] S3: `wildfire-monitor-data`
  - [ ] SecretsManager: read-only
  - [ ] OpenAI or external APIs
- [ ] Ensure EKS nodes or pods can reach `api.astronomer.io` (NAT/VPC settings)

#### 4. Deploy the Agent to EKS
- [ ] Add Astronomer Helm repo:
  ```bash
  helm repo add astronomer https://helm.astronomer.io
  helm repo update


  5. Validate Execution
	•	Push a test DAG with a PythonOperator to Astronomer
	•	Confirm that the Agent runs the task on EKS
	•	Monitor heartbeat in Astronomer UI

⸻

### Full Task Checklist

🔧 Infrastructure Setup
- Provision AWS EKS cluster for remote execution
- Set up S3 buckets for bronze/silver/gold data layers
- Configure IAM roles for Airflow Agents and workers
- Enable AWS Secrets Manager and store sensitive keys
- Configure VPC/NAT for Agent outbound internet access

⚙️ Airflow & Data Pipeline
-	Bootstrap Airflow project using astro dev init
-	Create ingest_data_dag.py for fetching wildfire + weather data
-	Create normalize_data_dag.py for transforming bronze → silver
-	Create aggregate_data_dag.py for silver → gold aggregations
-	Add Airflow datasets for inter-DAG dependency tracking
-	Set up test data + test DAGs locally with MinIO or mock APIs

🧠 LLM / AI Assistant
-	Choose model provider (OpenAI, Claude, or Ollama)
-	Define prompt templates for SQL generation and summaries
-	Implement backend service to route prompts → LLM → SQL
-	Integrate SQL-to-DuckDB execution
-	Store/generate AI-generated summaries for the frontend
 Backend API (Go)
-	Scaffold Go project (Fiber or Gin)
-	Create REST endpoints for:
-	/api/fire-summary
-	/api/top-states
-	/api/geo-fires
-	/api/query-llm
-	/api/summary
-	Integrate with DuckDB to query local or S3-based Parquet
-	Connect to LLM for dynamic query generation
-	Add middleware (logging, CORS, rate limiting)

🌐 Frontend UI (React + Chakra)
-	Bootstrap project with Vite + Chakra UI
-	Create dashboard layout and pages
-	Build:
-	FireTrendChart.tsx (Recharts)
-	TopStatesBar.tsx
-	FireMap.tsx (React Leaflet)
-	SummaryCard.tsx
-	Chatbot.tsx
-	Connect frontend to Go API via Axios
-	Add Chakra theming and responsive design

🧪 Testing & Local Dev
-	Create docker-compose.yml for local development
-	Set up MinIO to emulate S3
-	Add test data for Parquet in each lake layer
-	Create CI pipeline for linting, tests, and build
-	Document dev setup in README.-