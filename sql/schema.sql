CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
  id         BIGSERIAL PRIMARY KEY,
  doc_name   TEXT NOT NULL,          -- 'sustainability_2024', 'aif_2024'
  doc_year   INT,
  page       INT NOT NULL,
  chunk_idx  INT NOT NULL,
  content    TEXT NOT NULL,
  embedding  vector(384) NOT NULL,
  tsv        tsvector GENERATED ALWAYS AS (to_tsvector('english', content)) STORED
);
CREATE INDEX IF NOT EXISTS documents_embedding_hnsw ON documents USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS documents_tsv_gin ON documents USING gin (tsv);
CREATE INDEX IF NOT EXISTS documents_doc ON documents (doc_name, doc_year);

CREATE TABLE IF NOT EXISTS traces (
  trace_id    UUID, ts TIMESTAMPTZ DEFAULT now(),
  mode        TEXT, question TEXT,
  embed_ms    REAL, retrieve_ms REAL, rerank_ms REAL, llm_ms REAL, total_ms REAL,
  top_score   REAL, n_chunks INT,
  tokens_in   INT, tokens_out INT, cost_usd REAL,
  abstained   BOOLEAN, status TEXT, error TEXT
);
