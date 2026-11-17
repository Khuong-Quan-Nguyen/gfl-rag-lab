# gfl-rag-lab

Does hybrid search help when questions contain exact terms? A small, measured RAG lab on
GFL Environmental's public 2024 reports.

![dashboard](docs/dashboard.png)

## Why this exists

This project picks up two open questions from Arvind Pant's Medium articles
**_Building RAG You Can Trust_** and **_Benchmarking Vector Indexes in Postgres_**, and tests them
on a corpus from his own company. It builds on his work rather than reproducing it. The chunking
rules, the four-number dashboard idea and the long-lived-service fix all come from those articles.

| His open question | What this lab does |
|---|---|
| Hybrid search barely moved MRR (0.721 → 0.729) on conceptual textbook questions. He expected it to help on "codes, names, rare words". | GFL's reports are full of exact terms: figures, facility names, years, regulatory limits. The 40-question eval set is split **20 conceptual / 20 exact-term**, and results are reported per type. |
| "Expand the eval set to 30–50 questions." | 40 questions, each labelled with the page that holds the answer. `evals/verify_questions.py` checks every label against the PDF text. |
| 7-second queries came from reloading the model on every call. | A FastAPI service loads the embedder and cross-encoder once at startup. `scripts/latency_demo.py` measures both patterns. |
| A low top similarity score means the model is "working from thin context". | A Claude answer step with an **abstain guardrail** and `[doc p.N]` citations. |
| Evals belong on the same screen as health metrics. | A Streamlit ops console with p50/p99, tokens/request, cost/day, error rate, a trace waterfall, the eval table and a low-confidence feed. |

## Results

Corpus: GFL 2024 Sustainability Report (26 pp) + 2024 Annual Report incl. AIF, MD&A and financial
statements (172 pp) → 851 chunks of ~180 words. A hit counts if it comes from the right document
within ±1 page of the labelled page. k = 10.

| Mode | MRR conceptual | MRR exact | MRR all | recall@10 all | top-1 all | p50 ms |
|---|---:|---:|---:|---:|---:|---:|
| vector | 0.487 | 0.640 | 0.564 | 0.850 | 0.450 | 15 |
| hybrid (RRF k=60) | 0.633 | 0.764 | 0.698 | 0.925 | 0.600 | 44 |
| vector + rerank | 0.653 | 0.767 | 0.710 | 0.875 | 0.625 | 920 |
| hybrid + rerank | **0.681** | **0.825** | **0.753** | **0.950** | **0.675** | 944 |

What the numbers say, without overselling them:

- **Hybrid helps exact-term questions:** MRR 0.640 → 0.764, consistent with his hypothesis.
- **It also helped conceptual questions here** (0.487 → 0.633), unlike on the textbook. A likely
  reason: annual-report prose repeats domain nouns (RNG, MRF, EPR, landfill) that MiniLM embeds
  only loosely, so keyword matching adds signal even to "how/why" questions. That is a guess, not a test.
- **The reranker gives the biggest single gain on top-1** (exact: 0.600 → 0.750 over vector), and
  combining it with hybrid is best everywhere.
- **The cost is latency.** Reranking 30 candidates on CPU takes ~0.9 s, after capping the
  cross-encoder at 256 tokens, which halved the time with identical MRR.
- With 20 questions per type, one question moves recall and top-1 by 0.05. Treat differences
  under ~0.05 as noise.

**Long-lived service:** for the same 10 questions in `hybrid_rerank` mode, p50 is **8,595 ms** when
each query starts a fresh process that loads both models (the original bug), and **956 ms** through
the service: **9.0×** faster. Pure hybrid search through the service takes ~44 ms.

**Abstain guardrail:** if the best cosine similarity is under **0.38**, the LLM is skipped and the
answer is "Not found in the GFL documents." The threshold was calibrated so 4 of 5 out-of-scope
questions fall below it (0.13–0.29) and all 40 eval questions stay above it (lowest 0.458). The fifth,
*"What is GFL's stock price today?"*, scores **0.627**: it is on-topic but unanswerable, so a similarity
threshold cannot catch it. That case is handled by the prompt rule "answer only from the passages,
otherwise reply *Not found…*".

## Architecture

```
PDFs ─► ingest.py ─► Postgres 16 + pgvector (port 5433)
         PyMuPDF blocks             documents: embedding vector(384) HNSW cosine
         drop repeated headers      + tsv tsvector GIN (generated column)
         ~180-word chunks, overlap  traces: one row per /ask
         MiniLM embed, COPY load

question ─► service.py (FastAPI, models loaded once)
              retrieval.search(mode)  vector | hybrid (RRF) | vector_rerank | hybrid_rerank
              top_score < 0.38 ? ─► "Not found in the GFL documents."
              generate.answer ─► Claude (top 5 chunks, [doc p.N] citations)
              telemetry.record ─► traces
                                        ▲
dashboard/app.py (Streamlit) ───────────┘ reads traces, eval results; calls /ask
```

