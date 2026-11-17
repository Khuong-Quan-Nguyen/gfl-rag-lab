# gfl-rag-lab

Hybrid vs. vector retrieval, reranking, and an abstaining answer step, evaluated on GFL Environmental's public reports.
Builds on Arvind Pant's articles *Building RAG You Can Trust* and *Benchmarking Vector Indexes in Postgres*.

> Work in progress — full write-up, architecture and results come at the end of the build.

## Setup (Windows / PowerShell)

### 1. Postgres 16 + pgvector on port 5433

**Option A — Docker** (Linux/macOS, or Windows with Docker Desktop):

```powershell
docker compose up -d     # pgvector/pgvector:pg16, host port 5433, shm_size 1gb; applies sql/schema.sql
```

**Option B — native Windows, no Docker, no admin** (what this repo was developed with):

```powershell
# one-time: get micromamba (single exe) and install Postgres 16 + pgvector from conda-forge into .tools\pg
$env:MAMBA_ROOT_PREFIX = "D:\dev-cache\micromamba"
curl.exe -L -o D:\dev-cache\micromamba\micromamba.exe https://github.com/mamba-org/micromamba-releases/releases/latest/download/micromamba-win-64
D:\dev-cache\micromamba\micromamba.exe create -y -p .\.tools\pg -c conda-forge "postgresql=16" pgvector

.\scripts\db.ps1 init    # initdb into .pgdata, start on :5433, create db 'gfl', apply sql\schema.sql
.\scripts\db.ps1 start   # later sessions
.\scripts\db.ps1 stop
```

Both options expose the same DSN: `postgresql://rag:rag@localhost:5433/gfl`.

### 2. Python environment

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install torch --index-url https://download.pytorch.org/whl/cpu
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env   # then fill in ANTHROPIC_API_KEY
```

### 3. Check

```powershell
.\scripts\db.ps1 psql
# gfl=> SELECT extversion FROM pg_extension WHERE extname='vector';
```
