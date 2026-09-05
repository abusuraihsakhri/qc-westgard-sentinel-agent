# Qc Westgard Sentinel Agent

> **Domain:** Clinical Decision Support & Biomedical Computing
> **Reference Guidelines & Standards:** `Standard Clinical Formulations & ISO/IEC Quality Frameworks`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

**Qc Westgard Sentinel Agent** is an advanced analytical and computational platform implementing Real-Time Multi-Rule Analytical QC & Levey-Jennings Evaluator. It provides:

- Multi-agent analytical QC layer evaluating Levey-Jennings charts against Westgard rules
- Real-time quality control monitoring with automated batch halting
- HMAC-SHA256 tamper-evident audit trail for all evaluations
- Zero-PHI outbound guard to prevent protected health information leaks

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Core Algorithmic & Evaluation Engines

- **`Severity`** — dedicated module for severity evaluation and state verification.
- **`DomainKnowledgeRegistry`**: Enterprise domain rules, guideline matrices, and evidence benchmarks.
- **`AgentAlert`** — dedicated module for agent alert evaluation and state verification.
- **`LeveyJenningsEvaluatorAgent`**: Specialized Sub-Agent 1 for Levey-Jennings chart evaluation
- **`WestgardRuleEngineAgent`**: Specialized Sub-Agent 2 for Westgard rule engine processing
- **`CalibrationDriftDetectorAgent`**: Specialized Sub-Agent 3 for calibration drift detection

### 🛡️ Enterprise Security Features

- **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
- **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
- **Input Validation:** Bounds checking on metric values and path traversal protection for file operations.

---

## 🚀 Installation

### Prerequisites
- Python 3.9 or higher
- pip package manager

### Setup
```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/qc-westgard-sentinel-agent.git
cd qc-westgard-sentinel-agent

# Install dependencies
pip install -e .

# For development (includes test dependencies)
pip install -e ".[dev]"
```

---

## 💻 CLI Quickstart & Usage

### 1. Single Case Audit
```bash
python cli.py audit --task-id CASE-001 --primary 24.5 --secondary 14.0 --critical --status DISCORDANT
```

### 2. Batch Processing
```bash
python cli.py batch -i sample.csv -o results.csv
```

### 3. Interactive Chat
```bash
python cli.py chat "What is the system status?"
```

### 4. Verify Audit Trail Integrity
```bash
python cli.py verify-audit
```

### 5. Launch REST API Server
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

### Parameter Reference
| Parameter | Description | Default |
|:----------|:------------|:--------|
| `--task-id` | Unique task/case identifier | TASK-2026-001 |
| `--target` | Target identifier | KEY-TARGET-01 |
| `--primary` | Primary metric value (float) | 28.5 |
| `--secondary` | Secondary metric value (float) | 14.2 |
| `--critical` | Critical flag (boolean) | False |
| `--status` | Status descriptor | DISCORDANT |

### Input Data Schema (CSV Batch)

| Field | Description | Requirement |
|:------|:------------|:------------|
| `task_id` | Unique task identifier | Required |
| `target_identifier` | Target/entity identifier | Required |
| `primary_metric` | Primary measurement value | Required |
| `secondary_metric` | Secondary measurement value | Optional (default: 0.0) |
| `status_descriptor` | Status code or phenotype | Optional (default: NOMINAL) |
| `is_critical_flag` | Emergency escalation flag | Optional (default: False) |

---

## 🔌 REST API Endpoints

When running the server (`python cli.py serve`), the following endpoints are available:

| Method | Endpoint | Description |
|:-------|:---------|:------------|
| `GET` | `/health` | Health check |
| `GET` | `/metrics` | Operational metrics |
| `POST` | `/api/audit` | Submit audit task |
| `POST` | `/api/chat` | Query assistant |
| `GET` | `/api/audit/logs` | Get audit trail |

### Example API Request
```bash
curl -X POST http://localhost:8000/api/audit \
  -H "Content-Type: application/json" \
  -d '{"task-id": "CASE-001", "primary_metric": 24.5, "secondary_metric": 14.0}'
```

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

### Security Configuration

Set the `AUDIT_SECRET_KEY` environment variable for production deployments to ensure secure audit signing:

```bash
# Linux/macOS
export AUDIT_SECRET_KEY="your-secure-random-key-here"

# Windows
set AUDIT_SECRET_KEY=your-secure-random-key-here
```

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

```bash
docker build -t qc-westgard-sentinel-agent .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secure-key qc-westgard-sentinel-agent
```

Or using Docker Compose:

```bash
docker-compose up -d
```

---

## 📁 Project Structure

```
qc-westgard-sentinel-agent/
├── agents/                      # Core agent modules
│   ├── __init__.py             # Package initialization
│   ├── api.py                  # FastAPI REST API server
│   ├── base.py                 # Security, PHI guard, audit trail
│   ├── learning.py             # Bayesian calibration engine
│   ├── llm_factory.py          # LLM client factory
│   ├── metrics.py              # Prometheus metrics exporter
│   ├── models.py               # Pydantic data models
│   ├── streamer.py             # WebSocket telemetry streamer
│   ├── supervisor.py           # Supervisor orchestrator
│   └── workers.py              # Specialized worker agents
├── tests/                      # Test suite
│   ├── test_enrichment.py      # Enrichment module tests
│   └── test_qc_westgard_sentinel_agent.py  # Core agent tests
├── cli.py                      # Command line interface
├── westgard_sentinel.py        # Core evaluation agents
├── simulator.py                # High-throughput simulation
├── enrichment.py               # Feature enrichment modules
├── pyproject.toml              # Project configuration
├── Dockerfile                  # Container build
├── docker-compose.yml          # Container orchestration
└── README.md                   # This file
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