| Piece | Choice |
|---|---|
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (384-d) |
| Reranker | `cross-encoder/ms-marco-MiniLM-L-6-v2`, max 256 tokens |
| Keyword | Postgres FTS; the question's stemmed terms are OR-ed (AND rarely matches a whole question) |
| Fusion | Reciprocal Rank Fusion, k = 60, vector top-50 + keyword top-50 |
| LLM | Claude (`CLAUDE_MODEL`, default `claude-opus-5-5`), low effort, server-side refusal fallback |

## Setup (Windows / PowerShell)

### 1. Postgres 16 + pgvector on port 5433

**Option A, Docker** (Linux/macOS, or Windows with Docker Desktop):

```powershell
docker compose up -d     # pgvector/pgvector:pg16, host port 5433, shm_size 1gb; applies sql/schema.sql
```

Port 5433 avoids a local Postgres on 5432, and `shm_size: 1gb` avoids Docker's 64 MB `/dev/shm`
limit during index builds. Both problems are described in the index-benchmark article.

**Option B, native Windows, no Docker or admin rights** (what this repo was built with):

```powershell
$env:MAMBA_ROOT_PREFIX = "D:\dev-cache\micromamba"
curl.exe -L -o D:\dev-cache\micromamba\micromamba.exe https://github.com/mamba-org/micromamba-releases/releases/latest/download/micromamba-win-64
D:\dev-cache\micromamba\micromamba.exe create -y -p .\.tools\pg -c conda-forge "postgresql=16" pgvector

.\scripts\db.ps1 init    # initdb into .pgdata, start on :5433, create db 'gfl', apply sql\schema.sql
.\scripts\db.ps1 start   # later sessions (stop | status | psql)
```

Both options give the same DSN: `postgresql://rag:rag@localhost:5433/gfl`.

### 2. Python environment

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install torch --index-url https://download.pytorch.org/whl/cpu
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env      # add ANTHROPIC_API_KEY to enable the answer step
```

### 3. Data

Put the public PDFs in `data/raw/` (they are not committed):

- `sustainability_2024.pdf`: https://s24.q4cdn.com/409248530/files/Sustainability/2024-Sustainability-Report.pdf
- `annual_report_2024.pdf`: https://s24.q4cdn.com/409248530/files/doc_financials/2024/ar/Annual-Report.pdf

## Run

```powershell
$py = ".\.venv\Scripts\python.exe"
& $py -m app.ingest                          # 851 chunks -> Postgres
& $py -m scripts.sanity_query "landfill gas" # top hit: sustainability_2024 p.13
& $py -m evals.verify_questions              # 40 questions, 0 problems
& $py -m evals.run_evals                     # results table + evals/results/<timestamp>.json
& $py -m scripts.calibrate_threshold         # in-scope vs out-of-scope top scores
& $py -m scripts.latency_demo                # cold vs warm p50

& $py -m uvicorn app.service:app --port 8000          # API
& $py -m streamlit run dashboard/app.py               # dashboard on http://localhost:8501
& $py -m scripts.seed_traffic                          # optional: fill traces (uses Claude tokens if a key is set)
& $py -m pytest -q                                     # 12 tests (dashboard test needs Postgres)
```

**Static showcase (Vercel):** `site/` is a static page with the results, latency, guardrail and all 40
questions. After a new eval run, refresh it with `& $py -m scripts.build_site`, then commit `site/data.js`.
`vercel.json` serves `site/` with no build step; the Python service and database stay local because
torch and a local Postgres don't fit Vercel functions.

API: `POST /ask {"question": "...", "mode": "hybrid_rerank"}` returns the answer, citations, timings
and trace_id. `POST /search` returns retrieval only. `GET /health` reports service status.

## Limitations

- **40 questions is still small.** Differences under ~0.05 are within noise. The questions and page
  labels were drafted from the page text with an AI assistant and checked automatically
  (`verify_questions.py`); a full manual review of every answer is still pending.
- **Public documents only, one year, two PDFs.** No filtered search by year yet.
- **Infographic pages extract poorly.** Multi-column layouts in the sustainability report come out
  partly jumbled, and table rows become run-on "sentences" that are split into word windows.
- **One machine, CPU only.** Latency numbers are from a 6-core desktop CPU; the reranker dominates.
- **Figures are only as accurate as the PDFs and the extraction.** Answers cite pages so they can be checked.
- **The answer step only grounds and cites.** It is not scored for faithfulness yet (see Next).

## Next

- Filtered search (`WHERE doc_year = …`) and its recall cost with HNSW vs StreamingDiskANN.
- Faithfulness scoring of generated answers against their cited chunks.
- A live Ask demo: the FastAPI service on a container host plus hosted Postgres, called from the Vercel page.

## Credits

Method and framing from Arvind Pant's articles _Building RAG You Can Trust_ and _Benchmarking Vector
Indexes in Postgres_ (Medium). Source documents © GFL Environmental Inc., used for non-commercial
research. Not affiliated with GFL.
